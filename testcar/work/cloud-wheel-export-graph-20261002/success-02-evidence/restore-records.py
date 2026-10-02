"""Restore all original read-only graph records, with exact byte verification."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath


def safe_path(name):
    path = PurePosixPath(name)
    assert path.parts and not path.is_absolute() and '..' not in path.parts
    assert str(path) == name and '\\' not in name
    return Path(*path.parts)


def restore(folder, destination):
    assert not destination.exists(), 'Destination must be new'
    manifest = json.loads((folder / 'original-records.json').read_bytes())
    assert manifest['schema'] == 'MAZ_GRAPH_RUN02_TEXTS_V1'
    assert manifest['records_count'] == len(manifest['records']) == 15
    codec = folder / 'pack-wheel-interface-evidence.py'
    assert hashlib.sha256(codec.read_bytes()).hexdigest() == manifest['codec_sha256'] == '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
    spec = importlib.util.spec_from_file_location('graph_text_table_codec', codec)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payloads = json.loads(module.restore(folder / 'records-table'))
    assert len(payloads) == manifest['large_records'] == 6
    expected_large = {r['path'] for r in manifest['records'] if r['storage'] == 'plain-json-table'}
    assert set(payloads) == expected_large
    seen = set()
    originals = []
    for record in manifest['records']:
        name = record['path']
        relative = safe_path(name)
        assert name not in seen
        seen.add(name)
        if record['storage'] == 'plain-json-table':
            assert record['serialization'] == 'indent2 ensure_ascii=False plus LF'
            raw = (json.dumps(payloads[name], indent=2, ensure_ascii=False) + '\n').encode()
        else:
            assert record['storage'] == 'direct'
            source = folder / 'raw' / relative
            assert source.is_file() and not source.is_symlink()
            raw = source.read_bytes()
        raw.decode('utf-8')
        assert len(raw) == record['bytes'], name
        assert hashlib.sha256(raw).hexdigest() == record['sha256'], name
        originals.append((relative, raw))
    assert sum(len(raw) for _, raw in originals) == manifest['original_bytes']
    destination.mkdir(parents=True, exist_ok=False)
    for relative, raw in originals:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
    return {'status': 'ALL_ORIGINAL_TEXT_BYTES_EXACT', 'records': len(originals),
            'bytes': manifest['original_bytes'], 'asset_bytes': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(restore(args.package, args.out)))
