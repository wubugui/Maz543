"""Inspect the actual authored wet cavity, animated rotor and bearing assembly."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
scene=bpy.context.scene;root=bpy.data.objects['D12A_525A'];scene.frame_set(1)
items=[o for o in engine_descendants(root) if o.get('waterPump')]
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
    obj=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=obj.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([obj.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);obj.to_mesh_clear();return t
blades=[o for o in items if o.name.startswith('D12_water_impeller_blade_')]
balls=[o for o in items if o.name.startswith('D12_water_rolling_element_')]
assert len(blades)==6 and len(balls)==18,(len(blades),len(balls))
assert {o.get('figureItem') for o in items}>={str(i) for i in range(1,18)}
housing=[o for o in items if o.name.startswith(('D12_water_housing_','D12_water_suction_bell_'))]
hits=[];axis_error=0
if '--render-only' not in sys.argv:
 for i in range(37):
    f=1+i*240/36;scene.frame_set(math.floor(f),subframe=f%1)
    static=[(o,tree(o)) for o in housing]
    for o in blades+[bpy.data.objects['D12_water_impeller_backplate']]:
        t=tree(o)
        for h,ht in static:
            overlap=t.overlap(ht)
            if overlap:hits.append([i,o.name,h.name,len(overlap)])
    axis=(bpy.data.objects['D12_water_rotor'].matrix_world.to_3x3()@Vector((1,0,0))).normalized()
    axis_error=max(axis_error,(axis-C((0,-1,0))).length)
 report={'source':'MAZ1973 fig28; dimensions and bearing ball count fitted','pumpObjects':len(items),'blades':len(blades),'bearings':2,'balls':len(balls),'samples':37,'rotorHousingIntersections':hits,'maxAxisError':axis_error,'limits':'Kinematic no-slip bearing model. Not calibrated loads, clearances, pump curve, seal wear or complete circuit acceptance.'}
 (ROOT/'outputs/water-native-verification.json').write_text(json.dumps(report,indent=2))
 print('WATER_NATIVE_GEOMETRY',report,flush=True)
 assert not hits,hits[:20]
 assert axis_error<2e-6
if '--no-render' in sys.argv:sys.exit(0)
scene.frame_set(16)
for ob in engine_descendants(root):
    if ob.type in ['MESH','CURVE']:ob.hide_render=not ob.get('waterPump') or ob.get('waterHalf')==1 or ob.get('d12Role')=='water-pipe'
floor=bpy.data.objects.get('D12_STUDIO_FLOOR')
if floor:floor.hide_render=True
cam=scene.camera;center=C((-.665,-.335,0));cam.location=center+C((-.27,.16,.39));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=53
scene.render.resolution_x=1600;scene.render.resolution_y=1800;scene.render.resolution_percentage=100;scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.view_settings.exposure=-1.3
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.filepath=str(ROOT/'outputs/d12-water-pump-section.png');bpy.ops.render.render(write_still=True)
print('WATER_NATIVE_RENDERED',flush=True)
