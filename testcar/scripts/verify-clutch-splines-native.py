"""Verify the delivered native spline solids and their actual axial engagement."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
D=json.loads((ROOT/'work/transmission/poses.json').read_text());reports=[]
solids=[o for o in bpy.data.objects if o.get('clutchSpline')];assert len(solids)==sum(p['count']+p['springCount'] for p in D['clutches'].values())+8
for o in solids:
    bm=bmesh.new();bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges),o.name
    assert bm.calc_volume()>0,o.name
    bm.free()
def bounds(o):
    vs=[o.matrix_world@v.co for v in o.data.vertices]
    return min(v.x for v in vs),max(v.x for v in vs)
for name,pack in D['clutches'].items():
    minimum=1
    for frame in [0,120,240,360,480]:
        bpy.context.scene.frame_set(frame)
        hub=bpy.data.objects[f'TX_{name}_splined_hub'];lo,hi=bounds(hub)
        for j in range(1,pack['count'],2):
            ob=bpy.data.objects[f'TX_{name}_disc_{j:02}'];a,b=bounds(ob)
            minimum=min(minimum,min(hi,b)-max(lo,a))
            assert ob.parent.parent==hub.parent,(ob.name,'wrong angular body')
        for j in range(0,pack['count'],2):
            ob=bpy.data.objects[f'TX_{name}_disc_{j:02}']
            expected='TX_ring18' if name=='direct' else 'S543_TRANSMISSION'
            assert ob.parent.parent.name==expected,ob.name
    assert minimum>.0006
    reports.append(dict(pack=name,minimumNativeAxialEngagementMM=minimum*1000))
result=dict(manifoldPositiveVolumeSplineSolids=len(solids),packs=reports,
            limits='Discrete native axial geometry and parent topology. No spline flank force, fatigue, backlash dynamics or factory dimensional acceptance.')
(ROOT/'outputs/clutch-spline-native-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
