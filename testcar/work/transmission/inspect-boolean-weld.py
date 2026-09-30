import bpy,bmesh
bpy.ops.wm.open_mainfile(filepath='E:/Maz543/testcar/outputs/MAZ543A_Transmission.blend')
for name in ['TX_case47_front_web','TX_end_cover_-0.25']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10)
 print(name,'after weld',sum(not e.is_manifold for e in bm.edges),'volume',bm.calc_volume())
 bm.free()
