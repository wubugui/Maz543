report={'scope':'Complete upper rectangular mirrors seen in supplied bare MAZ543A chassis photographs; original fine rods retained','files':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();parts=[];checks=[]
    for side,parent_name in [(-1,'cab_pivot_001'),(1,'cab_pivot_005')]:
        p=bpy.data.objects[parent_name];steel=bpy.data.materials['MAZ543A_Front_dark_enamel']
        head=cube(f'BL_Front_upper_mirror_housing_{side}',[.022,.23,.16],[-5.415,2.57,side*1.55],steel,p);parts.append(head)
        face=cube(f'BL_Front_upper_mirror_face_{side}',[.0022,.208,.14],[-5.403,2.57,side*1.55],bpy.data.materials['Worn_steel'],p);parts.append(face)
        head['source']='maz543a-4.jpg and maz543a-5.jpg bare chassis; museum rod has missing mirror face';head['dimensionStatus']='Photo fitted; factory mirror dimensions, exact joint, optical behavior OPEN'
        bpy.context.view_layer.update();arm=bpy.data.objects[f'BL_Front_upper_fine_rod_{side}'];count=len(tree(head).overlap(tree(arm)));assert count>0,('Detached upper mirror housing',filename,side)
        checks.append({'housing':head.name,'rod':arm.name,'intersectionPairs':count,'faceDirection':'Rear-facing +X'})
    report['files'].append({'file':filename,'parts':[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in parts],'connections':checks,'limits':'Complete chassis reference assumption; exact dims, swivel range, optical rear view, full dynamic clearance OPEN'})
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
(OUT/'front-upper-mirrors-verification.json').write_text(json.dumps(report,indent=2))
