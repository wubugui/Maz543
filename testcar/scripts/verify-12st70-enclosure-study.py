"""Read back only the new enclosure stage and preservation of its73 inputs.

Whole-box separation or native exact Boolean intersection checks the new
forms. Piece boxes cover surfaces only; they do not by themselves prove solid
containment. This is not a factory mounting, removal or electrical safety test.
"""
import bpy,bmesh,json,hashlib,itertools
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-12st70-enclosure-20261001'
source=ROOT/'outputs/cloud-12st70-structure-20261001/12ST70_Family_Structure_Study.blend'
candidate=OUT/'12ST70_Enclosure_Form_Study.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [source,candidate]}
old_register=json.loads((source.parent/'parts-register.json').read_text())
def snapshot(o,dg):
    e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
    v=[e.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles]
    bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
    stats={'vertices':len(v),'triangles':len(f),'non_manifold_edges':sum(not x.is_manifold for x in bm.edges),'non_manifold_vertices':sum(not x.is_manifold for x in bm.verts),'signed_volume_m3':bm.calc_volume(signed=True),'degenerate_faces':sum(x.calc_area()<1e-15 for x in bm.faces)}
    tree=BVHTree.FromPolygons(v,f,all_triangles=True,epsilon=0)
    stats['nonadjacent_self_intersection_triangle_pairs']=sum(1 for a,b in tree.overlap(tree) if a<b and not set(f[a])&set(f[b]))
    bm.free();e.to_mesh_clear();return {'v':v,'f':f,'stats':stats,'tree':tree}
def bounds(v):return [min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
original={r['name']:snapshot(bpy.data.objects[r['name']],dg) for r in old_register}
bpy.ops.wm.open_mainfile(filepath=str(candidate));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
register=json.loads((OUT/'parts-register.json').read_text());data={r['name']:snapshot(bpy.data.objects[r['name']],dg) for r in register}
preserved=[]
for name,d in original.items():
    c=data[name];topology_same=c['f']==d['f'];delta=max((a-b).length for a,b in zip(c['v'],d['v'])) if len(c['v'])==len(d['v']) else None
    preserved.append({'part':name,'same_vertex_count':len(c['v'])==len(d['v']),'same_triangle_indices':topology_same,'max_world_vertex_difference_m':delta})
lid='FITTED_pressed_wood_overall_lid';hood='FITTED_terminal_protective_hood';added=[lid,hood]
# Convex cuboids covering all triangles (and therefore each triangle interior)
# of the closed U-form. Rounded edges stay inside the original solid stock.
lo,hi=bounds(data[hood]['v']);wall=.0015;cover_pad=2e-7;bevel_allowance=.00035
# Concave inner-corner bevels add material just outside the unrounded U union.
# Include the native bevel width in the covering boxes, then check EVERY
# evaluated triangle rather than assuming the nominal stock is still a cover.
piece_thickness=wall+bevel_allowance+cover_pad
pieces=[(lo,[lo[0]+piece_thickness,hi[1],hi[2]]),
        (lo,[hi[0],lo[1]+piece_thickness,hi[2]]),
        ([lo[0],hi[1]-piece_thickness,lo[2]],hi)]
def contained(points,box):
    a,b=box;return all(a[k]<=p[k]<=b[k] for p in points for k in range(3))
uncovered=[i for i,t in enumerate(data[hood]['f']) if not any(contained([data[hood]['v'][j] for j in t],box) for box in pieces)]
# Whole boxes expanded by20um exclude contained-volume collisions. Overlapping
# whole boxes use actual native Boolean solids, not just zero surface hits.
pad=2e-5
def gap(a,b):return max(max(a[0][k]-b[1][k],b[0][k]-a[1][k])-2*pad for k in range(3))
boxes={name:bounds(d['v']) for name,d in data.items()}
def native_intersection(a,b):
    copies=[]
    for source_object in [a,b]:
        evaluated=source_object.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(evaluated)
        obj=bpy.data.objects.new('READBACK_TEMP_INTERSECTION',mesh);bpy.context.scene.collection.objects.link(obj);obj.matrix_world=evaluated.matrix_world.copy();copies.append(obj)
    mod=copies[0].modifiers.new('Readback native exact solid intersection','BOOLEAN');mod.operation='INTERSECT';mod.solver='EXACT';mod.object=copies[1]
    bpy.context.view_layer.update();ev=copies[0].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh);bm.normal_update();result={'vertices':len(mesh.vertices),'faces':len(mesh.polygons),'absolute_volume_m3':abs(bm.calc_volume(signed=True))};bm.free();ev.to_mesh_clear()
    for o in copies:
        mesh=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(mesh)
    return result
# A positive containment control prevents treating zero triangle crossings as
# an empty intersection. Controls exist in this unsaved readback only.
control_objects=[]
for size,loc in [(1,(10,0,0)),(.2,(10,0,0)),(.2,(12,0,0)),(1,(10.5,0,0))]:
    bpy.ops.mesh.primitive_cube_add(size=size,location=loc);control_objects.append(bpy.context.object)
bpy.context.view_layer.update()
controls={name:native_intersection(control_objects[0],control_objects[i]) for name,i in [('contained',1),('disjoint',2),('overlap',3)]}
assert abs(controls['contained']['absolute_volume_m3']-.008)<1e-6 and controls['contained']['faces']>0
assert controls['disjoint']['vertices']==0 and abs(controls['overlap']['absolute_volume_m3']-.5)<1e-6
for o in control_objects:
    mesh=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(mesh)
checks=[]
for a,b in itertools.combinations(data,2):
    if a not in added and b not in added:continue
    a_parts=pieces if a==hood else [boxes[a]];b_parts=pieces if b==hood else [boxes[b]]
    gaps=[gap(x,y) for x,y in itertools.product(a_parts,b_parts)]
    hits=len(data[a]['tree'].overlap(data[b]['tree']))
    whole_gap=gap(boxes[a],boxes[b]);solid=None
    if whole_gap<=0:solid=native_intersection(bpy.data.objects[a],bpy.data.objects[b])
    passed=hits==0 and (whole_gap>0 or solid['vertices']==0)
    checks.append({'a':a,'b':b,'surface_triangle_intersections':hits,'whole_box_gap_after_20um_expansion_each_m':whole_gap,'piece_surface_box_gaps_m':gaps,'native_exact_boolean_intersection':solid,'status':'STATIC_DISJOINT_BY_WHOLE_BOX' if passed and whole_gap>0 else ('STATIC_NATIVE_BOOLEAN_EMPTY' if passed else 'UNRESOLVED_OR_INTERSECTING')})
points=[p for d in data.values() for p in d['v']];low,high=bounds(points)
report={'status':'UNACCEPTED_ENCLOSURE_FORM_STUDY','source_sha256':before[str(source)],'candidate_sha256':before[str(candidate)],'preserved_parts':preserved,'new_part_topology':{n:data[n]['stats'] for n in added},
 'hood_surface_covering_piece_boxes_m':pieces,'hood_triangles_outside_piece_box_cover':uncovered,'native_boolean_controls':controls,'new_part_static_pairs':checks,
 'modeled_bounds_m':{'min':low,'max':high,'extent':[b-a for a,b in zip(low,high)]},
 'source_boundary':'Generic1983 fig4 form; p11 confirms family cover/hood. Factory dimensions, fasteners, retention interaction, carrying hardware, insulation, vehicle installation and actual removal trajectory remain OPEN.',
 'inspection_offsets_are_not_kinematics':True,'source_images_embedded':any(im.source=='FILE' for im in bpy.data.images),'all16VehicleGates':'OPEN',
 'files_unchanged':all(sha(Path(p))==s for p,s in before.items())}
(OUT/'native-readback.json').write_text(json.dumps(report,indent=2))
assert len(preserved)==73 and all(x['same_vertex_count'] and x['same_triangle_indices'] and x['max_world_vertex_difference_m']==0 for x in preserved)
assert all(s['non_manifold_edges']==0 and s['non_manifold_vertices']==0 and s['signed_volume_m3']>0 and s['degenerate_faces']==0 and s['nonadjacent_self_intersection_triangle_pairs']==0 for s in report['new_part_topology'].values())
assert not uncovered and all(x['status'].startswith('STATIC_') for x in checks)
assert report['files_unchanged'] and not report['source_images_embedded']
print('ENCLOSURE_READBACK',len(preserved),'exactly preserved parts;',len(checks),'static new-part pairs;',len(uncovered),'uncovered hood triangles; factory assembly OPEN',flush=True)
