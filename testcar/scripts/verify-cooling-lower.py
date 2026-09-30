"""Inspect real native lower-drive geometry, not a duplicate drawing proxy."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'));scene=bpy.context.scene;scene.frame_set(0)
assembly=bpy.data.objects['COOL_lower_drive'];spec=json.loads((ROOT/'work/cooling-poses.json').read_text())['spec']
for o in assembly.children_recursive:o.animation_data_clear()
gears=[bpy.data.objects['COOL_lower_bevel_'+s] for s in ['input','output_0','output_1']]
bearing_checks=[];rolling_error=0
for b,s in enumerate(spec['lowerBearings']):
    inner=bpy.data.objects[f'COOL_lower_bearing_inner_{b}'];outer=bpy.data.objects[f'COOL_lower_bearing_outer_{b}']
    rad=lambda o:[math.hypot(v.co.y,v.co.z) for v in o.data.vertices]
    actual=[2*min(rad(inner)),2*max(rad(outer)),max(v.co.x for v in outer.data.vertices)-min(v.co.x for v in outer.data.vertices)]
    expected=[2*s['bore'],2*s['outer'],s['width']]
    assert max(abs(a-e) for a,e in zip(actual,expected))<1e-7,(b,actual,expected)
    bearing_checks.append({'index':b,'nominalMM':[round(v*1000,5) for v in actual]})
    R=s['pitch'];r=s['ball'];w=173;wc=w*(1-r/R)/2;wr=wc-w*(R*R-r*r)/(2*R*r)
    rolling_error=max(rolling_error,abs(R*wc-r*wr-(R-r)*w),abs(R*wc+r*wr))
assert rolling_error<1e-12
case=tree(bpy.data.objects['COOL_lower_cast_case']);pumpbody=tree(bpy.data.objects['COOL_lower_oil_pump_body'])
hits=[]
for sample in range(49):
    a=sample*math.tau/48
    bpy.data.objects['COOL_lower_input'].rotation_euler.x=-a
    for i in range(2):bpy.data.objects[f'COOL_lower_output_{i}'].rotation_euler.x=a*32/20
    bpy.data.objects['COOL_lower_pump_drive'].rotation_euler.x=a
    bpy.data.objects['COOL_lower_pump_driven'].rotation_euler.x=math.pi-math.pi/12-a
    bpy.context.view_layer.update();ts=[tree(o) for o in gears]
    for i,j in [(0,1),(0,2),(1,2)]:
        overlap=ts[i].overlap(ts[j])
        if overlap:hits.append({'sample':sample,'a':gears[i].name,'b':gears[j].name,'triangles':len(overlap)})
    for i,t in enumerate(ts):
        overlap=t.overlap(case)
        if overlap:hits.append({'sample':sample,'a':gears[i].name,'b':'casting','triangles':len(overlap)})
    pumps=[tree(bpy.data.objects['COOL_lower_oil_gear_'+s]) for s in ['drive','driven']]
    overlap=pumps[0].overlap(pumps[1])
    if overlap:hits.append({'sample':sample,'a':'pump drive','b':'pump driven','triangles':len(overlap)})
    for i,t in enumerate(pumps):
        overlap=t.overlap(pumpbody)
        if overlap:hits.append({'sample':sample,'a':'pump gear '+str(i),'b':'pump housing','triangles':len(overlap)})
report={'samples':49,'meshSurfaceIntersections':hits,'lowerAuthoredMeshes':len([o for o in assembly.children_recursive if o.type=='MESH']),'bearingNativeEnvelopes':bearing_checks,'idealBearingRollingError':rolling_error,'limits':'Sampled surface intersection check only; original tooth counts and dimensions, loaded contact, lubrication and full installation are not validated.'}
(ROOT/'outputs/cooling-lower-verification.json').write_text(json.dumps(report,indent=2));print('LOWER_GEOMETRY',json.dumps(report),flush=True)
if '--no-render' in sys.argv:
    assert not hits,hits[:8]
    sys.exit(0)
for o in bpy.data.objects:
    if o.type in ['MESH','CURVE']:o.hide_render=not o.get('lowerDrive',False)
for n in ['COOL_lower_input','COOL_lower_output_0','COOL_lower_output_1','COOL_lower_pump_drive']:bpy.data.objects[n].rotation_euler.x=0
bpy.data.objects['COOL_lower_pump_driven'].rotation_euler.x=math.pi-math.pi/12
world=bpy.data.worlds.new('Lower drive studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.15,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
target=C(spec['lowerOrigin'])+C((-.055,-.01,0))
for name,p,power,size in [('Key',(-.8,1,1),75,.8),('Rim',(.5,.7,-.7),110,.65),('Fill',(-.7,-.2,-.6),30,.7)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=target+C(p);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Lower inspection');cam=bpy.data.objects.new('Lower inspection',d);scene.collection.objects.link(cam);scene.camera=cam
cam.location=target+C((-.76,.39,.69));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=56
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except:pass
for opened in [False,True]:
    for o in assembly.children_recursive:
        if o.type in ['MESH','CURVE']:o.hide_render=opened and o.get('coolingRole') in ['housing','bearing-cover']
    scene.render.filepath=str(ROOT/('outputs/maz543-cooling-lower-internals.png' if opened else 'outputs/maz543-cooling-lower-exterior.png'));bpy.ops.render.render(write_still=True)
assert not hits,hits[:8]
