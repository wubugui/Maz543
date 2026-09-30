report={'scope':'Dark front painted metal matching clear photographic tone; no unapproved global material replacement','files':[]}
prefixes=('BL_Front_box_bumper','BL_Front_hook_mount','BL_Front_single_recovery_hook','BL_Front_lower_shield','BL_Front_bumper_frame_mount_','BL_Front_shield_stay_','BL_Front_mirror_root_mount_','BL_Front_upper_fine_rod_')
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0)
    mat=bpy.data.materials.new('MAZ543A_Front_dark_enamel');mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.009,.012,.010,1);bs.inputs['Metallic'].default_value=.12;bs.inputs['Roughness'].default_value=.72
    mat.diffuse_color=(.009,.012,.010,1);mat['source']='museum-front and museum-front-oblique; shade photo-fitted, no colorimetric factory calibration'
    changed=[]
    for o in bpy.data.objects:
        if o.parent and o.type in ['MESH','CURVE'] and o.name.startswith(prefixes):o.data.materials.clear();o.data.materials.append(mat);changed.append(o.name)
    assert len(changed)==12,('Unexpected front metal scope',len(changed),changed)
    report['files'].append({'file':filename,'changedMaterialOnly':changed,'limits':'Factory color, weathering, mechanical load rating and full-vehicle paint acceptance OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if filename.endswith('Textured.blend'):
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'front-dark-enamel-verification.json').write_text(json.dumps(report,indent=2))
