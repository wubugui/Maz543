import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/'MAZ543A_Textured.blend'))
scene=bpy.context.scene
scene.frame_set(1);door=bpy.data.objects['cab_pivot_002'];closed=door.rotation_quaternion.copy();piston=bpy.data.objects['engine_pivot_002'];p1=piston.location.copy()
scene.frame_set(9);assert (piston.location-p1).length>.01,'Native piston animation is static'
scene.frame_set(271);assert closed.rotation_difference(door.rotation_quaternion).angle>1.5,'Door animation did not open at the correct pivot'
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.cycles.samples=24;scene.render.resolution_percentage=75
scene.render.filepath=str(ROOT/'outputs'/'maz543a-door-inspection.png');bpy.ops.render.render(write_still=True)
scene.frame_set(151);scene.render.filepath=str(ROOT/'outputs'/'maz543a-running-inspection.png');bpy.ops.render.render(write_still=True)
report={'blender':bpy.app.version_string,'native_motion_nodes':sum(1 for o in bpy.data.objects if o.animation_data and o.animation_data.action),'piston_animation':'passed','door_animation':'passed','frame_range':[scene.frame_start,scene.frame_end]}
(ROOT/'outputs'/'blender-verification.json').write_text(json.dumps(report,indent=2));print('BLENDER_VERIFIED',json.dumps(report))
