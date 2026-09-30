"""Fresh-process readback of the independent FG16 study; never save production.

Triangle intersections, nearest vertex-to-surface gaps and sampled containment
have deliberately different meanings. No result certifies physical assembly.
"""
import bpy, bmesh, json, math, hashlib, itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
build=json.loads((OUT/'native-audit-build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(OUT/'FG16_Native_Structural_Study.blend'))
scene=bpy.data.scenes['FG16_ASSEMBLED_STUDY'];bpy.context.window.scene=scene
source_coll=bpy.data.collections['01_FG16_SOURCE_INDEXED_COMPONENTS']
objs=[o for o in source_coll.objects if o.type in {'MESH','CURVE'}]
dg=bpy.context.evaluated_depsgraph_get()
def snapshot(o):
    ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
    vertices=[o.matrix_world@v.co for v in me.vertices]
    faces=[tuple(t.vertices) for t in me.loop_triangles]
    bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
    stats={'name':o.name,'vertices':len(me.vertices),'faces':len(me.polygons),'boundary_edges':sum(e.is_boundary for e in bm.edges),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'non_manifold_vertices':sum(not v.is_manifold for v in bm.verts),'signed_volume_m3':bm.calc_volume(signed=True),'degenerate_faces':sum(f.calc_area()<1e-15 for f in bm.faces),'loose_vertices':sum(not v.link_edges for v in bm.verts)}
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True,epsilon=0.0)
    nonadjacent=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(faces[a]).intersection(faces[b])]
    stats['nonadjacent_self_intersection_triangle_pairs']=len(nonadjacent)
    bm.free();ev.to_mesh_clear();return stats,vertices,tree
data={o.name:snapshot(o) for o in objs}
topology=[r[0] for r in data.values()]
same=[]
for prior in build['topology']:
    now=data[prior['name']][0]
    same.append({'object':prior['name'],'vertices_equal':prior['vertices']==now['vertices'],'faces_equal':prior['faces']==now['faces'],'volume_difference_m3':now['signed_volume_m3']-prior['volume_m3_signed']})

def nearest(a,b):
    pts=data[a][1];tree=data[b][2]
    hits=[tree.find_nearest(p) for p in pts]
    hits=[(i,h) for i,h in enumerate(hits) if h[0] is not None]
    i,h=min(hits,key=lambda z:z[1][3])
    return {'distance_mm':h[3]*1000,'sample_point':list(pts[i]),'nearest_point':list(h[0])}

intended={frozenset([x['a'],x['b']]):x['intended_interface'] for x in build['contacts'] if x['intended_interface']}
pairs=[]
directions=[Vector(d).normalized() for d in [(1,.371,.119),(-.237,1,.461),(.317,-.219,1)]]
containment_diagnostics=[]
current_pair=None
def cast_path(p,tree,direction,offset):
    current=p.copy();hits=[]
    for _ in range(32):
        q,n,face,distance=tree.ray_cast(current,direction,2.)
        if q is None:break
        hits.append({'face':face,'distance_from_previous_m':distance,'point':list(q)})
        current=q+direction*offset
    return hits
def inside_material(p,tree):
    # Deterministic non-axis ray. Skip near-surface starts. This is a sampled
    # containment diagnostic, not exact volumetric Boolean or contact solution.
    nearest=tree.find_nearest(p)
    if nearest[0] is None or nearest[3]<1e-7:return None
    votes=[];paths=[]
    for direction in directions:
        hits=cast_path(p,tree,direction,1e-5);paths.append(hits);votes.append(bool(len(hits)%2))
    oldhits=cast_path(p,tree,directions[0],1e-7);oldvote=bool(len(oldhits)%2)
    unanimous=len(set(votes))==1
    if not unanimous or oldvote!=votes[0]:
        target_points=data[current_pair[1]][1]
        bounds={'min':[min(v[i] for v in target_points) for i in range(3)],'max':[max(v[i] for v in target_points) for i in range(3)]}
        containment_diagnostics.append({'sample_object':current_pair[0],'target_material_object':current_pair[1],'point':list(p),'target_aabb':bounds,'outside_target_aabb':any(p[i]<bounds['min'][i]-1e-7 or p[i]>bounds['max'][i]+1e-7 for i in range(3)),'old_single_ray_inside':oldvote,'old_offset_m':1e-7,'old_intersections':oldhits,'new_offset_m':1e-5,'new_directions':[list(d) for d in directions],'new_ray_inside_votes':votes,'new_intersections':paths,'status':'AMBIGUOUS_OPEN' if not unanimous else 'UNANIMOUS_NEW_RAYS_RECORDED_FOR_REVIEW'})
    return votes[0] if unanimous else None
for a,b in itertools.combinations(objs,2):
    hits=data[a.name][2].overlap(data[b.name][2]);key=frozenset([a.name,b.name])
    contained={}
    for one,other in [(a,b),(b,a)]:
        current_pair=(one.name,other.name)
        pts=data[one.name][1];stride=max(1,len(pts)//128);sample=pts[::stride][:128]
        statuses=[inside_material(v,data[other.name][2]) for v in sample]
        contained[one.name]={'sampled_vertices':len(statuses),'inside_other_material':sum(x is True for x in statuses),'on_surface_or_ambiguous_skipped':sum(x is None for x in statuses)}
    if hits or key in intended or any(x['inside_other_material'] for x in contained.values()):
        ab=nearest(a.name,b.name);ba=nearest(b.name,a.name)
        gap=ab if ab['distance_mm']<ba['distance_mm'] else ba
        reason=intended.get(key)
        status='FITTED_INTERFACE_UNCALIBRATED' if reason else 'UNRESOLVED_INTERSECTION_OR_CONTAINMENT'
        if hits and key==frozenset(['FG16_05_Hollow_optical_element','FG16_07_Cap_base']):
            status='UNRESOLVED_RIGID_INTERFACE_INTERFERENCE'
        pairs.append({'a':a.name,'b':b.name,'surface_triangle_intersections':len(hits),'nearest_vertex_to_surface':gap,'containment_samples':contained,'intended_interface':reason,'status':status})

# Direct body-only probes establish real hollow geometry and openings.
body=data['FG16_06_Hollow_curved_body'][2]
center=bpy.data.objects['FG16_OPTICAL_AXIS_X'].matrix_world.translation
probes=[]
for name,direction in [('front_open',(-1,0,0)),('rear_wall',(1,0,0)),('side_wall',(0,1,0)),('upper_wall',(0,0,1)),('wire_exit',(0,0,-1))]:
    hit,n,face,d=body.ray_cast(center,Vector(direction),1)
    probes.append({'ray':name,'hit':hit is not None,'distance_mm':d*1000 if d is not None else None,'location':list(hit) if hit is not None else None})

yaw=bpy.data.objects['CONTROL_YAW_340deg_SOURCE_ZERO_FITTED']
axis=[]
for angle in [-1000,-210]+[-170+i*8.5 for i in range(41)]+[210,1000]:
    yaw['azimuth_deg']=float(angle);yaw.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update()
    actual=math.degrees(yaw.evaluated_get(dg).matrix_world.to_euler().z)
    expect=max(-170,min(170,angle))
    axis.append({'requested_deg':angle,'evaluated_deg':actual,'error_deg':actual-expect})
yaw['azimuth_deg']=0.;yaw.update_tag();scene.frame_set(scene.frame_current);bpy.context.view_layer.update()

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

report={'status':'LIMITED_NATIVE_STUDY_ONLY_NOT_PRODUCTION','blender_version':bpy.app.version_string,'all_16_vehicle_gates':'OPEN','source_components_meshes':len(objs),'unmodeled_source_fastener_locator':bpy.data.objects['FG16_09_FASTENER_UNMODELED_LOCATOR']['modeling_status'],'native_source_curves':len(bpy.data.collections['02_EDITABLE_SOURCE_CURVES'].objects),'topology':topology,'readback_comparison':same,'all_closed_positive_volume':all(x['boundary_edges']==0 and x['non_manifold_edges']==0 and x['signed_volume_m3']>0 and x['loose_vertices']==0 for x in topology),'contact_pairs':pairs,'unclassified_contact_count':sum(x['status'].startswith('UNRESOLVED') for x in pairs),'contact_scope':'36 source-geometry pairs at rest. Triangle intersections plus at most 128 vertices per side sampled for material containment. Nearest-vertex-to-surface distances are mesh diagnostics; they are not exact minimum gap, manufacturing tolerance or proof that a load-bearing/sealed connection exists.','assembly_connection_status':'OPEN: retaining lip engagement, lamp seating, wire termination and seal compression need actual construction/reference dimensions. Zero triangle intersections does not establish connectivity.','body_hollow_probes':probes,'horizontal_axis_samples':axis,'horizontal_axis_pass':max(abs(x['error_deg']) for x in axis)<1e-4,'vertical_axis':'NOT MODELED; source provides no angular limit','packed_reference_images':[{'name':im.name,'packed':im.packed_file is not None} for im in bpy.data.images if im.name.startswith('1977-original')],'render_files':[{'file':name,'exists':(OUT/name).exists(),'bytes':(OUT/name).stat().st_size if (OUT/name).exists() else None,'sha256':sha(OUT/name) if (OUT/name).exists() else None} for name in ['cycles-assembled.png','cycles-section.png']],'candidate_bytes':(OUT/'FG16_Native_Structural_Study.blend').stat().st_size,'candidate_sha256':sha(OUT/'FG16_Native_Structural_Study.blend')}
benchobjs=[o for o in bpy.data.collections['03_STUDY_FIXTURE_NOT_VEHICLE_HARDWARE'].objects if o.type=='MESH']
benchdata={o.name:snapshot(o) for o in benchobjs}
benchpairs=[]
for a in objs:
    for b in benchobjs:
        overlaps=data[a.name][2].overlap(benchdata[b.name][2])
        if overlaps:benchpairs.append({'source_component':a.name,'display_fixture':b.name,'surface_triangle_pairs':len(overlaps),'status':'DISPLAY_FIXTURE_INTERFERENCE_UNRESOLVED; not original vehicle mounting'})
report['display_fixture_intersections']=benchpairs
report['unresolved_rigid_interface_count']=sum(x['status']=='UNRESOLVED_RIGID_INTERFACE_INTERFERENCE' for x in pairs)
report['unclassified_contact_count']=sum(x['status']=='UNRESOLVED_INTERSECTION_OR_CONTAINMENT' for x in pairs)
report['unresolved_contact_pairs_count']=sum(x['status'].startswith('UNRESOLVED') for x in pairs)
report['all_closed_positive_volume']=report['all_closed_positive_volume'] and all(x['non_manifold_vertices']==0 for x in topology)
report['source_geometry_self_intersection_pass']=all(x['nonadjacent_self_intersection_triangle_pairs']==0 for x in topology)
report['containment_method']='Up to 128 vertices per side, three non-axis directions with 0.01 mm post-hit offset; classify inside/outside only on unanimous votes. Disagreements remain OPEN. Prior 0.0001 mm single-ray results and changed classifications are retained with exact intersections and target bounds. No claim that sampling proves complete volumetric separation.'
report['containment_disagreement_count']=sum(x['status']=='AMBIGUOUS_OPEN' for x in containment_diagnostics)
report['containment_diagnostic_count']=len(containment_diagnostics)
(OUT/'containment-ray-diagnostics.json').write_text(json.dumps(containment_diagnostics,indent=2),encoding='utf8')

# Production files are only reopened to compare original object fingerprints.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'testcar/outputs/MAZ543A_Master.blend'))
fingerprints={}
for name,prior in build['production_three_parts_geometry_before'].items():
    o=bpy.data.objects[name]
    raw={'verts':[list(v.co) for v in o.data.vertices],'edges':[list(e.vertices) for e in o.data.edges],'faces':[list(p.vertices) for p in o.data.polygons],'matrix':[list(row) for row in o.matrix_world]}
    fingerprint=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
    fingerprints[name]={'geometry_matrix_sha256':fingerprint,'unchanged':fingerprint==prior['geometry_matrix_sha256']}
report['production_three_parts_geometry_after']=fingerprints
hashes={path:sha(ROOT/path) for path in build['production_sha256_before']}
report['production_sha256_after']=hashes
report['production_files_byte_unchanged']=hashes==build['production_sha256_before']
(OUT/'readback-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('FG16_READBACK',json.dumps({key:report[key] for key in ['all_closed_positive_volume','unclassified_contact_count','horizontal_axis_pass','assembly_connection_status','production_files_byte_unchanged','candidate_bytes']}),flush=True)
assert report['all_closed_positive_volume']
assert report['horizontal_axis_pass']
assert report['production_files_byte_unchanged']
assert len(report['packed_reference_images'])==2 and all(x['packed'] for x in report['packed_reference_images'])
assert all(x['unchanged'] for x in fingerprints.values())
assert all(x['vertices_equal'] and x['faces_equal'] and abs(x['volume_difference_m3'])<1e-12 for x in same)
