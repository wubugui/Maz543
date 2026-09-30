import bpy,json
from mathutils.bvhtree import BVHTree
from pathlib import Path
out=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(out/'FG16_Native_Structural_Study.blend'))
bpy.context.window.scene=bpy.data.scenes['FG16_ASSEMBLED_STUDY']
o=bpy.data.objects['FG16_06_Hollow_curved_body'];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
p=[o.matrix_world@v.co for v in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles]
t=BVHTree.FromPolygons(p,f,all_triangles=True,epsilon=0)
hits=[(a,b) for a,b in t.overlap(t) if a<b and not set(f[a]).intersection(f[b])]
detail=[]
for a,b in hits:
 detail.append({'triangles':[a,b],'vertices_a':[list(p[i]) for i in f[a]],'vertices_b':[list(p[i]) for i in f[b]],'closest_vertex_distance_m':min((p[i]-p[j]).length for i in f[a] for j in f[b])})
(out/'body-self-intersection-diagnostic.json').write_text(json.dumps(detail,indent=2))
print(json.dumps(detail,indent=2))
