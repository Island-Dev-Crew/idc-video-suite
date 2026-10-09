import copy
import hashlib
import importlib.util
import json
import pathlib
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('suite', ROOT / 'scripts/video_suite.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)

def transcript():
    return json.loads((ROOT/'examples/transcript.json').read_text())

def feedback():
    return json.loads((ROOT/'examples/feedback.json').read_text())

class IntakeTests(unittest.TestCase):
    def test_valid_and_empty_transcript_remain_unverified(self):
        doc = transcript()
        self.assertEqual(suite.validate_transcript(doc)['words'], 1)
        doc['sources'][0]['words'] = []
        self.assertIn('transcription accuracy', suite.validate_transcript(doc)['notVerified'])

    def test_word_bounds_and_boolean_times_rejected(self):
        for field, value in [('startMs', True), ('startMs', -1), ('endMs', 6000), ('endMs', 100)]:
            doc = transcript()
            doc['sources'][0]['words'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(suite.Invalid):
                suite.validate_transcript(doc)

    def test_sources_unique_and_words_ordered(self):
        doc = transcript()
        doc['sources'].append(copy.deepcopy(doc['sources'][0]))
        with self.assertRaises(suite.Invalid): suite.validate_transcript(doc)
        doc = transcript()
        doc['sources'][0]['words'].append({'text':'next', 'startMs':0,'endMs':50})
        with self.assertRaises(suite.Invalid): suite.validate_transcript(doc)

    def test_duplicate_keys_nonfinite_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp)/'input.json'
            for content in ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}']:
                path.write_text(content)
                with self.assertRaises(suite.Invalid): suite.read_json(path)
            with path.open('wb') as stream: stream.truncate(suite.MAX_JSON_BYTES+1)
            with self.assertRaises(suite.Invalid): suite.read_json(path)

    def test_word_count_bounded(self):
        doc = transcript()
        doc['sources'][0]['words'] = [{}] * (suite.MAX_WORDS+1)
        with self.assertRaises(suite.Invalid): suite.validate_transcript(doc)

class BoundariesTests(unittest.TestCase):
    def test_source_count_duration_and_id_boundaries(self):
        doc = transcript()
        doc['sources'][0]['id'] = 'a' * 100
        doc['sources'][0]['durationMs'] = 14400000
        suite.validate_transcript(doc)
        for field, value in [('id','a'*101),('durationMs',14400001)]:
            changed=copy.deepcopy(doc);changed['sources'][0][field]=value
            with self.assertRaises(suite.Invalid): suite.validate_transcript(changed)
        doc['sources']=[dict(doc['sources'][0],id=f'cam{i}') for i in range(32)]
        suite.validate_transcript(doc)
        doc['sources'].append(dict(doc['sources'][0],id='cam33'))
        with self.assertRaises(suite.Invalid): suite.validate_transcript(doc)

    def test_json_fifo_and_symlink_rejected_without_wait(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);actual=root/'input.json';actual.write_text('{}')
            link=root/'link.json';link.symlink_to(actual)
            fifo=root/'pipe.json';os.mkfifo(fifo)
            for path in (link,fifo):
                with self.assertRaises((OSError,suite.Invalid)): suite.read_json(path)

    def test_json_read_detects_concurrent_growth(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'input.json';p.write_text('{}')
            original=suite.os.fstat
            calls=0
            def mutate(fd):
                nonlocal calls
                calls+=1
                if calls==3: p.write_text('{"changed":true}')
                return original(fd)
            with patch.object(suite.os,'fstat',side_effect=mutate):
                with self.assertRaises(suite.Invalid): suite.read_json(p)

class BindingTests(unittest.TestCase):
    def test_exact_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'camera.mp4';p.write_bytes(b'original')
            doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':p.name,'sha256':hashlib.sha256(b'original').hexdigest(),'audioMode':'source'}]}
            self.assertEqual(suite.validate_bindings(doc, True, tmp)['status'],'bytes-verified')
            p.write_bytes(b'changed')
            with self.assertRaises(suite.Invalid): suite.validate_bindings(doc, True, tmp)

    def test_paths_and_modes_rejected(self):
        doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':'/absolute.mp4','sha256':'a'*64,'audioMode':'source'}]}
        with self.assertRaises(suite.Invalid): suite.validate_bindings(doc)
        doc['sources'][0]['localPath']='unused/file.mp4'
        doc['sources'][0]['audioMode']='music'
        with self.assertRaises(suite.Invalid): suite.validate_bindings(doc)

    def test_structural_result_never_claims_bytes_verified(self):
        doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':'unused/file.mp4','sha256':'a'*64,'audioMode':'silent'}]}
        self.assertEqual(suite.validate_bindings(doc)['status'],'structurally-valid')

    def test_project_required_and_unsafe_paths_rejected(self):
        doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':'raw/a.mp4','sha256':'a'*64,'audioMode':'silent'}]}
        with self.assertRaises(suite.Invalid): suite.validate_bindings(doc,True)
        for path in ('/tmp/a.mp4','../a.mp4','raw/../a.mp4','raw//a.mp4','raw/./a.mp4','raw\\a.mp4','a.wav'):
            doc['sources'][0]['localPath']=path
            with self.subTest(path=path),self.assertRaises(suite.Invalid): suite.validate_bindings(doc)
        doc['sources']=[dict(doc['sources'][0],sourceId=f'cam{i}',localPath='a.mp4') for i in range(33)]
        with self.assertRaises(suite.Invalid): suite.validate_bindings(doc)

    def test_symlink_components_and_fifo_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);(root/'raw').mkdir();actual=root/'raw/a.mp4';actual.write_bytes(b'original')
            (root/'alias').symlink_to(root/'raw',target_is_directory=True)
            (root/'raw/link.mp4').symlink_to(actual)
            os.mkfifo(root/'raw/pipe.mp4')
            doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':'a.mp4','sha256':hashlib.sha256(b'original').hexdigest(),'audioMode':'source'}]}
            for path in ('alias/a.mp4','raw/link.mp4','raw/pipe.mp4'):
                doc['sources'][0]['localPath']=path
                with self.subTest(path=path),self.assertRaises((OSError,suite.Invalid)):
                    suite.validate_bindings(doc,True,root)

    def test_media_mutation_and_name_swap_rejected(self):
        for mode in ('mutate','replace'):
            with tempfile.TemporaryDirectory() as tmp:
                root=pathlib.Path(tmp);p=root/'a.mp4';p.write_bytes(b'original')
                doc={'schemaVersion':'idc.video-bindings/1','sources':[{'sourceId':'cam','localPath':'a.mp4','sha256':hashlib.sha256(b'original').hexdigest(),'audioMode':'source'}]}
                original=suite.os.read
                changed=False
                def read(fd,n):
                    nonlocal changed
                    data=original(fd,n)
                    if not changed:
                        changed=True
                        if mode=='mutate': p.write_bytes(b'changed')
                        else:
                            other=root/'swap.mp4';other.write_bytes(b'original');os.replace(other,p)
                    return data
                with patch.object(suite.os,'read',side_effect=read):
                    with self.subTest(mode=mode),self.assertRaises(suite.Invalid): suite.validate_bindings(doc,True,root)

class FeedbackTests(unittest.TestCase):
    def test_only_accepted_reusable_feedback_is_learned(self):
        doc=feedback()
        original=copy.deepcopy(doc)
        self.assertEqual([r['id'] for r in suite.compile_style(doc)['rules']],['f1'])
        self.assertEqual(doc,original)
        for status,reusable in [('pending',True),('rejected',True),('accepted',False)]:
            doc['feedback'][0].update(status=status,reusable=reusable)
            self.assertEqual(suite.compile_style(doc)['rules'],[])

    def test_invalid_status_or_inferred_reusability_rejected(self):
        for field,value in [('status','approved-by-model'),('reusable','true'),('timestampMs',-1)]:
            doc=feedback();doc['feedback'][0][field]=value
            with self.assertRaises(suite.Invalid): suite.compile_style(doc)

class QualityTests(unittest.TestCase):
    def test_probe_reports_limits_and_mismatched_duration_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'export.mp4';p.write_bytes(b'mock container')
            result=subprocess.CompletedProcess([],0,json.dumps({'format':{'duration':'1'},'streams':[{'codec_type':'video','codec_name':'h264','width':1280,'height':720}]}),'')
            with patch.object(suite.subprocess,'run',return_value=result):
                report=suite.quality(p,1000)
                self.assertEqual(report['status'],'container-probed')
                self.assertEqual(report['schemaVersion'],'idc.video-container-probe/1')
                self.assertIn('music absence',report['notVerified'])
                with self.assertRaises(suite.Invalid): suite.quality(p,2000)

class DistributionTests(unittest.TestCase):
    def run_package(self,*args):
        return subprocess.run([sys.executable,str(ROOT/'scripts/package.py'),*map(str,args)],capture_output=True,text=True)

    def test_install_verify_tamper_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=pathlib.Path(tmp)/'idc-video-suite'
            self.assertEqual(self.run_package('install',target).returncode,0)
            self.assertEqual(self.run_package('verify',target).returncode,0)
            self.assertNotEqual(self.run_package('install',target).returncode,0)
            (target/'skills/cut/SKILL.md').write_text('tampered')
            self.assertNotEqual(self.run_package('verify',target).returncode,0)

    def test_bundle_contains_no_proprietary_assets(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            target=pathlib.Path(tmp)/'suite.zip'
            self.assertEqual(self.run_package('bundle',target).returncode,0)
            with zipfile.ZipFile(target) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('idc-video-suite/CHECKSUMS.json',archive.namelist())
                self.assertFalse(any(n.endswith(('.mp4','.png','.wav','.lut')) for n in archive.namelist()))

    def test_skill_metadata_and_local_references(self):
        import re
        for p in [ROOT/'SKILL.md', *sorted((ROOT/'skills').glob('*/SKILL.md'))]:
            text=p.read_text()
            expected='idc-video-suite' if p.parent==ROOT else p.parent.name
            self.assertTrue(text.startswith(f'---\nname: {expected}\n'),str(p))
            self.assertTrue((p.parent/'agents/openai.yaml').is_file(),str(p))
            for ref in re.findall(r'\]\(([^)]+)\)',text):
                if not ref.startswith('http'): self.assertTrue((p.parent/ref).exists(),ref)

if __name__=='__main__': unittest.main()
