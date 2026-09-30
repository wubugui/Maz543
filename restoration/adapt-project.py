"""Adapt active build entry points to this portable bundle, preserving a source backup."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'testcar'
replacements = {
    'blender-model.py': [("Path('D:/maz543-references')", "(ROOT.parent/'external/maz543-references')")],
    'blender-d12.py': [("Path('D:/maz543-references/engine/02-kmz-complete-after.webp')", "(ROOT.parent/'external/maz543-references/engine/02-kmz-complete-after.webp')")],
    'blender-starting.py': [("'D:/maz543-references/starting/'+path", "str(ROOT.parent/'external/maz543-references/starting'/path)")],
    'blender-suspension.py': [("Path('D:/maz543-references/", "(ROOT.parent/'external/maz543-references/")],
    'prepare-cam-profiles.py': [("Path('D:/maz543-references/engine/timing')", "(ROOT.parent/'external/maz543-references/engine/timing')")],
    'update-d12-cams.py': [("Path('D:/maz543-references/", "(ROOT.parent/'external/maz543-references/")],
    'repair-starting-action-slots.py': [("ROOT=Path('D:/testcar')", "ROOT=Path(__file__).resolve().parents[1]")],
}
changed = []
for name, pairs in replacements.items():
    path = PROJECT / 'scripts' / name
    original = path.read_text(encoding='utf-8')
    content = original
    for before, after in pairs:
        assert before in content, (name, before)
        content = content.replace(before, after)
    compile(content, str(path), 'exec')
    backup = ROOT / 'restoration/original-scripts' / name
    backup.parent.mkdir(exist_ok=True)
    assert not backup.exists(), backup
    shutil.copy2(path, backup)
    path.write_text(content, encoding='utf-8')
    changed.append(name)
(ROOT / 'restoration/adapted-scripts.json').write_text(json.dumps(changed, indent=2), encoding='utf-8')
print('Adapted', len(changed), 'active script entry points')
