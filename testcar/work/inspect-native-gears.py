import bpy,json
bpy.ops.wm.open_mainfile(filepath='D:/testcar/outputs/MAZ543A_Starting_Master.blend');bpy.context.scene.frame_set(105)
data={}
for name in ['C5_11_tooth_pinion','C5_flywheel_involute_ring','C5_pinion','C5_FLYWHEEL_RING']:
 o=bpy.data.objects[name];d={'position':list(o.matrix_world.translation),'rotation':list(o.matrix_world.to_euler()),'localrotation':list(o.rotation_euler)}
 if o.type=='MESH':d['vertices']=[list(o.matrix_world@v.co) for v in o.data.vertices];d['faces']=[list(p.vertices) for p in o.data.polygons]
 data[name]=d
open('D:/testcar/work/native-gears.json','w').write(json.dumps(data))
