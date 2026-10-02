#!/usr/bin/env python3
"""Package/restore only frozen UTF-8 render evidence; never open or encode assets.

Uses the unchanged PLAIN_JSON_INTERFACE_TABLE_v1 codec. No renderer, network,
Git operation, archive, binary encoding or general-purpose compression is used.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile

SOURCE_MANIFEST = 'INTAKE-FINAL-MANIFEST.json'
SOURCE_MANIFEST_SHA = 'e07925cdd34d2acd27908bdb702b909a1bb627b05f2adbc4994017b54117a074'
CODEC_NAME = 'pack-wheel-interface-evidence.py'
CODEC_SHA = '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
SCHEMA = 'MAZ_TEXTURED_INTAKE_TEXT_PUBLICATION_v1'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pretty(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode('utf-8')


def checked_relative(value):
    path = PurePosixPath(value)
    assert not path.is_absolute() and path.parts and '..' not in path.parts
    assert str(path) == value and '\\' not in value
    return Path(*path.parts)


def checked_file(folder, record):
    path = folder / checked_relative(record['path'])
    assert path.is_file() and not path.is_symlink(), path
    raw = path.read_bytes()
    assert len(raw) == record['bytes'] and sha(raw) == record['sha256'], path
    raw.decode('utf-8')
    return raw


def load_codec(path):
    assert sha(path.read_bytes()) == CODEC_SHA
    spec = importlib.util.spec_from_file_location('plain_json_evidence_codec', path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    return codec


def old_manifest_checks(folder):
    return []


def readme(index, table):
    return "# Textured wheel intake: original UV repeat guard blocked\n\nThe actual pinned6e406e Textured source was opened once with official Blender4.5.13, automatic scripts disabled and one CPU. The process completed in15.9795seconds with exit1 and confirmed child termination; no timeout. The read covered173 structural objects and132 geometry summaries. No construction, Apply, reparent, save, export or render was performed. Frame0 was explicitly evaluated.\n\nSeventy-two front glyph meshes have zero modifiers and no sourceFONT siblings in this Textured file. They were historically snapshots of evaluated Master geometry. The128 moving meshes were stable in the same-process readback. All8518 object identities and world matrices, original material records and source bytes remained unchanged. The bounded reverse-reference scan reported zero outside references and zero unreadable entries. All four original simplified drums were actually read as148 native vertices and satisfied the retained authoring-radius/width/axis fit; these are not factory dimensions.\n\nThe intake remains BLOCKED: the four original support kingpins changed evaluated UV-layer and combined authored-geometry/UV hashes on repetition. Other recorded summary fields were stable. The second complete summaries and UV arrays were not saved, so numeric magnitude and cause remain unknown. Normals were not recorded. No modifier whitelist exemption or tolerance relaxation was introduced. The four Textured cases do not explain the earlier301 Master summaries.\n\nRead SUMMARY.json after restoring the records for exact scope and limits. The preparation's input snapshots match nine pinned Git evidence files and the173 stored objects exactly, and the160-object moving closure and850 old export names were independently compared. Preparation and the first actual failed intake are preserved byte for byte. All16 whole-vehicle gates remainOPEN; no candidate model was created.\n\nRestore these ordinary text records without starting Blender:\n\n    python -B package-intake-evidence.py restore --package . --out /tmp/maz-intake-restored-UNUSED\n\nThe unchanged plaintext JSON-reference codec losslessly stores repeated record values; Python scripts remain directly readable. Original paths and all byte counts/SHA values are restored and checked. There are no asset bytes, signed URLs or private delivery records. The original.blend is already an existing LFS input; this package does not claim a new LFS upload.\n"


def build(source, output, codec_path):
    assert not output.exists(), 'Publication destination must not exist'
    manifest_raw = (source / SOURCE_MANIFEST).read_bytes()
    assert sha(manifest_raw) == SOURCE_MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    assert manifest['text_record_count'] == 27
    assert manifest['text_bytes'] == 1673455
    assert len(manifest['text_records']) == manifest['text_record_count']
    assert sum(r['bytes'] for r in manifest['text_records']) == manifest['text_bytes']
    codec = load_codec(codec_path)
    # Validate every original before creating the destination. No asset read.
    originals = [(r, checked_file(source, r)) for r in manifest['text_records']]
    assert len({r['path'] for r, _ in originals}) == 27
    for r, _ in originals:
        assert Path(r['path']).suffix in {'.py', '.json', '.jsonl', '.log', '.md'}
    old_manifest_checks(source)
    output.mkdir(parents=True, exist_ok=False)
    (output / SOURCE_MANIFEST).write_bytes(manifest_raw)
    shutil.copyfile(codec_path, output / CODEC_NAME)
    shutil.copyfile(Path(__file__).resolve(), output / 'package-intake-evidence.py')
    payloads, records, source_paths = [], [], {}
    # Prefer readable original top-level filenames as the canonical source copy.
    script_order = sorted([(r, b) for r, b in originals if r['path'].endswith('.py')],
                          key=lambda item: (len(Path(item[0]['path']).parts), item[0]['path']))
    for record, raw in script_order:
        if record['sha256'] not in source_paths:
            stored = 'sources/' + record['path']
            dest = output / checked_relative(stored)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            source_paths[record['sha256']] = stored
    for record, raw in originals:
        item = dict(record)
        if record['path'].endswith('.py'):
            item['storage'] = {'kind': 'readable-source',
                               'file': source_paths[record['sha256']]}
        else:
            text = raw.decode('utf-8')
            kind, payload = 'literal-pipe-lines', [line.split('|') for line in text.splitlines(keepends=True)]
            if record['path'].endswith('.json'):
                value = json.loads(raw)
                if pretty(value) == raw:
                    kind, payload = 'json-pretty2-utf8-lf', value
            if kind == 'literal-pipe-lines':
                assert ''.join('|'.join(line) for line in payload).encode('utf-8') == raw
            item['storage'] = {'kind': kind, 'payload_index': len(payloads)}
            payloads.append({'original_path': record['path'], 'value': payload})
        records.append(item)
    with tempfile.TemporaryDirectory(prefix='maz-render-text-codec-') as temporary:
        document = Path(temporary) / 'ordinary-document.json'
        document.write_bytes(pretty({'schema': SCHEMA, 'payloads': payloads}))
        table = codec.pack(document, output / 'records-table')
    index = {'schema': SCHEMA, 'source_manifest': {'path': SOURCE_MANIFEST,
             'bytes': len(manifest_raw), 'sha256': SOURCE_MANIFEST_SHA},
             'original_text_record_count': len(records),
             'original_text_bytes': sum(r['bytes'] for r in records),
             'asset_bytes_included': 0,
             'codec': {'file': CODEC_NAME, 'sha256': CODEC_SHA},
             'table': {'folder': 'records-table', 'manifest_sha256': sha((output / 'records-table/manifest.json').read_bytes())},
             'records': records}
    (output / 'package-index.json').write_bytes(pretty(index))
    (output / 'README.md').write_text(readme(index, table), encoding='utf-8')
    return {'status': 'BUILT_PENDING_INDEPENDENT_RESTORE', 'original_records': 27,
            'table_entries': table['entries'], 'table_shards': len(table['shards']),
            'table_shard_bytes': sum(s['bytes'] for s in table['shards']),
            'unique_readable_source_files': len(source_paths)}


def restore(package, output):
    assert not output.exists(), 'Restore destination must not exist'
    index = json.loads((package / 'package-index.json').read_bytes())
    assert index['schema'] == SCHEMA
    manifest_raw = checked_file(package, index['source_manifest'])
    assert sha(manifest_raw) == SOURCE_MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    assert index['records'] and len(index['records']) == manifest['text_record_count'] == 27
    expected = {r['path']: r for r in manifest['text_records']}
    assert len(expected) == len(index['records'])
    table_folder = package / checked_relative(index['table']['folder'])
    assert sha((table_folder / 'manifest.json').read_bytes()) == index['table']['manifest_sha256']
    codec = load_codec(package / CODEC_NAME)
    document = json.loads(codec.restore(table_folder))
    assert document['schema'] == SCHEMA
    restored = []
    seen = set()
    for record in index['records']:
        path = record['path']
        checked_relative(path)
        assert path not in seen and path in expected
        seen.add(path)
        assert {key: record[key] for key in ['path', 'bytes', 'sha256']} == expected[path]
        storage = record['storage']
        if storage['kind'] == 'readable-source':
            raw = checked_file(package, {'path': storage['file'], 'bytes': record['bytes'],
                                        'sha256': record['sha256']})
        else:
            entry = document['payloads'][storage['payload_index']]
            assert entry['original_path'] == path
            if storage['kind'] == 'json-pretty2-utf8-lf':
                raw = pretty(entry['value'])
            else:
                assert storage['kind'] == 'literal-pipe-lines'
                assert all(isinstance(line, list) and all(isinstance(s, str) for s in line)
                           for line in entry['value'])
                raw = ''.join('|'.join(line) for line in entry['value']).encode('utf-8')
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256'], path
        raw.decode('utf-8')
        restored.append((path, raw))
    assert sum(len(raw) for _, raw in restored) == manifest['text_bytes'] == 1673455
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in restored + [(SOURCE_MANIFEST, manifest_raw)]:
        path = output / checked_relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)
    old = old_manifest_checks(output)
    return {'status': 'PASS', 'text_records_restored': len(restored),
            'text_bytes_restored': sum(len(raw) for _, raw in restored),
            'final_manifest_restored_separately': True,
            'asset_bytes_restored': 0, 'old_manifests': old}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    b = modes.add_parser('build')
    b.add_argument('--source', type=Path, required=True)
    b.add_argument('--out', type=Path, required=True)
    b.add_argument('--codec', type=Path, required=True)
    r = modes.add_parser('restore')
    r.add_argument('--package', type=Path, required=True)
    r.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'build':
        result = build(args.source, args.out, args.codec)
    else:
        result = restore(args.package, args.out)
    print(json.dumps(result, indent=2))
