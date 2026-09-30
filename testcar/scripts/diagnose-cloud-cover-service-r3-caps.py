import bpy,bmesh,json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'outputs/cloud-cover-service-r3-20260930';bpy.ops.wm.open_mainfile(filepath=str(OUT/'MAZ543A_Master.blend'))
r=[]
for n in ['BL_Front_cover_latch_-0.46','BL_Front_cover_latch_0.46']:
 o=bpy.data.objects[n]
 def top():
  bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();bm=bmesh.new();bm.from_mesh(m);out={'vertices':len(m.vertices),'faces':len(m.polygons),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True),'boundaryPositions':[[list(v.co) for v in e.verts] for e in bm.edges if e.is_boundary]};bm.free();e.to_mesh_clear();return out
 row={'object':n,'useFillCaps':o.data.use_fill_caps,'before':top()}
 try:
  mod=o.modifiers.new('Test native welded cap rims 1um','WELD');mod.merge_threshold=.000001;row['afterWeld']=top()
 except Exception as e:row['error']=str(e)
 r.append(row)
(OUT/'latch-cap-diagnosis.json').write_text(json.dumps(r,indent=2));print([(x['object'],x['useFillCaps'],x['before']['boundaryEdges'],x.get('afterWeld',{}).get('boundaryEdges'),x.get('error')) for x in r])
