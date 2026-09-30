"""Read back the native grooved discs; export actual cap triangles for area audit."""
import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];temporary='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if temporary else 'outputs/MAZ543A_Transmission.blend')))
D=json.loads((ROOT/'work/transmission/poses.json').read_text(encoding='utf-8'))
S=json.loads((ROOT/'work/transmission/clutch-splines.json').read_text(encoding='utf-8'))
bpy.context.scene.frame_set(0);rows=[];exports={};depth_error=0;ray_checks=0
for name,pack in D['clutches'].items():
    for j in range(1,pack['count'],2):
        ob=bpy.data.objects[f'TX_{name}_disc_{j:02}'];bm=bmesh.new();bm.from_mesh(ob.data)
        bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume()
        assert bad==0,(ob.name,'nonmanifold edges',bad)
        assert volume>0,(ob.name,'volume',volume)
        bm.free();rows.append({'name':ob.name,'volumeM3':volume,'vertices':len(ob.data.vertices)})
        if j!=1:continue
        mesh=ob.data;mesh.calc_loop_triangles();vs=[v.co.copy() for v in mesh.vertices]
        centre=(min(v.x for v in vs)+max(v.x for v in vs))/2;half=D['contact']['plateThickness']/2
        tree=BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
        for path in S[name]['frictionGrooved']['paths']:
            pts=path['points']
            if path['kind']=='radial':pts=[tuple(a+(b-a)*k/30 for a,b in zip(pts[0],pts[-1])) for k in range(31)]
            for y,z in pts:
                r=math.hypot(y,z)
                if not pack['inner']+.0035<r<pack['outer']-.0003:continue
                for sign in [-1,1]:
                    hit,normal,index,distance=tree.ray_cast(Vector((centre+sign*(half+.001),-z,y)),Vector((-sign,0,0)),.003)
                    assert hit is not None,(name,path['kind'],r)
                    error=abs(distance-(.001+D['surfaces']['depth']));depth_error=max(depth_error,error);ray_checks+=1
                    assert error<5e-8,(name,path['kind'],error)
        def cap_triangles(obj,top):
            m=obj.data;m.calc_loop_triangles();x=max(v.co.x for v in m.vertices) if top else min(v.co.x for v in m.vertices)
            return [[[float(m.vertices[i].co.z),float(-m.vertices[i].co.y)] for i in t.vertices] for t in m.loop_triangles if all(abs(m.vertices[i].co.x-x)<2e-8 for i in t.vertices)]
        exports[name]={'landTriangles':cap_triangles(ob,True),'steelTriangles':cap_triangles(bpy.data.objects[f'TX_{name}_disc_00'],True)}
out=ROOT/('work/transmission' if temporary else 'outputs')
(out/'clutch-groove-native-caps.json').write_text(json.dumps(exports),encoding='utf-8')
report={'discs':rows,'manifoldPositiveVolumeDiscs':len(rows),'grooveDepthRayChecks':ray_checks,'maxDepthErrorM':depth_error,'limits':'Native manifold volume and both-face channel depths. Fitted dimensions; no fluid film, thermal or wear simulation.'}
assert len(rows)==23
(out/'clutch-groove-native-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='discs'},indent=2),flush=True)
