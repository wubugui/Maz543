"""Refresh neutral rest keys and web batching from the editable native master."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import export_suspension,descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'))
root=bpy.data.objects['S543_SUSPENSION'];poses=json.loads((ROOT/'work/suspension-poses.json').read_text())
for name,pose in poses['rest'].items():
    ob=bpy.data.objects.get(name)
    if ob:
        ob.location=(pose['p'][0],-pose['p'][2],pose['p'][1]);ob.rotation_euler.x=pose['rx']
        ob.keyframe_insert('location',frame=0);ob.keyframe_insert('rotation_euler',frame=0)
for ob in descendants(root):
    if ob.type=='MESH' and ob.data.shape_keys:
        for key in list(ob.data.shape_keys.key_blocks)[1:]:key.value=0;key.keyframe_insert('value',frame=0)
bpy.context.scene.frame_start=0;bpy.context.scene.frame_set(0)
reg=[{'node':o.name,'part':o['s543Part'],'source':o.get('sourceId'),'role':o.get('s543Role'),'dimensions':o.get('dimensionStatus')} for o in descendants(root) if 's543Part' in o]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'),compress=True)
export_suspension(root)
(ROOT/'outputs/suspension-parts-register.json').write_text(json.dumps(reg,indent=2),encoding='utf-8')
print('S543 neutral keys and batched GLB finalized',len(reg),flush=True)
