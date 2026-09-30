report={'scope':'Repair actual static mounting gaps revealed by native surface audit','files':[]}
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend');frame=bpy.data.objects['frame'];steel=bpy.data.materials['Phosphated_steel'];added=[];checks=[]
    for side,parent_name in [(-1,'cab_pivot_001'),(1,'cab_pivot_005')]:
        mount=cube(f'BL_Front_bumper_frame_mount_{side}',[.24,.12,.10],[-5.30,.945,side*.69],steel,frame);added.append(mount)
        stay=cube(f'BL_Front_shield_stay_{side}',[.04,.22,.06],[-5.35,.69,side*.48],steel,frame);added.append(stay)
        p=bpy.data.objects[parent_name];arm=bpy.data.objects[f'BL_Front_mirror_arm_{side}'];assert arm.type=='CURVE'
        root=C([-5.275,1.34,side*1.54]);arm.data.splines[0].bezier_points[0].co=arm.matrix_world.inverted()@root
        bracket=cube(f'BL_Front_mirror_root_mount_{side}',[.075,.08,.065],[-5.27,1.33,side*1.512],steel,p);added.append(bracket)
        # Fine upper front rod is independently visible in the museum oblique.
        added.append(tube(f'BL_Front_upper_fine_rod_{side}',[[-5.31,2.18,side*1.522],[-5.50,2.55,side*1.522],[-5.42,2.57,side*1.522]],.009,steel,p))
        bpy.context.view_layer.update()
        for a,b in [(mount,bpy.data.objects['BL_Front_box_bumper']),(mount,bpy.data.objects['frame_0002']),(stay,bpy.data.objects['BL_Front_box_bumper']),(stay,bpy.data.objects['BL_Front_lower_shield']),(bracket,arm)]:
            count=len(tree(a).overlap(tree(b)));assert count>0,('Detached actual mounting surfaces',filename,a.name,b.name,count);checks.append({'a':a.name,'b':b.name,'intersectionPairs':count})
        skin=bpy.data.objects[f'BL_Cab_{side}_side_monocoque'] if not tex else bpy.data.objects[f'BL_Merged_{parent_name}_OD_green_aged_enamel']
        count=len(tree(bracket).overlap(tree(skin)));assert count>0,('Mirror bracket detached from shell',filename,side);checks.append({'a':bracket.name,'b':skin.name,'intersectionPairs':count})
    report['files'].append({'file':filename,'added':[{'name':o.name,'parent':o.parent.name,'bounds':bounds(o)} for o in added],'staticSurfaceConnections':checks,'limits':'Intentional static mount overlap verified; fabricated mount dimensions, bolts/load rating/full motion clearance remain OPEN'})
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
(OUT/'front-mount-repair-verification.json').write_text(json.dumps(report,indent=2))
