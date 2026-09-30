"""Native pose parity, fitted bearing envelope and moving solid interference."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Cardan_Master.blend'))
scene=bpy.context.scene;root=bpy.data.objects['S543_CARDAN']
def C(p):return Vector((p[0],-p[2],p[1]))
def Q(q):return Quaternion((q[3],q[0],-q[2],q[1]))
def tree(objects):
    vs=[];fs=[]
    for o in objects:
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();offset=len(vs)
        vs.extend(ev.matrix_world@v.co for v in m.vertices);fs.extend(tuple(offset+i for i in f.vertices) for f in m.loop_triangles);ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs,fs,all_triangles=True)
data=json.loads((ROOT/'work/cardan-poses.json').read_text());max_position=0;max_angle=0
for f in data['frames'][::30]:
    scene.frame_set(f['frame'])
    for name,p in f['pose'].items():
        o=bpy.data.objects[name];max_position=max(max_position,(o.location-C(p['p'])).length)
        a=o.rotation_quaternion.normalized();b=Q(p['q']);max_angle=max(max_angle,2*math.acos(min(1,abs(a.dot(b)))))
assert max_position<1e-6 and max_angle<.001,(max_position,max_angle)
envelopes=[]
for end in range(2):
    for kind in ['flange','shaft']:
        caps=[bpy.data.objects[f'CJ_cap_{end}_{kind}_{s}'] for s in [-1,1]]
        pts=[v.co for o in caps for v in o.data.vertices]
        # Modeling Y is native Blender Z.
        span=max(v.z for v in pts)-min(v.z for v in pts);radius=max(math.hypot(v.x,v.y) for v in pts)
        assert abs(span-.073)<1e-7 and abs(radius-.014)<1e-7
        envelopes.append({'end':end,'kind':kind,'spanMM':span*1000,'cupDiameterMM':radius*2000})
for o in root.children_recursive:o.animation_data_clear()
hits=[];samples=json.loads((ROOT/'work/cardan-clearance-samples.json').read_text())
for k,sample in enumerate(samples):
    for name,p in sample['pose'].items():o=bpy.data.objects[name];o.location=C(p['p']);o.rotation_quaternion=Q(p['q'])
    bpy.context.view_layer.update()
    for end in range(2):
        f=tree([bpy.data.objects[f'CJ_flange_fork_{end}']]);s=tree([bpy.data.objects[f'CJ_sliding_fork_{end}']])
        c=tree([o for o in bpy.data.objects[f'CJ_cross_{end}'].children_recursive if o.type=='MESH'])
        for left,right,pair in [(f,s,'opposing forks'),(f,c,'flange fork / cross'),(s,c,'spline fork / cross')]:
            overlap=left.overlap(right)
            if overlap:hits.append({'sample':k,'bend':sample['bend'],'extension':sample['extension'],'angle':sample['angle'],'end':end,'pair':pair,'triangles':len(overlap)})
    overlap=tree([bpy.data.objects['CJ_male_spline']]).overlap(tree([bpy.data.objects['CJ_female_spline']]))
    if overlap:hits.append({'sample':k,'pair':'sliding splines','triangles':len(overlap)})
report={'samples':len(samples),'nativeJoints':190,'maxPositionError':max_position,'maxQuaternionAngleError':max_angle,'bearingEnvelopes':envelopes,'surfaceIntersections':hits,'limits':'Fitted independent inspection mechanism. This is not original-vehicle dimensional, load or installed clearance acceptance.'}
(ROOT/'outputs/cardan-native-verification.json').write_text(json.dumps(report,indent=2));print('CARDAN_NATIVE_QA',len(hits),'intersections',max_position,max_angle,flush=True)
if '--no-render' not in sys.argv:
    for name,p in data['frames'][0]['pose'].items():o=bpy.data.objects[name];o.location=C(p['p']);o.rotation_quaternion=Q(p['q'])
    world=bpy.data.worlds.new('Cardan inspection studio');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.09,.105,.12,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
    target=C((.12,0,.04))
    for name,p,power,size in [('Key',(-.25,.5,.5),45,.45),('Rim',(.5,.4,-.5),65,.4),('Fill',(-.4,.05,-.2),12,.3)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=target+C(p);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('Cardan inspection');cam=bpy.data.objects.new('Cardan inspection',d);scene.collection.objects.link(cam);scene.camera=cam;cam.location=target+C((-.28,.28,.57));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.lens=58
    scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.render.resolution_percentage=100
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type!='CPU'
        scene.cycles.device='GPU'
    except:pass
    for opened in [False,True]:
        for o in root.children_recursive:o.hide_render=opened and o.get('cardanRole') in ['yoke','cover','seal','clip']
        scene.render.filepath=str(ROOT/('outputs/maz543-cardan-internals.png' if opened else 'outputs/maz543-cardan-exterior.png'));bpy.ops.render.render(write_still=True)
assert not hits,hits[:12]
