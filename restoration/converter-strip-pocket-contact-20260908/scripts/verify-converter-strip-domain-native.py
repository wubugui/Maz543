"""Audit candidate beam solutions against the current saved pocket solids."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
suffix='strip-pocket-domain' if '--pocket' in sys.argv else 'strip-domain'
data=json.loads((ROOT/f'work/freewheel-contact/{suffix}.json').read_text());fit=data['fit']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend'))
bpy.context.view_layer.update()
def tree(ob):
    ob.data.calc_loop_triangles()
    return BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True)
outer=tree(bpy.data.objects['CS_outer_pocket']);inner=tree(bpy.data.objects['CS_fixed_inner_section']);rows=[]
alpha=math.radians(7);normal=(math.cos(alpha),math.sin(alpha));distance=.00625+(.056+.00625)*normal[0]
# Quantify the saved wedge vertices' deviation from the original exact plane.
# This is a storage bound, not a tunable collision tolerance.
saved_plane_errors=[]
for v in bpy.data.objects['CS_outer_pocket'].data.vertices:
    y,z=v.co.z,-v.co.y;angle=math.degrees(math.atan2(z,y));R=math.hypot(y,z)
    if -12.99<angle<7.99 and R<.08:saved_plane_errors.append(abs(normal[0]*y+normal[1]*z-distance))
saved_plane_error=max(saved_plane_errors)
for candidate in data['rows']:
    entry={k:v for k,v in candidate.items() if k!='solution'};rows.append(entry)
    if 'solution' not in candidate:continue
    points=candidate['solution']['points'];vertices,faces=geometry(points,fit['widthM'],fit['thicknessM'])
    mesh=bpy.data.meshes.new('domain_candidate');mesh.from_pydata([(x,-z,y) for x,y,z in vertices],[],faces);mesh.update();mesh.calc_loop_triangles()
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
    actual=BVHTree.FromPolygons([v.co for v in mesh.vertices],triangles,all_triangles=True)
    inner_pairs=actual.overlap(inner);outer_pairs=actual.overlap(outer);arc=[0.]
    for a,b in zip(points,points[1:]):arc.append(arc[-1]+math.dist(a,b))
    n=len(points);count=len(vertices)//2;contact_arc=0.;outside_seat_vertices=[]
    for face,_ in outer_pairs:
        for vertex in triangles[face]:
            i=vertex%count;i=i if i<n else i-n if i<2*n else n-1
            contact_arc=max(contact_arc,arc[i])
            if arc[i]>=.001:outside_seat_vertices.append(vertex)
    signed=[normal[0]*v.co.z-normal[1]*v.co.y-distance for v in mesh.vertices]
    ideal=[normal[0]*v[1]+normal[1]*v[2]-distance for v in vertices]
    vertex_error=max(abs(a-b) for a,b in zip(signed,ideal));max_plane_penetration=max(signed)
    contact_angles=[math.degrees(math.atan2(-mesh.vertices[i].co.y,mesh.vertices[i].co.z)) for i in outside_seat_vertices]
    supported_contact=bool(candidate['solution'].get('wedgeContacts')) and bool(contact_angles) and min(contact_angles)>-13 and max(contact_angles)<8
    within_storage_precision=max(ideal)<=1e-10 and max_plane_penetration<=vertex_error+saved_plane_error+1e-10
    allowed_wedge_contact=supported_contact and within_storage_precision
    entry.update({'innerRaceTrianglePairs':len(inner_pairs),'outerRaceTrianglePairs':len(outer_pairs),
      'maxIntersectingRootArcM':contact_arc,'outsideFittedSeat':contact_arc>=.001,
      'maxActualPlanePenetrationM':max_plane_penetration,'maxIdealPlanePenetrationM':max(ideal),
      'stripProjectionStorageErrorM':vertex_error,'savedPlaneDeviationM':saved_plane_error,
      'explicitWedgeContactWithinStoragePrecision':allowed_wedge_contact,
      'geometryValid':candidate['tipModelValid'] and not inner_pairs and (contact_arc<.001 or allowed_wedge_contact),
      'forceN':candidate['solution']['forceN'],'stressPa':candidate['solution']['maximumIncrementalBendingStressPa']})
    bpy.data.meshes.remove(mesh)
report={'rows':rows,'limits':'Actual saved pocket/inner-race surfaces against solved strip meshes. First 1 mm root-seat overlap remains an explicit fit. Active wedge touch may intersect only within measured float32 projection/plane storage error; not a claim of strictly zero BVH overlap. No factory seat or material acceptance.'}
(ROOT/f'outputs/converter-{suffix}-native.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'points':len(rows),'geometryValid':sum(r.get('geometryValid',False) for r in rows),
 'failures':[r for r in rows if not r.get('geometryValid',False)]},indent=2),flush=True)
