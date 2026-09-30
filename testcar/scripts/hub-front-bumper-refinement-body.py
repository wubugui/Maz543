# Helpers are prepended from hub-front-assembly-model.py.
report={'scope':'Archive redundant low front marker arms; retain corrected mirror arms; remove empty merged nodes','files':[]};targets=None
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend')
    if not tex:
        names=[f'BL_Width_marker_{s}' for s in [-1,1]]+[f'BL_Width_marker_cap_{s}' for s in [-1,1]]
        targets={n:bounds(bpy.data.objects[n])['min']+bounds(bpy.data.objects[n])['max'] for n in names}
    split_old(tex,targets)
    empty=[]
    for o in list(bpy.data.objects):
        if o.type=='MESH' and o.name.startswith('BL_Merged') and o.parent and len(o.data.polygons)==0:
            empty.append(o.name);archive(o)
    bpy.context.view_layer.update()
    parts=[o for o in bpy.data.objects if o.name.startswith('BL_Front_') and o.parent]
    report['files'].append({'file':filename,'archivedOriginalMarkers':list(targets),'archivedEmptyNodes':empty,'parts':[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in parts],'limits':'Photographic restoration; upper fine rods, mount clearance, factory dimensions and complete door sweep remain OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if tex:
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
(OUT/'front-bumper-refinement-verification.json').write_text(json.dumps(report,indent=2))
