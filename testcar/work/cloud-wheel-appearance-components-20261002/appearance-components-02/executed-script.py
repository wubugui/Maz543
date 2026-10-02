"""Read the same six appearance representatives at one fresh open; no model edits.

The four reported-variable objects and two reported-stable controls come from
the completed independent comparison, not from an assumed cause. Digests cover
original float32 bytes; complete mesh/UV arrays are not written.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);base=Path(a.base);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0'
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert sha(base.read_bytes())==a.sha
SELECTION=[('BL_Hub_0_cover','previous_combined_hash_differed'),('BL_Wheel_0_nut_0.26_1','previous_combined_hash_differed'),('BL_Wheel_0_washer_0.343_12','previous_combined_hash_differed'),('BL_Tyre_0_curved_tread_blocks','previous_combined_hash_differed'),('BL_Tyre_0_VI203_profile','previous_combined_hash_stable'),('BL_Rim_0_bead_lock','previous_combined_hash_stable')]
COMPARISON_SHA='1c211a71f014954c2919644c9ec2a1d51c053ff511d8dcf7c3fad7810fee5002'

def array_digest(array,shape):
 return {'dtype':array.dtype.str,'shape':shape,'bytes':array.nbytes,'sha256':sha(array.tobytes())}
def mesh_appearance(mesh,obj):
 layers=[];signature_layers=[]
 for layer in mesh.uv_layers:
  uv=np.empty(len(layer.data)*2,dtype=np.float32);layer.data.foreach_get('uv',uv);finite=np.isfinite(uv);v=uv.reshape(-1,2)
  signature_layers.append({'name':layer.name,'loops':len(layer.data),'sha256':sha(uv.tobytes()),'active_render':layer.active_render})
  layers.append({'name':layer.name,'active_render':layer.active_render,'raw_float_bytes':array_digest(uv,[len(layer.data),2]),'nonfinite_values':int(np.count_nonzero(~finite)),'negative_zero_values':int(np.count_nonzero((uv==0)&np.signbit(uv))),'finite_min_by_component':[float(v[:,i][np.isfinite(v[:,i])].min()) if np.isfinite(v[:,i]).any() else None for i in range(2)],'finite_max_by_component':[float(v[:,i][np.isfinite(v[:,i])].max()) if np.isfinite(v[:,i]).any() else None for i in range(2)]})
 indices=np.empty(len(mesh.polygons),dtype=np.int32);mesh.polygons.foreach_get('material_index',indices);values,counts=np.unique(indices,return_counts=True)
 materials=[m.name if m else None for m in mesh.materials];slots=[(s.link,s.material.name if s.material else None) for s in obj.material_slots];active=mesh.uv_layers.active.name if mesh.uv_layers.active else None
 signature={'uv':signature_layers,'active_uv':active,'evaluated_materials':materials,'object_material_slots':slots,'polygon_material_index_sha256':sha(indices.tobytes())}
 result={'uv_layers':layers,'active_uv':active,'material_list':materials,'object_material_slots':slots,'polygon_material_indices':{**array_digest(indices,[len(indices)]),'histogram':[[int(v),int(c)] for v,c in zip(values,counts)]},'original_combined_signature_components':signature,'original_combined_signature_sha256':sha(json.dumps(signature,sort_keys=True).encode())}
 return result

started=time.monotonic();cases=[]
for index in range(1):
 load_start=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(base))
 saved_frame=bpy.context.scene.frame_current;saved_subframe=bpy.context.scene.frame_subframe
 assert saved_frame==0 and saved_subframe==0
 bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();assert dg.mode=='VIEWPORT';load_seconds=time.monotonic()-load_start
 rows=[]
 for name,role in SELECTION:
  obj=bpy.data.objects[name];assert obj.type=='MESH'
  raw=mesh_appearance(obj.data,obj);ev=obj.evaluated_get(dg);mesh=ev.to_mesh()
  try:
   # Ordering digests help distinguish attribute changes from ordering changes;
   # no vertex, triangle or UV arrays are saved.
   xyz=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',xyz)
   loops=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',loops)
   mesh.calc_loop_triangles();tri=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',tri)
   evaluated=mesh_appearance(mesh,obj)
   geometry={'local_vertex_float_bytes':array_digest(xyz,[len(mesh.vertices),3]),'loop_vertex_indices':array_digest(loops,[len(mesh.loops)]),'triangle_indices':array_digest(tri,[len(mesh.loop_triangles),3])}
  finally:ev.to_mesh_clear()
  rows.append({'object':name,'selection_role':role,'rotation_mode':obj.rotation_mode,'parent':obj.parent.name if obj.parent else None,'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport} for m in obj.modifiers],'raw_mesh_appearance':raw,'evaluated_mesh_appearance':evaluated,'evaluated_geometry_ordering':geometry})
 case={'fresh_open':index,'saved_frame_before_init':saved_frame,'saved_subframe_before_init':saved_subframe,'evaluated_frame':bpy.context.scene.frame_current,'evaluated_subframe':bpy.context.scene.frame_subframe,'spin_rotation_mode':bpy.data.objects['wheels_pivot_002'].rotation_mode,'initialization_calls':['open_mainfile','scene.frame_set(0)','view_layer.update','evaluated_depsgraph_get'],'load_and_update_seconds':load_seconds,'elapsed_seconds':time.monotonic()-started,'rows':rows}
 (out/f'appearance-open-{index}.json').write_text(json.dumps(case,indent=2,allow_nan=False)+'\n');cases.append(case)
 print(json.dumps({'fresh_open':index,'objects':len(rows),'load_seconds':load_seconds,'elapsed_seconds':time.monotonic()-started}),flush=True)

assert sha(base.read_bytes())==a.sha
report={'status':'SMALL_READ_ONLY_APPEARANCE_SINGLE_OPEN_COMPLETE','source_sha256_before':a.sha,'source_sha256_after':sha(base.read_bytes()),'selection_basis_parent_comparison_sha256':COMPARISON_SHA,'blender_version':bpy.app.version_string,'blender_build_hash':bpy.app.build_hash.decode(),'autoexec':False,'objects':len(SELECTION),'fresh_opens':1,'saved_blend_glb':False,'transformed_applied_or_rendered':False,'limits':['This is one fresh open in a new process. Its complete case may be compared with the persisted first case from appearance-components-01; the unfinished second open of that timeout process is unavailable.','The same six objects, selection order, appearance function, and open_mainfile, scene.frame_set(0), view_layer.update, evaluated_depsgraph_get initialization are retained.','Six representatives cannot establish whole301object stability; earlier combined-only hashes do not localize their historical changes.','No object transform, modifier Apply, model save, or render. Material lists and bindings are read, not complete shader-node or renderer state.'],'all16VehicleGates':'OPEN'}
(out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(report['status'],flush=True)
