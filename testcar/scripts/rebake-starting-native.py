"""Update the editable starting module after changes to causal accessory loads."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Starting_Master.blend'))
data=json.loads((ROOT/'work/starting-poses.json').read_text())['frames']
for name,p0 in data[0]['pose'].items():
    ob=bpy.data.objects[name];ob.animation_data_clear()
    action=bpy.data.actions.new('Causal start '+name);slot=action.slots.new(id_type='OBJECT',name=name);ob.animation_data_create().action=action;ob.animation_data.action_slot=slot
    ob.location=(p0['p'][0],-p0['p'][2],p0['p'][1]);ob.rotation_euler=(p0['rx'],0,0);ob.scale=(p0.get('sx',1),1,1)
    for channel,index,getter in [('location',0,lambda p:p['p'][0]),('location',1,lambda p:-p['p'][2]),('location',2,lambda p:p['p'][1]),('rotation_euler',0,lambda p:p['rx']),('scale',0,lambda p:p.get('sx',1))]:
        vals=[getter(f['pose'][name]) for f in data]
        if max(vals)-min(vals)<1e-12:continue
        fc=action.fcurves.new(data_path=channel,index=index);fc.keyframe_points.add(len(data));fc.keyframe_points.foreach_set('co',[v for f,x in zip(data,vals) for v in (f['frame'],x)])
        for k in fc.keyframe_points:k.interpolation='LINEAR'
        fc.update()
bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Starting_Master.blend'),compress=True)
