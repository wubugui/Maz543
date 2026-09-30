import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from suspension_asset import descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Starting_Master.blend'))
scene=bpy.context.scene;data=json.loads((ROOT/'work/starting-poses.json').read_text());checks=[]
def tree(o):
 deps=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles()
 verts=[e.matrix_world@v.co for v in m.vertices];faces=[tuple(p.vertices) for p in m.loop_triangles];out=BVHTree.FromPolygons(verts,faces,all_triangles=True,epsilon=0);e.to_mesh_clear();return out
for f in data['frames']:
 if not f.get('mesh') or f['frame']%3:continue
 scene.frame_set(f['frame']);deps=bpy.context.evaluated_depsgraph_get();deps.update()
 pin=bpy.data.objects['C5_11_tooth_pinion'];ring=bpy.data.objects['C5_flywheel_involute_ring'];overlap=tree(pin).overlap(tree(ring));p=pin.matrix_world.translation;q=ring.matrix_world.translation
 checks.append({'frame':f['frame'],'axialOffsetWhileSliding':abs(p.x-q.x),'centreDistance':(p-q).length,'surfaceIntersections':len(overlap)})
pumpChecks=[]
for f in data['frames'][::15]:
 scene.frame_set(f['frame']);bpy.context.view_layer.update()
 overlap=tree(bpy.data.objects['MZN_drive_gear_7']).overlap(tree(bpy.data.objects['MZN_driven_gear_6']))
 pumpChecks.append({'frame':f['frame'],'surfaceIntersections':len(overlap)})
scene.frame_set(0);bpy.context.view_layer.update()
rotor=tree(bpy.data.objects['MN1_rotor_envelope_UNMEASURED']);statorChecks=[]
for ob in bpy.data.objects:
 if ob.name.startswith(('MN1_curved_pole_shoe_','MN1_field_core_fit_','MN1_insulated_field_bundle_')):
  statorChecks.append({'node':ob.name,'rotorEnvelopeIntersections':len(rotor.overlap(tree(ob)))})
report={'samples':len(checks),'maxAxialOffsetWhileSliding':max(c['axialOffsetWhileSliding'] for c in checks),'maxSurfaceIntersections':max(c['surfaceIntersections'] for c in checks),'samplesDetail':checks,
 'pumpSamples':len(pumpChecks),'pumpMaxSurfaceIntersections':max(c['surfaceIntersections'] for c in pumpChecks),'pumpSamplesDetail':pumpChecks,'statorChecks':statorChecks}
(ROOT/'outputs/starting-native-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('NATIVE_GEAR_CHECK',json.dumps(report),flush=True)
assert report['maxSurfaceIntersections']==0,'Actual starter tooth surfaces intersect'
assert report['pumpMaxSurfaceIntersections']==0,'Actual pump tooth surfaces intersect'
assert all(c['rotorEnvelopeIntersections']==0 for c in statorChecks),'Stator intersects the fitted rotor envelope'
scene.frame_set(0)
def C(p):return Vector((p[0],-p[2],p[1]))
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type!='CPU'
 scene.cycles.device='GPU'
except:pass
scene.render.resolution_x=1400;scene.render.resolution_y=950;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-3
w=bpy.data.worlds.new('Starting neutral studio');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Strength'].default_value=.25;scene.world=w
for name,p,power,size in [('KEY',(.2,1,-1.1),80,1.2),('RIM',(.5,.7,.3),100,1),('FILL',(-.5,.25,-.2),35,.6)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=C(p);o.rotation_euler=(C((.4,.16,-.322))-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('STARTING_CAMERA',bpy.data.cameras.new('STARTING_CAMERA'));scene.collection.objects.link(cam);cam.location=C((.95,.57,-1.15));cam.rotation_euler=(C((.39,.16,-.322))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=65;scene.camera=cam
for o in [bpy.data.objects['MZN_PREOIL']]+descendants(bpy.data.objects['MZN_PREOIL']):o.hide_render=True
for o in [bpy.data.objects['C5_FLYWHEEL_RING']]+descendants(bpy.data.objects['C5_FLYWHEEL_RING']):o.hide_render=True
scene.render.filepath=str(ROOT/'outputs/c5-assembled.png');bpy.ops.render.render(write_still=True)
for o in descendants(bpy.data.objects['C5_STARTER']):
 if o.get('startingRole')=='cover':o.hide_render=True
scene.render.filepath=str(ROOT/'outputs/c5-drive-internals.png');bpy.ops.render.render(write_still=True)
for o in [bpy.data.objects['C5_STARTER']]+descendants(bpy.data.objects['C5_STARTER']):o.hide_render=True
for o in [bpy.data.objects['MZN_PREOIL']]+descendants(bpy.data.objects['MZN_PREOIL']):o.hide_render=o.get('startingRole') in ['cover','envelope']
target=C((-.10,0,0));cam.location=C((-.56,.28,-.30));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=58
for name,p in [('KEY',(-.3,.5,-.35)),('RIM',(.2,.2,.4)),('FILL',(-.35,.05,-.1))]:
 o=bpy.data.objects[name];o.location=C(p);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ROOT/'outputs/mn1-stator-detail.png');bpy.ops.render.render(write_still=True)
print('STARTING_NATIVE_AND_PREVIEWS_DONE',flush=True)

