#!/usr/bin/env python3
"""Record local SimLUNA source identity, tools, dataset paths and file hashes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path, help='Directory containing SimLUNA.cc')
    p.add_argument('--data-file', action='append', type=Path, default=[], help='Relevant XS/cascade file; repeatable')
    a = p.parse_args()
    source = a.source.resolve()
    if not (source / 'SimLUNA.cc').is_file():
        p.error('Source must contain SimLUNA.cc')
    files = sorted(x for x in source.rglob('*') if x.is_file() and x.suffix in {'.cc', '.hh', '.txt'}
                   and not any(y.startswith('build') or y in {'.git', 'CMakeFiles'} for y in x.relative_to(source).parts))
    hashes = {str(x.relative_to(source)): hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
    report = {'source': str(source), 'source_files_sha256': hashes, 'tools': {}, 'datasets': {}, 'data_files': {}}
    for tool in ['cmake', 'geant4-config', 'root-config']:
        exe = shutil.which(tool)
        report['tools'][tool] = {'path': exe}
        if exe:
            result = subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=20)
            report['tools'][tool].update(returncode=result.returncode, version=result.stdout.strip())
    for k, v in sorted(os.environ.items()):
        if k.startswith('G4') and (k.endswith('DATA') or k == 'G4RADIATIVECAPTURE'):
            report['datasets'][k] = {'path': v, 'exists': Path(v).is_dir()}
    for x in a.data_file:
        report['data_files'][str(x.resolve())] = {'sha256': hashlib.sha256(x.read_bytes()).hexdigest(), 'bytes': x.stat().st_size}
    print(json.dumps(report, indent=2))
    return int(any(not v['exists'] for v in report['datasets'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
