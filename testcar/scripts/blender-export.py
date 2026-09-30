"""Bake Blender-authored materials to a shared PBR atlas, export the browser asset.
Run after blender-model.py. Master topology remains in MAZ543A_Master.blend.
"""
import bpy, bmesh, math, json, time
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs';TEX=ROOT/'public'/'models'/'textures'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'MAZ543A_Master.blend'))
scene=bpy.context.scene
root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
def descendants(o):
    result=[]
    for c in o.children:result.append(c);result+=descendants(c)
    return result
def separate_module(obj):
    while obj:
        if obj.name in ['D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT']:return True
        obj=obj.parent
    return False
model_objects=[o for o in descendants(root) if not separate_module(o)]

# Additional world-scale weathering: broad paint variation and dusty lower surfaces.
for name in ['OD_green_aged_enamel','OD_green_shadow']:
    mat=bpy.data.materials[name];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    original=bs.inputs['Base Color'].links[0].from_socket
    geo=nodes.new('ShaderNodeNewGeometry');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.8;noise.inputs['Detail'].default_value=4;links.new(geo.outputs['Position'],noise.inputs['Vector'])
    sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
    height=nodes.new('ShaderNodeMapRange');height.clamp=True;height.inputs['From Min'].default_value=.9;height.inputs['From Max'].default_value=2.0;height.inputs['To Min'].default_value=.38;height.inputs['To Max'].default_value=.025;links.new(sep.outputs['Z'],height.inputs['Value'])
    factor=nodes.new('ShaderNodeMath');factor.operation='MULTIPLY';links.new(noise.outputs['Fac'],factor.inputs[0]);links.new(height.outputs['Result'],factor.inputs[1])
    dirt=nodes.new('ShaderNodeMixRGB');dirt.blend_type='MIX';dirt.inputs[2].default_value=(.12,.10,.060,1);links.new(factor.outputs[0],dirt.inputs[0]);links.new(original,dirt.inputs[1]);links.new(dirt.outputs[0],bs.inputs['Base Color'])

# Evaluate bevel, subdivision and solidify for the browser while retaining pivots.
bpy.ops.object.select_all(action='DESELECT')
convert=[o for o in model_objects if o.type in {'MESH','CURVE','FONT'}]
for obj in convert:obj.hide_set(False);obj.select_set(True)
bpy.context.view_layer.objects.active=convert[0];bpy.ops.object.convert(target='MESH')
model_objects=[o for o in descendants(root) if not separate_module(o)]

# Mirrored authored shells must have outward face winding before AO ray baking.
# Cycles beauty shading hid reversed faces; the AO bake turned the left doors black.
normal_fixes=[]
for obj in model_objects:
    if obj.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(obj.data)
    ngons=[f for f in bm.faces if len(f.verts)>4]
    if ngons:bmesh.ops.triangulate(bm,faces=ngons,quad_method='BEAUTY',ngon_method='BEAUTY')
    before=[f.normal.copy() for f in bm.faces]
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
    flipped=sum(1 for old,face in zip(before,bm.faces) if old.dot(face.normal)<-.5)
    if flipped:normal_fixes.append({'object':obj.name,'flipped_faces':flipped})
    bm.to_mesh(obj.data);bm.free();obj.data.update()
(OUT/'normal-repair.json').write_text(json.dumps(normal_fixes,indent=2))

# Merge fixed detailed siblings by material, preserving every imported rig object.
batches={}
for obj in model_objects:
    if obj.type=='MESH' and obj.name.startswith('BL_') and len(obj.data.materials)==1:
        key=(obj.parent,obj.data.materials[0],obj.get('surface',''))
        batches.setdefault(key,[]).append(obj)
for (parent,mat,surface),objects in batches.items():
    if len(objects)<3:continue
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    active=objects[0];bpy.context.view_layer.objects.active=active;bpy.ops.object.join()
    active.name=f'BL_Merged_{parent.name}_{mat.name}';active['surface']=surface;active['detail_meshes']=len(objects)
model_objects=[o for o in descendants(root) if not separate_module(o)]
targets=[o for o in model_objects if o.type=='MESH' and o.name.startswith('BL_') and all(m.name not in ['Laminated_glass','Headlamp_prismatic_glass','Amber_signal_glass'] for m in o.data.materials)]
print('BAKE_TARGETS',len(targets),'POLYGONS',sum(len(o.data.polygons) for o in targets),flush=True)

# Shared non-overlapping texture atlas, unwrapped and packed natively in Blender.
bpy.ops.object.select_all(action='DESELECT')
for obj in targets:obj.select_set(True)
bpy.context.view_layer.objects.active=targets[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(70),island_margin=.003,area_weight=.1,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
print('UV_ATLAS_READY',flush=True)

# One temporary bake mesh avoids rebuilding the scene once for each of 89 objects.
# Copying preserves the original articulated model and its UV atlas exactly.
original_targets=targets[:]
bpy.ops.object.select_all(action='DESELECT')
duplicates=[]
for source in original_targets:
    duplicate=source.copy();duplicate.data=source.data.copy();bpy.context.collection.objects.link(duplicate);duplicate.select_set(True);duplicates.append(duplicate)
bpy.context.view_layer.objects.active=duplicates[0];bpy.ops.object.join();bake_object=duplicates[0];bake_object.name='TEMP_ATLAS_BAKE_MESH';targets=[bake_object]

try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.bake.margin=8;scene.render.bake.use_clear=True;scene.render.bake.use_selected_to_active=False
for obj in bpy.data.objects:
    if obj not in targets:obj.hide_render=True
materials=set(m for o in targets for m in o.data.materials)
def bake_map(name,kind,size=2048,noncolor=False):
    image=bpy.data.images.new(name,width=size,height=size,alpha=False)
    if noncolor:image.colorspace_settings.name='Non-Color'
    for mat in materials:
        nodes=mat.node_tree.nodes;node=nodes.new('ShaderNodeTexImage');node.name='BAKE_TARGET';node.image=image;nodes.active=node
    scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
    bpy.ops.object.bake(type=kind)
    image.filepath_raw=str(TEX/(name+'.png'));image.file_format='PNG';image.save()
    for mat in materials:
        for node in list(mat.node_tree.nodes):
            if node.name.startswith('BAKE_TARGET'):mat.node_tree.nodes.remove(node)
    print('BAKED',name,flush=True);return image
color=bake_map('MAZ543A_BaseColor','DIFFUSE',4096)
rough=bake_map('MAZ543A_Roughness','ROUGHNESS',2048,True)
normal=bake_map('MAZ543A_Normal','NORMAL',2048,True)
# AO is baked with the full assembly present, so recesses reflect real geometry.
for obj in model_objects:obj.hide_render=obj in original_targets
ao=bake_map('MAZ543A_Occlusion','AO',2048,True)

# Bake actual per-material metalness; rubber must not inherit painted-metal values.
saved_outputs=[]
for mat in materials:
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    saved_outputs.append((mat,out,out.inputs['Surface'].links[0].from_socket))
    emit=nodes.new('ShaderNodeEmission');emit.name='TEMP_METALNESS';value=bs.inputs['Metallic'].default_value;emit.inputs['Color'].default_value=(value,value,value,1);links.new(emit.outputs[0],out.inputs['Surface'])
metal=bake_map('MAZ543A_Metallic','EMIT',2048,True)
for mat,out,socket in saved_outputs:
    mat.node_tree.links.new(socket,out.inputs['Surface']);mat.node_tree.nodes.remove(mat.node_tree.nodes['TEMP_METALNESS'])

# Pack occlusion / roughness / metallic in glTF's standard RGB layout.
arr=np.empty(2048*2048*4,dtype=np.float32);aa=np.empty_like(arr);rr=np.empty_like(arr);mm=np.empty_like(arr)
ao.pixels.foreach_get(aa);rough.pixels.foreach_get(rr);metal.pixels.foreach_get(mm);arr[0::4]=aa[0::4];arr[1::4]=rr[0::4];arr[2::4]=mm[0::4];arr[3::4]=1
orm=bpy.data.images.new('MAZ543A_ORM',width=2048,height=2048,alpha=False);orm.colorspace_settings.name='Non-Color';orm.pixels.foreach_set(arr);orm.filepath_raw=str(TEX/'MAZ543A_ORM.png');orm.file_format='PNG';orm.save()

atlas=bpy.data.materials.new('MAZ543A_Baked_PBR');atlas.use_nodes=True;n=atlas.node_tree.nodes;l=atlas.node_tree.links;bs=n.get('Principled BSDF')
tex=n.new('ShaderNodeTexImage');tex.image=color;l.new(tex.outputs['Color'],bs.inputs['Base Color'])
texorm=n.new('ShaderNodeTexImage');texorm.image=orm;sep=n.new('ShaderNodeSeparateColor');sep.mode='RGB';l.new(texorm.outputs['Color'],sep.inputs[0]);l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Blue'],bs.inputs['Metallic'])
tn=n.new('ShaderNodeTexImage');tn.image=normal;nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.75;l.new(tn.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal'])
group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat');gin=n.new('ShaderNodeGroup');gin.node_tree=group;l.new(sep.outputs['Red'],gin.inputs['Occlusion'])
for obj in original_targets:obj.data.materials.clear();obj.data.materials.append(atlas)
bpy.data.objects.remove(bake_object,do_unlink=True)

# Plain non-atlas metals and glazing use explicit glTF-compatible Principled values.
body_materials={m for o in model_objects if o.type=='MESH' for m in o.data.materials}
for mat in list(bpy.data.materials):
    if mat not in body_materials:continue
    if mat==atlas or not mat.use_nodes:continue
    bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not bs:continue
    for key in ['Base Color','Roughness','Normal']:
        for link in list(bs.inputs[key].links):mat.node_tree.links.remove(link)
    bs.inputs['Base Color'].default_value=mat.diffuse_color
    if mat.name=='Laminated_glass':bs.inputs['Alpha'].default_value=.33
    if mat.name=='Headlamp_prismatic_glass':bs.inputs['Emission Color'].default_value=(.7,.65,.45,1);bs.inputs['Emission Strength'].default_value=.04

# Export only the vehicle. Studio and reference planes remain in the .blend.
for obj in bpy.data.objects:obj.hide_render=False
for obj in bpy.data.collections['00_REFERENCE_PHOTOGRAPHS'].objects:obj.hide_render=True
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for obj in descendants(root):
    if not separate_module(obj):obj.hide_set(False);obj.select_set(True)
bpy.context.view_layer.objects.active=root
export_path=ROOT/'public'/'models'/'maz543a-blender.glb'
bpy.ops.export_scene.gltf(filepath=str(export_path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
for image in [color,normal,orm]:image.pack()
scene.render.filepath=str(OUT/'maz543a-textured-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Textured.blend'))
report={'created_with':bpy.app.version_string,'file':export_path.name,'bytes':export_path.stat().st_size,'objects':len(descendants(root)),'mesh_objects':len([o for o in descendants(root) if o.type=='MESH']),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in descendants(root) if o.type=='MESH'),'texture_atlas':'4096 base color / 2048 normal and ORM','accuracy':'Photographic reference reconstruction; mechanical interior simplified; not factory CAD'}
info_path=ROOT/'public'/'models'/'model-info.json'
info=json.loads(info_path.read_text()) if info_path.exists() else {}
info.update(report);info_path.write_text(json.dumps(info,indent=2))
print('BLENDER_EXPORT_READY',json.dumps(report),flush=True)
bpy.ops.render.render(write_still=True)
