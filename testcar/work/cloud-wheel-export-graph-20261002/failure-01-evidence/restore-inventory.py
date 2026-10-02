"""Restore the exact UTF-8 native inventory from ordinary JSON value tables."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def restore(folder, destination):
    assert not destination.exists(), 'Destination must be new'
    codec = folder / 'pack-wheel-interface-evidence.py'
    assert hashlib.sha256(codec.read_bytes()).hexdigest() == '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
    spec = importlib.util.spec_from_file_location('graph_text_table_codec', codec)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = json.loads(module.restore(folder / 'object-inventory-table'))
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    manifest = json.loads((folder / 'original-records.json').read_bytes())
    records = [r for r in manifest['records'] if r['path'] == 'native/object-inventory.json']
    assert len(records) == 1
    record = records[0]
    assert len(raw) == record['bytes'] == 10668164
    assert hashlib.sha256(raw).hexdigest() == record['sha256'] == '3c9d293ee551a1ab6dfa93c6c82ce98634e1997c8ed691f94d534169e434feb3'
    assert len(value) == 8522
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(raw)
    return {'bytes': len(raw), 'sha256': record['sha256'], 'objects': len(value)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(restore(args.package, args.out)))
