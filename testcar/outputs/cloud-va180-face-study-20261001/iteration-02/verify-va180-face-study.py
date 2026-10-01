"""Fresh structural checks of the partial, explicitly fitted VA180 front study."""
import bpy,bmesh,json,hashlib,argparse,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'outputs/cloud-va180-face-study-20261001/study.blend')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);path=args.input.resolve();out=path.parent/'readback.json';assert not out.exists()
manifest=json.loads((path.parent/'build.json').read_text());sha=hashlib.sha256(path.read_bytes()).hexdigest();assert sha==manifest['model_sha256']
bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.view_layer.update();fail=[];rows=[]
def mesh(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();return e,m
def tree(o):
 e,m=mesh(o);v=[e.matrix_world@x.co for x in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return BVHTree.FromPolygons(v,ts,all_triangles=True)
for name in manifest['closed_solids']:
 o=bpy.data.objects[name];e,m=mesh(o);bm=bmesh.new();bm.from_mesh(m);vol=bm.calc_volume(signed=True);closed=bool(bm.faces) and all(x.is_manifold for x in bm.edges);finite=all(math.isfinite(x) for v in bm.verts for x in v.co);euler=len(bm.verts)-len(bm.edges)+len(bm.faces)
 row={'name':name,'vertices':len(m.vertices),'triangles':len(m.loop_triangles),'closed':closed,'finite':finite,'signed_volume_m3':vol,'euler':euler,'hide_render':o.hide_render};rows.append(row)
 if not closed or not finite or vol<=1e-13 or o.hide_render:fail.append({'name':name,'reason':'closed finite positive-volume renderable solid required'})
 bm.free();e.to_mesh_clear()
front=bpy.data.objects['FRONT — opaque lower mask and upper opening'];ft=tree(front)
points={'upper_window':(0,.02),'button_hole':(.0104,-.033),'correction_hole':(-.004,-.025)};holes=[]
for name,(x,y) in points.items():
 clear=ft.ray_cast(Vector((x,y,.02)),Vector((0,0,-1)),.04)[0] is None;holes.append({'name':name,'front_plate_ray_clear':clear})
 if not clear:fail.append({'name':name,'reason':'claimed front opening blocked'})
front_row=next(x for x in rows if x['name']==front.name)
if front_row['euler']!=-4:fail.append({'name':front.name,'reason':'three distinct through-holes require Euler -4','actual':front_row['euler']})
mods=[m for m in front.modifiers if m.type=='BOOLEAN'];old=[m.show_viewport for m in mods]
for m in mods:m.show_viewport=False
bpy.context.view_layer.update();negative=tree(front);negative_hits=[negative.ray_cast(Vector((x,y,.02)),Vector((0,0,-1)),.04)[0] is not None for x,y in points.values()]
for m,v in zip(mods,old):m.show_viewport=v
bpy.context.view_layer.update()
if not all(negative_hits):fail.append({'reason':'disabled-Boolean negative opening control failed'})
button=bpy.data.objects['BUTTON PRESS REVIEW — travel is fitted'];moving=[bpy.data.objects[n] for n in ['BUTTON — movable stem','BUTTON — movable cap']];stationary={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects if o.name not in {button.name,*[x.name for x in moving]}}
released=[o.matrix_world.copy() for o in moving];poses=[]
for mm in [0,.5,1,0]:
 button['press_mm']=mm;button.update_tag();bpy.context.view_layer.update();errors=[]
 for o,base in zip(moving,released):
  expected=base.copy();expected.translation.z-=mm/1000;errors.append(max(abs(o.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4)))
 still=all([list(r) for r in bpy.data.objects[n].matrix_world]==v for n,v in stationary.items());poses.append({'review_press_mm':mm,'max_matrix_error':max(errors),'all_other_object_matrices_unchanged':still})
 if max(errors)>1e-7 or not still:fail.append({'reason':'independent button travel or isolation failed','mm':mm})
for mark in manifest['readable_marks']:
 o=bpy.data.objects[mark['object']]
 if o.type!='FONT' or o.data.body!=mark['text'] or not o.data.font.packed_file:fail.append({'name':o.name,'reason':'editable mark or portable font missing'})
if any(i.source=='FILE' for i in bpy.data.images):fail.append({'reason':'source image pixels unexpectedly loaded'})
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
report={'source_sha256':sha,'fresh_open':True,'physical_solids':rows,'front_openings':holes,'disabled_boolean_negative_controls':negative_hits,'button_review_poses':poses,'readable_marks_checked':len(manifest['readable_marks']),'failures':fail,'status':'PARTIAL_STRUCTURAL_CHECK_PASS' if not fail else 'FAIL','limits':['No real instrument metrology or electrical calibration','Minor ticks and voltage markings omitted as unreadable','Button travel is fitted and sampled, not a continuous mechanism/clearance proof','No rear clamp, connector, shunt or internal mechanism acceptance','Not installed or accepted for the vehicle'],'all16VehicleGates':'OPEN'}
out.write_text(json.dumps(report,indent=2)+'\n');print('VA180_FACE_READBACK',len(rows),len(holes),len(fail),flush=True)
if fail:raise SystemExit(1)
