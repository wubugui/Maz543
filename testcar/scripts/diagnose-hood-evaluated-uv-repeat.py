"""Read-only repeated evaluated-UV control; does not save modified scenes.

Run with matching Blender --threads 1 or 4. Set MAZ_UV_CONTROL_OUTPUT
to a separate directory to retain each run. Source/candidate paths are fixed
to this study; differences are reported, never converted into acceptance.
"""
import os
import bpy,numpy as np,json,hashlib
from pathlib import Path
base=Path(__file__).resolve().parents[1]/'outputs';candidate_dir=base/'cloud-hood-tyre-composite-20261001';out=Path(os.environ.get('MAZ_UV_CONTROL_OUTPUT',str(candidate_dir/'uv-repeat-reproduction')));out.mkdir(parents=True,exist_ok=True);arrays={};rows=[]
for stage,path in [('source',base/'cloud-cover-contour-20261001/MAZ543A_Master.blend'),('candidate',candidate_dir/'MAZ543A_Master.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();o=bpy.data.objects['BL_Front_cover_front_panel']
 if stage=='source':
  fn=o.bl_rna.functions['to_mesh'];rows.append({'runtime_api_description':fn.description,'preserve_parameter':fn.parameters['preserve_all_data_layers'].description})
 for mode in ['full','without_final_boolean','no_modifiers']:
  if mode=='without_final_boolean':o.modifiers[-1].show_viewport=False
  if mode=='no_modifiers':
   for mod in o.modifiers:mod.show_viewport=False
  bpy.context.view_layer.update()
  for repeat in range(2):
   dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);m=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
   m.calc_loop_triangles();layer=m.uv_layers[0];a=np.full(len(layer.uv)*2,np.nan,dtype=np.float32);layer.uv.foreach_get('vector',a)
   assert np.isfinite(a).all();key=f'{stage}_{mode}_{repeat}';arrays[key]=a
   rows.append({'key':key,'length':len(a),'min':float(a.min()),'max':float(a.max()),'sha':hashlib.sha256(a.tobytes()).hexdigest()});e.to_mesh_clear()
for key,a in arrays.items():
 if not key.startswith('source_') or not key.endswith('_0'):continue
 for other in [key[:-1]+'1',key.replace('source_','candidate_')]:
  b=arrays[other]
  if a.shape!=b.shape:rows.append({'a':key,'b':other,'shape_changed':True});continue
  idx=np.flatnonzero(a!=b);d=np.abs(a.astype(float)-b.astype(float));rows.append({'a':key,'b':other,'float_values_equal':bool(np.array_equal(a,b)),'different_float_count':len(idx),'different_bits_count':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'max_abs_difference':float(d.max()),'examples':[{'index':int(i),'a':float(a[i]),'b':float(b[i]),'delta':float(d[i])} for i in idx[:12]]})
np.savez_compressed(out/'uv-repeat-control.npz',**arrays);(out/'uv-repeat-control.json').write_text(json.dumps(rows,indent=2));print('UV_REPEAT_CONTROLS_WRITTEN',flush=True)
