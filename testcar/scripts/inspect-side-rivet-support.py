"""Read-only named side-skin support probes for retained rivet-head geometry.

The full lateral box gap is sufficient separation from the named skin only.
Nine base-footprint rays per component are samples, not whole-area coverage or
manufacturer fastener acceptance. No vertex, object, parent or pose is changed.
"""
import bpy,hashlib,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
COMPONENTS=ROOT/'work/cloud-closed-door-contact-components-20261001/component-report.json'
OUT=ROOT/'work/cloud-side-rivet-support-20261001';OUT.mkdir(parents=True,exist_ok=True)
EXPECTED='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
components=json.loads(COMPONENTS.read_text());assert components['source_sha256']==EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()

def mesh(name):
    o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh()
    try:
        xyz=np.asarray([tuple(v.co) for v in m.vertices],dtype=np.float64)
        w=np.asarray(e.matrix_world,dtype=np.float64);xyz=xyz@w[:3,:3].T+w[:3,3]
        m.calc_loop_triangles();tri=np.asarray([tuple(t.vertices) for t in m.loop_triangles],dtype=np.int32)
        return xyz,tri
    finally:e.to_mesh_clear()

def bvh(s):return BVHTree.FromPolygons(s[0].tolist(),s[1].tolist(),all_triangles=True,epsilon=0.)
def hit(tree,point,direction,distance=.15):
    location,normal,index,length=tree.ray_cast(Vector(point),Vector(direction),distance)
    return None if location is None else {'point':list(location),'triangle':index,'distance_m':length,'normal':list(normal)}

report={'status':'NAMED_SIDE_SKIN_MOUNT_RELATION_DIAGNOSTIC_ONLY','source_sha256':EXPECTED,
        'component_report_sha256':sha(COMPONENTS),'blender_version':bpy.app.version_string,'frame':0,
        'source_saved':False,'geometry_modified':False,'sides':[],'whole_vehicle_acceptance':'16 OPEN',
        'limits':['A lateral box gap proves separation only from the named monocoque mesh, not every hidden or other vehicle part',
                  'Nine base-ring footprint rays are finite point samples; they do not prove complete disk support or exact nearest surface distance',
                  'A zero skin sample with a door hit locates an ownership/installation conflict; it is not permission to delete or relocate hardware',
                  'No manufacturer head type/count, shank, actual mounting dimensions or batch identity is established',
                  'All current parts, visibility, parents and closed poses are retained']}
for side in [-1,1]:
    # NativeY reverses the browser/model side sign under C=(x,-z,y).
    outward=-side
    rivet_name=f'BL_Cab_{side}_side_rivets';skin_name=f'BL_Cab_{side}_side_monocoque'
    door_names=[f'BL_Door_{side}_{i}_pressed_shell' for i in [0,1]]
    rivets=mesh(rivet_name);skin=mesh(skin_name);doors=[mesh(n) for n in door_names]
    skin_tree=bvh(skin);door_trees=[bvh(s) for s in doors]
    groups=components['fixed_objects'][rivet_name]['exact_coordinate_components']
    assert len(groups)==75 and len(rivets[0])==1800 and len(rivets[1])==2850
    assert sorted(v for g in groups for v in g['vertices'])==list(range(len(rivets[0])))
    skin_axis=outward*skin[0][:,1];rivet_axis=outward*rivets[0][:,1]
    gap=float(rivet_axis.min()-skin_axis.max())
    assert gap>0, 'Unexpected geometry change; direct skin separation no longer holds'
    # Actual-surface positive and far-away negative controls for the same BVH.
    triangles=skin[0][skin[1]];normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    index=int(np.argmax(np.linalg.norm(normals,axis=1)));normal=normals[index];normal/=np.linalg.norm(normal)
    center=triangles[index].mean(0);positive=hit(skin_tree,center+normal*.01,-normal,.02)
    negative=hit(skin_tree,center+np.array([100.,0,0]),-normal,.02)
    assert positive is not None and negative is None
    rows=[]
    for group in groups:
        ids=group['vertices'];assert len(ids)==24 and len(group['triangles'])==38
        xyz=rivets[0][ids];axis=outward*xyz[:,1];base=xyz[np.abs(axis-axis.min())<1e-7]
        assert len(base)==8
        base_center=base.mean(0);samples=np.vstack([base_center,base]);rays=[]
        direction=[0.,-float(outward),0.]
        for point in samples:
            origin=point+np.array([0.,float(outward)*.02,0.])
            rays.append({'base_point':point.tolist(),'skin':hit(skin_tree,origin,direction),
                         'doors':[hit(tree,origin,direction) for tree in door_trees]})
        rows.append({'component':group['component'],'base_ring_vertices':8,'base_center':base_center.tolist(),
            'base_to_named_skin_global_box_gap_m':float(axis.min()-skin_axis.max()),
            'skin_hit_samples':sum(r['skin'] is not None for r in rays),
            'door_hit_samples':[sum(r['doors'][i] is not None for r in rays) for i in [0,1]],'rays':rays})
    candidates=[r['component'] for r in rows if r['skin_hit_samples']==0 and any(r['door_hit_samples'])]
    prior=[x for x in components['contacts'] if x['fixed']==rivet_name]
    prior_ids=sorted({h['fixed_component'] for c in prior for h in c['hit_components']})
    assert prior_ids==[50,51,52]
    detail={'rivet_object':rivet_name,'side_skin_object':skin_name,'door_objects':door_names,
            'native_outward_y_sign':outward,'skin_lateral_range_m':[float(skin_axis.min()),float(skin_axis.max())],
            'rivet_lateral_range_m':[float(rivet_axis.min()),float(rivet_axis.max())],
            'whole_rivet_mesh_named_skin_axis_gap_m':gap,'controls':{'skin_positive':positive,'far_negative':negative},
            'rivet_components':rows,'no_skin_samples_but_door_samples':candidates,'previous_closed_contact_components':prior_ids}
    path=OUT/f'side_{side}.json';path.write_text(json.dumps(detail,ensure_ascii=False,separators=(',',':'))+'\n')
    entry={'side':side,'components':len(rows),'samples':len(rows)*9,'lateral_box_gap_m':gap,
           'components_all9_skin_hits':sum(r['skin_hit_samples']==9 for r in rows),
           'components_no_skin_hits':sum(r['skin_hit_samples']==0 for r in rows),
           'components_partial_skin_hits':sum(0<r['skin_hit_samples']<9 for r in rows),
           'no_skin_samples_but_door_samples':candidates,
           'previous_contact_rows':[r for r in rows if r['component'] in prior_ids],
           'detail_file':path.name,'detail_sha256':sha(path)}
    report['sides'].append(entry)
    print('RIVET_SUPPORT',side,'gap',gap,'whole',entry['components_all9_skin_hits'],'none',entry['components_no_skin_hits'],'partial',entry['components_partial_skin_hits'],'door_projection',candidates,flush=True)
report['source_sha256_after']=sha(SOURCE);assert report['source_sha256_after']==EXPECTED
(OUT/'support-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
