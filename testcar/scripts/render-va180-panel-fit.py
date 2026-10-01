"""Actual whole-cab native renders; no scene geometry hidden for inspection."""
import argparse
import bpy
import hashlib
import json
import sys
import itertools
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/cloud-va180-panel-fit-20261001'
parser = argparse.ArgumentParser()
parser.add_argument('--view',required=True,choices=['before-detail','after-detail','after-cab','after-whole'])
parser.add_argument('--directory', default='outputs/cloud-va180-panel-fit-20261001')
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=(ROOT/args.directory).resolve()
assert OUT.is_relative_to(ROOT/'outputs') and OUT.name.startswith('cloud-')
build = json.loads((OUT/'build.json').read_text())
audit = json.loads((OUT/'readback.json').read_text())
assert not audit['identity_failures']
source = (ROOT/'outputs/cloud-steering-photo-hypothesis-20261001/MAZ543A_Master.blend'
          if args.view == 'before-detail' else OUT/build.get('candidate_file','MAZ543A_Master.blend'))
assert args.view!='before-detail' or args.directory=='outputs/cloud-va180-panel-fit-20261001'
expected = build['base_sha256'] if args.view == 'before-detail' else build['candidate_sha256']
sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source) == expected
path = OUT/(args.view+'.png'); assert not path.exists()
bpy.ops.wm.open_mainfile(filepath=str(source)); scene=bpy.context.scene; scene.frame_set(0); bpy.context.view_layer.update()
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.render.threads_mode='FIXED'; scene.render.threads=2
scene.cycles.samples=32; scene.cycles.use_denoising=False; scene.render.use_motion_blur=False
scene.cycles.max_bounces=4; scene.cycles.glossy_bounces=2; scene.cycles.transmission_bounces=4; scene.cycles.transparent_max_bounces=4
scene.render.resolution_x=1000; scene.render.resolution_y=800; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('VA180 cab review environment'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.38,.42,1); world.node_tree.nodes['Background'].inputs[1].default_value=.8; scene.world=world
data=bpy.data.cameras.new('VA180 actual cab camera'); camera=bpy.data.objects.new(data.name,data); scene.collection.objects.link(camera); scene.camera=camera
root_matrix=Matrix(build['new_root_world'])
target=root_matrix@Vector((0,0,0))
normal=(root_matrix.to_3x3()@Vector((0,0,1))).normalized()
up=(root_matrix.to_3x3()@Vector((0,1,0))).normalized()
whole_bounds=None
if args.view=='after-whole':
    # Original vehicle outer envelope is unchanged by this internal candidate.
    minimum=(-5.749101161956787,-1.8629999160766602,-.003979163244366646)
    maximum=(5.519999980926514,1.8629999160766602,2.994999885559082)
    target=Vector(tuple((a+b)/2 for a,b in zip(minimum,maximum)))
    camera.location=(-11,-9,7);data.type='ORTHO';data.ortho_scale=13.8
    scene.render.resolution_x=1000;scene.render.resolution_y=750
    scene.cycles.samples=24
    whole_bounds=[Vector(v) for v in itertools.product(*zip(minimum,maximum))]
elif args.view.endswith('detail'):
    camera.location=target+normal*.17+up*.015; data.lens=45
else:
    camera.location=(-4.40,-1.025,2.32); target=Vector((-4.82,-1.025,1.97)); data.lens=17
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler(); data.clip_start=.005; data.clip_end=100
if whole_bounds:
    bpy.context.view_layer.update()
    for _ in range(10):
        uv=[world_to_camera_view(scene,camera,p) for p in whole_bounds]
        if all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv):break
        data.ortho_scale*=1.08;bpy.context.view_layer.update()
    assert all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv)
lights=([((-3,7,10),2300,6),((1,-5,7),1500,6)] if whole_bounds else
        [((-4.40,-1.025,2.40),90,.22),((-4.9,-1.0,2.48),50,.16)])
for position,power,size in lights:
    light_data=bpy.data.lights.new('Cab inspection fill','AREA'); light_data.energy=power; light_data.size=size
    light=bpy.data.objects.new(light_data.name,light_data); scene.collection.objects.link(light); light.location=position
    light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
assert sha(source)==expected
record={'view':args.view,'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size,
        'source_sha256':expected,'renderer':'Blender4.5.13 actual Cycles CPU2threads, no denoise','samples':scene.cycles.samples,
        'camera_world':[list(r) for r in camera.matrix_world],'lens_mm':data.lens,
        'extra_geometry_hidden':False,'source_saved':False,'production_changed':False,
        'installation':'FITTED B4 visual study; caption conflict and existing three assembly collision pairs remain unresolved',
        'whole_vehicle_acceptance':'16 OPEN'}
if whole_bounds:
    record['outer_extent_camera_coordinates']=[list(p) for p in uv]
    record['ortho_scale']=data.ortho_scale
    record['scope']='Whole current candidate appearance. Small internal B4 detail is not visible at this scale.'
(OUT/(args.view+'.render.json')).write_text(json.dumps(record,indent=2)+'\n')
print('VA180_CAB_RENDERED',args.view,flush=True)
