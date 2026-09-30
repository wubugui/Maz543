"""Actual authored cam gear meshes, spline interfaces and technical renders."""
import bpy,json,sys,math,re
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from d12_asset import engine_descendants
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'))
scene=bpy.context.scene;root=bpy.data.objects['D12A_525A'];scene.frame_set(1)
parts=[o for o in engine_descendants(root) if o.get('camTrain')]
for ob in parts:
    if not ob.get('camBank'):
        match=re.search(r'_([LR])(?:_|[1-6]|$)',ob.name)
        assert match,ob.name
        ob['camBank']=match.group(1)
exec(compile((ROOT/'scripts/d12-cam-finish.py').read_text(encoding='utf-8'),str(ROOT/'scripts/d12-cam-finish.py'),'exec'))
def tree(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
    t=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return t

if '--render-only' not in sys.argv:
    hits=[]
    # 121 frames of actual teeth cover a complete input revolution, with different
    # tooth registrations; independent planar sweep already sampled 1,441 positions.
    for f in range(1,242,2):
        scene.frame_set(f)
        for bank in ['L','R']:
            a=bpy.data.objects[f'D12_cam_22_spur_{bank}_intake'];b=bpy.data.objects[f'D12_cam_22_spur_{bank}_exhaust']
            overlap=tree(a).overlap(tree(b))
            if overlap:hits.append([f,bank,len(overlap)])
    assert not hits,hits[:5]
    scene.frame_set(1)
    for bank in ['L','R']:
        for kind in ['intake','exhaust']:
            gear=bpy.data.objects[f'D12_cam_22_spur_{bank}_{kind}'];sleeve=bpy.data.objects[f'D12_cam_41_10_sleeve_{bank}_{kind}'];shaft=bpy.data.objects[f'D12_cam_10_spline_{bank}_{kind}']
            assert gear['toothCount']==22 and sleeve['externalSplines']==41 and sleeve['internalSplines']==10
            assert not tree(gear).overlap(tree(sleeve)),f'gear/sleeve collision {bank}/{kind}'
            assert not tree(shaft).overlap(tree(sleeve)),f'shaft/sleeve collision {bank}/{kind}'
            assert bpy.data.objects[f'D12_cam_threaded_retainer_{bank}_{kind}']['threadHand']==('LEFT' if kind=='intake' else 'RIGHT')
        assert bpy.data.objects[f'D12_cam_24_bevel_{bank}']['toothCount']==24
    report={'camAuthoredObjects':len(parts),'meshFrames':121,'spurMeshIntersections':hits,'interfacesChecked':8,'gearCounts':[22,22,24],'sleeveSplines':[41,10],'source':'MAZ 1973 figures 7–9','limits':'Dimensions, 20 degree tooth form and 9 mm quartic lift are reconstructed. Upstream bevel mating train, lash and valve dynamics not accepted.'}
    (ROOT/'outputs/cam-native-verification.json').write_text(json.dumps(report,indent=2))
else:
    report=json.loads((ROOT/'outputs/cam-native-verification.json').read_text())
# Persist migration metadata before render-only visibility/camera changes.
source_text=bpy.data.texts.get('D12_REFERENCE_AND_SCOPE');source_text.clear();source_text.write((ROOT/'docs/D12_REFERENCE_REGISTER.md').read_text(encoding='utf-8'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'outputs/D12A525A_Engine_Master.blend'),compress=True)
for ob in engine_descendants(root):
    if ob.type in ['MESH','CURVE']:ob.hide_render=not(ob.get('camTrain') and ob.get('camBank')=='L')
floor=bpy.data.objects.get('D12_STUDIO_FLOOR')
if floor:floor.hide_render=True
def C(p):return Vector((p[0],-p[2],p[1]))
cam=scene.camera;cam.location=C((-.99,.91,-.10));cam.rotation_euler=(C((-.636,.658,-.336))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=52
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.view_settings.exposure=-1.3
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    scene.cycles.device='GPU'
except:pass
scene.render.filepath=str(ROOT/'outputs/d12-cam-gear-detail.png');bpy.ops.render.render(write_still=True)
cam.location=C((-1.55,1.25,.75));cam.rotation_euler=(C((-.04,.658,-.336))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(ROOT/'outputs/d12-cam-bank-detail.png');bpy.ops.render.render(write_still=True)
print('CAM_NATIVE_VERIFIED',report,flush=True)
