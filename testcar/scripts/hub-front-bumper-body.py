# Helpers are prepended from hub-front-assembly-model.py by the local builder.
report={'scope':'Boxed front bumper, central single hook and underside shield','files':[]};target_bounds=None
def subset_archive(o,ids):
    bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o;chosen=set(ids)
    for v in o.data.vertices:v.select=v.index in chosen
    for e in o.data.edges:e.select=all(i in chosen for i in e.vertices)
    for f in o.data.polygons:f.select=all(i in chosen for i in f.vertices)
    before=set(bpy.data.objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
    new=set(bpy.data.objects)-before;assert len(new)==1
    old=new.pop();old.name='ARCHIVED_seed_front_towing_eyes';archive(old)
    return len(chosen)
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();tex=filename.endswith('Textured.blend')
    names=['BL_Front_crossmember','BL_Tow_shackle_-1','BL_Tow_shackle_1','frame_0001']
    if not tex:
        target_bounds={n:bounds(bpy.data.objects[n])['min']+bounds(bpy.data.objects[n])['max'] for n in names if bpy.data.objects.get(n)}
    # frame_0001 is separately addressable in both native files.
    separate={n:b for n,b in target_bounds.items() if n!='frame_0001'}
    split_old(tex,separate);archive(bpy.data.objects['frame_0001'])
    old=bpy.data.objects['frame_0002'];ids=[]
    for part in components(old):
        ps=[old.matrix_world@old.data.vertices[i].co for i in part]
        if max(p.x for p in ps)<-5.40 and max(p.z for p in ps)<1.10 and min(p.z for p in ps)>.65 and all(.80<abs(p.y)<1.11 for p in ps):ids.extend(part)
    assert len(ids)>100,('seed towing ring selection absent',len(ids));removed=subset_archive(old,ids)
    frame=bpy.data.objects['frame'];steel=bpy.data.materials['Phosphated_steel'];added=[]
    beam=cube('BL_Front_box_bumper',[.25,.49,3.03],[-5.485,.945,0],steel,frame);beam.modifiers.clear();added.append(beam)
    def cutter(name,size,pos,rot=None):
        bpy.ops.mesh.primitive_cube_add(size=1,location=C(pos));q=bpy.context.object;q.name=name;q.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if rot:q.rotation_euler=rot
        q.hide_render=True;q.hide_set(True);m=beam.modifiers.new(name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=q
    cutter('Bumper central recovery-hook recess',[.5,.30,.25],[-5.485,1.165,0])
    for side in [-1,1]:cutter('Bumper tapered lower end '+str(side),[.5,.32,.32],[-5.485,.64,side*1.54],(side*math.pi/4,0,0))
    bevel(beam,.012)
    added.append(cube('BL_Front_hook_mount',[.16,.15,.15],[-5.47,.965,0],steel,frame))
    added.append(tube('BL_Front_single_recovery_hook',[[-5.54,.97,0],[-5.66,.90,0],[-5.71,.81,0],[-5.65,.76,0],[-5.60,.81,0]],.038,steel,frame))
    shield=cube('BL_Front_lower_shield',[.47,.015,1.20],[-5.26,.65,0],steel,frame);shield.rotation_euler.y=math.radians(-18);added.append(shield)
    bpy.context.view_layer.update();report['files'].append({'file':filename,'seedTowVerticesArchived':removed,'parts':[{'name':a.name,'bounds':bounds(a),'modifiers':[m.type for m in a.modifiers]} for a in added],'status':'Photo fit; dimensional/load rating acceptance OPEN'})
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
(OUT/'front-bumper-verification.json').write_text(json.dumps(report,indent=2))
