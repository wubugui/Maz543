"""Read-back regression of actual saved candidate geometry; no source writes."""
import bpy, os, json, math
from pathlib import Path
from mathutils import Matrix
from mathutils.kdtree import KDTree

root=Path(os.environ['MAZ_CANDIDATE_DIR']).resolve()
results=[]
def local_vertices(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ev.to_mesh()
    points=[v.co.copy() for v in mesh.vertices]
    ev.to_mesh_clear()
    if not points:raise RuntimeError('Empty evaluated geometry: '+obj.name)
    return points
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(root/filename))
    hinge=bpy.data.objects['BL_Front_cover_hinge']
    bpy.context.view_layer.update()
    assert (hinge.matrix_world.translation-__import__('mathutils').Vector((-4.58,0,2.336))).length<1e-6,'Incorrect actual hinge origin'
    moving=[o for o in hinge.children if o.type in {'MESH','CURVE'} and not o.hide_render]
    base=hinge.matrix_basis.copy()
    reference={o.name:local_vertices(o) for o in moving}
    trees={}
    for name,points in reference.items():
        k=KDTree(len(points))
        for i,p in enumerate(points):k.insert(p,i)
        k.balance();trees[name]=k
    frames=[]
    for degrees in range(0,61,3):
        hinge.matrix_basis=base@Matrix.Rotation(math.radians(degrees),4,'Y')
        bpy.context.view_layer.update()
        for obj in moving:
            pts=local_vertices(obj)
            k=KDTree(len(pts))
            for i,p in enumerate(pts):k.insert(p,i)
            k.balance()
            deviation=max(max(trees[obj.name].find(p)[2] for p in pts),max(k.find(p)[2] for p in reference[obj.name]))
            frames.append({'degrees':degrees,'object':obj.name,'vertices':len(pts),'referenceVertices':len(reference[obj.name]),'localVertexHausdorffM':deviation})
    hinge.matrix_basis=base;bpy.context.view_layer.update()
    results.append({'file':filename,'maxLocalDeviationM':max(r['localVertexHausdorffM'] for r in frames),'samples':frames,'limitM':2e-5,'limitations':'Vertex-set shape regression only; no continuous collision proof, dimensional calibration, or user acceptance.'})
report={'scope':'Saved candidate read-back, rigid evaluated shape at 21 discrete hinge angles','files':results}
(root/'saved-rig-regression.json').write_text(json.dumps(report,indent=2))
assert all(r['maxLocalDeviationM']<=r['limitM'] for r in results),report
print('RIG_GEOMETRY_REGRESSION',[(r['file'],r['maxLocalDeviationM']) for r in results])
