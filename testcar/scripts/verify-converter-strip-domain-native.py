"""Audit candidate beam solutions against the current saved pocket solids."""
import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
suffix='strip-surface-verified-domain' if '--surface' in sys.argv else 'strip-deep-domain' if '--deep' in sys.argv else 'strip-pocket-domain' if '--pocket' in sys.argv else 'strip-domain'
data=json.loads((ROOT/f'work/freewheel-contact/{suffix}.json').read_text());fit=data['fit']
saved='--saved' in sys.argv
assert not saved or '--surface' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('outputs/MAZ543A_Converter_StripSurfaceStudy.blend' if saved else 'outputs/MAZ543A_Converter_CurvedStripStudy.blend')))
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
for index,candidate in enumerate(data['rows']):
    entry={k:v for k,v in candidate.items() if k!='solution'};rows.append(entry)
    if 'solution' not in candidate:continue
    points=candidate['solution']['points'];vertices,faces=geometry(points,fit['widthM'],fit['thicknessM'])
    if saved:
        bpy.context.scene.frame_set(index);bpy.context.view_layer.update()
        ob=bpy.data.objects['CS_curved_strip'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(ob);mesh.transform(ob.matrix_world)
    else:
        mesh=bpy.data.meshes.new('domain_candidate');mesh.from_pydata([(x,-z,y) for x,y,z in vertices],[],faces)
    mesh.update();mesh.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));closed=all(e.is_manifold for e in bm.edges);volume=bm.calc_volume();bm.to_mesh(mesh);bm.free();mesh.calc_loop_triangles()
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
    # Every actual triangle edge is checked against the analytic roller cylinder.
    # Compare with the same ideal vertices to quantify float32 storage effects.
    centre=candidate['centreM'];roller_radius=fit['rollerRadiusM'];actual_gap=1.;ideal_gap=1.
    actual_points=[(v.co.z,-v.co.y) for v in mesh.vertices];ideal_points=[(v[1],v[2]) for v in vertices]
    roller_storage_error=max(math.dist(a,b) for a,b in zip(actual_points,ideal_points))
    def edge_gap(a,b):
        dy,dz=b[0]-a[0],b[1]-a[1];ay,az=a[0]-centre[0],a[1]-centre[1]
        t=max(0,min(1,-(ay*dy+az*dz)/max(1e-30,dy*dy+dz*dz)))
        return math.hypot(ay+t*dy,az+t*dz)-roller_radius
    for ids in triangles:
        for a,b in zip(ids,ids[1:]+ids[:1]):
            actual_gap=min(actual_gap,edge_gap(actual_points[a],actual_points[b]));ideal_gap=min(ideal_gap,edge_gap(ideal_points[a],ideal_points[b]))
    outline=list(range(n))+list(range(2*n,count-1))+list(range(2*n-1,n-1,-1));profile=[actual_points[i] for i in outline]
    def orient(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    crossings=0
    for i,(a,b) in enumerate(zip(profile,profile[1:]+profile[:1])):
        for j in range(i+2,len(profile)):
            if i==0 and j==len(profile)-1:continue
            c=profile[j];d=profile[(j+1)%len(profile)]
            if max(a[0],b[0])<min(c[0],d[0]) or max(c[0],d[0])<min(a[0],b[0]) or max(a[1],b[1])<min(c[1],d[1]) or max(c[1],d[1])<min(a[1],b[1]):continue
            if orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0:crossings+=1
    roller_valid=ideal_gap>=-1e-10 and actual_gap>=-roller_storage_error-1e-10
    entry.update({'innerRaceTrianglePairs':len(inner_pairs),'outerRaceTrianglePairs':len(outer_pairs),
      'maxIntersectingRootArcM':contact_arc,'outsideFittedSeat':contact_arc>=.001,
      'maxActualPlanePenetrationM':max_plane_penetration,'maxIdealPlanePenetrationM':max(ideal),
      'stripProjectionStorageErrorM':vertex_error,'savedPlaneDeviationM':saved_plane_error,
      'explicitWedgeContactWithinStoragePrecision':allowed_wedge_contact,
      'closedStripMesh':closed,'positiveVolumeM3':volume,'profileSelfCrossings':crossings,
      'actualStripRollerGapM':actual_gap,'idealStripRollerGapM':ideal_gap,'rollerVertexStorageErrorM':roller_storage_error,
      'geometryValid':candidate['tipModelValid'] and not inner_pairs and (contact_arc<.001 or allowed_wedge_contact) and closed and volume>0 and crossings==0 and roller_valid,
      'forceN':candidate['solution']['forceN'],'stressPa':candidate['solution']['maximumIncrementalBendingStressPa']})
    bpy.data.meshes.remove(mesh)
report={'rows':rows,'limits':'Actual saved pocket/inner-race surfaces against solved strip meshes. First 1 mm root-seat overlap remains an explicit fit. Active wedge touch may intersect only within measured float32 projection/plane storage error; not a claim of strictly zero BVH overlap. No factory seat or material acceptance.'}
report['stripGeometrySource']='reopened saved shape keys' if saved else 'temporary mesh reconstructed from solver'
saved_suffix='-saved' if saved else ''
(ROOT/f'outputs/converter-{suffix}{saved_suffix}-native.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'points':len(rows),'geometryValid':sum(r.get('geometryValid',False) for r in rows),
 'failures':[r for r in rows if not r.get('geometryValid',False)]},indent=2),flush=True)
assert all(r.get('geometryValid',False) for r in rows) if saved else True
