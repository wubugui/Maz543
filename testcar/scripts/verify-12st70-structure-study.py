"""Fresh native readback; keeps structural and electrical-layout claims limited."""
import bpy,bmesh,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-12st70-structure-20261001'
source=OUT/'12ST70_Family_Structure_Study.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
register=json.loads((OUT/'parts-register.json').read_text());parts=[bpy.data.objects[r['name']] for r in register]
def snapshot(o):
    ev=o.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles();v=[ev.matrix_world@x.co for x in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles]
    bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
    stats={'name':o.name,'vertices':len(v),'triangles':len(f),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'non_manifold_vertices':sum(not x.is_manifold for x in bm.verts),'signed_volume_m3':bm.calc_volume(signed=True),'degenerate_faces':sum(p.calc_area()<1e-15 for p in bm.faces)}
    tree=BVHTree.FromPolygons(v,f,all_triangles=True,epsilon=0.)
    stats['nonadjacent_self_intersection_triangle_pairs']=sum(1 for a,b in tree.overlap(tree) if a<b and not set(f[a]).intersection(f[b]))
    bm.free();ev.to_mesh_clear();return stats,v,tree
data={o.name:snapshot(o) for o in parts};topology=[v[0] for v in data.values()]
cavities=[]
for block in range(3):
    name=f'EBONITE_block_{block+1}_FOUR_CHAMBERS';tree=data[name][2]
    zmax=max(p.z for p in data[name][1]);zmin=min(p.z for p in data[name][1])
    for ix,iy in itertools.product(range(2),repeat=2):
        cutter=bpy.data.objects[f'TOOL_block{block+1}_chamber{ix}_{iy}'];xy=cutter.evaluated_get(dg).matrix_world.translation
        start=Vector((xy.x,xy.y,zmax+.01));hit,n,face,d=tree.ray_cast(start,Vector((0,0,-1)),1.)
        assert hit is not None and zmin<hit.z<zmax-.1,(name,ix,iy,'not an open deep chamber')
        middle=Vector((xy.x,xy.y,(zmin+zmax)/2));sides=[]
        for direction in [Vector((1,0,0)),Vector((-1,0,0)),Vector((0,1,0)),Vector((0,-1,0))]:
            p,n,face,dist=tree.ray_cast(middle,direction,1.);assert p is not None and 0<dist<.12;sides.append(dist)
        cavities.append({'tank':name,'grid':[ix,iy],'floor_z_m':hit.z,'open_depth_from_tank_rim_m':zmax-hit.z,'four_side_wall_distances_m':sides})
weld=[]
for o in parts:
    if 'editable_curve_source' not in o:continue
    src=bpy.data.objects[o['editable_curve_source']];_,original,_=snapshot(src);current=data[o.name][1]
    def max_nearest(a,b):
        kd=KDTree(len(b))
        for i,p in enumerate(b):kd.insert(p,i)
        kd.balance();return max(kd.find(p)[2] for p in a)
    difference=max(max_nearest(original,current),max_nearest(current,original));assert difference<=1e-7,(o.name,difference)
    weld.append({'part':o.name,'curve_source':src.name,'maximum_bidirectional_vertex_set_difference_m':difference,'original_vertices':len(original),'welded_vertices':len(current)})
expected=set()
for i in range(1,12):
    link=f'SERIES_LINK_{i:02d}_{i+1:02d}'
    expected.add(frozenset([link,f'CELL_{i:02d}_positive_post']))
    expected.add(frozenset([link,f'CELL_{i+1:02d}_negative_post']))
for polarity,cell in [('negative',1),('positive',12)]:
    expected.add(frozenset([polarity+'_front_lead',f'CELL_{cell:02d}_{polarity}_post']))
    expected.add(frozenset([polarity+'_front_lead','FRONT_'+polarity+'_terminal_lug']))
conductive=[o for o in parts if o['role'] in {'series_link','lead_post','front_terminal','front_lead','steel_band'}]
contacts=[]
unresolved_volume_pairs=[];disjoint_nonjoint_pairs=0
for a,b in itertools.combinations(conductive,2):
    key=frozenset([a.name,b.name]);hits=data[a.name][2].overlap(data[b.name][2])
    if key not in expected and not hits:
        av,bv=data[a.name][1],data[b.name][1]
        gap=max(max(min(p[k] for p in av)-max(p[k] for p in bv),min(p[k] for p in bv)-max(p[k] for p in av)) for k in range(3))
        if gap>2e-7:disjoint_nonjoint_pairs+=1
        else:unresolved_volume_pairs.append({'a':a.name,'b':b.name,'aabb_axis_gap_m':gap,'status':'SURFACE_CLEAR_BUT_FULL_CONTAINMENT_OR_CONTACT_UNRESOLVED'})
    if hits or key in expected:
        contacts.append({'a':a.name,'b':b.name,'surface_triangle_pairs':len(hits),'expected_electrical_joint':key in expected,'status':'FITTED_JOINT_REQUIRES_WELD_DETAIL' if key in expected and hits else ('INTENDED_JOINT_WITHOUT_SURFACE_CROSSING_UNRESOLVED' if key in expected else 'UNEXPECTED_CONDUCTOR_OR_STEEL_INTERSECTION')})
positions=[p for o in parts for p in data[o.name][1]];minimum=[min(p[i] for p in positions) for i in range(3)];maximum=[max(p[i] for p in positions) for i in range(3)]
report={'status':'NATIVE_STRUCTURE_STUDY_ONLY_NOT_ACCEPTED_BATTERY','source_sha256':before,'topology':topology,'physical_chamber_probes':cavities,'weld_source_comparisons':weld,'conductive_surface_contacts':contacts,
        'unexpected_conductive_intersections':sum(x['status'].startswith('UNEXPECTED') for x in contacts),
        'missing_expected_surface_contact_checks':sum(x['status'].startswith('INTENDED') for x in contacts),
        'nonjoint_conductor_pairs_disjoint_by_padded_boxes':disjoint_nonjoint_pairs,'unresolved_nonjoint_volume_pairs':unresolved_volume_pairs,
        'modeled_geometry_bounds_m':{'min':minimum,'max':maximum,'extent':[b-a for a,b in zip(minimum,maximum)]},
        'published_complete_unit_envelope_m':[.587,.238,.239],
        'dimension_interpretation':'Current fitted wood case/tanks/links are incomplete. Overall published dimensions include an unresolved complete configuration; this smaller study does not pass factory dimension acceptance.',
        'electrical_scope':'12-cell series graph and modeled contact locations only; no plate packs, separator count, electrolyte, resistance, electrochemistry, thermal/ventilation or insulation-clearance verification. Copper inserts and weld details not modeled.',
        'omitted_hardware':['terminal protective hood','pressed wood overall lid','precise carrying hardware','vehicle box/mounts and four-unit placement'],
        'no_original_scan_pixels_embedded':not any(im.source=='FILE' for im in bpy.data.images),
        'all16VehicleGates':'OPEN','file_unchanged_after_readback':sha(source)==before}
(OUT/'native-readback.json').write_text(json.dumps(report,indent=2))
print('BATTERY_READBACK',len(parts),'parts',len(cavities),'chambers',len(weld),'weld comparisons',report['unexpected_conductive_intersections'],'unexpected intersections',report['missing_expected_surface_contact_checks'],'unresolved joints',flush=True)
assert all(x['non_manifold_edges']==0 and x['non_manifold_vertices']==0 and x['signed_volume_m3']>0 and x['degenerate_faces']==0 for x in topology)
assert len(cavities)==12 and len(weld)==13
assert report['file_unchanged_after_readback'] and report['no_original_scan_pixels_embedded']
