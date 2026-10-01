"""Locate actual upper-arm surfaces above the retained support-bolt cap.

This is sampled line-of-adjustment diagnosis, not a continuous contact solution,
thread-engagement certification or modification of the suspension.
"""
import bpy
import hashlib
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
EXPECTED='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
OUT=ROOT/'outputs/cloud-suspension-stop-axis-20261001';OUT.mkdir(exist_ok=True)
assert not (OUT/'axis-probe.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED
mapping=json.loads((ROOT/'outputs/cloud-suspension-installation-20261001/reference-mapping.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
def C(p):return Vector((p[0],-p[2],p[1]))
def geometry(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    v=[ev.matrix_world@p.co for p in m.vertices];t=[tuple(p.vertices) for p in m.loop_triangles];ev.to_mesh_clear()
    return v,t
rows=[]
for measurement in mapping['measurements']:
    bpy.context.scene.frame_set(0)
    for name,pose in measurement['pose'].items():
        ob=bpy.data.objects[name];ob.location=C(pose['p']);ob.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update()
    index=0;prefix=f'S543_{index}'
    bolt=bpy.data.objects[prefix+'_droop_limit_bolt'];nut=bpy.data.objects[prefix+'_droop_locknut'];upper=bpy.data.objects[prefix+'_upper']
    bv,_=geometry(bolt);nv,_=geometry(nut)
    _,axes=np.linalg.eigh(np.cov(np.array(bv).T));axis=axes[:,-1]
    assert abs(axis[2])>1-1e-6, 'Vertical adjustment assumption does not match retained bolt geometry'
    top=max(v.z for v in bv);bottom=min(v.z for v in bv)
    centre=Vector((sum(v.x for v in bv)/len(bv),sum(v.y for v in bv)/len(bv),top))
    radius=max(math.hypot(v.x-centre.x,v.y-centre.y) for v in bv if abs(v.z-top)<1e-6)
    trees=[]
    for obj in upper.children_recursive:
        if obj.type not in {'MESH','CURVE'}:continue
        v,t=geometry(obj)
        if t:trees.append((obj.name,BVHTree.FromPolygons(v,t,all_triangles=True)))
    # Interior rings avoid claiming a cap-edge sample establishes continuous fit.
    samples=[centre.copy()]+[centre+Vector((radius*r*math.cos(i*2*math.pi/48),radius*r*math.sin(i*2*math.pi/48),0))
                            for r in [.25,.5,.75,.95] for i in range(48)]
    hits=[]
    for sample_index,p in enumerate(samples):
        candidates=[]
        for name,tree in trees:
            hit,normal,face,distance=tree.ray_cast(p+Vector((0,0,1e-6)),Vector((0,0,1)),.6)
            if hit is not None:candidates.append((hit.z-p.z,name,list(hit),list(normal)))
        if candidates:
            distance,name,point,normal=min(candidates)
            hits.append({'sample':sample_index,'required_upward_translation_m':distance,'upper_object':name,'hit':point,'normal':normal})
    nut_min=min(v.z for v in nv);nut_max=max(v.z for v in nv)
    smallest=min((r['required_upward_translation_m'] for r in hits),default=None)
    rows.append({'station':index,'side':'right','requested_lower_head_vertical_difference_m':measurement['requestedVerticalDropM'],
                 'actual_bolt_cap_centre':list(centre),'actual_cap_radius_m':radius,'bolt_z_extent_m':[bottom,top],
                 'bolt_principal_axis':axis.tolist(),
                 'retained_nut_z_extent_m':[nut_min,nut_max],'cap_samples':len(samples),'hit_samples':len(hits),
                 'sampled_first_translation_m':smallest,'hits':hits,
                 'bolt_nut_axial_interval_overlap_after_sampled_translation_m':
                     max(0,min(top+smallest,nut_max)-max(bottom+smallest,nut_min)) if smallest is not None else None,
                 'limits':'Vertical cap rays only. Positive axial interval overlap does not establish real threads, adequate engagement, cap pressure or full swept-volume clearance.'})
report={'status':'READ_ONLY_SAMPLED_ADJUSTMENT_AXIS_DIAGNOSIS','source_sha256':EXPECTED,'source_sha256_after':sha(SOURCE),
        'reference':'1977 printed p320; support bolt must be screwed to touch upper arm during specified torsion installation setting.',
        'rows':rows,'saved_blend':False,'whole_vehicle_acceptance':'16 OPEN'}
assert report['source_sha256_after']==EXPECTED
(OUT/'axis-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print('STOP_AXIS_PROBE',json.dumps([{k:r[k] for k in ['requested_lower_head_vertical_difference_m','hit_samples','sampled_first_translation_m','bolt_nut_axial_interval_overlap_after_sampled_translation_m']} for r in rows]))
