import bpy,bmesh
bpy.ops.wm.open_mainfile(filepath='E:/Maz543/testcar/outputs/MAZ543A_Transmission.blend')
for name in ['TX_case47_front_web','TX_case47_reverse_web','TX_second_booster_back_wall','TX_reverse_booster_back_wall','TX_end_cover_-0.25']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bad=[e for e in bm.edges if not e.is_manifold]
 print(name,'bad',len(bad),'verts',len(bm.verts),'faces',len(bm.faces))
 for e in bad[:8]:print('edge faces',len(e.link_faces),'length',e.calc_length(),'coords',[tuple(v.co) for v in e.verts])
 bm.free()
