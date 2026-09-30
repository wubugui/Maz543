import bpy,bmesh,json
bpy.ops.wm.open_mainfile(filepath='E:/Maz543/testcar/outputs/MAZ543A_Transmission.blend')
for name in ['TX_direct_body46_sleeve','TX_direct_booster_back_wall']:
    bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data)
    before=sum(not e.is_manifold for e in bm.edges)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-10)
    bad=[e for e in bm.edges if not e.is_manifold]
    print(name,'before',before,'after',len(bad))
    print(json.dumps([{'faces':len(e.link_faces),'length':e.calc_length(),'verts':[list(v.co) for v in e.verts]} for e in bad]))
    bm.free()
