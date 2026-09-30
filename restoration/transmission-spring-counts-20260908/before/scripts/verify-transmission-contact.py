"""Independent evaluated mesh contact/round-wire checks at N/1/2/3/R.
No claim of hydraulic forces, seal deformation or complete assembly clearance.
Run audit-transmission-assembly.py first against the same native build.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'work/transmission/poses.json').read_text())
A=json.loads((ROOT/'outputs/transmission-assembly-audit.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Transmission.blend'))
selected={0:0,120:1,240:2,360:3,480:-1};worst_gap=0
for row in A['clutches']:
    pack=D['clutches'][row['pack']];engaged=pack['gear']==selected[row['frame']]
    expected=0 if engaged else 2.1+(pack['count']-1)*.3
    worst_gap=max(worst_gap,abs(row['totalRemainingGapMM']-expected))
    assert row['minInterDiscMM']>-.00005,row
    assert abs(row['stopGapMM'])<.00005,row
    assert abs(row['totalRemainingGapMM']-expected)<.00005,row
rigid=A['unexpectedCrossings']
assert not rigid,rigid
coils=[o for o in bpy.data.objects if o.get('parametricSpring')];assert len(coils)==32
worst_wire=worst_end=worst_radius=0;checks=0
for frame,gear in selected.items():
    bpy.context.scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
    for ob in coils:
        pack=D['clutches'][ob['springPack']];s=D['contact'];travel=(s['pistonGap']+(pack['count']-1)*s['plateGap']) if pack['gear']==gear else 0
        length=s['springLength']-travel;sweep=s['springTurns']*math.tau
        radius=math.sqrt(s['springLength']**2+(s['springRadius']*sweep)**2-length**2)/sweep
        evaluated=ob.evaluated_get(dg);mesh=evaluated.to_mesh();assert len(mesh.vertices)==161*12
        centres=[]
        for row in range(161):
            verts=[mesh.vertices[row*12+j].co for j in range(12)];centre=sum(verts,Vector())/12;centres.append(centre)
            worst_radius=max(worst_radius,abs(math.hypot(centre.y,centre.z)-radius))
            for v in verts:worst_wire=max(worst_wire,abs((v-centre).length-s['springWire']))
        assert abs((centres[-1]-centres[0]).length-length)<1e-7
        piston_x=pack['start']-pack['direction']*.005;end_x=piston_x+pack['direction']*.021
        j=int(ob.name.split('_')[-1]);r=pack['springMountRadius'];a=j*math.pi/4
        expected=ob.parent.parent.matrix_world@Vector((end_x,-r*math.sin(a),r*math.cos(a)))
        offset=evaluated.matrix_world@centres[-1]-expected
        axis=(ob.parent.parent.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
        worst_end=max(worst_end,abs(offset.dot(axis)))
        assert .0016<offset.length-s['springWire'] and offset.length+s['springWire']<.005
        evaluated.to_mesh_clear();checks+=1
assert max(worst_wire,worst_radius,worst_end)<1e-7,(worst_wire,worst_radius,worst_end)
report=dict(clutchStates=len(A['clutches']),springStates=checks,maxStackGapErrorMM=worst_gap,
            maxWireRadiusErrorM=worst_wire,maxHelixRadiusErrorM=worst_radius,maxFixedEndPlaneErrorM=worst_end,
            rigidCrossingCandidates=0,sealCrossingCandidates=len(A['crossingCandidates']),
            limits='Five discrete states; nominal seals have tessellated surface crossings and no elastic solve. No continuous collision, solid-containment, hydraulic pressure or force validation.')
(ROOT/'outputs/transmission-contact-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
