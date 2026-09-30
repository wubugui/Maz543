import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from starting_asset import attach_starting
for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
 file=ROOT/'outputs'/name;bpy.ops.wm.open_mainfile(filepath=str(file));attach_starting();bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
print('REFRESHED_STARTING_MODULE_IN_BOTH_VEHICLE_MASTERS',flush=True)
