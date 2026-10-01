"""Render the isolated source-traced panel study, with review annotations distinct."""
import bpy,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cab-panel-study-20261001';SOURCE=OUT/'study.blend'
before=hashlib.sha256(SOURCE.read_bytes()).hexdigest();audit=json.loads((OUT/'native-readback.json').read_text());assert audit['file_sha256']==before and not audit['failures']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=2200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
manifest=json.loads((OUT/'build-manifest.json').read_text());points=[];dg=bpy.context.evaluated_depsgraph_get()
for name in manifest['claimed_closed_solids']:
 o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh();points.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
lo=[min(p[k] for p in points) for k in range(3)];hi=[max(p[k] for p in points) for k in range(3)]
light=bpy.data.lights.new('Additional rear inspection fill','AREA');light.energy=90;light.size=1.1;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=(-.3,.5,-1.4);o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
review=bpy.data.collections['95 REVIEW LABELS — not factory markings'];records=[]
for suffix,camera in [('front','REVIEW FRONT ORTHOGRAPHIC'),('oblique','REVIEW OBLIQUE'),('rear','REVIEW REAR ORTHOGRAPHIC')]:
 cam=bpy.data.objects[camera];scene.camera=cam;cam.data.ortho_scale=1.52;review.hide_render=suffix!='front';bpy.context.view_layer.update()
 corners=[world_to_camera_view(scene,cam,Vector(p)) for p in itertools.product(*zip(lo,hi))]
 assert all(.025<=p.x<=.975 and .025<=p.y<=.975 for p in corners),(suffix,[list(p) for p in corners])
 path=OUT/('native-panel-study-'+suffix+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'file':path.name,'source_sha256':before,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'actual_renderer':'Cycles CPU2threads48samples no denoise','resolution':[2200,1100],'camera':camera,'camera_world':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'review_annotations_rendered':suffix=='front','physical_geometry_hidden_for_image':False,'all_claimed_solids_inside_frame':[list(p) for p in corners],'independent_study_not_installed':True,'factory_metric_calibration':'OPEN','all16VehicleGates':'OPEN'})
 (OUT/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('PANEL_STUDY_RENDERED',suffix,flush=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
