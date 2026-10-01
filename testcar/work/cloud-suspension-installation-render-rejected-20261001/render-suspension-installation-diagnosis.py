"""Actual isolated native link/stop views; never saves or replaces a master."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-suspension-installation-20261001'
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
mapping=json.loads((OUT/'reference-mapping.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(SOURCE)
assert before=='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene;scene.frame_set(0);bpy.context.view_layer.update()
def descendants(o):
    for c in o.children:
        yield c
        yield from descendants(c)
shown=set()
for name in ['S543_0_lower','S543_0_upper','S543_0_upright']:
    shown.update(o.name for o in descendants(bpy.data.objects[name]) if o.type in {'MESH','CURVE'})
shown.update(['S543_0_droop_limit_bolt','S543_0_droop_locknut'])
for o in bpy.data.objects:
    if o.type in {'MESH','CURVE','FONT'}:o.hide_render=o.name not in shown
    elif o.type=='LIGHT':o.hide_render=True
bpy.ops.object.camera_add(location=(-1.38,1.57,1.27))
camera=bpy.context.object;target=Vector((-3.08,.82,.83))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=1.18;scene.camera=camera
for name,location,power,size in [('key',(-1.7,1.4,2.7),650,2),('fill',(-3.5,-.5,1.8),350,1.8)]:
    bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.name='DIAGNOSTIC_'+name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('DIAGNOSTIC_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.10,.12,.14,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
textmat=bpy.data.materials.new('DIAGNOSTIC_TEXT');textmat.use_nodes=True
bs=textmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.9,.94,.95,1);bs.inputs['Emission Color'].default_value=(.9,.94,.95,1);bs.inputs['Emission Strength'].default_value=1
texts=[]
for y,size in [(.49,.024),(-.49,.017),(-.52,.017)]:
    cu=bpy.data.curves.new('DIAGNOSTIC_LABEL','FONT');cu.size=size;o=bpy.data.objects.new('DIAGNOSTIC_LABEL',cu);scene.collection.objects.link(o);o.parent=camera;o.location=(-.56,y,-1);cu.materials.append(textmat);texts.append(cu)
texts[1].body='ACTUAL NATIVE LINKAGE / ISOLATED PARTS / FITTED HARDPOINTS'
texts[2].body='INSTALLATION DATUM IS NOT WHEEL TRAVEL OR RIDE HEIGHT'
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
records=[]
for label,filename,measurement in [('CURRENT DECLARED ZERO','native-zero-links.png',None),('136-141 mm INSTALLATION DATUM: MIDPOINT DIAGNOSIS','native-installation-links.png',mapping['measurements'][1])]:
    scene.frame_set(0);bpy.context.view_layer.update()
    if measurement:
        for name,pose in measurement['pose'].items():
            o=bpy.data.objects[name];p=pose['p'];o.location=(p[0],-p[2],p[1]);o.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update();texts[0].body=label;scene.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True)
    records.append({'file':filename,'sha256':sha(OUT/filename),'camera_matrix_world':[list(r) for r in camera.matrix_world],'diagnostic_drop_m':measurement['requestedVerticalDropM'] if measurement else None})
assert sha(SOURCE)==before
(OUT/'render-provenance.json').write_text(json.dumps({'engine':'Actual Cycles CPU 48 samples','source_sha256':before,'source_unchanged':True,'shown_actual_parts':sorted(shown),'records':records,'scope':'Isolated arm/upright/bolt details only. Torsion shafts, frame support and full suspension are deliberately not portrayed as a validated installed assembly. No source model saved.'},indent=2))
