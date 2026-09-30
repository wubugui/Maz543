"""Incremental timing-train migration, preserving all existing engine detail."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/blender-d12.py').read_text(encoding='utf-8')
exec(compile(source[:source.index('# Split aluminium')],str(ROOT/'scripts/blender-d12.py'),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
root=bpy.data.objects['D12A_525A'];bpy.context.scene.frame_set(1)
for symbol,name in [('CAST','D12_cast_aluminium'),('POLISH','D12_machined_steel'),('STEEL','D12_forged_steel'),('BRONZE','D12_bearing_bronze')]:globals()[symbol]=bpy.data.materials[name]
from d12_asset import engine_descendants
for ob in list(engine_descendants(root)):
    if (ob.get('timingTrain') and not ob.name.startswith('D12_cam_22_spur_')) or ob.get('timingMount') or ob.get('timingShaft') or ob.name.startswith(('D12_timing_tower_','D12_bevel_case_','D12_cam_24_bevel_')):
        bpy.data.objects.remove(ob,do_unlink=True)
exec(compile((ROOT/'scripts/d12-timing-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-timing-detail.py'),'exec'))
build_timing_train()
for n,p0 in POSES['frames'][0]['pose'].items():
    ob=bpy.data.objects[n];ob.animation_data_clear();ob.location=C(p0['p']);ob.rotation_euler=(p0['rx'],0,0);ob.scale=(1,1,p0.get('sy',1))
    action=bpy.data.actions.new('MAZ documented timing '+n);slot=action.slots.new(id_type='OBJECT',name=n)
    ob.animation_data_create().action=action;ob.animation_data.action_slot=slot
    for channel,index,getter in [('location',0,lambda p:p['p'][0]),('location',1,lambda p:-p['p'][2]),('location',2,lambda p:p['p'][1]),('rotation_euler',0,lambda p:p['rx']),('scale',2,lambda p:p.get('sy',1))]:
        values=[getter(f['pose'][n]) for f in POSES['frames']]
        if max(values)-min(values)<1e-12:continue
        fc=action.fcurves.new(data_path=channel,index=index);fc.keyframe_points.add(len(values));fc.keyframe_points.foreach_set('co',[v for f,x in zip(POSES['frames'],values) for v in (f['frame'],x)])
        for key in fc.keyframe_points:key.interpolation='LINEAR'
        fc.update()
collection=bpy.data.collections['D12_ENGINE']
for ob in engine_descendants(root):
    for col in list(ob.users_collection):col.objects.unlink(ob)
    collection.objects.link(ob)
# Sharp machining steps retain their normals in native and exported materials.
exec(compile((ROOT/'scripts/d12-cam-finish.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-finish.py'),'exec'))
for ob in engine_descendants(root):
    if ob.get('timingTrain') and ob.type=='MESH':
        if ob.data.materials[0].name=='D12_machined_steel':ob.data.materials[0]=ground
        if ob.data.materials[0].name=='D12_forged_steel':ob.data.materials[0]=forged
        bm=bmesh.new();bm.from_mesh(ob.data);bm.edges.ensure_lookup_table()
        sharp=[e.calc_face_angle(0)>.52 for e in bm.edges];bm.free()
        for p in ob.data.polygons:p.use_smooth=True
        for e,value in zip(ob.data.edges,sharp):e.use_edge_sharp=value
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'),compress=True)
print('TIMING_NATIVE_UPDATED',len(POSES['frames'][0]['pose']),len([o for o in engine_descendants(root) if o.get('timingTrain')]),flush=True)
