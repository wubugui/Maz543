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

SOURCE_MANIFEST = 'STATION0-FINAL-MANIFEST.json'
SOURCE_MANIFEST_SHA = '8c5928ae9b8b6731cab529fc5f92bb2858ccaa76c9b396221f0ae8d0f24180fd'
CODEC_NAME = 'pack-wheel-interface-evidence.py'
CODEC_SHA = '2334d0734b5e6edbd289692be6d4c8da50daba4b3f770142400971c75091a11d'
SCHEMA = 'MAZ_RENDER_TEXT_PUBLICATION_v1'


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
    """Verify old failed-attempt snapshots separately, not just outer hashes."""
    results = []
    for name in ['attempt-01/FREEZE-MANIFEST.json',
                 'attempt-02/FREEZE-MANIFEST.json',
                 'FINAL-TEXT-RECORDS-MANIFEST.json']:
        path = folder / name
        manifest = json.loads(path.read_bytes())
        total = 0
        for record in manifest['files']:
            total += len(checked_file(path.parent, record))
        assert len(manifest['files']) == manifest['file_count']
        assert total == manifest['total_bytes']
        results.append({'manifest': name, 'records_verified': len(manifest['files']),
                        'bytes_verified': total, 'status': 'PASS'})
    return results


def readme(index, table):
    return f'''# MAZ native wheel render text evidence — 2026-10-02

This is a lossless plaintext publication package, not a model change. It holds
{index['original_text_record_count']} original text records ({index['original_text_bytes']:,} bytes) through readable
Python source files and ordinary JSON value/reference tables. It also preserves
the final source manifest separately, byte for byte. Nothing here executes a
renderer unless someone explicitly chooses to execute an original render script.

## What the evidence establishes

- The full four-station / 72-glyph verification belongs to method commit
  66085d7f353b6a5ee6d441243f3e0618e2ac0b64. Render records identify actual HEAD
  bc5eced9a3c9470e2b0cff538821d701cada08de.
- The two successful views demonstrate station 0 only: each fresh process
  applied 18 qualified native Shrinkwrap modifiers and reparented one station.
  Complete four-station / 72-glyph eligibility checks and the original
  full-scene dependency guards remained. These views do not extend the full
  verification to a new four-station render replay.
- The original source SHA-256 before and after both successful runs was
  8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70.
  Source bytes remained unchanged. Both successful finally-restorations passed.
- Both views used exactly the same camera matrix, orthographic scale, lights
  settings and resolution. Original material/world/visibility/identity guards
  passed within each process. Pointer-derived material/shader fingerprints
  are not comparable across processes; no cross-process pixel-identity claim
  is made.
- All 16 whole-vehicle gates remain OPEN. Original materials, original geometry,
  occlusions and step interference remain. Camber remains zero; drums remain
  the original simplified proxies.
- The wheel, hub inflation line, nuts and tread visibly change orientation.
  Lettering is not clearly readable in either image, so the pair does not
  visually establish readable lettering movement. The interior drum remains
  occluded and has numerical witness evidence only.

## Attempts and qualifications

| Attempt | Process elapsed | Result |
| --- | ---: | --- |
| attempt-01 | 117.239 s | Internal planned deadline; 0 PNG; restoration unconfirmed |
| attempt-02 | 150.068 s | Unexpected SIGKILL before its deadline; cause UNKNOWN; 0 PNG; restoration unconfirmed |
| attempt-station0-neutral-01 | 112.018 s | One actual local PNG; successful station-0-only run |
| attempt-station0-spin-01 | 110.494 s | One actual local PNG; successful station-0-only run |

The failed-attempt records, partial logs and historical manifests are preserved
exactly. Later success does not rewrite the earlier failures or prove the cause
of the SIGKILL. Failure-specific diagnostic snapshots remain as original
relevant evidence; no unrelated host inventory is added.

## Images are references, not payloads

The final source manifest records these two original local images:

| Original relative path | Bytes | SHA-256 |
| --- | ---: | --- |
| attempt-station0-neutral-01/wheel-neutral.png | 1,178,213 | 7b173610175dbc2f894c1b8fc23708c0d1a090429701de1cb615938ffb8306a8 |
| attempt-station0-spin-01/wheel-spin-0p731.png | 1,178,538 | 1291eb1f34f4d40d15cb6fbf58c8995d572081f9324ecb5ba67e53d9cb1be8a2 |

The two views were delivered through the authorized channel. Returned delivery
copies contained 511 fewer PNG-encoding bytes each, while their decoded RGBA
pixel bytes matched their corresponding originals exactly. The manifest hashes
above identify the original local PNG encodings, not the returned encodings.
No channel identifier, link, or delivery receipt is included here.

Their combined 2,356,751 bytes are absent from this package. PNG, blend and GLB
bytes are never packed into JSON, text, or Git blobs. No new LFS upload exists;
this package does not claim that images are in Git or LFS. It contains no private
message destination, signed storage URL or delivery receipt.

## Read and restore

1. Read this README, STATION0-FINAL-MANIFEST.json and package-index.json first.
2. Original Python scripts are directly readable under sources/. The index
   explicitly maps every original script path to its stored source file.
   Equal source files share one exact copy; all original paths are restored.
3. Run the following command from this package, using an output path that does
   not exist:

   python -B package-wheel-render-evidence.py restore --package . --out /tmp/maz-render-restored-UNUSED

Restoration writes only the 67 original text records and the separate final
manifest. It verifies every byte count and SHA-256 and then independently checks
the three older failed-attempt manifests against their referenced records. It
never creates PNG/blend/GLB files, starts Blender, or changes a repository.
An existing restore destination is refused before anything is written.

To inspect or audit an original run, read the restored attempt's executed-runner.py,
executed-script.py, launch.json, reviewed-plan.json and process.json, together
with its log, terminal record and outcome/report. Those are the exact replay
sources and original launch records. Their absolute paths and prerequisites
are historical evidence, not a claim of portability or authorization to rerun
an engine. Text restoration is the only replay performed for this package.

## Representation and reproducibility

The unchanged codec pack-wheel-interface-evidence.py has SHA-256
{CODEC_SHA} and uses PLAIN_JSON_INTERFACE_TABLE_v1. Its
{len(table['shards'])} table shards total {sum(s['bytes'] for s in table['shards']):,} bytes.
Entries are plain JSON scalar values, arrays of references, or objects with
named fields and references; references point backward. There is no zlib,
base64, binary string wrapper, or asset encoding.

For each original .json record, structured storage is selected only when
Python json.dumps(value, indent=2, ensure_ascii=True) plus LF, UTF-8 encoded,
reproduces its exact source bytes. Otherwise its original text is stored.
For text/log records, each line retains its original line ending and is split
only at literal |. Restoration joins each line's parts with |, then concatenates
all lines. Unknown lines remain unchanged. No normalization or approximation
occurs. package-index.json records the representation of every original path.

To rebuild in another unused directory from the original frozen source:

   python -B package-wheel-render-evidence.py build --source /path/to/maz-native-wheel-views-20261002 --out /tmp/maz-render-package-UNUSED --codec ./pack-wheel-interface-evidence.py

The builder pins the source manifest hash to
{SOURCE_MANIFEST_SHA}. It reads
only the 67 allowlisted original text files and that manifest. The PNG manifest
entries are preserved as references only; the builder never opens asset bytes.

VERIFICATION.json records a separate-process restoration and independent
byte-for-byte comparison against all originals, plus the old manifest checks.
PUBLICATION-FILES-MANIFEST.json inventories the complete publication package,
excluding itself. No publication or external delivery is performed by these tools.
'''


def build(source, output, codec_path):
    assert not output.exists(), 'Publication destination must not exist'
    manifest_raw = (source / SOURCE_MANIFEST).read_bytes()
    assert sha(manifest_raw) == SOURCE_MANIFEST_SHA
    manifest = json.loads(manifest_raw)
    assert manifest['text_record_count'] == 67
    assert manifest['text_bytes'] == 6643853
    assert len(manifest['text_records']) == manifest['text_record_count']
    assert sum(r['bytes'] for r in manifest['text_records']) == manifest['text_bytes']
    codec = load_codec(codec_path)
    # Validate every original before creating the destination. No asset read.
    originals = [(r, checked_file(source, r)) for r in manifest['text_records']]
    assert len({r['path'] for r, _ in originals}) == 67
    for r, _ in originals:
        assert Path(r['path']).suffix in {'.py', '.json', '.jsonl', '.log', '.md'}
    old_manifest_checks(source)
    output.mkdir(parents=True, exist_ok=False)
    (output / SOURCE_MANIFEST).write_bytes(manifest_raw)
    shutil.copyfile(codec_path, output / CODEC_NAME)
    shutil.copyfile(Path(__file__).resolve(), output / 'package-wheel-render-evidence.py')
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
    return {'status': 'BUILT_PENDING_INDEPENDENT_RESTORE', 'original_records': 67,
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
    assert index['records'] and len(index['records']) == manifest['text_record_count'] == 67
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
    assert sum(len(raw) for _, raw in restored) == manifest['text_bytes'] == 6643853
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
