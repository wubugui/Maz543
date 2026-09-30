import bpy,json
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath='D:/testcar/outputs/MAZ543A_Cardan_Master.blend')
s=json.load(open('D:/testcar/work/cardan-clearance-samples.json'))[0]
for n,p in s['pose'].items():
    o=bpy.data.objects[n];o.animation_data_clear();o.location=(p['p'][0],-p['p'][2],p['p'][1]);q=p['q'];o.rotation_quaternion=(q[3],q[0],-q[2],q[1])
bpy.context.view_layer.update()
def tree(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@v.co for v in m.vertices];f=[tuple(p.vertices) for p in m.loop_triangles];t=BVHTree.FromPolygons(v,f,all_triangles=True);e.to_mesh_clear();return t,v,f
a=bpy.data.objects['CJ_male_spline'];b=bpy.data.objects['CJ_female_spline']
for mode in ['bevelled','raw']:
    if mode=='raw':a.modifiers.clear();b.modifiers.clear();bpy.context.view_layer.update()
    ta,va,fa=tree(a);tb,vb,fb=tree(b);hits=ta.overlap(tb);print(mode,len(hits),flush=True)
    for x,y in hits[:3]:print([[tuple(va[i]) for i in fa[x]],[tuple(vb[i]) for i in fb[y]]],flush=True)
