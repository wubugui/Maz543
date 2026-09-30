# Correct actual native hinge pivots to authored front/rear door leading edges.
# Rebase each actual child transform while retaining its world geometry exactly.
report={'scope':'Native door hinge relocation with exact closed geometry preservation','files':[]}
def descendants(o):
    for c in o.children:yield c;yield from descendants(c)
def union(parts):
    boxes=[bounds(o) for o in parts];return {'min':[min(b['min'][i] for b in boxes) for i in range(3)],'max':[max(b['max'][i] for b in boxes) for i in range(3)]}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();rows=[]
    for name,x in [('cab_pivot_002',-4.91),('cab_pivot_003',-3.96),('cab_pivot_006',-4.91),('cab_pivot_007',-3.96)]:
        door=bpy.data.objects[name];children=list(door.children);old={c:c.matrix_world.copy() for c in children};oldp=door.matrix_world.copy();parts=[o for o in descendants(door) if o.type in ['MESH','CURVE']];before=union(parts)
        m=oldp.copy();m.translation.x=x;door.matrix_world=m;bpy.context.view_layer.update()
        for c in children:c.matrix_world=old[c]
        bpy.context.view_layer.update();after=union(parts)
        drift=max(abs(a-b) for key in ['min','max'] for a,b in zip(before[key],after[key]));assert drift<1e-6,('World geometry moved during native pivot rebase',filename,name,drift)
        door['hingeCorrection']='Front/rear leading edge shared by runtime source, matching actual doorway; closed child world geometry preserved';door['dimensionStatus']='Authored leading edge, not factory hinge measurement'
        rows.append({'hinge':name,'oldNativeX':oldp.translation.x,'newNativeX':door.matrix_world.translation.x,'directChildren':[c.name for c in children],'allDoorMeshCurveParts':len(parts),'closedWorldBounds':after,'maxBoundsDriftM':drift})
    report['files'].append({'file':filename,'doors':rows,'limits':'Hinges now agree with runtime source; factory axis tolerance/hinge internals/full travel still OPEN'})
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    if filename.endswith('Textured.blend'):
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        for o in descendants(root):
            if allowed(o):o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
(OUT/'cab-hinge-rebase-verification.json').write_text(json.dumps(report,indent=2))
