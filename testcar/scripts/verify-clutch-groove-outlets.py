"""Check channel centreline surface clearance in each closed native clutch pack.
Checks include the adjacent discs and all other saved transmission solids.
This is a bounded centreline test, not a pressure/flow or solid-containment solve.
"""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];temporary='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if temporary else 'outputs/MAZ543A_Transmission.blend')))
D=json.loads((ROOT/'work/transmission/poses.json').read_text(encoding='utf-8'));S=json.loads((ROOT/'work/transmission/clutch-splines.json').read_text(encoding='utf-8'));rows=[]
for name,frame in [('first',120),('second',240),('direct',360),('reverse',480)]:
    bpy.context.scene.frame_set(frame)
    if temporary:
        for key,pose in D['samples'][frame]['pose'].items():
            ob=bpy.data.objects[key];ob.rotation_euler.x=pose['rx']
            if 'p' in pose:ob.location=(pose['p'][0],-pose['p'][2],pose['p'][1])
        bpy.context.view_layer.update()
    pack=D['clutches'][name];ob=bpy.data.objects[f'TX_{name}_disc_01'];centre=(min(v.co.x for v in ob.data.vertices)+max(v.co.x for v in ob.data.vertices))/2
    offset=D['contact']['plateThickness']/2-D['surfaces']['depth']/2
    geometry=[]
    # Restrict broad phase to the actual axial oil-film interval.
    axial=[(ob.matrix_world@Vector((centre+sign*offset,0,0))).x for sign in [-1,1]]
    for other in bpy.data.objects:
        if other.type!='MESH':continue
        bounds=[other.matrix_world@Vector(v) for v in other.bound_box]
        lo=[min(v[k] for v in bounds) for k in range(3)];hi=[max(v[k] for v in bounds) for k in range(3)]
        if hi[0]<min(axial)-1e-7 or lo[0]>max(axial)+1e-7:continue
        m=other.data;m.calc_loop_triangles();vs=[other.matrix_world@v.co for v in m.vertices]
        geometry.append((other.name,lo,hi,BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)))
    segments=0;outlets=0
    for path in S[name]['frictionGrooved']['paths']:
        points=path['points']
        # The radial groove is straight; both its bore-side land and outer
        # annular clearance are included. The spline bore outlet is not claimed.
        if path['kind']=='radial':
            y,z=points[0];a=math.atan2(z,y)
            points=[(r*math.cos(a),r*math.sin(a)) for r in [pack['inner']+.0035,pack['outer']+.0004]]
            outlets+=2
        else:points=[p for p in points if pack['inner']+.0035<math.hypot(*p)<pack['outer']+.0004]
        for sign in [-1,1]:
            world=[ob.matrix_world@Vector((centre+sign*offset,-z,y)) for y,z in points]
            for a,b in zip(world,world[1:]):
                d=b-a;length=d.length;d.normalize();segments+=1
                for label,lo,hi,tree in geometry:
                    if any(max(a[k],b[k])<lo[k]-1e-8 or min(a[k],b[k])>hi[k]+1e-8 for k in range(3)):continue
                    hit,normal,index,distance=tree.ray_cast(a,d,length)
                    assert hit is None,(name,path['kind'],sign,label,tuple(a),tuple(b),distance)
    rows.append({'pack':name,'closedFrame':frame,'testedSegments':segments,'radialOutletsBothFaces':outlets,'candidateSolids':len(geometry)})
out=ROOT/('work/transmission' if temporary else 'outputs');report={'packs':rows,'limits':'Closed-pack centreline surface clearance through spiral/radial grooves to the outer annular gap. No inner spline outlet, solid-containment, finite-width fluid flow or oil-film pressure claim.'}
(out/'clutch-groove-outlet-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
