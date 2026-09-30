"""Check actual Blender gear surfaces and fixed-axis mounting, then render."""
import bpy,json,sys,math,itertools
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
scene=bpy.context.scene;root=bpy.data.objects['D12A_525A'];scene.frame_set(1)
poses=json.loads((ROOT/'work/d12-poses.json').read_text());timing=poses['timing']
gears={o['timingGearId']:o for o in engine_descendants(root) if o.get('timingGearId')}
assert set(gears)==set(timing['gears']),(set(timing['gears'])-set(gears))
def C(p):return Vector((p[0],-p[2],p[1]))
def tree(o):
    m=o.data;m.calc_loop_triangles()
    return BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
hits=[];axis_error=0
if '--render-only' not in sys.argv:
 for i in range(73):
    frame=1+i*240/72;scene.frame_set(math.floor(frame),subframe=frame%1)
    trees={id:tree(o) for id,o in gears.items()}
    for edge in timing['edges']:
        overlaps=trees[edge['a']].overlap(trees[edge['b']])
        if overlaps:hits.append({'frame':scene.frame_current,'a':edge['a'],'b':edge['b'],'faces':len(overlaps)})
    for sh in timing['shafts'].values():
        ob=bpy.data.objects[sh['node']]
        axis=(root.matrix_world.inverted().to_3x3()@ob.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
        axis_error=max(axis_error,(axis-C(sh['axis'])).length)
 assert not hits,hits[:15]
 assert axis_error<2e-6,axis_error
 scene.frame_set(1)
 unrelated=[];edges={frozenset((e['a'],e['b'])) for e in timing['edges']}
 trees={id:tree(o) for id,o in gears.items()}
 for a,b in itertools.combinations(gears,2):
    if frozenset((a,b)) in edges or timing['gears'][a]['shaft']==timing['gears'][b]['shaft']:continue
    overlap=trees[a].overlap(trees[b])
    if overlap:unrelated.append([a,b,len(overlap)])
 assert not unrelated,unrelated
 report={'gearMeshes':len(gears),'gearPairs':len(timing['edges']),'samplesPerPair':73,'surfaceIntersections':hits,
         'unrelatedGearIntersectionsAtDatum':unrelated,'maxAxisError':axis_error,
         'newAnimatedShafts':sum(not s['existing'] for s in timing['shafts'].values()),
         'rates':{n:s['rate'] for n,s in timing['shafts'].items()},
         'limits':'Rigid ideal kinematic ratios only. Fitted dimensions and spherical tooth form; not original cutter data. Housing, load, backlash, lubrication and accessory internals not accepted.'}
 (ROOT/'outputs/timing-native-verification.json').write_text(json.dumps(report,indent=2))
 print('TIMING_NATIVE_VERIFIED',report,flush=True)
else:report=json.loads((ROOT/'outputs/timing-native-verification.json').read_text())
if '--no-render' in sys.argv:sys.exit(0)
for ob in engine_descendants(root):
    if ob.type in ['MESH','CURVE']:ob.hide_render=not(ob.get('timingTrain') or ob.get('camTrain'))
floor=bpy.data.objects.get('D12_STUDIO_FLOOR')
if floor:floor.hide_render=True
cam=scene.camera;cam.location=C((-2.3,1.3,1.2));cam.rotation_euler=(C((-.38,.32,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=55
scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.render.resolution_percentage=100;scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.view_settings.exposure=-1.3
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.filepath=str(ROOT/'outputs/d12-timing-train.png');bpy.ops.render.render(write_still=True)
cam.location=C((-1.04,.16,.30));cam.rotation_euler=(C((-.625,.10,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=52
scene.render.filepath=str(ROOT/'outputs/d12-timing-crank-detail.png');bpy.ops.render.render(write_still=True)
print('TIMING_RENDERS_WRITTEN',flush=True)
