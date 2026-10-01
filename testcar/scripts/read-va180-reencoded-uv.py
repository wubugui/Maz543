"""Read evaluated corner UVs of the two re-encoded inherited meshes. No edits/save."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend'
expected='6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266'
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();rows=[]
for name in ['cab_0064','BL_Left_driver_steering_column_retained']:
 o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
 layers=[{'name':u.name,'active_render':u.active_render,'corners':[[float(v.uv.x),float(1-v.uv.y)] for v in u.data]} for u in m.uv_layers]
 rows.append({'name':name,'positions_local_gltf':[[float(v.co.x),float(v.co.z),float(-v.co.y)] for v in m.vertices], 'corner_vertex_indices':[l.vertex_index for l in m.loops], 'triangles':[list(t.loops) for t in m.loop_triangles], 'uv_layers':layers,'material_slots':[s.material.name if s.material else None for s in o.material_slots]});ev.to_mesh_clear()
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
out=ROOT/'work/cloud-va180-uv-20261001';out.mkdir(exist_ok=True)
(out/'native-corner-uv.json').write_text(json.dumps({'source_sha256':expected,'meshes':rows,'source_saved':False,'scope':'Read-only corner position/UV references of two inherited re-encoded meshes; glTF V convention applied.'},separators=(',',':'))+'\n');print('NATIVE_UV_READ',[(r['name'],len(r['corner_vertex_indices']),[(u['name'],u['active_render']) for u in r['uv_layers']]) for r in rows],flush=True)
