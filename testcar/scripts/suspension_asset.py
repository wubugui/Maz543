import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def descendants(o):
    result=[]
    for c in o.children:result.append(c);result+=descendants(c)
    return result
def export_suspension(root):
    # Apply each authored edge/normal modifier before joining, so differing cast
    # and machined edge radii survive batching without inheriting one radius.
    bpy.ops.object.select_all(action='DESELECT')
    rigid=[o for o in descendants(root) if o.type=='MESH' and o.get('s543Role')!='torsion']
    for o in rigid:o.select_set(True)
    if rigid:
        bpy.context.view_layer.objects.active=rigid[0];bpy.ops.object.convert(target='MESH')
    # Preserve deforming torsion meshes; batch fixed siblings for browser draw cost.
    for holder in [root]+[o for o in descendants(root) if o.type=='EMPTY']:
        batches={}
        for ob in holder.children:
            if ob.type!='MESH' or ob.get('s543Role')=='torsion':continue
            role=ob.get('s543Role');role=role if role in ['cover','internal','torsion'] else 'visible'
            key=(ob.data.materials[0].name,role);batches.setdefault(key,[]).append(ob)
        for key,batch in batches.items():
            if len(batch)<2:continue
            bpy.ops.object.select_all(action='DESELECT')
            for ob in batch:ob.select_set(True)
            sources=list(set(ob.get('sourceId','') for ob in batch));bpy.context.view_layer.objects.active=batch[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=holder.name+'_'+key[0]+'_'+key[1];ob['detail_meshes']=len(batch);ob['s543Role']=key[1];ob['sourceIds']=sources
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [root]+descendants(root):
        ob.select_set(True)
        if ob.type=='MESH' and any(len(p.vertices)>4 for p in ob.data.polygons):
            tri=ob.modifiers.new('Triangulate n-gons for tangent export','TRIANGULATE');tri.min_vertices=5
            if hasattr(tri,'keep_custom_normals'):tri.keep_custom_normals=True
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/maz543a-suspension.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_tangents=True,export_extras=True,export_animations=False,export_morph=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
