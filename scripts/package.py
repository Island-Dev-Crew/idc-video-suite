#!/usr/bin/env python3
"""Build a portable bundle or install into a new namespaced skill directory."""
import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

def files():
    manifest = json.loads((ROOT / 'package.json').read_text())
    result = []
    for entry in manifest['files']:
        path = ROOT / entry
        if not path.exists():
            raise ValueError(f'missing manifest entry: {entry}')
        result.extend([path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts))
    return manifest, sorted(set(result))

def stage(directory):
    manifest, paths = files()
    hashes = {}
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('package input must be a regular file inside this repository')
        relative = path.relative_to(ROOT)
        data = path.read_bytes()
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[str(relative)] = hashlib.sha256(data).hexdigest()
    (directory / 'CHECKSUMS.json').write_text(json.dumps({'version': manifest['version'], 'files': hashes}, indent=2) + '\n')
    return manifest, len(paths)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['bundle', 'install', 'verify'])
    parser.add_argument('destination', type=pathlib.Path)
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    try:
        if args.mode == 'verify':
            checksum = json.loads((destination / 'CHECKSUMS.json').read_text())
            for name, expected in checksum['files'].items():
                path = destination / name
                if path.is_symlink() or not path.resolve().is_relative_to(destination) or not path.is_file():
                    raise ValueError(f'invalid or missing package file: {name}')
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    raise ValueError(f'package byte mismatch: {name}')
            actual = {str(p.relative_to(destination)) for p in destination.rglob('*') if p.is_file()
                      and '__pycache__' not in p.parts and p.name != 'CHECKSUMS.json'}
            if actual != set(checksum['files']):
                raise ValueError('package contains unrecorded or missing files')
            print(json.dumps({'status': 'bytes-verified', 'version': checksum['version'], 'files': len(actual),
                              'loaderInvocation': 'unverified'}))
            return 0
        if destination.exists():
            raise ValueError('destination exists; choose a new path to preserve installed versions')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
            root = pathlib.Path(temporary) / 'idc-video-suite'
            root.mkdir()
            manifest, count = stage(root)
            if args.mode == 'bundle':
                with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
                    for path in sorted(root.rglob('*')):
                        if path.is_file():
                            archive.write(path, path.relative_to(root.parent))
            else:
                if destination.name != 'idc-video-suite':
                    raise ValueError('install destination must end in idc-video-suite to preserve root skill name')
                shutil.copytree(root, destination)
        print(json.dumps({'version': manifest['version'], 'files': count, 'destination': str(destination),
                          'status': 'packaged' if args.mode == 'bundle' else 'copied',
                          'loaderInvocation': 'unverified'}))
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
