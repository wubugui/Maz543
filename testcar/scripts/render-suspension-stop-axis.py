"""Actual isolated retained upper arm/bolt in a fixed installation pose; no save."""
import bpy
import hashlib
import json
import argparse
import sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
OUT=ROOT/'outputs/cloud-suspension-stop-axis-20261001'
parser=argparse.ArgumentParser();parser.add_argument('--framed-oblique',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
EXPECTED='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(SOURCE)==EXPECTED
mapping=json.loads((ROOT/'outputs/cloud-suspension-installation-20261001/reference-mapping.json').read_text())
measurement=mapping['measurements'][1]
projection=json.loads((OUT/'projection-probe.json').read_text())['rows'][1]
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(0)
for name,pose in measurement['pose'].items():
    ob=bpy.data.objects[name];ob.animation_data_clear();p=pose['p'];ob.location=(p[0],-p[2],p[1]);ob.rotation_euler.x=pose['rx']
bpy.context.view_layer.update()
shown={o.name for o in bpy.data.objects['S543_0_upper'].children_recursive if o.type in {'MESH','CURVE'}}
shown.update(['S543_0_droop_limit_bolt','S543_0_droop_locknut'])
for o in bpy.data.objects:
    if o.type in {'MESH','CURVE','FONT'}:o.hide_render=o.name not in shown
    elif o.type=='LIGHT':o.hide_render=True
gold=bpy.data.materials.new('DIAGNOSTIC bolt highlight, not original finish');gold.use_nodes=True
bs=gold.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.8,.24,.025,1);bs.inputs['Metallic'].default_value=.1;bs.inputs['Roughness'].default_value=.45
for name in ['S543_0_droop_limit_bolt','S543_0_droop_locknut']:
    o=bpy.data.objects[name];o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(gold)
target=Vector((-3.08,.805,.85))
camera_data=bpy.data.cameras.new('Actual stop-axis inspection');camera=bpy.data.objects.new(camera_data.name,camera_data);scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=.77
for name,loc,power,size in [('key',(-2.5,1.2,2.6),170,1.4),('fill',(-3.6,.2,1.8),100,1.2)]:
    d=bpy.data.lights.new('DIAGNOSTIC '+name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
w=bpy.data.worlds.new('Stop-axis inspection background');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.08,.10,.12,1);w.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=w
mat=bpy.data.materials.new('DIAGNOSTIC caption');mat.use_nodes=True;n=mat.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(.9,.95,1,1);n.inputs['Emission Color'].default_value=(.9,.95,1,1);n.inputs['Emission Strength'].default_value=1
labels=[]
for y,text,size in [(.27,'RETAINED PARTS / ISOLATED INSPECTION',.018),(-.255,'UPPER ARM + BOLT/NUT (ORANGE = DIAGNOSTIC)',.013),(-.28,'138.5 mm installation setting; dimensions remain FITTED',.012)]:
    cu=bpy.data.curves.new('Inspection caption','FONT');cu.body=text;cu.size=size;cu.materials.append(mat);o=bpy.data.objects.new(cu.name,cu);scene.collection.objects.link(o);o.parent=camera;o.location=(-.355,y,-1)
    labels.append((o,y,size))
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.use_motion_blur=False
records=[]
pose_before={name:[list(r) for r in bpy.data.objects[name].matrix_world] for name in measurement['pose']}
views=[('oblique-framed',(-2.2,1.45,1.75))] if args.framed_oblique else [('top',(-3.08,.805,3)),('oblique',(-2.2,1.45,1.75))]
for label,location in views:
    path=OUT/('native-stop-'+label+'.png');assert not path.exists()
    camera.location=location;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(path)
    if args.framed_oblique:
        bpy.context.view_layer.update()
        corners=[bpy.data.objects[name].matrix_world@Vector(c) for name in shown for c in bpy.data.objects[name].bound_box]
        for _ in range(20):
            uv=[world_to_camera_view(scene,camera,p) for p in corners]
            if all(.07<=p.x<=.93 and .17<=p.y<=.86 for p in uv):break
            camera_data.ortho_scale*=1.08;bpy.context.view_layer.update()
        assert all(.07<=p.x<=.93 and .17<=p.y<=.86 for p in uv), 'Inspection parts clipped'
        ratio=camera_data.ortho_scale/.77
        for label_obj,y,size in labels:label_obj.location=(-.355*ratio,y*ratio,-1);label_obj.data.size=size*ratio
    bpy.ops.render.render(write_still=True)
    assert all([list(r) for r in bpy.data.objects[name].matrix_world]==matrix for name,matrix in pose_before.items()), 'Render changed the diagnostic pose'
    records.append({'file':path.name,'sha256':sha(path),'camera':[list(r) for r in camera.matrix_world],'ortho_scale':camera_data.ortho_scale})
assert sha(SOURCE)==EXPECTED
(OUT/('framed-render-provenance.json' if args.framed_oblique else 'render-provenance.json')).write_text(json.dumps({'source_sha256':EXPECTED,'shown_actual_parts':sorted(shown),'inspection_material_override':['S543_0_droop_limit_bolt','S543_0_droop_locknut'],'source_unchanged':True,'saved_blend':False,'engine':'Actual Cycles CPU2 48samples native denoise','records':records,'scope':'Isolated upper-arm/bolt/nut, not full suspension or original paint. Source dimensions remain FITTED. Contact conclusion comes from full projection data, not these images.'},indent=2)+'\n')
print('STOP_AXIS_RENDERS_FINISHED',flush=True)
