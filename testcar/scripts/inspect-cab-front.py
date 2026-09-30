"""Orthographic native shape inspection, not a photoreal acceptance render."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
study='--study' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs'/('MAZ543A_CabFit_Study.blend' if study else 'MAZ543A_Master.blend')))
scene=bpy.context.scene;scene.frame_set(0)
camera=bpy.data.cameras.new('Front_shape_inspection');cam=bpy.data.objects.new('Front_shape_inspection',camera);scene.collection.objects.link(cam)
cam.location=(-15,0,1.65);cam.rotation_euler=(Vector((-4,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler()
camera.type='ORTHO';camera.ortho_scale=3.65;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.world.color=(.14,.14,.14)
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'outputs'/('cab-front-profile-study.png' if study else 'cab-front-shape-inspection.png'))
bpy.ops.render.render(write_still=True)
# Native scene is intentionally not saved: this is an audit camera only.
