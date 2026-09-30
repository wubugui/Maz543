"""Read actual native pressure face, seal envelope and neighbouring clearance.
Dimensions are fitted. This checks the geometry/solver contract, not factory CAD.
"""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
temporary='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if temporary else 'outputs/MAZ543A_Transmission.blend')))
DATA=json.loads((ROOT/'work/transmission/poses.json').read_text());D=DATA['directBooster']
root=bpy.data.objects['S543_TRANSMISSION'];piston=bpy.data.objects['TX_direct_annular_piston']
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
mesh=piston.data;mesh.calc_loop_triangles()
face=D['pressureFace'];triangles=[]
for tri in mesh.loop_triangles:
    vs=[piston.matrix_world@mesh.vertices[i].co for i in tri.vertices]
    if all(abs(v.x-face)<1e-7 for v in vs):triangles.append(vs)
area=sum(abs((v[1]-v[0]).cross(v[2]-v[0]).x)/2 for v in triangles)
radii=[math.hypot(v.y,v.z) for vs in triangles for v in vs]
inner=min(radii);outer=max(radii)
seal=bpy.data.objects['TX_direct_piston_seal_outer_moving']
seal_radius=max(math.hypot(v.co.y,v.co.z) for v in seal.data.vertices)
effective=math.pi*(seal_radius**2-inner**2)
expected=math.pi*(D['outerSealRadius']**2-D['innerSealRadius']**2)
assert abs(effective/expected-1)<1e-6,(effective,expected)
assert abs(area/(math.pi*(outer**2-inner**2))-1)<.0002
assert inner<.5*outer,'broad annular pressure face; not the superseded outboard-only flange'
checks=0
for stroke in [0,.001125,.00225,.003375,.0045]:
    bpy.data.objects['TX_piston_direct'].location.x=stroke;bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get();trees=[]
    for ob in root.children_recursive:
        if ob.type!='MESH':continue
        ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        trees.append((ob.name,BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)))
        ev.to_mesh_clear()
    # Sample the broad chamber, not just the original feed point at r=99 mm.
    for j in range(24):
        a=j*math.tau/24
        for k in range(12):
            r=inner+.001+(outer-inner-.002)*k/11
            origin=Vector((face+stroke-.0002,-r*math.sin(a),r*math.cos(a)))
            hits=[]
            for name,tree in trees:
                hit=tree.ray_cast(origin,Vector((1,0,0)),.001)
                if hit[0] is not None:hits.append((hit[3],name))
            assert hits and min(hits)[1]==piston.name,(stroke,r,a,hits[:4])
            # A radial line in the fluid layer must stay open from hub to rim.
            end=Vector((origin.x,-(outer-.001)*math.sin(a),(outer-.001)*math.cos(a)))
            delta=end-origin
            if delta.length>1e-7:
                for name,tree in trees:
                    hit=tree.ray_cast(origin,delta.normalized(),delta.length)
                    assert hit[0] is None,(stroke,r,a,name,'blocked broad chamber')
            checks+=1
report={'pressureFaceAreaM2':area,'effectiveAreaFromNativeSealsM2':effective,'solverAreaM2':expected,
        'innerSealRadiusM':inner,'outerSealRadiusM':seal_radius,'chamberChecks':checks,
        'limits':'Fitted dimensions. Native polygon area, seal boundary and 5 strokes/24 azimuths/12 radii; not factory pressure or load acceptance.'}
out=ROOT/('work/transmission/direct-area-checks.json' if temporary else 'outputs/direct-pressure-area-checks.json')
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
