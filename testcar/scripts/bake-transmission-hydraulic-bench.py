"""Additional native hydraulic/load sequence; preserve the source endpoint audit.
All rotations use quaternion keys so long accumulated angles remain precise.
"""
import bpy,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import weights
D=json.loads((ROOT/'work/hydraulics/native-bench.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
for ob in bpy.data.objects:
    ob.animation_data_clear()
    if ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.animation_data_clear()
for action in list(bpy.data.actions):
    if action.users==0:bpy.data.actions.remove(action)
# Same spring parameters that produced the exported Pitch and Radius targets.
for sample in D['samples']:
    frame=sample['frame']
    for name,pose in sample['pose'].items():
        ob=bpy.data.objects[name];ob.rotation_mode='QUATERNION';a=pose['rx']/2
        ob.rotation_quaternion=(math.cos(a),math.sin(a),0,0);ob.keyframe_insert('rotation_quaternion',frame=frame)
        if 'p' in pose:
            p=pose['p'];ob.location=(p[0],-p[2],p[1]);ob.keyframe_insert('location',frame=frame)
        if 'springPack' in pose:
            spring=bpy.data.objects[f"TX_{pose['springPack']}_return_spring_{name.split('_')[-1]}"]
            c=D['contact'];pack=D['clutches'][pose['springPack']]
            spec=dict(releaseSpringLength=c['springLength'],releaseSpringRadius=c['springRadius'],releaseSpringWire=c['springWire'],releaseSpringTurns=c['springTurns'],clutchTravel=c['pistonGap']+(pack['count']-1)*c['plateGap'])
            for key,value in zip(['Pitch','Radius'],weights(spec,pose['springTravel'])):
                block=spring.data.shape_keys.key_blocks[key];block.value=value;block.keyframe_insert('value',frame=frame)
    for pack,b in sample['boosters'].items():
        ob=bpy.data.objects['TX_piston_'+pack]
        for key,value in [('pressure_Pa',b['pressure']),('normal_force_N',b['normalForce']),('torque_capacity_Nm',b['capacity']),('slip_rad_s',sample['slip'][pack])]:
            ob[key]=float(value);ob.keyframe_insert(data_path='["'+key+'"]',frame=frame)
for ob in bpy.data.objects:
    blocks=[ob]
    if ob.type=='MESH' and ob.data.shape_keys:blocks.append(ob.data.shape_keys)
    for block in blocks:
        if block.animation_data and block.animation_data.action:
            for fc in block.animation_data.action.fcurves:
                for key in fc.keyframe_points:key.interpolation='LINEAR'
scene=bpy.context.scene;scene.render.fps=60;scene.frame_start=0;scene.frame_end=1800;scene.frame_set(0)
text=bpy.data.texts.new('HYDRAULIC_BENCH_README');text.write(D['limits']+'\n0-4 N/start, 4-8 first, 8-10 N/brake, 10-14 second, 14-16 N/brake, 16-20 direct, 20-22 N/brake, 22-26 reverse, 26-30 N/stop. Piston custom properties carry pressure, force, capacity and slip.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission_HydraulicBench.blend'),compress=True)
exec(compile((ROOT/'scripts/verify-transmission-hydraulic-bench.py').read_text(),str(ROOT/'scripts/verify-transmission-hydraulic-bench.py'),'exec'),globals())
