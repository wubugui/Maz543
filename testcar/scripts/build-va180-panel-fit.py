"""Append the retained VA180 partial study into a separate whole-cab candidate.

The B4 caption/identity conflict and all fitted dimensions remain unresolved.
Only B4's old proxy descendants are archived by object visibility, never removed.
"""
import bpy
import hashlib
import json
import shutil
import argparse
import sys
import numpy as np
from pathlib import Path
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'outputs/cloud-steering-photo-hypothesis-20261001/MAZ543A_Master.blend'
DEVICE = ROOT/'outputs/cloud-va180-face-study-20261001/iteration-04/study.blend'
OUT = ROOT/'outputs/cloud-va180-panel-fit-20261001'
BASE_SHA = 'ba622e6dad9a74b7ee39058d1ca88b6f75fd85bd3923ab0629b87e812c9b7864'
DEVICE_SHA = '5f22280d7f2f9f56ec06ae333a4e46f9632860b534ad540a9bda6bae1223d670'
parser=argparse.ArgumentParser()
parser.add_argument('--base',type=Path)
parser.add_argument('--base-sha')
parser.add_argument('--output',type=Path)
parser.add_argument('--candidate-name',choices=['MAZ543A_Master.blend','MAZ543A_Textured.blend'],default='MAZ543A_Master.blend')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if args.base:
    assert args.base_sha and len(args.base_sha)==64, 'Explicit alternate source requires its exact identity'
    BASE=args.base.resolve();BASE_SHA=args.base_sha
if args.output:OUT=args.output.resolve()
assert ROOT in OUT.parents and OUT.name.startswith('cloud-'), 'Dedicated candidate directory required'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE) == BASE_SHA and sha(DEVICE) == DEVICE_SHA
OUT.mkdir(exist_ok=True)
TARGET = OUT/args.candidate_name
assert TARGET not in {BASE,DEVICE,ROOT/'outputs/MAZ543A_Master.blend',ROOT/'outputs/MAZ543A_Textured.blend'}
assert not TARGET.exists()

def geometry(o):
    h = hashlib.sha256()
    if o.type == 'MESH':
        m = o.data
        for seq, prop, n, dtype in [(m.vertices,'co',3,np.float32), (m.loops,'vertex_index',1,np.int32),
                                    (m.polygons,'loop_start',1,np.int32), (m.polygons,'loop_total',1,np.int32),
                                    (m.polygons,'material_index',1,np.int32)]:
            a = np.empty(len(seq)*n,dtype=dtype); seq.foreach_get(prop,a); h.update(a.tobytes())
        for uv in m.uv_layers:
            a = np.empty(len(uv.uv)*2,dtype=np.float32); uv.uv.foreach_get('vector',a); h.update(a.tobytes())
    elif o.type == 'CURVE':
        h.update(json.dumps([(s.type,s.use_cyclic_u,[list(p.co) for p in s.points],
                             [(list(p.co),list(p.handle_left),list(p.handle_right)) for p in s.bezier_points])
                            for s in o.data.splines]).encode())
    elif o.type == 'FONT':
        h.update(o.data.body.encode())
    return h.hexdigest()

def state(o):
    return {'type':o.type, 'authored_geometry_uv':geometry(o),
            'parent':o.parent.name if o.parent else None,
            'world':[list(r) for r in o.matrix_world],
            'local':[list(r) for r in o.matrix_local],
            'hide_render':o.hide_render, 'hide_viewport':o.hide_viewport,
            'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],
            'collections':sorted(c.name for c in o.users_collection)}

def write_report(path, report):
    # Keep a complete, grep-friendly single line per retained object rather than
    # expanding every matrix element into hundreds of thousands of lines.
    metadata={k:v for k,v in report.items() if k!='old_object_snapshot'}
    prefix=json.dumps(metadata,ensure_ascii=False,indent=2).rstrip()[:-1].rstrip()
    rows=[json.dumps(k,ensure_ascii=False)+': '+json.dumps(v,ensure_ascii=False,separators=(',',':'))
          for k,v in report['old_object_snapshot'].items()]
    content=prefix+',\n  "old_object_snapshot": {\n    '+',\n    '.join(rows)+'\n  }\n}\n'
    assert json.loads(content)==report
    path.write_text(content)

bpy.ops.wm.open_mainfile(filepath=str(BASE)); bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
before = {o.name:state(o) for o in bpy.data.objects}
images_before = set(bpy.data.images)
slot = bpy.data.objects['LEFT B4 / drawing leader 64']
old = list(slot.children_recursive)
assert len(old) >= 7 and all(o.name.startswith('LEFT B4 ') for o in old), [o.name for o in old]
old_names = {o.name for o in old}
for o in old:
    o.hide_render = True
    o.hide_set(True)

hole = bpy.data.objects['L-HOLE-B4']
hole_radius = max((v.co.x**2+v.co.y**2)**.5 for v in hole.data.vertices)
# Native primitive dimensions may have been applied to the object transform.
hole_radius *= abs(hole.scale.x)
assert abs(abs(hole.scale.x)-abs(hole.scale.y)) < 1e-6
assert .01 < hole_radius < .06, hole_radius
clearance = .0003  # fitted radial assembly gap, not an original tolerance
scale = (hole_radius-clearance)/.042
z_front = .0015 + .0015*scale + .0001
root = bpy.data.objects.new('VA180 PARTIAL — B4 PHOTO-FORM REVIEW',None)
slot.users_collection[0].objects.link(root); root.parent = slot
root.matrix_basis = Matrix.Translation((hole.location.x,hole.location.y,z_front)) @ Matrix.Scale(scale,4)
root['status'] = 'FITTED PHOTO-FORM INSTALLATION; B4 caption conflict OPEN; incomplete VA180'
root['source_device_sha256'] = DEVICE_SHA
root['fitted_uniform_scale'] = scale
root['fitted_case_radial_gap_in_panel_local_m'] = clearance

existing = set(bpy.data.objects)
with bpy.data.libraries.load(str(DEVICE),link=False) as (available, loaded):
    loaded.collections = [n for n in available.collections if not n.startswith('99 ')]
    loaded.texts = [n for n in available.texts if n.startswith('PACKED FONT LICENSE')]
for collection in loaded.collections:
    bpy.context.scene.collection.children.link(collection)
incoming = [o for o in bpy.data.objects if o not in existing]
name_map = {}
for o in incoming:
    old_name = o.name
    o.name = 'VA180 B4 / '+old_name
    name_map[old_name] = o.name
    if o.parent is None:
        o.parent = root
        o.matrix_parent_inverse = Matrix.Identity(4)
    o['installed_in_vehicle'] = True
    o['installation_status'] = 'Independent unaccepted B4 fitted review; physical caption mapping unresolved'
bpy.context.view_layer.update()
assert set(bpy.data.images) == images_before, 'The appended study must not import photographic pixels'

fail = []
for name, prior in before.items():
    obj = bpy.data.objects.get(name)
    if obj is None:
        fail.append((name,'missing')); continue
    now = state(obj)
    for key in prior:
        if key == 'hide_render' and name in old_names:
            if now[key] is not True: fail.append((name,'archive visibility'))
        elif now[key] != prior[key]: fail.append((name,key))
assert not fail, fail[:20]
button = bpy.data.objects[name_map['BUTTON PRESS REVIEW — travel is fitted']]
assert len(button.animation_data.drivers) == 1
assert button.animation_data.drivers[0].driver.variables[0].targets[0].id == button
for o in incoming:
    if o.type == 'FONT': assert o.data.font.packed_file
assert loaded.texts
shutil.copyfile(DEVICE.parent/'FONT-LICENSE.txt',OUT/'FONT-LICENSE.txt')
bpy.context.scene['VA180_B4_status'] = 'Partial photo-form review only. Existing cab-panel/seat collision failures remain. All16 OPEN.'
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
report = {'status':'SAVED_UNACCEPTED_CANDIDATE_REQUIRES_FRESH_READBACK',
          'candidate_file':TARGET.name,
          'base_sha256':BASE_SHA,'device_sha256':DEVICE_SHA,'candidate_sha256':sha(TARGET),
          'old_object_count':len(before),'incoming_object_count':len(incoming),'old_proxy_archive':sorted(old_names),
          'old_object_snapshot':before,'device_object_name_map':name_map,
          'fitted_hole_radius_local_m':hole_radius,'fitted_uniform_scale':scale,
          'fitted_radial_clearance_local_m':clearance,'fitted_front_plane_local_m':z_front,
          'new_root_world':[list(r) for r in root.matrix_world],
          'unchanged_old_object_scoped_identity_failures':fail,
          'identity_limits':'Authored geometry/UV, parent and matrix, material slot names, collection membership and hide flags only. Fresh saved-file readback still required. Material node internals/custom normals not certified.',
          'caption_mapping_conflict':'B4 drawing leader64 caption says fan switch; photographic VA180-like form does not resolve this.',
          'whole_vehicle_acceptance':'16 OPEN'}
assert sha(BASE) == BASE_SHA and sha(DEVICE) == DEVICE_SHA
write_report(OUT/'build.json',report)
print('VA180_PANEL_CANDIDATE_SAVED', json.dumps({k:report[k] for k in ['candidate_sha256','old_object_count','incoming_object_count','fitted_uniform_scale']}))
