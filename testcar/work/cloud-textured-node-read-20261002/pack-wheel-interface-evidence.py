"""Pack ordinary interface JSON into readable, interned JSON tables; no assets.

The decoded document must recover the exact original UTF-8 JSON bytes. Table
entries refer only backwards, and contain plain JSON values rather than binary
or compressed strings. This does not encode Blender/mesh/image files.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(b):
    return hashlib.sha256(b).hexdigest()


def wire(v):
    return (json.dumps(v, ensure_ascii=True, separators=(',', ':')) + '\n').encode()


def pack(source, folder):
    raw = source.read_bytes()
    document = json.loads(raw)
    assert (json.dumps(document, indent=2) + '\n').encode() == raw
    nodes, seen = [], {}
    def intern(value):
        key = wire(value)
        if key in seen:
            return seen[key]
        if isinstance(value, dict):
            item = ['object', [[k, intern(v)] for k, v in value.items()]]
        elif isinstance(value, list):
            item = ['array', [intern(v) for v in value]]
        else:
            item = ['value', value]
        index = len(nodes)
        nodes.append(item)
        seen[key] = index
        return index
    root = intern(document)
    folder.mkdir(parents=True, exist_ok=False)
    shards, current, start = [], [], 0
    def flush():
        nonlocal current, start
        if not current:
            return
        b = wire({'start_index': start, 'entries': current})
        filename = f'entries-{len(shards):03d}.json'
        (folder / filename).write_bytes(b)
        shards.append({'file': filename, 'start_index': start, 'entries': len(current),
                       'bytes': len(b), 'sha256': sha(b)})
        start += len(current)
        current = []
    for item in nodes:
        if current and len(wire({'start_index': start, 'entries': current + [item]})) > 110000:
            flush()
        current.append(item)
    flush()
    manifest = {'schema': 'PLAIN_JSON_INTERFACE_TABLE_v1', 'root': root, 'entries': len(nodes),
                'original_bytes': len(raw), 'original_sha256': sha(raw),
                'serialization': 'Python json.dumps(indent=2, ensure_ascii=True) plus LF', 'shards': shards}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    assert restore(folder) == raw
    return manifest


def restore(folder):
    m = json.loads((folder / 'manifest.json').read_bytes())
    assert m['schema'] == 'PLAIN_JSON_INTERFACE_TABLE_v1'
    nodes = []
    for shard in m['shards']:
        filename = shard['file']
        assert Path(filename).name == filename
        raw = (folder / filename).read_bytes()
        assert len(raw) == shard['bytes'] and sha(raw) == shard['sha256']
        j = json.loads(raw)
        assert j['start_index'] == shard['start_index'] == len(nodes)
        assert len(j['entries']) == shard['entries']
        nodes.extend(j['entries'])
    assert len(nodes) == m['entries']
    values = []
    def ref(i):
        assert type(i) is int and 0 <= i < len(values)
        return values[i]
    for tag, payload in nodes:
        if tag == 'value':
            assert not isinstance(payload, (list, dict))
            value = payload
        elif tag == 'array':
            value = [ref(i) for i in payload]
        else:
            assert tag == 'object'
            assert all(isinstance(k, str) for k, _ in payload)
            assert len({k for k, _ in payload}) == len(payload)
            value = {k: ref(i) for k, i in payload}
        values.append(value)
    assert type(m['root']) is int and 0 <= m['root'] < len(values)
    raw = (json.dumps(values[m['root']], indent=2) + '\n').encode()
    assert len(raw) == m['original_bytes'] and sha(raw) == m['original_sha256']
    return raw


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='mode', required=True)
    e = sub.add_parser('pack'); e.add_argument('--input', type=Path, required=True); e.add_argument('--out', type=Path, required=True)
    d = sub.add_parser('restore'); d.add_argument('--input', type=Path, required=True); d.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.mode == 'pack':
        m = pack(a.input, a.out)
        print(json.dumps({'shards': len(m['shards']), 'bytes': sum(s['bytes'] for s in m['shards']), 'original_sha256': m['original_sha256']}))
    else:
        assert not a.out.exists()
        raw = restore(a.input)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open('xb') as f:
            f.write(raw)
        print(json.dumps({'bytes': len(raw), 'sha256': sha(raw)}))
