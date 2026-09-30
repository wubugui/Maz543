import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'work/hydraulics/native-bench.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission_HydraulicBench.blend'))
scene=bpy.context.scene
worst=0;checks=0;forceChecks=0;morphChecks=0
for sample in D['samples'][::5]:
    scene.frame_set(sample['frame'])
    for name,pose in sample['pose'].items():
        ob=bpy.data.objects[name];q=ob.rotation_quaternion.normalized();expected=(math.cos(pose['rx']/2),math.sin(pose['rx']/2),0,0)
        chord=min(sum((q[i]-sign*expected[i])**2 for i in range(4))**.5 for sign in [1,-1]);worst=max(worst,4*math.asin(min(1,chord/2)))
        if 'p' in pose:
            p=pose['p'];expected=(p[0],-p[2],p[1]);assert max(abs(ob.location[i]-expected[i]) for i in range(3))<1e-7
        if 'springPack' in pose:
            c=D['contact'];pack=D['clutches'][pose['springPack']];L=c['springLength'];R=c['springRadius'];sweep=math.tau*c['springTurns'];maximum=c['pistonGap']+(pack['count']-1)*c['plateGap'];x=pose['springTravel']
            radius=lambda x:math.sqrt(L*L+(R*sweep)**2-(L-x)**2)/sweep
            expected=(x/maximum,(radius(x)-R)/(radius(maximum)-R))
            spring=bpy.data.objects[f"TX_{pose['springPack']}_return_spring_{name.split('_')[-1]}"]
            for key,value in zip(['Pitch','Radius'],expected):assert abs(spring.data.shape_keys.key_blocks[key].value-value)<1e-7
            morphChecks+=1
        checks+=1
    for pack,b in sample['boosters'].items():
        ob=bpy.data.objects['TX_piston_'+pack]
        for key,value in [('pressure_Pa',b['pressure']),('normal_force_N',b['normalForce']),('torque_capacity_Nm',b['capacity']),('slip_rad_s',sample['slip'][pack])]:
            assert abs(ob[key]-value)<max(1e-6,abs(value)*2e-7),(key,ob[key],value)
            forceChecks+=1
assert worst<2e-6,worst
report={'samples':len(D['samples']),'durationSeconds':30,'poseChecks':checks,'forceChecks':forceChecks,'springChecks':morphChecks,'maxAngleError':worst,'limits':D['limits']}
(ROOT/'outputs/transmission-hydraulic-native-checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
