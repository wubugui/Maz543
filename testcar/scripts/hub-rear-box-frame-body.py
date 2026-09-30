report={'scope':'Rear toolbox assembly moved between actual third/fourth axles; original box dimensions retained; only frame paint corrected','files':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
targets=None
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend');body=bpy.data.objects['body'];parts=[];checks=[]
    names=[f'BL_Rear_box_{s}' for s in [-1,1]]+[f'BL_Rear_box_lid_{s}' for s in [-1,1]]+[f'BL_Rear_box_latch_{s}_{x}' for s in [-1,1] for x in [4.94,5.24]]
    if not tex:
        targets={n:bounds(bpy.data.objects[n])['min']+bounds(bpy.data.objects[n])['max'] for n in names}
    # Each separate original piece is kept in the archive. Its duplicate retains
    # authored geometry, modifiers and UVs; no manually generated mesh topology.
    for index,n in enumerate(names):
        before=set(bpy.data.objects);split_old(tex,{n:targets[n]})
        if tex:
            extracted=set(bpy.data.objects)-before;assert len(extracted)==1,(n,'Expected one original component');original=extracted.pop()
        else:original=bpy.data.objects[n]
        o=original.copy();o.data=original.data.copy();bpy.context.collection.objects.link(o);o.name='BL_RearRestoration_'+n.removeprefix('BL_');o.hide_render=False;o.hide_set(False);parent(o,body);o.location.x-=1.57;o['source']='maz543a-4.jpg, maz543a-5.jpg and factory-543a-profile.jpg';o['dimensionStatus']='Original fitted box dimensions retained; factory dimensions, lid internals OPEN';parts.append(o)
    paint=bpy.data.materials.get('MAZ543A_Frame_dark_enamel') or bpy.data.materials.new('MAZ543A_Frame_dark_enamel');paint.use_nodes=True;p=paint.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.006,.008,.007,1);p.inputs['Metallic'].default_value=.15;p.inputs['Roughness'].default_value=.76
    frame_names=['frame_0002','frame_0003','frame_0004']
    for n in frame_names:
        o=bpy.data.objects[n];o.data.materials.clear();o.data.materials.append(paint)
    for side in [-1,1]:
        box=bpy.data.objects[f'BL_RearRestoration_Rear_box_{side}']
        for x in [3.37,3.67]:
            support=cube(f'BL_RearRestoration_mount_{side}_{x}',[.12,.08,.61],[x,1.175,side*.98],paint,body);parts.append(support);bpy.context.view_layer.update()
            for mate in [box,bpy.data.objects['frame_0002']]:
                pairs=len(tree(support).overlap(tree(mate)));checks.append({'mount':support.name,'mate':mate.name,'intersectionPairs':pairs});assert pairs>0,('Disconnected mounting interface',filename,support.name,mate.name)
    bpy.context.view_layer.update()
    for s in [-1,1]:
        moved=bounds(bpy.data.objects[f'BL_RearRestoration_Rear_box_{s}']);ref=targets[f'BL_Rear_box_{s}'];expected=ref[:];expected[0]-=1.57;expected[3]-=1.57;actual=moved['min']+moved['max'];assert max(abs(a-b) for a,b in zip(actual,expected))<2e-5,('Original box dimensions changed',filename,s)
    report['files'].append({'file':filename,'parts':[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in parts],'connections':checks,'frameMaterials':frame_names,'axleCentersX':[2.42,4.62],'boxCenterX':3.52,'limits':'Photographic position correction; existing approximate box proportions retained. Mount geometry is fitted, not factory calibrated; lid internals, suspension travel and whole undercarriage paint remain OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if tex:
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'rear-box-frame-verification.json').write_text(json.dumps(report,indent=2))
