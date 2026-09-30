import bpy,bmesh,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
D=json.loads((ROOT/'work/transmission/poses.json').read_text());worst=0;count=0
for sample in D['samples'][::30]:
    bpy.context.scene.frame_set(sample['frame'])
    for name,pose in sample['pose'].items():
        ob=bpy.data.objects[name]
        if name.startswith('TX_feed_ball_'):
            expected=(math.cos(pose['rx']/2),math.sin(pose['rx']/2),0,0)
            q=ob.rotation_quaternion.normalized()
            # Chord distance remains stable for tiny errors, unlike acos(dot).
            chord=min(sum((q[i]-sign*expected[i])**2 for i in range(4))**.5 for sign in [1,-1])
            error=4*math.asin(min(1,chord/2))
        else:error=abs(ob.rotation_euler.x-pose['rx'])
        worst=max(worst,error)
        if 'p' in pose:
            expected=(pose['p'][0],-pose['p'][2],pose['p'][1]);assert max(abs(ob.location[i]-expected[i]) for i in range(3))<1e-7
        count+=1
gears=[o for o in bpy.data.objects if o.get('teeth')]
assert len(gears)==10
for ob in gears:
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges),ob.name
    assert bm.calc_volume()>0,ob.name
    bm.free()
assert worst<2e-5
assert len([o for o in bpy.data.objects if '_disc_' in o.name and o.type=='MESH'])==50
assert len([im for im in bpy.data.images if im.packed_file])==4
report={'poseChecks':count,'maxAngleError':worst,'manifoldGears':len(gears),'discCount':50,'packedReferences':4,'errors':0,'limits':'Native local poses and gear topology only; full assembly clearance and load behavior remain unverified.'}
(ROOT/'outputs/planetary-native-verification.json').write_text(json.dumps(report,indent=2));print(report)
