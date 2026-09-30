"""Measure saved strip mesh, its contact gap and discrete bending energy."""
import bpy,bmesh,json,math,hashlib,sys,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_spring import StripSpring
D=json.loads((ROOT/'work/freewheel-contact/strip-spring-study.json').read_text());f=D['fit']
path=ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
strip=bpy.data.objects['CS_curved_strip'];roller=bpy.data.objects['CS_roller_12_5x22'];root=bpy.data.objects['S543_CURVED_STRIP_STUDY']
beam=StripSpring(D['restPoints'],f['widthM'],f['thicknessM'],f['youngPa']);n=len(D['restPoints']);count=len(strip.data.vertices)//2
rows=[];volumes=[];maxPositionError=0.;maxEnergyRelativeError=0.;minCylinderGap=1.;maxCylinderGap=-1.;maxLengthError=0.
baseSolids=0
for ob in bpy.data.objects:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data);assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,ob.name;bm.free();baseSolids+=1
def tree(ob):
    ob.data.calc_loop_triangles();return BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True)
outer=tree(bpy.data.objects['CS_outer_pocket']);inner=tree(bpy.data.objects['CS_fixed_inner_section']);maxSeatContactArc=0.;seatFrames=0
arc=np.r_[0,np.cumsum(beam.lengths)]
for frame,row in enumerate(D['rows']):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();e=strip.evaluated_get(deps);mesh=e.to_mesh();mesh.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(mesh);assert all(edge.is_manifold for edge in bm.edges) and bm.calc_volume()>0;volumes.append(bm.calc_volume());bm.free()
    points=[v.co.copy() for v in mesh.vertices];centre=roller.location
    world=[strip.matrix_world@p for p in points];minimum=float('inf')
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles];actual=BVHTree.FromPolygons(world,triangles,all_triangles=True)
    assert not actual.overlap(inner),(frame,'strip intersects fixed inner race')
    overlaps=actual.overlap(outer)
    if overlaps:
        seatFrames+=1
        indices=[]
        for face,_ in overlaps:
            for vertex in triangles[face]:
                i=vertex%count;indices.append(i if i<n else i-n if i<2*n else n-1)
        maxSeatContactArc=max(maxSeatContactArc,float(max(arc[i] for i in indices)))
        assert max(arc[i] for i in indices)<.001,(frame,'contact outside the explicitly fitted root seat',max(arc[i] for i in indices))
    for tri in mesh.loop_triangles:
        ids=tuple(tri.vertices)
        for ia,ib in zip(ids,ids[1:]+ids[:1]):
            a=world[ia]-centre;b=world[ib]-centre;dy,dz=b.y-a.y,b.z-a.z;t=max(0,min(1,-(a.y*dy+a.z*dz)/max(1e-30,dy*dy+dz*dz)))
            minimum=min(minimum,math.hypot(a.y+t*dy,a.z+t*dz)-f['rollerRadiusM'])
    assert minimum>-5e-8 and minimum<3e-7,(frame,'actual strip/roller gap',minimum)
    minCylinderGap=min(minCylinderGap,minimum);maxCylinderGap=max(maxCylinderGap,minimum)
    # Neutral line from opposite actual strip skins. Keep coordinates local
    # during differentiation to avoid world-translation float cancellation.
    neutral=np.array([[(points[i].z+points[n+i].z)/2,-(points[i].y+points[n+i].y)/2] for i in range(n)])
    target=np.array(row['points'])-D['restPoints'][0];maxPositionError=max(maxPositionError,float(np.max(np.abs(neutral-target))))
    segments=np.diff(neutral,axis=0);length=np.linalg.norm(segments,axis=1);maxLengthError=max(maxLengthError,float(np.max(np.abs(length-beam.lengths))))
    angles=np.unwrap(np.arctan2(segments[:,1],segments[:,0]));angles+=round((beam.rest_angles[0]-angles[0])/(2*math.pi))*2*math.pi
    changes=beam.D@(angles-beam.rest_angles);energy=.5*np.sum(beam.k*changes*changes);error=abs(energy-row['energyJ'])/row['energyJ'];maxEnergyRelativeError=max(maxEnergyRelativeError,float(error))
    assert error<.001,(frame,'saved geometric bending energy',error)
    assert root['spring_force_N']==float(np.float32(row['forceN'])),(frame,root['spring_force_N'],row['forceN'],'float32 F-curve readback')
    rows.append({'frame':frame,'actualStripRollerGapM':minimum,'bendingEnergyFromMeshJ':float(energy),'forceN':row['forceN']});e.to_mesh_clear()
report={'baseClosedSolids':baseSolids,'savedEquilibria':len(rows),'closedStripMeshes':len(rows),'stripVertices':len(strip.data.vertices),'maxNeutralCoordinateErrorM':maxPositionError,'maxSegmentLengthErrorM':maxLengthError,'maxGeometricEnergyRelativeError':maxEnergyRelativeError,'stripCylinderGapRangeM':[minCylinderGap,maxCylinderGap],'volumeRangeM3':[min(volumes),max(volumes)],'rootSeatIntersectionFrames':seatFrames,'maxIntersectingRootArcM':maxSeatContactArc,'blendBytes':path.stat().st_size,'blendSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows,'limits':'Actual strip/roller/inner-race meshes checked. Outer-race intersection is confined to the first 1 mm of the explicitly fitted clamped root seat; the seat geometry is not factory accepted. Full assembly, strength and factory spring identification remain unaccepted.'}
(ROOT/'outputs/converter-strip-native-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
