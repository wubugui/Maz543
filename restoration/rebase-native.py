"""Relocate known image references in current masters; retain original blend backups."""
import bpy
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'testcar'
BACKUP = ROOT / 'restoration/original-native'
BACKUP.mkdir(exist_ok=True)
for path in (PROJECT / 'outputs').glob('*.blend*'):
    target = BACKUP / path.name
    if not target.exists():
        shutil.copy2(path, target)

reports = []
for path in sorted((PROJECT / 'outputs').glob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    changes = []
    for image in bpy.data.images:
        if image.source != 'FILE' or not image.filepath:
            continue
        previous = image.filepath
        absolute = bpy.path.abspath(previous).replace('\\', '/')
        candidate = None
        if '/maz543-references/' in absolute:
            candidate = ROOT / 'external/maz543-references' / absolute.split('/maz543-references/', 1)[1]
        elif '/testcar/' in absolute:
            candidate = PROJECT / absolute.split('/testcar/', 1)[1]
        if candidate is not None and candidate.is_file():
            relative = bpy.path.relpath(str(candidate.resolve()))
            if relative != previous:
                image.filepath = relative
                changes.append({'image': image.name, 'before': previous, 'after': relative})
            # Packed images retain a separate source path used by auto-pack on save.
            for packed in image.packed_files:
                if packed.filepath != relative:
                    changes.append({'image': image.name, 'packedSourceBefore': packed.filepath, 'after': relative})
                    packed.filepath = relative
    if changes:
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
        bpy.ops.wm.open_mainfile(filepath=str(path))
    missing = [{'image': im.name, 'path': im.filepath} for im in bpy.data.images
               if im.source == 'FILE' and im.filepath and not im.packed_file
               and not Path(bpy.path.abspath(im.filepath)).is_file()]
    reports.append({'file': path.name, 'changes': changes, 'missingUnpackedImages': missing})
    print('RELOCATED', path.name, len(changes), 'missing', len(missing), flush=True)
(ROOT / 'restoration/native-path-verification.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
assert not any(row['missingUnpackedImages'] for row in reports), 'Unresolved native image references'
