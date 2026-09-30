"""Update the editable engine cam bank without rebuilding unrelated assemblies."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'scripts/blender-d12.py').read_text(encoding='utf-8')
exec(compile(source[:source.index('# Split aluminium')],str(ROOT/'scripts/blender-d12.py'),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
root=bpy.data.objects['D12A_525A'];bpy.context.scene.frame_set(1)
for symbol,name in [('CAST','D12_cast_aluminium'),('POLISH','D12_machined_steel'),('STEEL','D12_forged_steel'),('BRONZE','D12_bearing_bronze')]:globals()[symbol]=bpy.data.materials[name]
from d12_asset import engine_descendants
exec(compile((ROOT/'scripts/d12-cam-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-detail.py'),'exec'))
if '--sleeves-only' in sys.argv:
    for bank in ['L','R']:
        CAM_BANK=bank
        for kind in ['intake','exhaust']:
            name=f'D12_cam_41_10_sleeve_{bank}_{kind}'
            bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
            cam=bpy.data.objects[f'D12_cam_{bank}_{kind}']
            sleeve=cam_section(name,CAM_PROFILES['sections']['sleeve'],-.657,-.615,cam)
            sleeve['externalSplines']=41;sleeve['internalSplines']=10
            drill(sleeve,'Sleeve spring release hole',.0017,.056,(-.650,0,0),cam,'y',0)
else:
    for bank in ['L','R']:
        for kind in ['intake','exhaust']:
            ob=bpy.data.objects.get(f'D12_cam_{bank}_{kind}')
            if ob:
                for o in reversed([ob]+engine_descendants(ob)):bpy.data.objects.remove(o,do_unlink=True)
    for ob in list(bpy.data.objects):
        if ob.get('camTrain') or ob.name.startswith('D12_cam_bearing_'):bpy.data.objects.remove(ob,do_unlink=True)
    exec(compile((ROOT/'scripts/d12-cam-detail.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-detail.py'),'exec'))
    for bank,s in [('L',-1),('R',1)]:build_cam_bank(bank,s,bpy.data.objects['D12_head_'+bank])

# Retain every original semantic joint and rebake its source-driven cycle.
for n,p0 in POSES['frames'][0]['pose'].items():
    ob=bpy.data.objects[n];ob.animation_data_clear();ob.location=C(p0['p']);ob.rotation_euler=(p0['rx'],0,0);ob.scale=(1,1,p0.get('sy',1))
    action=bpy.data.actions.new('MAZ documented phase '+n);slot=action.slots.new(id_type='OBJECT',name=n)
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
refs=bpy.data.collections.get('D12_REFERENCE_IMAGES')
for path in [*Path('D:/maz543-references/engine/timing').glob('*.jpg'),Path('D:/maz543-references/engine/05-family-camshafts.jpg')]:
    image=bpy.data.images.load(str(path),check_existing=True);image.pack()
    name='D12_REF_'+path.stem
    if bpy.data.objects.get(name):continue
    ob=bpy.data.objects.new(name,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=image;ob.empty_display_size=1.5;ob.location=(0,4,1);ob.hide_render=True;ob.hide_viewport=True
text=bpy.data.texts.get('D12_REFERENCE_AND_SCOPE');text.clear();text.write((ROOT/'docs/D12_REFERENCE_REGISTER.md').read_text(encoding='utf-8'))
bpy.context.scene.frame_set(1);root['camRevision']=1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'),compress=True)
print('CAM_NATIVE_UPDATED',len([o for o in engine_descendants(root) if o.get('camTrain')]),flush=True)
