"""Bake the native casting finish into portable UV maps for the browser asset."""
def bake_cooling_surfaces(material_name, flag, prefix):
    material=bpy.data.materials[material_name];nodes=material.node_tree.nodes;links=material.node_tree.links
    objects=[o for o in bpy.data.objects if o.get(flag) and o.type in ['MESH','CURVE'] and material in list(o.data.materials)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.convert(target='MESH')
    for o in objects:
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(o.data);bm.free()
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type!='CPU'
        scene.cycles.device='GPU'
    except:pass
    bsdf=nodes.get('Principled BSDF');output=nodes.get('Material Output')
    target=nodes.new('ShaderNodeTexImage');normal=bpy.data.images.new(prefix+'_normal',2048,2048,alpha=False);normal.colorspace_settings.name='Non-Color';target.image=normal;nodes.active=target
    scene.render.bake.margin=8;bpy.ops.object.bake(type='NORMAL');normal.pack()
    # A separate scalar roughness bake keeps the photo's uneven storage enamel.
    rough=bpy.data.images.new(prefix+'_roughness',2048,2048,alpha=False);rough.colorspace_settings.name='Non-Color';target.image=rough
    ramp=nodes.new('ShaderNodeValToRGB');lo,hi=(.28,.48) if flag=='lowerDrive' else (.40,.60);ramp.color_ramp.elements[0].color=(lo,lo,lo,1);ramp.color_ramp.elements[1].color=(hi,hi,hi,1)
    links.new(nodes.get('Noise Texture').outputs['Fac'],ramp.inputs[0]);emission=nodes.new('ShaderNodeEmission');links.new(ramp.outputs['Color'],emission.inputs['Color']);links.new(emission.outputs[0],output.inputs[0]);bpy.ops.object.bake(type='EMIT');rough.pack()
    links.new(bsdf.outputs[0],output.inputs[0]);nodes.remove(emission)
    target.image=normal;normalmap=nodes.new('ShaderNodeNormalMap');links.new(target.outputs['Color'],normalmap.inputs['Color']);links.new(normalmap.outputs['Normal'],bsdf.inputs['Normal'])
    roughnode=nodes.new('ShaderNodeTexImage');roughnode.image=rough;links.new(roughnode.outputs['Color'],bsdf.inputs['Roughness'])
    for o in objects:o['surfaceEvidence']='Procedural cast finish; lower storage enamel photo-guided, upper alloy finish unverified; not measured surface topography'
    print('COOLING_BAKED_SURFACES',material_name,len(objects),flush=True)
bake_cooling_surfaces('COOL_lower_black_storage_enamel','lowerDrive','COOL_lower_cast')
bake_cooling_surfaces('COOL_upper_cast_alloy','upperGearbox','COOL_upper_cast')
