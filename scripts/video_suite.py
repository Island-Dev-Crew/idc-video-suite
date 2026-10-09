#!/usr/bin/env python3
"""Dependency-free, bounded companion tools for IDC Video Suite."""
import argparse
import hashlib
import json
import math
import os
import stat
from contextlib import contextmanager, ExitStack
import pathlib
import re
import subprocess
import sys

MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_WORDS = 100000
MAX_SOURCES = 32
MAX_DURATION_MS = 14400000
MAX_MEDIA_BYTES = 100 * 1024**3
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$')

class Invalid(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise Invalid(message)

def stamp(details):
    return (details.st_dev, details.st_ino, details.st_size, details.st_mtime_ns, details.st_ctime_ns)

@contextmanager
def regular_fd(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        details = os.fstat(descriptor)
        require(stat.S_ISREG(details.st_mode), 'input must be a regular file')
        require(details.st_size <= limit, 'input exceeds byte limit')
        yield descriptor
    finally:
        os.close(descriptor)

def read_json(path):
    def duplicate_safe(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'duplicate JSON key: {key}')
            result[key] = value
        return result
    with regular_fd(path, MAX_JSON_BYTES) as descriptor:
        before = os.fstat(descriptor)
        # fdopen keeps custody while the descriptor context owns closure.
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        require(len(raw) <= MAX_JSON_BYTES, 'JSON exceeds 8 MiB limit')
        require(stamp(before) == stamp(os.fstat(descriptor)), 'JSON changed during read')
    value = json.loads(raw, object_pairs_hook=duplicate_safe,
                       parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f'nonfinite JSON: {value}')))
    require(isinstance(value, dict), 'document must be an object')
    return value

def integer(value, where):
    require(type(value) is int and 0 <= value <= MAX_DURATION_MS, f'{where} must be an integer millisecond time within 4 hours')
    return value

def nonempty(value, where, limit=4096):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit, f'{where} must be nonempty text up to {limit} characters')
    return value

def records(value, where, maximum):
    require(isinstance(value, list) and len(value) <= maximum, f'{where} must be an array of at most {maximum} records')
    require(all(isinstance(x, dict) for x in value), f'{where} entries must be objects')
    return value

def identified(items, where):
    result = {}
    for item in items:
        ident = item.get('id')
        require(isinstance(ident, str) and ID.fullmatch(ident), f'{where}: invalid id')
        require(ident not in result, f'{where}: duplicate id {ident}')
        result[ident] = item
    return result

def schema(doc, expected):
    require(doc.get('schemaVersion') == expected, f'schemaVersion must be {expected}')

def validate_transcript(doc):
    schema(doc, 'idc.video-transcript/1')
    sources = identified(records(doc.get('sources'), 'sources', MAX_SOURCES), 'sources')
    require(bool(sources), 'at least one source is required')
    total_words = 0
    for ident, source in sources.items():
        nonempty(source.get('name'), f'{ident}.name', 256)
        duration = integer(source.get('durationMs'), f'{ident}.durationMs')
        require(duration > 0, 'source duration must be positive')
        words = records(source.get('words'), f'{ident}.words', MAX_WORDS)
        total_words += len(words)
        require(total_words <= MAX_WORDS, 'project exceeds 100000 words')
        previous = -1
        for i, word in enumerate(words):
            start = integer(word.get('startMs'), f'{ident}.words[{i}].startMs')
            end = integer(word.get('endMs'), f'{ident}.words[{i}].endMs')
            require(previous <= start < end <= duration, f'{ident}.words[{i}]: unordered or out-of-bounds word')
            nonempty(word.get('text'), f'{ident}.words[{i}].text', 512)
            previous = start
    return {'sources': len(sources), 'words': total_words, 'status': 'structurally-valid',
            'notVerified': ['transcription accuracy', 'speaker identity', 'capture synchronization']}

def hash_fd(descriptor):
    before = os.fstat(descriptor)
    require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_MEDIA_BYTES, 'media must be a regular file under 100 GiB')
    os.lseek(descriptor, 0, os.SEEK_SET)
    h = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(descriptor, min(1024 * 1024, MAX_MEDIA_BYTES + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        require(total <= MAX_MEDIA_BYTES, 'media exceeds 100 GiB limit')
        h.update(chunk)
    after = os.fstat(descriptor)
    require(stamp(before) == stamp(after) and total == after.st_size, 'media changed during hash')
    return h.hexdigest(), stamp(after)

def hash_file(path):
    with regular_fd(path, MAX_MEDIA_BYTES) as descriptor:
        digest, identity = hash_fd(descriptor)
        with regular_fd(path, MAX_MEDIA_BYTES) as named:
            require(stamp(os.fstat(named)) == identity, 'named media changed during hash')
        return digest

def relative_parts(value):
    text = nonempty(value, 'localPath')
    require(not text.startswith('/') and '\\' not in text and '\x00' not in text,
            'localPath must be a safe project-relative path')
    parts = text.split('/')
    require(all(part not in ('', '.', '..') for part in parts), 'localPath contains unsafe components')
    require(pathlib.PurePosixPath(text).suffix.lower() in ('.mp4', '.mov', '.m4v', '.mkv', '.webm'),
            'binding must name a supported video container')
    return parts

@contextmanager
def media_fd(project, parts):
    with ExitStack() as stack:
        directory = os.open(project, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        for part in parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            stack.callback(os.close, directory)
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        stack.callback(os.close, descriptor)
        details = os.fstat(descriptor)
        require(stat.S_ISREG(details.st_mode) and details.st_size <= MAX_MEDIA_BYTES,
                'media must be a regular file under 100 GiB')
        yield descriptor

def validate_bindings(doc, verify_media=False, project=None):
    schema(doc, 'idc.video-bindings/1')
    sources = records(doc.get('sources'), 'bindings.sources', MAX_SOURCES)
    require(bool(sources), 'at least one binding is required')
    require(not verify_media or project is not None, '--verify-media requires --project')
    seen = set()
    for record in sources:
        source = record.get('sourceId')
        require(isinstance(source, str) and ID.fullmatch(source) and source not in seen, 'invalid or duplicate source binding')
        seen.add(source)
        parts = relative_parts(record.get('localPath'))
        digest = record.get('sha256')
        require(isinstance(digest, str) and re.fullmatch('[0-9a-fA-F]{64}', digest), 'sha256 must contain 64 hexadecimal characters')
        require(record.get('audioMode') in ('source', 'silent'), 'audioMode must be source or silent')
        if verify_media:
            with media_fd(project, parts) as descriptor:
                actual, identity = hash_fd(descriptor)
                require(actual == digest.lower(), f'source bytes changed: {source}')
                # Rewalk components to bind the advertised name to inspected bytes.
                with media_fd(project, parts) as named:
                    require(stamp(os.fstat(named)) == identity, f'named media changed: {source}')
    return {'status': 'bytes-verified' if verify_media else 'structurally-valid', 'bindings': len(seen)}

def compile_style(doc):
    schema(doc, 'idc.video-feedback/1')
    feedback = identified(records(doc.get('feedback'), 'feedback', 5000), 'feedback')
    rules = []
    for ident, item in feedback.items():
        for field in ('projectId', 'targetId', 'note'):
            nonempty(item.get(field), f'{ident}.{field}')
        integer(item.get('timestampMs'), f'{ident}.timestampMs')
        require(item.get('status') in ('pending', 'accepted', 'rejected'), f'{ident}: invalid status')
        require(type(item.get('reusable')) is bool, f'{ident}: reusable must be boolean')
        if item['status'] == 'accepted' and item['reusable']:
            text = nonempty(item.get('rule'), f'{ident}.rule')
            rules.append({'id': ident, 'text': text, 'sourceFeedbackId': ident,
                          'projectId': item['projectId'], 'targetId': item['targetId'], 'timestampMs': item['timestampMs']})
    return {'schemaVersion': 'idc.video-style/1', 'rules': rules,
            'enforcement': 'advisory; explicit project instructions take precedence',
            'provenance': 'accepted reusable feedback only; no model inference or auto-acceptance'}

def quality(path, expected_ms=None):
    p = pathlib.Path(path).absolute()
    with regular_fd(p, MAX_MEDIA_BYTES) as descriptor:
        digest, identity = hash_fd(descriptor)
        require(os.fstat(descriptor).st_size > 0, 'export is empty')
        os.lseek(descriptor, 0, os.SEEK_SET)
        completed = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
            'format=duration:stream=codec_type,codec_name,width,height', '-of', 'json', f'/dev/fd/{descriptor}'],
            pass_fds=(descriptor,), capture_output=True, text=True, timeout=60, check=True)
        require(stamp(os.fstat(descriptor)) == identity, 'export changed during probe')
        with regular_fd(p, MAX_MEDIA_BYTES) as named:
            require(stamp(os.fstat(named)) == identity, 'named export changed during probe')
    require(len(completed.stdout) <= MAX_JSON_BYTES, 'ffprobe output exceeds limit')
    probe = json.loads(completed.stdout)
    duration = float(probe['format']['duration']) * 1000
    require(math.isfinite(duration) and duration > 0, 'invalid export duration')
    videos = [stream for stream in probe.get('streams', []) if stream.get('codec_type') == 'video']
    require(bool(videos), 'export has no video stream')
    require(all(stream.get('width', 0) > 0 and stream.get('height', 0) > 0 for stream in videos), 'invalid video dimensions')
    if expected_ms is not None:
        require(abs(duration - expected_ms) <= 100, 'export duration differs by more than 100 ms')
    return {'schemaVersion': 'idc.video-container-probe/1', 'status': 'container-probed', 'path': str(p),
            'sha256': digest, 'durationMs': round(duration), 'streams': probe['streams'],
            'notVerified': ['full decode', 'lip sync', 'visual quality', 'captions accuracy', 'music absence', 'platform acceptance']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    transcript = commands.add_parser('transcript')
    transcript.add_argument('document')
    binding = commands.add_parser('bindings')
    binding.add_argument('document')
    binding.add_argument('--verify-media', action='store_true')
    binding.add_argument('--project', type=pathlib.Path)
    style = commands.add_parser('style')
    style.add_argument('feedback')
    quality_parser = commands.add_parser('quality')
    quality_parser.add_argument('export')
    quality_parser.add_argument('--expected-ms', type=int)
    args = parser.parse_args()
    try:
        if args.command == 'transcript':
            result = validate_transcript(read_json(args.document))
        elif args.command == 'bindings':
            result = validate_bindings(read_json(args.document), args.verify_media, args.project)
        elif args.command == 'style':
            result = compile_style(read_json(args.feedback))
        else:
            result = quality(args.export, args.expected_ms)
        print(json.dumps(result, indent=2))
    except (Invalid, ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
