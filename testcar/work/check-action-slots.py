import bpy
bpy.ops.wm.open_mainfile(filepath='D:/testcar/outputs/MAZ543A_Textured.blend')
for f in [0,105,180]:
 bpy.context.scene.frame_set(f)
 for n in ['D12_crankshaft','C5_FLYWHEEL_RING']:
  ob=bpy.data.objects[n];ad=ob.animation_data;ac=ad.action
  print('FRAME',f,n,ob.rotation_euler.x,'SLOT',ad.action_slot,'SLOTS',[(x.identifier,x.handle) for x in ac.slots],[(fc.data_path,fc.array_index,len(fc.keyframe_points),fc.evaluate(f)) for fc in ac.fcurves],flush=True)
