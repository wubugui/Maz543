"""Check actual Blender geometry and evaluated animation, then render an inspection."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
from cooling_spring_geometry import weights
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'));scene=bpy.context.scene
data=json.loads((ROOT/'work/cooling-poses.json').read_text())['frames'];root=bpy.data.objects['S543_COOLING']
blades=[o for o in root.children_recursive if o.get('coolingRole')=='fan-blade'];assert len(blades)==24
needles=[o for o in root.children_recursive if o.name.startswith('COOL_needle_') and o.type=='MESH' and 'race' not in o.name];assert len(needles)==96
max_position=0;max_angle=0;max_scale=0
spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec'];max_morph=0
for f in data[::30]:
    scene.frame_set(f['frame'])
    for n,p in f['pose'].items():
        ob=bpy.data.objects[n];max_position=max(max_position,(ob.location-C(p['p'])).length)
        max_angle=max(max_angle,abs(ob.rotation_euler.x-p['rx']),abs(ob.rotation_euler.z-p.get('ry',0)))
        max_scale=max(max_scale,abs(ob.scale.x-p.get('sx',1)))
    for side in range(2):
        keys=bpy.data.objects[f'COOL_release_spring_{side}'].data.shape_keys.key_blocks
        target=weights(spec,f['pose'][f'COOL_spring_{side}']['springTravel'])
        max_morph=max(max_morph,*(abs(keys[name].value-value) for name,value in zip(('Pitch','Radius'),target)))
assert max_morph<2e-6,max_morph
assert max_position<2e-6 and max_angle<.0002 and max_scale<2e-6,(max_position,max_angle,max_scale)
hits=[]
for sample in range(25):
    scene.frame_set(100+sample*7)
    for i in range(2):
        shroud=bpy.data.objects[f'COOL_shroud_{i}'];ts=tree(shroud)
        for o in blades:
            if o.parent.name==f'COOL_fan_{i}':
                hit=tree(o).overlap(ts)
                if hit:hits.append([sample,o.name,len(hit)])
assert not hits,hits[:10]
scene.frame_set(0)
for o in root.children_recursive:
    if o.name.startswith('COOL_water_tube_'):
        pts=[o.matrix_world@v.co for v in o.data.vertices]
        assert min(v.x for v in pts)>-5.34 and max(v.x for v in pts)<-5.19,o.name
report={'blades':len(blades),'needleRollers':len(needles),'poseBindings':len(data[0]['pose']),'nativeFramesCompared':len(data[::30]),'maxPositionError':max_position,'maxAngleError':max_angle,'maxScaleError':max_scale,'maxSpringMorphWeightError':max_morph,'fanShroudSamples':25,'fanShroudIntersections':hits,'limitations':'No verification of full vehicle installation clearance, fan aerodynamics, gear train or complete water passages.'}
(ROOT/'outputs/cooling-native-verification.json').write_text(json.dumps(report,indent=2));print('COOLING_NATIVE',report,flush=True)
if '--no-render' in sys.argv:sys.exit(0)
scene.frame_set(240)
world=bpy.data.worlds.new('Cooling studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.28,1);world.node_tree.nodes['Background'].inputs[1].default_value=.35
def area(name,p,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=C(p);o.rotation_euler=(C((-5,1.55,0))-o.location).to_track_quat('-Z','Y').to_euler()
area('Cooling key',(-2.8,4,2.5),650,3);area('Cooling rim',(-6.3,3,-2),850,2);area('Cooling fill',(-2.4,1,-2),350,2)
d=bpy.data.cameras.new('Cooling inspection camera');cam=bpy.data.objects.new('Cooling inspection camera',d);scene.collection.objects.link(cam);scene.camera=cam
target=C((-4.95,1.64,0));cam.location=target+C((2.5,1,2.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=53
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.filepath=str(ROOT/'outputs/maz543-cooling-inspection.png');bpy.ops.render.render(write_still=True)
