"""Same-camera native before/after and full independent candidate view."""
import bpy,json,hashlib,itertools,os,numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-cover-grips-20261001';records=[]
only=os.environ.get('MAZ_GRIP_RENDER_ONLY','')
if only and (OUT/'render-provenance.json').exists():records=json.loads((OUT/'render-provenance.json').read_text())
for variant,path in [('r3-before',ROOT/'outputs/cloud-cover-service-r3-20260930/MAZ543A_Master.blend'),('photo-grips-candidate',OUT/'MAZ543A_Master.blend')]:
    if only=='whole-front' and variant=='r3-before':continue
    before=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;scene.frame_set(0)
    c=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];c['service_stage']=0.;c.update_tag();bpy.context.view_layer.update()
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.use_motion_blur=False
    scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    w=bpy.data.worlds.new('Photo grip review world');w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.25,.28,.32,1);w.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=w
    cd=bpy.data.cameras.new('Photo grip review camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.clip_start=.01;cd.clip_end=100
    for loc,energy in [((-3,7,10),2300),((1,-5,7),1500)]:
        ld=bpy.data.lights.new('Photo grip review area','AREA');ld.energy=energy;ld.size=6;o=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((-4.4,0,2.18))-o.location).to_track_quat('-Z','Y').to_euler()
    views=[('front-cover-detail',(-6.8,-1.2,3.0),(-5.23,0,2.13),1.65)]
    if variant=='photo-grips-candidate':views.append(('whole-front',(-11,-9,7),(-.11455,0,1.4955),13.8))
    for label,loc,target,scale in views:
        if only and label!=only:continue
        cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;bpy.context.view_layer.update();corner_proof=None
        if label=='whole-front':
            # Two prior whole-view runs ended with exit137 near the last
            # samples. Cause is unconfirmed. Avoid optional denoise transient
            # allocations; retain every model part/resolution and use64samples.
            scene.cycles.use_denoising=False;scene.cycles.samples=64
            dg=bpy.context.evaluated_depsgraph_get();low=np.full(3,np.inf);high=np.full(3,-np.inf)
            for obj in scene.objects:
                if obj.type not in {'MESH','CURVE','SURFACE','FONT'} or obj.hide_render or obj.name.startswith(('CUTTER_','TOOL_','SOURCE_','ARCHIVE')):continue
                # The existing100m studio floor stays rendered, but is not a
                # vehicle component and must not define the car framing box.
                if obj.name=='STUDIO_FLOOR':continue
                # Curve bound_box may be stale/inflated before conversion.
                # Use actual evaluated mesh vertices instead of accepting it.
                e=obj.evaluated_get(dg);m=e.to_mesh();a=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',a)
                if len(a):
                    matrix=np.array(e.matrix_world);world=a.reshape(-1,3)@matrix[:3,:3].T+matrix[:3,3];low=np.minimum(low,world.min(axis=0));high=np.maximum(high,world.max(axis=0))
                e.to_mesh_clear()
            low=low.tolist();high=high.tolist();print('ACTUAL_WHOLE_GEOMETRY_BOUNDS',low,high,flush=True)
            corners=[Vector(v) for v in itertools.product(*zip(low,high))]
            for _ in range(10):
                uv=[world_to_camera_view(scene,cam,p) for p in corners]
                if all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv):break
                cd.ortho_scale*=1.08;bpy.context.view_layer.update()
            assert all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv);corner_proof={'actual_active_vehicle_bounds':[low,high],'image_corners':[list(p) for p in uv],'bounds_only_exclusion':'STUDIO_FLOOR remains rendered'}
        name=variant+'-'+label+'.png';scene.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)
        records.append({'file':name,'source_sha256':before,'variant':variant,'camera_matrix':[list(r) for r in cam.matrix_world],'ortho_scale':cd.ortho_scale,'whole_view_corner_check':corner_proof,'status':'INDEPENDENT_CANDIDATE_NOT_PRODUCTION;R3_FAILURES_AND_16_GATES_OPEN','actual_renderer':f'Cycles CPU{scene.cycles.samples}samples4threads;denoise={scene.cycles.use_denoising}'})
        (OUT/'render-provenance.json').write_text(json.dumps(records,indent=2));print('PHOTO_GRIP_RENDERED',name,flush=True)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
