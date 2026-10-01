"""Fresh, fully framed views of unchanged production native geometry."""
import bpy,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'testcar/outputs/MAZ543A_Master.blend'
OUT=ROOT/'testcar/outputs/cloud-whole-production-20261001';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3';assert sha(SOURCE)==expected
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
for im in bpy.data.images:
    ref=ROOT/'external/maz543-references'/im.name
    if im.source=='FILE' and not im.packed_file and ref.exists():im.filepath=str(ref);im.reload()
scene=bpy.context.scene;scene.frame_set(0);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.use_motion_blur=False
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
w=bpy.data.worlds.new('Current production review world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs['Color'].default_value=(.25,.28,.32,1);w.node_tree.nodes['Background'].inputs['Strength'].default_value=.8;scene.world=w
cd=bpy.data.cameras.new('Whole vehicle review camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
# Measured extent of this exact source SHA. Fit all eight enclosing corners;
# do not crop the rear just to make a local equipment detail fill the image.
minimum=(-5.749101161956787,-1.8629999160766602,-.003979163244366646)
maximum=(5.519999980926514,1.8629999160766602,2.994999885559082)
target=Vector(tuple((a+b)/2 for a,b in zip(minimum,maximum)))
corners=[Vector(v) for v in itertools.product(*zip(minimum,maximum))]
for loc,energy in [((-3,7,10),2300),((1,-5,7),1500)]:
    d=bpy.data.lights.new('Whole production review area','AREA');d.energy=energy;d.size=6;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
records=[]
for view,location in [('front-three-quarter',(-11,-9,7)),('rear-three-quarter',(11,9,7))]:
    cam.location=location;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=13.8
    bpy.context.view_layer.update()
    for _ in range(10):
        uv=[world_to_camera_view(scene,cam,p) for p in corners]
        if all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv):break
        cd.ortho_scale*=1.08;bpy.context.view_layer.update()
    assert all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv),'Whole vehicle bounds clipped'
    scene.render.filepath=str(OUT/(view+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'file':view+'.png','sha256':sha(OUT/(view+'.png')),'camera_world':[list(r) for r in cam.matrix_world],'ortho_scale':cd.ortho_scale,'car_extent_corner_image_coordinates':[list(p) for p in uv]})
assert sha(SOURCE)==expected
(OUT/'render-manifest.json').write_text(json.dumps({'source_sha256':expected,'production_version':'rear-box-frame-20260930','native_cycles_cpu_samples':24,'threads':4,'images':records,'vehicle_geometry_hidden_or_changed':False,'source_file_unchanged':True,'candidate_improvements_integrated':False,'all16VehicleGates':'OPEN'},indent=2))
