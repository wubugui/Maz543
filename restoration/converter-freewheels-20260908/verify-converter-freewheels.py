"""Read saved dual freewheel geometry; source topology and fitted contact only."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_Freewheels.blend'))
root=bpy.data.objects['S543_CONVERTER_FREEWHEELS'];S=json.loads(root['fit'])
ri=S['innerRadius'];r=S['rollerRadius'];rho=ri+r;alpha=S['wedgeAngle']
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(ob):
    mesh=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();mesh.calc_loop_triangles()
    result=BVHTree.FromPolygons([ob.matrix_world@v.co for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
    ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear();return result
assert len([o for o in bpy.data.objects if o.name=='CV_shared_fixed_inner_race'])==1
assert len([o for o in bpy.data.objects if '_wedged_outer_race' in o.name])==2
assert len([o for o in bpy.data.objects if '_roller_' in o.name])==24
assert len([o for o in bpy.data.objects if '_engagement_spring_' in o.name])==24
solids=0
for ob in bpy.data.objects:
    for animated in [ob,ob.data.shape_keys if ob.type=='MESH' else None]:
        if animated is None or not animated.animation_data or not animated.animation_data.action:continue
        assert all(key.interpolation=='CONSTANT' for curve in animated.animation_data.action.fcurves for key in curve.keyframe_points),'Endpoint poses must not imply valid continuous interpolation'
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    assert all(e.is_manifold for e in bm.edges) and bm.calc_volume()>0,(ob.name,bm.calc_volume(),sum(not e.is_manifold for e in bm.edges))
    bm.free();solids+=1
rows=[]
for frame in [0,60,120]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    for row,x in zip(['front','rear'],S['rowX']):
        race=tree(bpy.data.objects['CV_'+row+'_wedged_outer_race'])
        inner=tree(bpy.data.objects['CV_shared_fixed_inner_race'])
        for j in range(S['rollerCount']):
            ob=bpy.data.objects[f'CV_{row}_roller_{j}'];cell=ob.parent
            centre=ob.matrix_world.translation;beta=0 if frame!=60 else S['releaseAngle']
            expected=cell.matrix_world@C((x,rho*math.cos(beta),rho*math.sin(beta)))
            assert (centre-expected).length<1e-8,(ob.name,'centre',centre,expected)
            outward=cell.matrix_world.to_3x3()@C((0,math.cos(alpha),math.sin(alpha)))
            inward=cell.matrix_world.to_3x3()@C((0,-math.cos(beta),-math.sin(beta)))
            actualRoll=tree(ob)
            _,_,_,raceDistance=race.ray_cast(centre,outward,.025)
            _,_,_,rollerDistance=actualRoll.ray_cast(centre,outward,.025)
            _,_,_,innerDistance=inner.ray_cast(centre,inward,.025)
            assert None not in [raceDistance,rollerDistance,innerDistance]
            gap=raceDistance-rollerDistance
            expectedGap=rho*(math.cos(alpha)-math.cos(beta-alpha))
            assert abs(gap-expectedGap)<3e-6,(row,j,frame,gap,expectedGap)
            assert abs(innerDistance-r)<1e-5,(row,j,frame,innerDistance)
            if frame==60:assert gap>.0004,(row,j,gap)
            else:assert -1e-7<gap<3e-6,(row,j,gap)
            # The actual freewheel pocket must not cut through a roller.
            assert not actualRoll.overlap(race),(ob.name,frame,'wedge/roller surface crossing')
            spring=tree(bpy.data.objects[f'CV_{row}_engagement_spring_{j}'])
            assert not spring.overlap(race),(ob.name,frame,'spring crosses outer race')
            assert not spring.overlap(inner),(ob.name,frame,'spring crosses inner race')
            assert not spring.overlap(actualRoll),(ob.name,frame,'spring crosses roller')
            rows.append({'frame':frame,'row':row,'roller':j,'wedgeGapM':gap,'innerRayDistanceM':innerDistance})
report={'closedPositiveVolumeSolids':solids,'rollerStates':len(rows),'rows':rows,
        'limits':'Saved static endpoints only; approximate faceted contact to fitted 7-degree ramps. No roller friction, wedging load, spring force, blade flow or strength acceptance. Roller count remains fitted.'}
(ROOT/'outputs/converter-freewheel-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2),flush=True)
