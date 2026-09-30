import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 file=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(file));count=0
 for ob in bpy.data.objects:
  ad=ob.animation_data
  if ad and ad.action and ad.action.name.startswith('Causal start ') and ad.action.slots:
   slot=ad.action.slots[0];slot.target_id_type='OBJECT';ad.action_slot=slot;count+=1
 bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True);print('BOUND_ACTION_SLOTS',name,count,flush=True)
