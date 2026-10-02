"""View the already saved candidate at its unchanged frame0; no model save."""
import ast,hashlib,json,math,os,sys,time,traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(sys.argv[sys.argv.index('--')+1]);START=time.monotonic()
BASE=Path('/workspace/scratch/a29d03198654/maz-textured-front-wheel-fixed-20261002/fixed-01/MAZ543A_Textured_Front_Wheel_Parent_Study.blend')
EXPECTED='48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea'
sha_bytes=lambda b:hashlib.sha256(b).hexdigest()
def emit(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def phase(value):
 row={'phase':value,'elapsed_seconds':time.monotonic()-START}
 with (OUT/'phase.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print('PHASE',json.dumps(row),flush=True)
report={'status':'VIEW_IN_PROGRESS','source_sha256':EXPECTED,'source_delivery':'LOCAL_ONLY_LFS_BLOCKED','saved_model':False,'mechanical_pose_changed':False,'timeline_advanced':False,'all16_vehicle_gates':'OPEN','scope':'One frame0 native view of already saved candidate. No replay of construction and no mechanical, timeline, export or browser acceptance.'}
original_camera=None;added=[];objects=None
try:
 assert BASE.stat().st_size==100052636 and sha_bytes(BASE.read_bytes())==EXPECTED
 assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0' and not bpy.context.preferences.filepaths.use_scripts_auto_execute
 helper=Path('/workspace/scratch/a29d03198654/maz-tyre-letter-closeup-20261002/render-letter-closeup.py');assert sha_bytes(helper.read_bytes())=='0f69bdc9c06f6460325f012981466d589fc4d23ebed37c643f6bca0b2d2bb2f6'
 names={'matrix','plain','shader_tree','material_signature','object_visibility','object_bindings','collection_visibility'}
 defs=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(defs)==7
 exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'),globals())
 bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene;assert scene.frame_current==0 and scene.frame_subframe==0;bpy.context.view_layer.update()
 objects=tuple(bpy.data.objects);assert len(objects)==8522
 identities={o.name:o.as_pointer() for o in objects};worlds={o.name:matrix(o.matrix_world) for o in objects};visibility=object_visibility(objects);bindings=object_bindings(objects);collections=collection_visibility();materials=material_signature();world=scene.world;world_sig=shader_tree(world.node_tree) if world else None
 image_rows=[{'name':im.name,'source':im.source,'packed':bool(im.packed_file or len(im.packed_files))} for im in bpy.data.images]
 assert all(r['packed'] for r in image_rows if r['source'] in {'FILE','TILED','MOVIE','SEQUENCE'})
 report['image_resource_check']=image_rows
 spin=bpy.data.objects['wheels_pivot_002'];assert spin.rotation_mode=='XYZ' and spin.animation_data.action
 assert bpy.data.objects['brakes_0003'].parent==spin and spin.parent.parent.name=='S543_0_native_steering_joint_frame'
 reference=Path('/workspace/scratch/a29d03198654/maz-native-wheel-views-20261002/attempt-station0-neutral-01/ready-to-render.json');assert sha_bytes(reference.read_bytes())=='054d8e227e1947ae27e49ace5dbe9601cbcd648960e3d8223cf069ff523defe0';ref=json.loads(reference.read_text())
 center=spin.matrix_world.translation.copy();target=Vector(ref['camera_target_m']);original_camera=scene.camera
 camera_data=bpy.data.cameras.new('SAVED_CANDIDATE_VIEW_CAMERA');camera=bpy.data.objects.new(camera_data.name,camera_data);scene.collection.objects.link(camera);added.append(camera)
 camera.matrix_world=Matrix(ref['camera_world_matrix']);camera_data.type='ORTHO';camera_data.ortho_scale=2.6;camera_data.clip_start=.01;camera_data.clip_end=100;scene.camera=camera
 for i,row in enumerate(ref['additional_lights']):
  data=bpy.data.lights.new('SAVED_CANDIDATE_VIEW_LIGHT_'+str(i),'AREA');data.energy=row['watts'];data.shape='DISK';data.size=row['disk_size_m'];o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);added.append(o);o.location=Vector(row['world_position_m']);o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.samples=12;scene.cycles.use_denoising=True
 if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=False
 scene.cycles.use_adaptive_sampling=False;scene.cycles.seed=20261002;scene.cycles.use_animated_seed=False;scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2;scene.cycles.transmission_bounces=4;scene.cycles.transparent_max_bounces=8
 scene.render.use_persistent_data=False;scene.render.use_simplify=False;scene.render.use_motion_blur=False;scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8';scene.render.film_transparent=False;scene.render.use_compositing=False;scene.render.use_sequencer=False;scene.render.use_stamp=False;scene.render.use_border=False;scene.render.use_crop_to_border=False
 scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1;scene.view_settings.use_curve_mapping=False;bpy.context.view_layer.update()
 cam_error=max(abs(camera.matrix_world[r][c]-ref['camera_world_matrix'][r][c]) for r in range(4) for c in range(4));assert cam_error<1e-6
 tyre=bpy.data.objects['BL_Merged_wheels_pivot_002_Tyre_rubber'];ev=tyre.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 try:proj=np.asarray([world_to_camera_view(scene,camera,ev.matrix_world@v.co) for v in mesh.vertices]);assert proj[:,0].min()>.02 and proj[:,0].max()<.98 and proj[:,1].min()>.02 and proj[:,1].max()<.98
 finally:ev.to_mesh_clear()
 def unchanged():
  assert all(bpy.data.objects.get(o.name)==o and o.as_pointer()==identities[o.name] for o in objects)
  assert {o.name:matrix(o.matrix_world) for o in objects}==worlds
  assert object_visibility(objects)==visibility and object_bindings(objects)==bindings and collection_visibility()==collections
  assert material_signature()==materials and scene.world==world and (shader_tree(world.node_tree) if world else None)==world_sig
  assert scene.frame_current==0 and scene.frame_subframe==0
 unchanged()
 report.update(camera_world_matrix=matrix(camera.matrix_world),camera_matrix_max_difference_from_reference=cam_error,camera_ortho_scale_m=2.6,resolution=[1100,1000],cycles_samples=12,additional_lights=ref['additional_lights'],original_lights_retained=True,original_geometry_visibility_retained=True,original_world_and_materials_retained=True,original_objects=8522,tyre_projected_bounds=[proj.min(axis=0).tolist(),proj.max(axis=0).tolist()],notes=['Original lower-step/body interference remains visible; no part is moved or hidden','Lettering may remain unreadable at this full-wheel scale','This is Textured candidate48dbc498, not the previous Master-based visualization'])
 emit('ready-to-render.json',report);phase('ORIGINAL_STATE_PROTECTED_READY_TO_RENDER')
 png=OUT/'saved-textured-wheel-neutral.png';assert not png.exists();scene.render.filepath=str(png);t=time.monotonic();result=bpy.ops.render.render(write_still=True)
 assert result=={'FINISHED'} and png.is_file() and png.stat().st_size>10000
 report.update(render_operator_return=sorted(result),render_elapsed_seconds=time.monotonic()-t,png=png.name,png_bytes=png.stat().st_size,png_sha256=sha_bytes(png.read_bytes()));phase('RENDER_FILE_COMPLETE')
 unchanged();assert sha_bytes(BASE.read_bytes())==EXPECTED
 report.update(status='SAVED_CANDIDATE_VIEW_COMPLETE',final_original_identity_matrices_material_visibility_world='PASS',source_file_unchanged=True)
except BaseException as exc:
 report.update(status='VIEW_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc());raise
finally:
 if original_camera is not None:bpy.context.scene.camera=original_camera
 # Presentation additions exist only in this process and are never saved.
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 report['elapsed_seconds']=time.monotonic()-START;emit('native-report.json',report)
print(report['status'],flush=True)
