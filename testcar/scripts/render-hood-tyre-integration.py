"""Render the integrated candidate with explicit unresolved derived-UV status."""
import bpy,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-hood-tyre-composite-20261001';SOURCE=OUT/'MAZ543A_Master.blend'
before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
audit=next(r for r in json.loads((OUT/'integration-preservation.json').read_text()) if r['file']==SOURCE.name)
assert audit['candidate_sha256']==before and not audit['unrelated_geometry_authored_uv_modifier_input_material_slot_or_parent_changes']
previous=next(r for r in json.loads((ROOT/'outputs/cloud-cover-grips-20261001/render-provenance.json').read_text()) if r['file']=='photo-grips-candidate-whole-front.png')
low,high=previous['whole_view_corner_check']['actual_active_vehicle_bounds']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(0);control=bpy.data.objects['BL_Cover_service_DIAGNOSTIC_CONTROL'];control['service_stage']=0;control.update_tag();bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
# Scoped readback establishes unchanged unrelated geometry. Check the hood
# and all restored glyphs against the measured complete vehicle envelope.
for name in ['BL_Front_cover_front_panel','BL_Photo_front_cover_top_grip_-1','BL_Photo_front_cover_top_grip_1']+[o.name for o in bpy.data.objects if o.name.startswith('BL_Tyre_') and '_emboss_' in o.name]:
    e=bpy.data.objects[name].evaluated_get(dg);m=e.to_mesh()
    assert all(low[k]<=p[k]<=high[k] for v in m.vertices for p in [e.matrix_world@v.co] for k in range(3)),name
    e.to_mesh_clear()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.use_motion_blur=False
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
world=bpy.data.worlds.new('Photo grip review world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.28,.32,1);world.node_tree.nodes['Background'].inputs[1].default_value=.8;scene.world=world
cd=bpy.data.cameras.new('Photo grip review camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.clip_start=.01;cd.clip_end=100
for loc,energy in [((-3,7,10),2300),((1,-5,7),1500)]:
    d=bpy.data.lights.new('Photo grip review area','AREA');d.energy=energy;d.size=6;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((-4.4,0,2.18))-o.location).to_track_quat('-Z','Y').to_euler()
records=[]
for name,loc,target,scale,samples,denoise in [('hood-tyre-composite-whole-front',(-11,-9,7),(-.11455,0,1.4955),previous['ortho_scale'],64,False)]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;scene.cycles.samples=samples;scene.cycles.use_denoising=denoise;bpy.context.view_layer.update();proof=None
    if name.endswith('whole-front'):
        uv=[world_to_camera_view(scene,cam,Vector(p)) for p in itertools.product(*zip(low,high))];assert all(.06<=p.x<=.94 and .06<=p.y<=.94 for p in uv)
        proof={'retained_verified_vehicle_envelope':[low,high],'modified_panel_grips_and_all_glyphs_inside_envelope':True,'unchanged_other_geometry_readback_sha256':before,'image_corners':[list(p) for p in uv],'studio_floor_rendered_not_part_of_vehicle_envelope':True}
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'file':name+'.png','candidate_sha256':before,'actual_renderer':f'Cycles CPU4threads{samples}samples;denoise={denoise}','camera_world':[list(r) for r in cam.matrix_world],'ortho_scale':scale,'whole_vehicle_framing':proof,'comparison_before':'outputs/cloud-cover-grips-20261001/photo-grips-candidate-front-cover-detail.png' if proof is None else None,'all16VehicleGates':'OPEN','strict_derived_uv_gate':audit['status'],'integrated_changes':['photo-guided45mmfittedhoodrelief','144nativewheelglyphs'],'not_integrated':['FG16lamp','batterycase','suspensioninstallationcandidate']})
    (OUT/'render-provenance.json').write_text(json.dumps(records,indent=2));print('CONTOUR_RENDERED',name,flush=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
