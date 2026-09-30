"""CPU renders of independently reopened r2/r3 native files, identical paired cameras.
Does not save scene changes; no fabricated pixels or generated reference imagery.
"""
import bpy,json,math,os
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cover-service-r3-20260930'
rows=[]
for variant,source in [('r2',ROOT/'outputs/cloud-three-cover-r2-portable-20260930/MAZ543A_Master.blend'),('r3',OUT/'MAZ543A_Master.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
 scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
 world=bpy.data.worlds.new('R3 native inspection world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.20,.23,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;scene.world=world
 cd=bpy.data.cameras.new('R3 native review camera');cam=bpy.data.objects.new('R3 native review camera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.clip_start=.01;cd.clip_end=100
 for name,pos,power,size in [('R3 key',(-7,-5,9),1800,5),('R3 fill',(-2,5,7),1300,4)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((-4.4,0,2.18))-o.location).to_track_quat('-Z','Y').to_euler()
 hinge=bpy.data.objects['BL_Front_cover_hinge'];base=hinge.matrix_basis.copy()
 for view,pos,target,scale,angle in [('closed-detail',(-6.6,-1.6,3.2),(-5.38,0,2.08),1.9,0),('open-detail',(-6.6,-1.6,3.2),(-5.38,0,2.08),1.9,60),('open-context',(-8.6,-5.8,5.6),(-4.4,0,2.18),3.65,60)]:
  if variant=='r3':
   c=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];c['service_stage']=0 if angle==0 else 2;c.update_tag()
  else:hinge.matrix_basis=base@Matrix.Rotation(math.radians(angle),4,'Y')
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;bpy.context.view_layer.update()
  f=OUT/f'native-{variant}-{view}.png';scene.render.filepath=str(f);bpy.ops.render.render(write_still=True)
  rows.append({'file':f.name,'variant':variant,'source':str(source.relative_to(ROOT)),'view':view,'lidDegrees':angle,'latchDegrees':0 if variant=='r2' or angle==0 else -100,'cameraMatrixWorld':[list(r) for r in cam.matrix_world],'orthoScale':scale,'resolution':[1100,800],'renderer':'Cycles CPU, 4 threads, 16 samples; original native material/geometry','scope':'Native inspection only, not web screenshot, calibrated dimensions, photorealism acceptance or continuous collision proof'})
  (OUT/'native-render-manifest.json').write_text(json.dumps(rows,indent=2));print('RENDER_DONE',f.name,flush=True)
print('R3_NATIVE_COMPARISON_COMPLETE',flush=True)
