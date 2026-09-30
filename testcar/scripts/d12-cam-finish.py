"""Ground steel / forged shaft finish and discontinuous machined normals.
Only normals and material assignments change; no vertex position is modified.
"""
import bpy,bmesh,math

def cam_material(name,color,roughness):
    m=bpy.data.materials.get(name)
    if m:return m
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=.88;bs.inputs['Roughness'].default_value=roughness
    return m
ground=cam_material('D12_cam_ground_steel',(.13,.145,.132),.38)
forged=cam_material('D12_cam_forged_shaft',(.043,.05,.043),.49)
for ob in bpy.data.objects:
    if not ob.get('camTrain') or ob.type not in ['MESH','CURVE']:continue
    if ob.data.materials and ob.data.materials[0].name.startswith(('D12_machined_steel','D12_forged_steel','D12_cam_ground_steel','D12_cam_forged_shaft')):
        ob.data.materials[0]=forged if ob.name.startswith(('D12_camshaft_','D12_cam_sleeve_lock','D12_cam_retainer_lock','D12_cam_rear_circlip')) else ground
    if ob.type!='MESH':continue
    # Direct mesh flags preserve the tested geometry and avoid BMesh rewriting
    # Boolean-cut lobe polygons. Sharp shoulders must not shade like soft metal.
    bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
    bm.edges.ensure_lookup_table();sharp={e.index for e in bm.edges if not e.is_manifold or e.calc_face_angle(0)>.52};bm.free()
    for p in ob.data.polygons:p.use_smooth=True
    for e in ob.data.edges:e.use_edge_sharp=e.index in sharp
    ob.data.update()
