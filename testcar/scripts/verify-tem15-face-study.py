"""Fresh, scoped structure and static triangle-contact check of partial TEM15 face."""
import bpy,bmesh,json,hashlib,math,itertools,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--directory',default='outputs/cloud-tem15-face-study-20261001');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);OUT=(ROOT/args.directory).resolve();assert OUT.is_relative_to(ROOT/'outputs/cloud-tem15-face-study-20261001')
p=OUT/'study.blend';manifest=json.loads((OUT/'build.json').read_text());sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==manifest['model_sha256']
bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.view_layer.update();rows=[];trees={};fail=[]
for name in manifest['physical_solids']:
 o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();bm=bmesh.new();bm.from_mesh(m)
 closed=bool(bm.faces) and all(x.is_manifold for x in bm.edges);vol=bm.calc_volume(signed=True);finite=all(math.isfinite(x) for v in bm.verts for x in v.co)
 trees[name]=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
 rows.append({'name':name,'closed':closed,'volume_m3':vol,'finite':finite,'vertices':len(m.vertices),'triangles':len(m.loop_triangles),'euler':len(bm.verts)-len(bm.edges)+len(bm.faces)})
 if not closed or vol<=1e-13 or not finite or o.hide_render:fail.append(name+' solid gate')
 bm.free();e.to_mesh_clear()
contacts=[]
for a,b in itertools.combinations(trees,2):
 n=len(trees[a].overlap(trees[b]))
 if n:contacts.append({'a':a,'b':b,'triangle_pairs':n})
if contacts:fail.append('Undeclared physical study surfaces intersect')
case=bpy.data.objects['CASE FRONT ENVELOPE — no rear hardware or internals'];clear=trees[case.name].ray_cast(Vector((0,0,.004)),Vector((0,0,-1)),.02)[0] is None
boolean=next(m for m in case.modifiers if m.type=='BOOLEAN');boolean.show_viewport=False;bpy.context.view_layer.update();e=case.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(x.vertices) for x in m.loop_triangles],all_triangles=True);negative=t.ray_cast(Vector((0,0,.004)),Vector((0,0,-1)),.02)[0] is not None;e.to_mesh_clear();boolean.show_viewport=True;bpy.context.view_layer.update()
if not clear or not negative:fail.append('Native cavity/disabled Boolean control')
for mark in manifest['observed_text']:
 o=bpy.data.objects[mark['object']]
 if o.type!='FONT' or o.data.body!=mark['text'] or not o.data.font.packed_file:fail.append(mark['object']+' portable editable text')
source_curve_check=None
if 'pointer_cap_repair' in manifest:
 source_curve=bpy.data.objects.get(manifest['pointer_cap_repair']['editable_source_retained'])
 pointer=bpy.data.objects['POINTER — fitted uncalibrated photo pose']
 if source_curve is None or source_curve.type!='CURVE' or not source_curve.hide_render:fail.append('Editable original Curve source absent or unexpectedly visible')
 else:
  def coordinates(o):
   e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v={tuple(x.co) for x in m.vertices};e.to_mesh_clear();return v
  source_curve_check=coordinates(source_curve)==coordinates(pointer)
  if not source_curve_check:fail.append('Saved repaired pointer differs from editable Curve source positions')
 if pointer.type!='MESH' or not any(m.type=='WELD' and abs(m.merge_threshold-1e-7)<1e-12 for m in pointer.modifiers):fail.append('Native cap-seam Weld modifier absent')
assert not any(i.source=='FILE' for i in bpy.data.images)
assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
r={'status':'PASS_PARTIAL_TEM15_STRUCTURE' if not fail else 'FAIL_PARTIAL_TEM15_STRUCTURE','source_sha256':sha,'fresh_open':True,'physical_solids':rows,'static_pair_count':len(trees)*(len(trees)-1)//2,'surface_contacts':contacts,'cavity_front_ray_clear':clear,'disabled_boolean_negative_control':negative,'observed_text_checked':len(manifest['observed_text']),'saved_editable_curve_matches_pointer_position_set':source_curve_check,'failures':fail,'source_saved':False,'limits':['Static pairwise triangle-surface check only, not general containment proof','Only incomplete front face; fitted dimensions and typography','No scale calibration, actual pressure mechanism, sensor or rear mounting','Not installed in vehicle; no whole-vehicle acceptance'],'whole_vehicle_acceptance':'16 OPEN'};(OUT/'readback.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],len(rows),len(contacts),fail,flush=True)
if fail:raise SystemExit(1)
