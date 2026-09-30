"""Export the separate tyre-lettering candidate, never production assets."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/cloud-tyre-lettering-20260930'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'MAZ543A_Textured.blend'));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
def allowed(obj):
 if obj.hide_render or obj.name.startswith(('SOURCE_','ARCHIVE_','CUTTER_')):return False
 while obj:
  if obj.name in excluded:return False
  obj=obj.parent
 return True
def descendants(obj):
 for child in obj.children:yield child;yield from descendants(child)
root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS'];bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
selected=[]
for obj in descendants(root):
 if allowed(obj):obj.hide_set(False);obj.select_set(True);selected.append(obj)
assert len([o for o in selected if o.name.startswith('BL_Tyre_') and '_emboss_' in o.name])==144
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'native-export.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('CANDIDATE_EXPORT_COMPLETE')
