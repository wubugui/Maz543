"""Fresh-file verification of the bounded native driver-side correction."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'outputs/cloud-hood-tyre-composite-20261001';OUT=ROOT/'outputs/cloud-left-driver-side-20261001'
reports=json.loads((OUT/'build-report.json').read_text());results=[]
def snapshot(o):
 h=hashlib.sha256();d=o.data
 if o.type=='MESH':
  a=np.empty(len(d.vertices)*3,dtype=np.float32);d.vertices.foreach_get('co',a);h.update(a.tobytes())
  a=np.empty(len(d.loops),dtype=np.int32);d.loops.foreach_get('vertex_index',a);h.update(a.tobytes())
  for prop in ['loop_start','loop_total','material_index']:
   a=np.empty(len(d.polygons),dtype=np.int32);d.polygons.foreach_get(prop,a);h.update(a.tobytes())
  for layer in d.uv_layers:
   a=np.full(len(layer.uv)*2,np.nan,dtype=np.float32);layer.uv.foreach_get('vector',a);assert np.isfinite(a).all();h.update(a.tobytes())
 elif o.type in {'CURVE','SURFACE','FONT'}:h.update(repr([(s.type,[(tuple(p.co),tuple(p.handle_left),tuple(p.handle_right)) for p in s.bezier_points],[tuple(p.co) for p in s.points]) for s in getattr(d,'splines',[])]).encode())
 return {'data':h.hexdigest(),'world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render}
def faces(o):
 m=o.data;res=[]
 for p in m.polygons:
  corners=[tuple(float(x) for x in m.vertices[m.loops[i].vertex_index].co)+tuple(float(x) for uv in m.uv_layers for x in uv.uv[i].vector) for i in p.loop_indices]
  res.append((m.materials[p.material_index].name if m.materials[p.material_index] else None,min(tuple(corners[i:]+corners[:i]) for i in range(len(corners)))))
 return sorted(res)
for report in reports:
 name=report['file'];src=SOURCE/name;dst=OUT/name
 assert hashlib.sha256(src.read_bytes()).hexdigest()==report['input_sha256'];assert hashlib.sha256(dst.read_bytes()).hexdigest()==report['candidate_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 before={o.name:snapshot(o) for o in bpy.data.objects if o.type in {'MESH','CURVE','SURFACE','FONT'}}
 roots=['cab_0062','cab_0063','cab_0066','cab_0069'];old_faces={n:faces(bpy.data.objects[n]) for n in roots}
 wheel=bpy.data.objects['cab_pivot_004'];old_wheel=wheel.matrix_world.copy();descendants=[o.name for o in wheel.children_recursive]
 bpy.ops.wm.open_mainfile(filepath=str(dst));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();changed=[]
 for n,s in before.items():
  if n in roots or n in descendants:continue
  if snapshot(bpy.data.objects[n])!=s:changed.append(n)
 assert not changed,changed
 groups={'cab_0062':['steering_column','pedal_link_a','pedal_link_b'],'cab_0063':['floor_side_lever_proxy'],'cab_0066':['floor_side_lever_knob_proxy'],'cab_0069':['pedal_plate_a','pedal_plate_b']}
 for original,labels in groups.items():
  now=faces(bpy.data.objects[original])
  for label in labels:now.extend(faces(bpy.data.objects['BL_Left_driver_'+label+'_retained']))
  assert sorted(now)==old_faces[original],original+' face/UV/material preservation'
 delta=Vector((0,-2.05,0));wheel=bpy.data.objects['cab_pivot_004'];shift=wheel.matrix_world.translation-old_wheel.translation
 assert (shift-delta).length<5e-7;assert wheel.matrix_world.to_3x3()==old_wheel.to_3x3()
 for n in descendants:
  now=snapshot(bpy.data.objects[n]);assert now['data']==before[n]['data'] and now['parent']==before[n]['parent']
  old=np.array(before[n]['world']);new=np.array(now['world']);expected=old.copy();expected[:3,3]+=np.array(delta);assert np.max(np.abs(new-expected))<5e-7
 moved=[]
 for item in report['separated_parts']:
  o=bpy.data.objects[item['name']];assert o.parent.name==item['parent'];assert len(o.data.vertices)==item['vertices'];assert all((o.matrix_world@v.co).y<0 for v in o.data.vertices)
  moved.append(o.name)
 results.append({'file':name,'status':'PASS_NATIVE_SIDE_CORRECTION_ONLY','candidate_sha256':report['candidate_sha256'],'unrelated_geometry_authored_uv_transform_parent_preserved':len(before)-len(roots)-len(descendants),'source_faces_uvs_materials_accounted_without_loss':True,'steering_world_translation_m':list(shift),'steering_orientation_and_shape_preserved':True,'seven_controls_entirely_in_left_half_space':moved,'runtime_pose_override':'OPEN; existing web rig must be explicitly reconciled','factory_internal_dimensions_and_control_identities':'OPEN','all16VehicleGates':'OPEN'})
 assert hashlib.sha256(dst.read_bytes()).hexdigest()==report['candidate_sha256']
 (OUT/'native-readback.json').write_text(json.dumps(results,indent=2)+'\n');print('LEFT_DRIVER_READBACK',name,len(moved),flush=True)
assert len(results)==2
