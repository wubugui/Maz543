"""Correct only the retained driving controls' cab side, using native separation.
Factory left-cab ownership is sourced; existing local proxy shape/placement is not.
"""
import bpy,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-hood-tyre-composite-20261001'
OUT=ROOT/'outputs/cloud-left-driver-side-20261001';OUT.mkdir(exist_ok=True)
TARGETS=[('steering_column','cab_0062',[-4.675,1,1.47],[-4.625,1.05,2.11],148),('pedal_link_a','cab_0062',[-4.912,1.173,1.477],[-4.838,1.197,1.683],148),('pedal_link_b','cab_0062',[-4.912,.893,1.477],[-4.838,.917,1.683],148),('pedal_plate_a','cab_0069',[-4.94,1.14,1.666],[-4.86,1.23,1.694],24),('pedal_plate_b','cab_0069',[-4.94,.86,1.666],[-4.86,.95,1.694],24),('floor_side_lever_proxy','cab_0063',[-4.282,.733,1.497],[-4.148,.757,1.943],148),('floor_side_lever_knob_proxy','cab_0066',[-4.302,.713,1.9175],[-4.238,.777,1.9625],148)]
DELTA=Vector((0,-2.05,0))
assert Vector((-1,0,0)).cross(Vector((0,0,1)))==Vector((0,1,0))
def face_records(o):
 mesh=o.data;records=[]
 for poly in mesh.polygons:
  corners=[]
  for li in poly.loop_indices:
   co=mesh.vertices[mesh.loops[li].vertex_index].co
   uv=tuple(float(x) for layer in mesh.uv_layers for x in layer.uv[li].vector)
   corners.append(tuple(float(x) for x in co)+uv)
  canonical=min(tuple(corners[i:]+corners[:i]) for i in range(len(corners)))
  material=mesh.materials[poly.material_index].name if mesh.materials[poly.material_index] else None
  records.append((material,canonical))
 return sorted(records)
def base_snapshot(o):
 h=hashlib.sha256();data=o.data
 if o.type=='MESH':
  for v in data.vertices:h.update(struct.pack('<fff',*v.co))
  for p in data.polygons:h.update(struct.pack('<I',len(p.vertices))+b''.join(struct.pack('<I',i) for i in p.vertices))
 elif o.type in {'CURVE','SURFACE','FONT'}:
  h.update(repr([(s.type,[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)) for p in s.bezier_points],[tuple(p.co) for p in s.points]) for s in getattr(data,'splines',[])]).encode())
 return {'geometry':h.hexdigest(),'world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}
reports=[]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 path=SOURCE/filename;sha=hashlib.sha256(path.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 originals={o.name:base_snapshot(o) for o in bpy.data.objects if o.type in {'MESH','CURVE','SURFACE','FONT'}}
 affected={t[1] for t in TARGETS};before_faces={n:face_records(bpy.data.objects[n]) for n in affected};made={n:[] for n in affected};parts=[]
 for label,name,lo,hi,count in TARGETS:
  o=bpy.data.objects[name];assert o.type=='MESH' and not o.modifiers,(name,'unexpected modifiers')
  ids={v.index for v in o.data.vertices if all(lo[k]-2e-6<=(o.matrix_world@v.co)[k]<=hi[k]+2e-6 for k in range(3))}
  assert len(ids)==count,(label,len(ids),count)
  assert not any(any(i in ids for i in p.vertices) and not all(i in ids for i in p.vertices) for p in o.data.polygons),label
  bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
  for v in o.data.vertices:v.select=v.index in ids
  for e in o.data.edges:e.select=all(i in ids for i in e.vertices)
  for p in o.data.polygons:p.select=all(i in ids for i in p.vertices)
  existing=set(bpy.data.objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
  new=set(bpy.data.objects)-existing;assert len(new)==1;part=new.pop();part.name='BL_Left_driver_'+label+'_retained'
  assert part.matrix_world==o.matrix_world;assert len(part.data.vertices)==count
  part['source_cab_ownership']='1977 manual p11, Fig101 p174: driving controls in LEFT cab'
  part['dimension_status']='Retained fitted proxy; no new OEM dimensions. Translation only, not mirrored.'
  part['identity_limit']='Floor-side lever is NOT a validated gear selector; original p110 puts selector on steering column. Pedal identities/order remain unvalidated.'
  made[name].append(part);parts.append(part)
 for name in affected:
  combined=face_records(bpy.data.objects[name])+[r for part in made[name] for r in face_records(part)]
  assert sorted(combined)==before_faces[name],(name,'native separation changed face/UV/material data')
 # Preserve complete wheel transform except the shared lateral displacement.
 wheel=bpy.data.objects['cab_pivot_004'];old_wheel=wheel.matrix_world.copy();wheel_children={o.name for o in wheel.children_recursive}
 for part in parts:
  m=part.matrix_world.copy();m.translation+=DELTA;part.matrix_world=m
 m=wheel.matrix_world.copy();m.translation+=DELTA;wheel.matrix_world=m
 wheel['candidate_cab_side']='LEFT by forward -X, up +Z, right +Y convention'
 wheel['candidate_lateral_translation_m']=-2.05
 bpy.context.view_layer.update();unchanged=[]
 for name,before in originals.items():
  if name in affected or name in wheel_children:continue
  assert base_snapshot(bpy.data.objects[name])==before,('Unrelated original changed',name)
  unchanged.append(name)
 assert all((part.matrix_world@v.co).y<0 for part in parts for v in part.data.vertices)
 assert wheel.matrix_world.translation.y<0
 row={'file':filename,'input_sha256':sha,'status':'SIDE_OWNERSHIP_CORRECTION_ONLY','lateral_translation_blender_xyz_m':list(DELTA),'existing_fitted_cab_centres_y_m':[1.025,-1.025],'separated_parts':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'parent':o.parent.name if o.parent else None} for o in parts],'selected_vertex_total':sum(len(o.data.vertices) for o in parts),'native_separation_original_face_corner_uv_material_records_preserved':True,'unrelated_original_geometry_objects_preserved':len(unchanged),'steering_group_original_matrix':[list(r) for r in old_wheel],'steering_group_candidate_matrix':[list(r) for r in wheel.matrix_world],'browser_pose_binding':'NOT_UPDATED: existing runtime would reset cab_pivot_004 position; do not promote this native file as browser-ready','all16VehicleGates':'OPEN'}
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
 row['candidate_sha256']=hashlib.sha256((OUT/filename).read_bytes()).hexdigest();assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
 reports.append(row);(OUT/'build-report.json').write_text(json.dumps(reports,indent=2)+'\n');print('LEFT_DRIVER_SAVED',filename,row['selected_vertex_total'],row['unrelated_original_geometry_objects_preserved'],flush=True)
