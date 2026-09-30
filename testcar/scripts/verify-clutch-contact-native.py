"""Check authored friction/magnetic clearances and spring envelope at five travels."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from cooling_spring_geometry import apply_travel,STEPS,SIDES
spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
bpy.context.scene.frame_set(0)
def geometry(o,centred=False):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    transform=ev.matrix_world.to_3x3() if centred else ev.matrix_world
    vertices=[transform@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles]
    ev.to_mesh_clear();return vertices,BVHTree.FromPolygons(vertices,faces,all_triangles=True)
rows=[]
for i in range(2):
    fan=bpy.data.objects[f'COOL_fan_{i}'];spring=bpy.data.objects[f'COOL_spring_{i}']
    fan.animation_data_clear();spring.animation_data_clear()
    coil=bpy.data.objects[f'COOL_release_spring_{i}'];assert coil.get('parametricSpring')
    coil.data.shape_keys.animation_data_clear()
    arm=bpy.data.objects[f'COOL_armature_plate_{i}'];armx=max(p.x for p in geometry(arm)[0])
    for travel in [0,.000375,.00075,.001125,.0015]:
        fan.location.x=-travel;spring.location.x=-.0155;spring.scale=(1,1,1)
        apply_travel(coil,spec,travel);bpy.context.view_layer.update()
        friction=geometry(bpy.data.objects[f'COOL_friction_ring_{i}'])[0]
        magnet=geometry(bpy.data.objects[f'COOL_magnet_{i}'])[0]
        gap=min(p.x for p in friction)-armx;air=min(p.x for p in magnet)-armx
        assert abs(gap-(.0015-travel))<2e-6,(i,travel,gap)
        assert abs(air-(.0021-travel))<2e-6,(i,travel,air)
        spring_mesh,ts=geometry(bpy.data.objects[f'COOL_release_spring_{i}']);hits=[]
        # Measure all opposite diameters in the evaluated, actually deformed
        # mesh. An affine 0.85 X scale would fail this by about 0.21 mm.
        # Remove common world translation before subtracting diameters: at X=-5m
        # Blender float32 world coordinates lose sub-micron wire precision.
        wire_vertices=geometry(coil,centred=True)[0]
        diameters=[(wire_vertices[row*SIDES+j]-wire_vertices[row*SIDES+j+SIDES//2]).length
                   for row in range(STEPS+1) for j in range(SIDES//2)]
        diameter_error=max(abs(d-2*spec['releaseSpringWire']) for d in diameters)
        assert diameter_error<2e-7,(i,travel,diameter_error)
        centres=[sum(wire_vertices[row*SIDES:(row+1)*SIDES],Vector())/SIDES for row in range(STEPS+1)]
        axis=(coil.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
        average=sum(centres[:-1],Vector())/STEPS
        radius=sum(((c-average)-axis*(c-average).dot(axis)).length for c in centres)/len(centres)
        length=(centres[-1]-centres[0]).length
        arc=math.hypot(length,radius*math.tau*spec['releaseSpringTurns'])
        original_arc=math.hypot(spec['releaseSpringLength'],spec['releaseSpringRadius']*math.tau*spec['releaseSpringTurns'])
        assert abs(length-(spec['releaseSpringLength']-travel))<2e-7,(i,travel,length)
        assert abs(arc-original_arc)<2e-7,(i,travel,arc-original_arc)
        # The detailed upper gearbox replaced COOL_output_shaft with this
        # authored stepped shaft; check the actual installed replacement.
        obstacles=[f'COOL_upper_output_stepped_shaft_{i}',f'COOL_magnet_{i}']+[f'COOL_needle_outer_race_{i}_{k}' for k in range(2)]
        for name in obstacles:
            collisions=ts.overlap(geometry(bpy.data.objects[name])[1])
            if collisions:hits.append(dict(name=name,triangles=len(collisions)))
        assert not hits,(i,travel,hits)
        rows.append(dict(fan=i,travelMM=travel*1000,frictionGapMM=gap*1000,magneticGapMM=air*1000,wireDiameterMM=[min(diameters)*1000,max(diameters)*1000],maxWireDiameterErrorMM=diameter_error*1000,centrelineArcLengthMM=arc*1000,arcLengthErrorMM=(arc-original_arc)*1000,checkedObstacles=obstacles,springObstacleIntersections=hits))
report=dict(samples=rows,limits='Evaluated native contact planes, circular wire diameters and selected spring surface interference only; fitted analytic helix/seat dimensions, no elastic stress solve, measured tolerances or complete clutch/cab collision acceptance.')
(ROOT/'outputs/clutch-native-contact-verification.json').write_text(json.dumps(report,indent=2))
print('CLUTCH_NATIVE_CONTACT',len(rows),'poses checked',flush=True)
