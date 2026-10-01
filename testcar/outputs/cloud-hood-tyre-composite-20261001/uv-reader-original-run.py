# Archived script for evidence only; absolute execution path redacted.
import bpy,json,hashlib,numpy as np
from pathlib import Path
base=Path('__ORIGINAL_PROJECT_OUTPUTS_PATH__');out=base/'cloud-hood-tyre-composite-20261001'
rows=[]
def stats(a):
 return {'length':len(a),'nan':int(np.isnan(a).sum()),'finite':int(np.isfinite(a).sum()),'first12':a[:12].tolist(),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
for stage,path in [('source',base/'cloud-cover-contour-20261001/MAZ543A_Master.blend'),('source_again',base/'cloud-cover-contour-20261001/MAZ543A_Master.blend'),('candidate',out/'MAZ543A_Master.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['BL_Front_cover_front_panel'];ev=o.evaluated_get(dg)
 for preserve in [False,True]:
  m=ev.to_mesh(preserve_all_data_layers=preserve,depsgraph=dg);m.calc_loop_triangles()
  for layer in m.uv_layers:
   a=np.full(len(layer.data)*2,np.nan,dtype=np.float32);layer.data.foreach_get('uv',a)
   manual=np.array([tuple(x.uv) for x in layer.data],dtype=np.float32).ravel()
   b=np.full(len(layer.uv)*2,np.nan,dtype=np.float32);layer.uv.foreach_get('vector',b)
   rows.append({'stage':stage,'preserve_all':preserve,'layer':layer.name,'loop_count':len(m.loops),'legacy_bulk':stats(a),'direct_items':stats(manual),'modern_bulk':stats(b),'modifier_stack':[(v.name,v.type) for v in o.modifiers]})
  ev.to_mesh_clear()
(out/'uv-readback-diagnostic.json').write_text(json.dumps(rows,indent=2));print('UV_DIAGNOSTIC',json.dumps(rows),flush=True)
print('API_TO_MESH',bpy.types.Object.to_mesh.__doc__,flush=True)
