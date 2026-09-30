"""Native upper bevel, bearing envelope, gear/case and brush contact checks."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();t=BVHTree.FromPolygons([ev.matrix_world@v.co for v in m.vertices],[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);ev.to_mesh_clear();return t
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cooling_Master.blend'));scene=bpy.context.scene;scene.frame_set(0)
data=json.loads((ROOT/'work/cooling-poses.json').read_text());spec=data['spec'];hits=[];bearings=[];brush_gaps=[]
for i in range(2):
    drive=bpy.data.objects[f'COOL_upper_drive_{i}']
    for o in drive.children_recursive:o.animation_data_clear()
    for b,s in enumerate(spec['upperBearings']):
        inner=bpy.data.objects[f'COOL_upper_bearing_inner_{b}_{i}'];outer=bpy.data.objects[f'COOL_upper_bearing_outer_{b}_{i}'];r=lambda o:[math.hypot(v.co.y,v.co.z) for v in o.data.vertices]
        actual=[2*min(r(inner)),2*max(r(outer)),max(v.co.x for v in outer.data.vertices)-min(v.co.x for v in outer.data.vertices)];expected=[s['bore']*2,s['outer']*2,s['width']]
        assert max(abs(a-e) for a,e in zip(actual,expected))<1e-7,(i,b,actual,expected);bearings.append([i,b,*[round(v*1000,5) for v in actual]])
    gears=[bpy.data.objects[f'COOL_upper_bevel_{s}_{i}'] for s in ['output','input']];case=tree(bpy.data.objects[f'COOL_upper_case_{i}'])
    for sample in range(49):
        a=sample*math.tau/48;bpy.data.objects[f'COOL_upper_output_{i}'].rotation_euler.x=a;bpy.data.objects[f'COOL_upper_input_{i}'].rotation_euler.x=-a*1.6;bpy.context.view_layer.update();ts=[tree(o) for o in gears]
        for x,y,label in [(ts[0],ts[1],'bevel pair'),(ts[0],case,'output gear / case'),(ts[1],case,'input gear / case')]:
            overlap=x.overlap(y)
            if overlap:hits.append([i,sample,label,len(overlap)])
    brush=bpy.data.objects[f'COOL_upper_end_brush_{i}'];shaft=bpy.data.objects[f'COOL_upper_output_stepped_shaft_{i}']
    gap=min((brush.matrix_world@v.co).x for v in brush.data.vertices)-max((shaft.matrix_world@v.co).x for v in shaft.data.vertices)
    assert abs(gap)<1e-6,'End brush must contact, not penetrate, the actual shaft tip';brush_gaps.append(gap*1000)
report={'samplesPerSide':49,'surfaceIntersections':hits,'nativeBearingEnvelopesMM':bearings,'endBrushGapMM':brush_gaps,'upperMeshes':len([o for o in bpy.data.objects if o.type=='MESH' and o.get('upperGearbox')]),'limits':'Original tooth counts, fits, load-bearing contact, Cardan closure and full vehicle clearances are not verified.'}
(ROOT/'outputs/cooling-upper-verification.json').write_text(json.dumps(report,indent=2));print('UPPER_NATIVE',json.dumps(report),flush=True)
if '--no-render' in sys.argv:
    assert not hits,hits[:8]
    sys.exit(0)
for o in bpy.data.objects:
    if o.type in ['MESH','CURVE']:o.hide_render=not(o.get('upperGearbox') and o.get('upperSide')==0) or o.get('coolingRole')=='support'
for s in ['output','input']:bpy.data.objects[f'COOL_upper_{s}_0'].rotation_euler.x=0
target=bpy.data.objects['COOL_upper_drive_0'].matrix_world.translation+C((0,-.018,0))
world=bpy.data.worlds.new('Upper drive inspection studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.15,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,p,power,size in [('Key',(-.8,1,1),75,.8),('Rim',(.5,.7,-.7),110,.65),('Fill',(-.7,-.2,-.6),30,.7)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=target+C(p);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Upper inspection');cam=bpy.data.objects.new('Upper inspection',d);scene.collection.objects.link(cam);scene.camera=cam;cam.location=target+C((-.7,.34,.67));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=58
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1400;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    scene.cycles.device='GPU'
except:pass
for opened in [False,True]:
    for o in bpy.data.objects:
        if o.type in ['MESH','CURVE'] and o.get('upperGearbox') and o.get('upperSide')==0:o.hide_render=o.get('coolingRole')=='support' or (opened and o.get('coolingRole') in ['housing','bearing-cover'])
    scene.render.filepath=str(ROOT/('outputs/maz543-cooling-upper-internals.png' if opened else 'outputs/maz543-cooling-upper-exterior.png'));bpy.ops.render.render(write_still=True)
assert not hits,hits[:8]
