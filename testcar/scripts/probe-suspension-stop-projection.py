"""Conservative full-bolt XY footprint versus actual upper-arm triangle projections."""
import bpy
import hashlib
import json
import math
import sys
import argparse
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from planar_clearance import hull,distance
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
EXPECTED='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
OUT=ROOT/'outputs/cloud-suspension-stop-axis-20261001'
parser=argparse.ArgumentParser();parser.add_argument('--all-stations',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
output=OUT/('projection-all-stations.json' if args.all_stations else 'projection-probe.json')
assert not output.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SOURCE)==EXPECTED
mapping=json.loads((ROOT/'outputs/cloud-suspension-installation-20261001/reference-mapping.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def C(p):return Vector((p[0],-p[2],p[1]))
def geometry(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    v=[ev.matrix_world@p.co for p in m.vertices];t=[tuple(p.vertices) for p in m.loop_triangles];ev.to_mesh_clear();return v,t
def bbox(p):return [min(q[0] for q in p),min(q[1] for q in p),max(q[0] for q in p),max(q[1] for q in p)]
def lower_bound(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def inspect_station(station,measurement):
    bv,_=geometry(bpy.data.objects[f'S543_{station}_droop_limit_bolt'])
    _,axes=np.linalg.eigh(np.cov(np.array(bv).T));axis=axes[:,-1]
    assert abs(axis[2])>1-1e-6, 'Retained bolt axis is not vertical'
    footprint=hull([(v.x,v.y) for v in bv]);box=bbox(footprint)
    best=float('inf');nearest=None;triangle_count=0;tested=0
    for o in bpy.data.objects[f'S543_{station}_upper'].children_recursive:
        if o.type not in {'MESH','CURVE'}:continue
        v,t=geometry(o)
        for index,tri in enumerate(t):
            triangle_count+=1;p=hull([(v[i].x,v[i].y) for i in tri])
            if lower_bound(box,bbox(p))>=best:continue
            tested+=1;gap=distance(footprint,p)
            if gap<best:best=gap;nearest={'object':o.name,'triangle':index,'world_vertices':[list(v[i]) for i in tri]}
    assert math.isfinite(best)
    return {'station':station,'requested_lower_head_vertical_difference_m':measurement['requestedVerticalDropM'],
                 'bolt_principal_axis':axis.tolist(),
                 'bolt_full_projection_hull':footprint,'upper_triangles':triangle_count,'polygon_pairs_evaluated':tested,
                 'minimum_xy_projection_gap_m':best,'nearest_triangle':nearest,
                 'clear_of_entire_bolt_vertical_extrusion_at_this_pose':best>2e-5,
                 'numerical_guard_m':2e-5}
rows=[]
for measurement in mapping['measurements']:
    bpy.context.scene.frame_set(0)
    for name,pose in measurement['pose'].items():
        o=bpy.data.objects[name];o.location=C(pose['p']);o.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update()
    for station in (range(8) if args.all_stations else [0]):rows.append(inspect_station(station,measurement))
report={'source_sha256':EXPECTED,'source_sha256_after':sha(SOURCE),'rows':rows,'saved_blend':False,
        'logic':'The full evaluated bolt lies inside its XY convex hull. If that hull is separated from every upper-arm triangle projection, translating the bolt only along Z cannot touch those triangles. This is a sufficient condition at each stated pose.',
        'stations_checked':list(range(8)) if args.all_stations else [0],
        'limits':'Numerical polygon computations with a 20 micrometre guard, not formal interval arithmetic. Only three sampled suspension settings at the listed stations. Does not establish factory bolt position, thread travel, assembly strength or intermediate suspension poses.',
        'whole_vehicle_acceptance':'16 OPEN'}
assert report['source_sha256_after']==EXPECTED
output.write_text(json.dumps(report,indent=2)+'\n')
print('STOP_PROJECTION',json.dumps([{k:r[k] for k in ['requested_lower_head_vertical_difference_m','minimum_xy_projection_gap_m','clear_of_entire_bolt_vertical_extrusion_at_this_pose']} for r in rows]))
