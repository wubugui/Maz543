"""Read-only source check: evaluate tangent attributes; never save/re-export."""
import bpy,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tangent-audit';OUT.mkdir(parents=True,exist_ok=True)
cases=[('MAZ543A_Textured.blend',['BL_Merged_body_OD_green_aged_enamel','BL_Merged_body_Rubber_window_seals','BL_Merged_wheels_pivot_002_Tyre_rubber']),('MAZ543A_Cooling_Master.blend',['COOL_upper_input_flange_0']),('D12A525A_Engine_Master.blend',['D12_cover_L_D12_cover_enamel_cover'])]
rows=[]
for file,names in cases:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/file));depsgraph=bpy.context.evaluated_depsgraph_get()
 for name in names:
  obj=bpy.data.objects.get(name)
  if obj is None:rows.append({'file':file,'name':name,'missing':True,'candidates':[o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(name.split('_D12_')[0])]});continue
  evaluated=obj.evaluated_get(depsgraph);mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
  try:
   mesh.calc_loop_triangles();mesh.calc_tangents();tangents=np.empty(len(mesh.loops)*3,dtype=np.float32);mesh.loops.foreach_get('tangent',tangents);tangents=tangents.reshape(-1,3);lengths=np.linalg.norm(tangents.astype(np.float64),axis=1)
   uv=np.empty(len(mesh.loops)*2,dtype=np.float32);mesh.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
   bad=np.flatnonzero(lengths<.01);samples=[]
   coords=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',coords);coords=coords.reshape(-1,3).astype(float);bad_set=set(map(int,bad));incident=[]
   for triangle in mesh.loop_triangles:
    if not bad_set.intersection(triangle.loops):continue
    a,b,c=coords[list(triangle.vertices)];incident.append(float(np.linalg.norm(np.cross(b-a,c-a))/2))
   for loop in bad[:12]:
    triangles=[]
    for triangle in mesh.loop_triangles:
     if int(loop) not in triangle.loops:continue
     a,b,c=uv[list(triangle.loops)];p,q,r=coords[list(triangle.vertices)];triangles.append({'loops':list(triangle.loops),'uvDeterminant':float(np.linalg.det(np.stack([b-a,c-a]))),'surfaceArea':float(np.linalg.norm(np.cross(q-p,r-p))/2)})
    samples.append({'loop':int(loop),'tangent':tangents[loop].tolist(),'triangles':triangles})
   rows.append({'file':file,'name':name,'mesh':mesh.name,'vertices':len(mesh.vertices),'loops':len(mesh.loops),'triangles':len(mesh.loop_triangles),'minimumLength':float(lengths.min()),'maximumLength':float(lengths.max()),'tinyLoopCount':int(len(bad)),'nonUnitAt1e4':int(np.count_nonzero(np.abs(lengths-1)>1e-4)),'uvLayer':mesh.uv_layers.active.name,'tinyIncidentTriangles':len(incident),'tinyIncidentMinArea':min(incident,default=0),'tinyIncidentMaxArea':max(incident,default=0),'tinyIncidentZeroAreas':sum(value==0 for value in incident),'samples':samples})
  finally:evaluated.to_mesh_clear()
report={'readOnly':True,'savedNativeFiles':False,'cases':rows}
(OUT/'native-source-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('NATIVE_TANGENT_AUDIT',json.dumps([{k:v for k,v in row.items() if k!='samples'} for row in rows]),flush=True)
