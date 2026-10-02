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

SOURCE_MANIFEST = 'FIXED-FINAL-MANIFEST.json'
SOURCE_MANIFEST_SHA = '2d7cbcbf64baf1548799de648679723ae67d959198a2b3dcd18e3fd84498aae1'
CODEC_NAME = 'pack-wheel-interface-evidence.py'
CODEC_SHA = '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
SCHEMA = 'MAZ_TEXTURED_FRONT_FIXED_TEXT_PUBLICATION_v1'


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
    return "# Saved Textured front-four native hierarchy candidate\n\nA real editable Blender candidate has been constructed and saved from the exact Textured6e source. Build:52.730708seconds/exit0; independent fresh-open:12.253417seconds/exit0. Both terminated normally without timeout. The source file stayed unchanged.\n\nThe candidate adds four native EMPTY joint frames on the retained kingpin axes, parents the original carriers and stationary brakes under those frames, and places each original simplified drum under its existing wheel spin. It changes the four spin modes from QUATERNION to XYZ, matching their unchanged original Euler action channels. The eight former parent-coordinate carrier/brake actions are detached but preserved with fake users; all552 original action key/handle records are unchanged. No vertex or face construction, modifier Apply, part deletion, relocation of other systems or new font was used.\n\nAll128 moving meshes preserve their local geometry, UV, real corner/vertex/polygon normals, topology and materials exactly. Neutral world vertex error is at most0.070460micrometres, below the original2micrometre gate. Four wheels at0.731 and pi radians produce eight actual fixed-frame rotations: maximum rigid error0.315052micrometres and radius-path error0.201747micrometres, below the original20micrometre gates. Each drum and tyre actually moves; all fixed brake geometry has0 displacement. Each finite property trial restores exactly. These are samples, not a continuous mechanical proof.\n\nAll8518 original objects remain,12 parent edges change, and8358 outside neutral matrices stay exact. All82 materials and132 selected raw meshes remain unchanged in the build. The saved file fresh-opens with8522 objects, all saved world matrices and parent edges exact, all552 original action key records exact,132 raw/128 evaluated meshes exact, and the selected original material node graphs unchanged. Packed image resources were checked before saving.\n\nBinary:100052636bytes, SHA-256 48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea. It currently exists only in the authorized cloud workspace as fixed-01/MAZ543A_Textured_Front_Wheel_Parent_Study.blend. Delivery status is LOCAL_ONLY_LFS_BLOCKED: no GitHub binary upload or missing-entity pointer is claimed. The full recipe and verification evidence below are published and replayable against the existing tracked6e asset.\n\nGlobal timeline playback remains BLOCKED and was not executed: trial01's nine-node preflight failure is preserved separately in5e36960f. This stage holds frame0 and does not give arbitrary NODES or SUBSURF permission. Activating matching Euler mode is a concrete edit, not evidence that frames31/91, steering, CV, suspension installation or continuous mechanics pass. The original exact132-mesh MetricUV intake remains BLOCKED; the four original support meshes retain their known evaluated UV differences while their raw data, positions, full recorded topology and actual normals are protected. All16 vehicle gates remain OPEN. No fresh render, GLB export or browser validation occurred in this stage.\n\nRestore all frozen text into a new unused directory:\n\n    python -B package-fixed-evidence.py restore --package . --out /tmp/maz-fixed-restored-UNUSED\n\nThe ordinary JSON value/reference tables preserve scripts, inputs, exact evidence, original logs, both terminal processes and the independent result review. No blend/PNG/GLB bytes are encoded. Source asset paths remain explicit; ordinary engine launches require a coordinated cloud compute window, not renewed user permission.\n"


def build(source, output, codec_path):
    assert not output.exists(), 'Publication destination must not exist'
    manifest_raw = (source / SOURCE_MANIFEST).read_bytes()
    assert sha(manifest_raw) == SOURCE_MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    assert manifest['text_record_count'] == 42
    assert manifest['text_bytes'] == 2647291
    assert len(manifest['text_records']) == manifest['text_record_count']
    assert sum(r['bytes'] for r in manifest['text_records']) == manifest['text_bytes']
    codec = load_codec(codec_path)
    # Validate every original before creating the destination. No asset read.
    originals = [(r, checked_file(source, r)) for r in manifest['text_records']]
    assert len({r['path'] for r, _ in originals}) == 42
    for r, _ in originals:
        assert Path(r['path']).suffix in {'.py', '.json', '.jsonl', '.log', '.md'}
    old_manifest_checks(source)
    output.mkdir(parents=True, exist_ok=False)
    (output / SOURCE_MANIFEST).write_bytes(manifest_raw)
    shutil.copyfile(codec_path, output / CODEC_NAME)
    shutil.copyfile(Path(__file__).resolve(), output / 'package-fixed-evidence.py')
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
    return {'status': 'BUILT_PENDING_INDEPENDENT_RESTORE', 'original_records': 42,
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
    assert index['records'] and len(index['records']) == manifest['text_record_count'] == 42
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
    assert sum(len(raw) for _, raw in restored) == manifest['text_bytes'] == 2647291
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
