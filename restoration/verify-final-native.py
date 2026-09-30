"""Check final cooling geometry and provenance are identical in all three saved assemblies."""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'testcar'
poses = json.loads((PROJECT / 'work/cooling-poses.json').read_text())['frames'][0]['pose']
reference = json.loads((PROJECT / 'outputs/cooling-reference-register.json').read_text())
expected_names = {row['name'] for row in reference}
baseline = None
reports = []
for filename in ['MAZ543A_Cooling_Master.blend', 'MAZ543A_Master.blend', 'MAZ543A_Textured.blend']:
    path = PROJECT / 'outputs' / filename
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bpy.context.scene.frame_set(0)
    root = bpy.data.objects['S543_COOLING']
    parts = sorted([o for o in root.children_recursive if o.type in ['MESH', 'CURVE']], key=lambda o: o.name)
    assert {o.name for o in parts} == expected_names
    assert len(parts) == 1241
    assert all(name in bpy.data.objects for name in poses)
    rows = []
    for ob in parts:
        assert ob.get('sourceSupports') and ob.get('individualPhotoStatus')
        geom = [list(v.co) for v in ob.data.vertices] if ob.type == 'MESH' else [[list(p.co) for p in s.points] for s in ob.data.splines]
        rows.append([ob.name, ob.parent.name, ob.type, geom, ob.get('sourceSupports'), ob.get('referenceURLs')])
    digest = hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    if baseline is None:
        baseline = digest
    assert digest == baseline, (filename, 'Cooling geometry/provenance mismatch')
    missing = [im.filepath for im in bpy.data.images if im.source == 'FILE' and im.filepath and not im.packed_file
               and not Path(bpy.path.abspath(im.filepath)).is_file()]
    assert not missing, (filename, missing)
    reports.append({'file': filename, 'authoredParts': len(parts), 'poseBindings': len(poses),
                    'geometryAndProvenanceSha256': digest, 'missingUnpackedImages': missing})
result = {'assemblies': reports, 'passed': True,
          'scope': 'Final saved cooling local geometry and provenance parity; no complete vehicle collision or factory dimensional acceptance.'}
(ROOT / 'restoration/final-native-parity.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
