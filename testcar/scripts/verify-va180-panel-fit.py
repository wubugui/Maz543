"""Fresh-read retained identities, B4 geometry contacts and sampled button motion."""
import bpy
import hashlib
import json
import argparse
import sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/cloud-va180-panel-fit-20261001'
parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
if args.directory:OUT=args.directory.resolve()
build = json.loads((OUT/'build.json').read_text())
SOURCE = OUT/build.get('candidate_file','MAZ543A_Master.blend')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE) == build['candidate_sha256']
# Extract only pure snapshot functions; never execute the construction script.
import ast
tree = ast.parse((ROOT/'scripts/build-va180-panel-fit.py').read_text())
pure = ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'geometry','state'}],type_ignores=[])
exec(compile(pure,'shared_snapshot_functions','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
fail = []
archived = set(build['old_proxy_archive'])
for name, old in build['old_object_snapshot'].items():
    obj = bpy.data.objects.get(name)
    if obj is None:
        fail.append([name,'missing']); continue
    now = state(obj)
    for key in old:
        if key in {'world','local'}:
            if float(np.max(np.abs(np.array(now[key])-np.array(old[key])))) > 1e-6: fail.append([name,key])
        elif key == 'hide_render' and name in archived:
            if not now[key]: fail.append([name,key])
        elif now[key] != old[key]: fail.append([name,key])

seat_obj = bpy.data.objects['cab_0064']
seats = []
for x in [-4.45,-3.38]:
    for y in [-1.025,1.025]:
        indices = {v.index for v in seat_obj.data.vertices if all(abs((seat_obj.matrix_world@v.co)[k]-c)<=r+3e-6 for k,c,r in [(0,x,.23),(1,y,.23),(2,1.6,.125)])}
        count = sum(set(p.vertices)<=indices for p in seat_obj.data.polygons)
        valid = len(indices)==900 and count==300 and not seat_obj.hide_render
        seats.append({'centre':[x,y,1.6],'vertices':len(indices),'faces':count,'retained_semantic_region':valid})
        if not valid: fail.append(['seat',x,y])

def eligible(obj):
    if obj.hide_render or obj.type != 'MESH': return False
    # Collection paths are read from each enabled render layer. An object may
    # belong to multiple paths; one eligible path is sufficient.
    available = set()
    def visit(lc,blocked=False):
        blocked = blocked or lc.exclude or lc.holdout or lc.indirect_only or lc.collection.hide_render
        if not blocked: available.add(lc.collection.name)
        for c in lc.children: visit(c,blocked)
    for layer in bpy.context.scene.view_layers:
        if layer.use: visit(layer.layer_collection)
    return any(c.name in available for c in obj.users_collection) and getattr(obj,'visible_camera',True)

assert eligible(seat_obj), 'Retained seat mesh must remain eligible in a render layer'
dg = bpy.context.evaluated_depsgraph_get()
def meshdata(obj):
    ev = obj.evaluated_get(dg); m = ev.to_mesh(); m.calc_loop_triangles()
    v = [ev.matrix_world@p.co for p in m.vertices]; t = [tuple(p.vertices) for p in m.loop_triangles]; ev.to_mesh_clear()
    return v,t
def bounds(v): return (np.min(np.array(v),axis=0),np.max(np.array(v),axis=0))
def overlap(a,b): return bool(np.all(a[0]<=b[1]+1e-7) and np.all(b[0]<=a[1]+1e-7))

device_build = json.loads((ROOT/'outputs/cloud-va180-face-study-20261001/iteration-04/build.json').read_text())
solids = [bpy.data.objects[build['device_object_name_map'][n]] for n in device_build['closed_solids']]
cache = {}
for obj in solids:
    v,t = meshdata(obj); cache[obj.name] = (bounds(v),BVHTree.FromPolygons(v,t,all_triangles=True))
possible = []
for name in build['old_object_snapshot']:
    obj = bpy.data.objects[name]
    if not eligible(obj): continue
    bb = bounds([obj.matrix_world@Vector(c) for c in obj.bound_box])
    matches = [s for s in solids if overlap(bb,cache[s.name][0])]
    if not matches: continue
    v,t = meshdata(obj)
    if not t: continue
    actual_bb = bounds(v); tree = BVHTree.FromPolygons(v,t,all_triangles=True)
    for s in matches:
        if not overlap(actual_bb,cache[s.name][0]): continue
        contacts = cache[s.name][1].overlap(tree)
        possible.append({'device':s.name,'existing':name,'surface_triangle_pairs':len(contacts)})

button = bpy.data.objects[build['device_object_name_map']['BUTTON PRESS REVIEW — travel is fitted']]
stem = bpy.data.objects[build['device_object_name_map']['BUTTON — movable stem']]
cap = bpy.data.objects[build['device_object_name_map']['BUTTON — movable cap']]
moving = {button.name,stem.name,cap.name}
all_before = {o.name:np.array(o.matrix_world) for o in bpy.data.objects}
root = bpy.data.objects['VA180 PARTIAL — B4 PHOTO-FORM REVIEW']
travel_axis = root.matrix_world.to_3x3() @ Vector((0,0,1))
button_rows = []
for press in [0,.5,1,0]:
    button['press_mm'] = press; button.update_tag(); bpy.context.view_layer.update()
    changed = [o.name for o in bpy.data.objects if o.name not in moving and np.max(np.abs(np.array(o.matrix_world)-all_before[o.name]))>1e-7]
    if changed: fail.append(['unexpected_button_dependent_objects',changed])
    expected = Vector(all_before[cap.name][:3,3]) - travel_axis*(press/1000)
    error = (cap.matrix_world.translation-expected).length
    if error > 1e-6: fail.append(['button_scaled_translation',press,error])
    button_rows.append({'press_mm_review_input':press,'cap_world_m':list(cap.matrix_world.translation),
                        'scaled_translation_error_m':error,'unexpected_changed_count':len(changed)})
assert sha(SOURCE) == build['candidate_sha256']
contacts = [r for r in possible if r['surface_triangle_pairs']]
report = {'candidate_sha256':build['candidate_sha256'],'identity_failures':fail,'seats':seats,
          'old_object_count':len(build['old_object_snapshot']),'actual_object_count':len(bpy.data.objects),
          'new_to_existing_broadphase_pairs':possible,'new_to_existing_surface_contacts':contacts,
          'button_samples':button_rows,'saved_blend':False,
          'status':'PASS_SCOPED_READBACK_ONLY' if not fail and not contacts else 'FAILED_SCOPED_READBACK_OR_CONTACTS',
          'limits':['Contact audit detects surface triangle intersections, not complete solid containment or continuous sweeps.',
                    'Original three cab installation collision pairs and uncertain caption mapping remain unresolved.',
                    'Preserved material slot names do not certify material node internals.',
                    'Button sample inputs are fitted travel, not manufacturer mechanism validation.'],
          'whole_vehicle_acceptance':'16 OPEN'}
(OUT/'readback.json').write_text(json.dumps(report,indent=2)+'\n')
print('VA180_PANEL_READBACK',json.dumps({'identity_failures':len(fail),'surface_contacts':len(contacts),'seats':len(seats)}))
if fail or contacts: raise SystemExit(2)
