"""Read back both saved typography candidates and check their actual geometry."""
import bpy,bmesh,json,math,os
from pathlib import Path
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('MAZ_LETTERING_DIR',str(ROOT/'outputs/cloud-tyre-lettering-20260930'))).resolve()
def evaluated(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
 vs=[ev.matrix_world@v.co for v in m.vertices];tris=[tuple(t.vertices) for t in m.loop_triangles];bm=bmesh.new();bm.from_mesh(m);info={'vertices':len(vs),'triangles':len(tris),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)};bm.free();ev.to_mesh_clear();return vs,tris,info
def kd(points):
 k=KDTree(len(points))
 for i,p in enumerate(points):k.insert(p,i)
 k.balance();return k
reference={};rows=[];failures=[]
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(OUT/filename));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
 letters=sorted([o for o in bpy.data.objects if o.name.startswith('BL_Tyre_') and '_emboss_' in o.name],key=lambda o:o.name)
 assert len(letters)==144 and all(o.type=='MESH' for o in letters)
 tyres={}
 if filename=='MAZ543A_Master.blend':
  for index in range(8):
   vs,tris,_=evaluated(bpy.data.objects[f'BL_Tyre_{index}_VI203_profile']);tyres[index]=BVHTree.FromPolygons(vs,tris,all_triangles=True)
 for obj in letters:
  vs,tris,info=evaluated(obj);assert info['nonManifoldEdges']==0 and info['volume']>0,(filename,obj.name,info)
  row={'file':filename,'name':obj.name,**info}
  if filename=='MAZ543A_Master.blend':
   reference[obj.name]=vs;index=obj['tyreIndex'];distances=[]
   for p in vs:
    hit,normal,_,distance=tyres[index].find_nearest(p);assert hit is not None
    # Orient the queried sidewall normal towards the known outside of this wheel.
    side=1 if index%2 else -1
    if normal.y*(-side)<0:normal=-normal
    distances.append((p-hit).dot(normal))
   row['minSignedSidewallDistanceM']=min(distances);row['maxSignedSidewallDistanceM']=max(distances)
   assert -.0002<min(distances)<0 and .0003<max(distances)<.002,(obj.name,min(distances),max(distances))
  else:
   a=kd(vs);b=kd(reference[obj.name]);error=max(max(b.find(p)[2] for p in vs),max(a.find(p)[2] for p in reference[obj.name]));row['masterWorldVertexHausdorffM']=error
   if error>=2e-5:failures.append({'name':obj.name,'vertexDeviationM':error})
  rows.append(row)
report={'status':'FAIL_NATIVE_PARITY' if failures else 'PASS_NATIVE_GLYPH_GEOMETRY_ONLY','failures':failures,'glyphsPerFile':144,'results':rows,'limits':'Position, native manifold solids, sidewall attachment and Master/Textured evaluated vertex correspondence only. Typography size/style and original fitment remain reconstructed. No browser or entire-vehicle acceptance.'}
report_path=Path(os.environ.get('MAZ_NATIVE_REPORT',str(OUT/'lettering-readback.json'))).resolve()
report_path.parent.mkdir(parents=True,exist_ok=True)
report_path.write_text(json.dumps(report,indent=2))
assert not failures,failures
print('NATIVE_LETTERING_READBACK_PASS',len(rows),'max correspondence',max(r.get('masterWorldVertexHausdorffM',0) for r in rows))
