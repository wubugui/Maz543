"""Retain four editable diagnostic scenes, without changing production files."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-suspension-installation-20261001'
SOURCE=ROOT/'outputs/MAZ543A_Suspension_Master.blend'
DEST=OUT/'MAZ543A_Installation_Reference_Scenes.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(SOURCE)
assert before=='1332163b7c99da0bf3b11d3e9c250b451ceba3430b8935bde919ae4a55b6a51d'
mapping=json.loads((OUT/'reference-mapping.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
archive=bpy.context.scene;archive.name='ARCHIVE_ORIGINAL_SUSPENSION_MODULE';archive.frame_set(0)
bpy.context.view_layer.update()
def descendants(o):
    for c in o.children:yield c;yield from descendants(c)
shown=set()
for name in ['S543_0_lower','S543_0_upper','S543_0_upright']:
    shown.update(o.name for o in descendants(bpy.data.objects[name]) if o.type in {'MESH','CURVE'})
shown.update(['S543_0_droop_limit_bolt','S543_0_droop_locknut'])
needed=set(shown)
for name in list(shown):
    p=bpy.data.objects[name].parent
    while p:needed.add(p.name);p=p.parent
source={name:bpy.data.objects[name] for name in needed}
records=[]
specs=[('01_CURRENT_DECLARED_ZERO',None)]+[(f'{i+2:02d}_INSTALLATION_{round(v["requestedVerticalDropM"]*10000):04d}',v) for i,v in enumerate(mapping['measurements'])]
for scene_name,measurement in specs:
    scene=bpy.data.scenes.new(scene_name);bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.;scene.unit_settings.length_unit='MILLIMETERS'
    scene['status']='DIAGNOSTIC_REFERENCE_ONLY; NOT_ACCEPTED_ASSEMBLY'
    scene['reference']='1977 MAZ technical manual p320; lower-arm head vertical separation136-141mm during torsion installation; not wheel travel or ride height'
    scene['unresolved']='Existing unadjusted stop does not touch arm; support geometry, adjustment range, preload and factory hardpoints uncalibrated'
    scene['source_url']='https://drive.google.com/file/d/1quwh1UlmlDyw-WHAIPwLYbylRmNDXUr1/view?usp=drivesdk'
    scene['source_component_sha256']=before
    copies={}
    for name,o in source.items():
        clone=o.copy();clone.animation_data_clear()
        if o.data:clone.data=o.data.copy()
        clone.name=scene_name+'__'+name
        clone['source_object_name']=name
        clone.hide_render=name not in shown
        scene.collection.objects.link(clone);copies[name]=clone
    for name,o in source.items():
        copies[name].parent=copies.get(o.parent.name) if o.parent else None
        copies[name].matrix_parent_inverse=o.matrix_parent_inverse.copy()
        copies[name].matrix_basis=o.matrix_basis.copy()
    if measurement:
        for name,pose in measurement['pose'].items():
            if name in copies:
                o=copies[name];p=pose['p'];o.location=(p[0],-p[2],p[1]);o.rotation_euler.x=pose['rx']
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    actual=copies['S543_0_lower'].evaluated_get(dg).matrix_world.translation.z-copies['S543_0_upright'].evaluated_get(dg).matrix_world.translation.z
    target=measurement['requestedVerticalDropM'] if measurement else 0.
    assert abs(actual-target)<2e-6
    scene['requested_lower_head_drop_m']=target
    # Same actual view framing used in the verified Cycles diagnostic.
    bpy.ops.object.camera_add(location=(-1.38,1.57,1.27));cam=bpy.context.object;focus=Vector((-3.08,.82,.83))
    cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.18;scene.camera=cam
    for loc,power in [((-1.7,1.4,2.7),650),((-3.5,-.5,1.8),350)]:
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=2.;light.rotation_euler=(focus-light.location).to_track_quat('-Z','Y').to_euler()
    world=bpy.data.worlds.new(scene_name+'_WORLD');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.1,.12,.14,1);world.node_tree.nodes['Background'].inputs[1].default_value=.7;scene.world=world
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.use_motion_blur=False
    scene.render.resolution_x=1200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
    records.append({'scene':scene.name,'target_drop_m':target,'actual_drop_m':actual,'copied_source_parts':sorted(shown),'copied_rig_and_geometry_count':len(copies)})
note=bpy.data.texts.new('READ_ME_INSTALLATION_REFERENCE')
note.write('Four isolated editable diagnostic scenes, not a repaired or accepted suspension.\nThe original complete source module remains in ARCHIVE_ORIGINAL_SUSPENSION_MODULE.\nInstallation vertical head-center dimension136-141mm is from the original1977 p320.\nCurrent bolt/locknut remain unadjusted and lack verified support/contact.\nAll copied hardpoints, dimensions and interfaces remain reconstruction geometry.\nNo original manual scan pixels added. Source archive unchanged on disk.\nSee CLOUD_SUSPENSION_INSTALLATION_20261001.md and actual native report for boundaries.\n')
bpy.context.window.scene=bpy.data.scenes[records[0]['scene']]
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
assert sha(SOURCE)==before
(OUT/'editable-scenes-build.json').write_text(json.dumps({'status':'EDITABLE_DIAGNOSTIC_ONLY','source_sha256':before,'source_unchanged':True,'file':DEST.name,'sha256':sha(DEST),'bytes':DEST.stat().st_size,'scenes':records,'original_archive_scene':archive.name,'wholeVehicleAcceptance':'16 OPEN'},indent=2))
