#!/usr/bin/env python3
"""Independent byte-level verification of the frozen text publication package.

Invokes restoration in a distinct Python process, then compares each restored
file with the original source directly and with the pinned original manifest.
Does not import the packer or codec. Does not read or create binary assets.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

PINNED_FINAL_MANIFEST_SHA = '8c5928ae9b8b6731cab529fc5f92bb2858ccaa76c9b396221f0ae8d0f24180fd'
PINNED_CODEC_SHA = '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pretty(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def run(package, source, output):
    assert not output.exists(), 'Independent restore output must not exist'
    original_manifest_raw = (source / 'STATION0-FINAL-MANIFEST.json').read_bytes()
    assert digest(original_manifest_raw) == PINNED_FINAL_MANIFEST_SHA
    assert (package / 'STATION0-FINAL-MANIFEST.json').read_bytes() == original_manifest_raw
    assert digest((package / 'pack-wheel-interface-evidence.py').read_bytes()) == PINNED_CODEC_SHA
    manifest = json.loads(original_manifest_raw)
    command = [sys.executable, '-B', str(package / 'package-wheel-render-evidence.py'),
               'restore', '--package', str(package), '--out', str(output)]
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    assert process.returncode == 0, process.stderr
    restore_result = json.loads(process.stdout)
    records = []
    for record in manifest['text_records']:
        relative = record['path']
        original = (source / relative).read_bytes()
        restored = (output / relative).read_bytes()
        assert original == restored, relative
        assert len(restored) == record['bytes'], relative
        assert digest(restored) == record['sha256'], relative
        records.append(dict(record, independent_byte_comparison='PASS'))
    assert len(records) == 67 and sum(r['bytes'] for r in records) == 6643853
    assert (output / 'STATION0-FINAL-MANIFEST.json').read_bytes() == original_manifest_raw
    expected = {record['path'] for record in records} | {'STATION0-FINAL-MANIFEST.json'}
    actual = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}
    assert actual == expected, actual ^ expected
    old_checks = []
    for name in ['attempt-01/FREEZE-MANIFEST.json',
                 'attempt-02/FREEZE-MANIFEST.json',
                 'FINAL-TEXT-RECORDS-MANIFEST.json']:
        old = json.loads((output / name).read_bytes())
        base = (output / name).parent
        total = 0
        for record in old['files']:
            raw = (base / record['path']).read_bytes()
            assert len(raw) == record['bytes'] and digest(raw) == record['sha256']
            total += len(raw)
        assert total == old['total_bytes']
        assert len(old['files']) == old['file_count']
        old_checks.append({'path': name, 'records_verified': len(old['files']),
                           'bytes_verified': total, 'status': 'PASS'})
    index = json.loads((package / 'package-index.json').read_bytes())
    script_mappings = []
    for record in index['records']:
        if record['storage']['kind'] == 'readable-source':
            stored = record['storage']['file']
            assert (package / stored).read_bytes() == (source / record['path']).read_bytes()
            script_mappings.append({'original_path': record['path'], 'stored_path': stored,
                                    'exact_bytes': True})
    scanned = []
    # Explicit URLs/tokens only; ordinary status words are not channel IDs.
    forbidden = [re.compile(r'https?://[^\s"<>]*slack\.[^\s"<>]*', re.I),
                 re.compile(r'[?&](?:sig|signature|token|X-Amz-[A-Za-z-]+)='),
                 re.compile(r'\bxox[baprs]-[A-Za-z0-9-]+'),
                 re.compile(r'\b[CGD][A-Z0-9]{8,12}\b')]
    for path in sorted(p for p in package.rglob('*') if p.is_file()):
        assert not path.is_symlink()
        assert path.suffix in {'.json', '.py', '.md'}, path
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        assert b'\x00' not in raw, path
        for pattern in forbidden:
            for match in pattern.finditer(text):
                # Source logs contain the named engineering object CORRECTOR.
                assert match.group() == 'CORRECTOR', (str(path), 'forbidden-pattern')
        scanned.append(str(path.relative_to(package)))
    source_total = manifest['text_bytes']
    report = {
        'status': 'PASS_INDEPENDENT_PROCESS_AND_DIRECT_BYTE_COMPARISON',
        'scope': 'Text packaging only; no engine, Git, network or asset operation',
        'original_manifest_sha256': PINNED_FINAL_MANIFEST_SHA,
        'separate_process_restore_exit_code': process.returncode,
        'text_records_compared': len(records),
        'original_text_bytes': source_total,
        'extra_original_final_manifest_bytes': len(original_manifest_raw),
        'extra_original_final_manifest_exact': True,
        'asset_payload_bytes_included_or_restored': 0,
        'restored_file_set_exact': True,
        'old_failed_attempt_manifests': old_checks,
        'readable_source_mappings': script_mappings,
        'representation_counts': dict(Counter(r['storage']['kind'] for r in index['records'])),
        'plaintext_scan': {'status': 'PASS', 'files_scanned': len(scanned),
                           'private_destination_signed_url_credential_matches': 0},
        'restore_result': restore_result,
        'all_original_record_comparisons': records
    }
    (package / 'VERIFICATION.json').write_bytes(pretty(report))
    inventory = []
    for path in sorted(p for p in package.rglob('*') if p.is_file()):
        if path.name == 'PUBLICATION-FILES-MANIFEST.json':
            continue
        raw = path.read_bytes()
        inventory.append({'path': str(path.relative_to(package)), 'bytes': len(raw),
                          'sha256': digest(raw)})
    summary = {'status': 'VERIFIED_PLAINTEXT_PUBLICATION_PACKAGE',
               'self_excluded': 'PUBLICATION-FILES-MANIFEST.json',
               'file_count': len(inventory),
               'total_bytes_excluding_self': sum(r['bytes'] for r in inventory),
               'files': inventory}
    (package / 'PUBLICATION-FILES-MANIFEST.json').write_bytes(pretty(summary))
    all_bytes = sum(p.stat().st_size for p in package.rglob('*') if p.is_file())
    return {'status': 'PASS', 'text_records_exact': len(records),
            'original_text_bytes': source_total, 'original_final_manifest_extra': True,
            'old_failed_attempt_manifests_verified': len(old_checks),
            'package_files': len(inventory) + 1, 'package_total_bytes': all_bytes,
            'size_reduction_vs_original_text_bytes_percent': round(100 * (1 - all_bytes / source_total), 3),
            'restore_directory': str(output), 'asset_payload_bytes': 0,
            'publication_manifest_sha256': digest((package / 'PUBLICATION-FILES-MANIFEST.json').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    output = args.out
    if output is None:
        temporary = Path(tempfile.mkdtemp(prefix='maz-render-independent-'))
        output = temporary / 'restored'
    print(json.dumps(run(args.package.resolve(), args.source.resolve(), output.resolve()), indent=2))
