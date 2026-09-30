"""Correct the prototype damper's rebound clearance, then refresh its GLB."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import export_suspension
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'))
root=bpy.data.objects['S543_SUSPENSION']
if not root.get('damper_clearance_revision'):
    for i in range(8):
        for kind,base,old,new in [('outer_reservoir',.07,.405,.445),('working_cylinder',.092,.370,.410)]:
            ob=bpy.data.objects[f'S543_{i}_damper_{kind}']
            for v in ob.data.vertices:v.co.z=base+(v.co.z-base)*new/old
        for name in ['end_cap_0.466','rod_guide','gland_seal']:
            ob=bpy.data.objects[f'S543_{i}_damper_{name}']
            for v in ob.data.vertices:v.co.z+=.04
    root['damper_clearance_revision']=1
bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Suspension_Master.blend'),compress=True)
export_suspension(root)
print('Rebound piston/guide clearance corrected; GLB refreshed.',flush=True)
