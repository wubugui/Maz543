"""Check authored friction/magnetic clearances and spring envelope at five travels."""
import bpy,json,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'))
bpy.context.scene.frame_set(0)
def geometry(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    vertices=[ev.matrix_world@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles]
    ev.to_mesh_clear();return vertices,BVHTree.FromPolygons(vertices,faces,all_triangles=True)
rows=[]
for i in range(2):
    fan=bpy.data.objects[f'COOL_fan_{i}'];spring=bpy.data.objects[f'COOL_spring_{i}']
    fan.animation_data_clear();spring.animation_data_clear()
    arm=bpy.data.objects[f'COOL_armature_plate_{i}'];armx=max(p.x for p in geometry(arm)[0])
    for travel in [0,.000375,.00075,.001125,.0015]:
        fan.location.x=-travel;spring.location.x=-.0155;spring.scale.x=(.01-travel)/.01;bpy.context.view_layer.update()
        friction=geometry(bpy.data.objects[f'COOL_friction_ring_{i}'])[0]
        magnet=geometry(bpy.data.objects[f'COOL_magnet_{i}'])[0]
        gap=min(p.x for p in friction)-armx;air=min(p.x for p in magnet)-armx
        assert abs(gap-(.0015-travel))<2e-6,(i,travel,gap)
        assert abs(air-(.0021-travel))<2e-6,(i,travel,air)
        spring_mesh,ts=geometry(bpy.data.objects[f'COOL_release_spring_{i}']);hits=[]
        # The detailed upper gearbox replaced COOL_output_shaft with this
        # authored stepped shaft; check the actual installed replacement.
        obstacles=[f'COOL_upper_output_stepped_shaft_{i}',f'COOL_magnet_{i}']+[f'COOL_needle_outer_race_{i}_{k}' for k in range(2)]
        for name in obstacles:
            collisions=ts.overlap(geometry(bpy.data.objects[name])[1])
            if collisions:hits.append(dict(name=name,triangles=len(collisions)))
        assert not hits,(i,travel,hits)
        rows.append(dict(fan=i,travelMM=travel*1000,frictionGapMM=gap*1000,magneticGapMM=air*1000,checkedObstacles=obstacles,springObstacleIntersections=hits))
report=dict(samples=rows,limits='Evaluated native contact planes and spring surface interference only; fitted seats/spring, affine coil compression, no measured tolerances or complete clutch/cab collision acceptance.')
(ROOT/'outputs/clutch-native-contact-verification.json').write_text(json.dumps(report,indent=2))
print('CLUTCH_NATIVE_CONTACT',len(rows),'poses checked',flush=True)
