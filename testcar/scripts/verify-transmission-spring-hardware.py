"""Saved-file catalogue counts and continuous fitted telescoping clearances."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];temporary='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if temporary else 'outputs/MAZ543A_Transmission.blend')))
D=json.loads((ROOT/'work/transmission/poses.json').read_text(encoding='utf-8'));bpy.context.scene.frame_set(0)
expected={'first':30,'second':16,'direct':16,'reverse':30};rows=[];solids=0;pair_checks=0
def geometry(ob):
    m=ob.data;m.calc_loop_triangles();vs=[ob.matrix_world@v.co for v in m.vertices]
    return ([min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)],BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True))
def clear(a,b):
    global pair_checks
    pair_checks+=1;lo,hi,ta=a;lb,hb,tb=b
    if min(min(hi[k],hb[k])-max(lo[k],lb[k]) for k in range(3))<1e-7:return
    assert not ta.overlap(tb),'Rigid surfaces intersect in the saved telescoping hardware'
for name,count in expected.items():
    coils=[o for o in bpy.data.objects if o.get('parametricSpring') and o.get('springPack')==name]
    assert len(coils)==count,(name,len(coils),count)
    for family in ['spring_guide','moving_spring_seat','fixed_spring_seat','pusher_tab','anchor']:
        assert len([o for o in bpy.data.objects if o.name.startswith(f'TX_{name}_{family}_') and o.name[len(f'TX_{name}_{family}_'):].isdigit() and o.type=='MESH'])==count,(name,family)
    ob=coils[0];vs=ob.data.vertices;centres=[sum((vs[i*12+j].co for j in range(12)),Vector())/12 for i in range(161)]
    wire=sum((vs[i*12+j].co-centres[i]).length for i in range(161) for j in range(12))/(161*12)
    radius=sum(math.hypot(c.y,c.z) for c in centres)/len(centres)
    angles=[math.atan2(c.z,c.y) for c in centres];turns=abs(sum((b-a+math.pi)%math.tau-math.pi for a,b in zip(angles,angles[1:])))/math.tau
    row={'pack':name,'springs':count,'wireDiameterM':wire*2,'meanCoilDiameterM':radius*2,'installedLengthM':(centres[-1]-centres[0]).length,'effectiveTurnsMeasured':turns}
    assert abs(turns-5)<1e-6
    if name in ['first','reverse']:
        for family,n in [('pusher_sleeve',count),('pusher_bush',2*count),('pusher_pin',count),('spring_guide_boss',count)]:
            assert len([o for o in bpy.data.objects if o.name.startswith(f'TX_{name}_{family}_') and o.type=='MESH'])==n,(name,family)
        # All instances use the same local solid templates. Check both opposite
        # installation directions through 25 travel positions, plus global audit.
        fixed=[bpy.data.objects[f'TX_{name}_{suffix}'] for suffix in ['spring_guide_0','pusher_bush_0_0','pusher_bush_0_1','pusher_pin_0','spring_guide_boss_0','fixed_spring_seat_0']]
        moving=[bpy.data.objects[f'TX_{name}_{suffix}'] for suffix in ['pusher_sleeve_0','moving_spring_seat_0']]
        clear(geometry(fixed[0]),geometry(fixed[3]))
        piston=bpy.data.objects['TX_piston_'+name];pack=D['clutches'][name];travel=D['contact']['pistonGap']+(pack['count']-1)*D['contact']['plateGap']
        for k in range(25):
            piston.location.x=pack['direction']*travel*k/24;bpy.context.view_layer.update()
            for a in moving:
                for b in fixed:
                    try:clear(geometry(a),geometry(b))
                    except AssertionError:raise AssertionError((name,k,a.name,b.name))
        piston.location.x=0;bpy.context.view_layer.update();row['sampledTravelStates']=25
    rows.append(row)
for ob in bpy.data.objects:
    if not ob.get('springHardware'):continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name
    bm.free();solids+=1
report={'packs':rows,'springs':sum(expected.values()),'hardwareSolids':solids,'clearancePairChecks':pair_checks,'limits':'Catalogue counts; fitted hardware through 25 travel positions per installation direction. Measured coil geometry remains reconstruction, not factory spring dimensions or fatigue approval.'}
out=ROOT/('work/transmission' if temporary else 'outputs');(out/'transmission-spring-hardware-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
