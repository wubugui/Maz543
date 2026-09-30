"""Temporary fidelity comparison; keep the saved native files untouched."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/tangent-audit';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Textured.blend'));bpy.context.scene.frame_set(0)
bpy.ops.object.select_all(action='DESELECT')
names=['BL_Merged_body_OD_green_aged_enamel','BL_Merged_wheels_pivot_002_Tyre_rubber']
for name in names:
 obj=bpy.data.objects[name];obj.hide_set(False);obj.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects[names[0]]
common=dict(export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False)
for compressed in [False,True]:
 name='native-samples-draco-lossless.glb' if compressed else 'native-samples-plain.glb'
 options=dict(export_draco_mesh_compression_enable=compressed)
 if compressed:options.update(export_draco_mesh_compression_level=6,export_draco_position_quantization=0,export_draco_normal_quantization=0,export_draco_texcoord_quantization=0,export_draco_color_quantization=0,export_draco_generic_quantization=0)
 bpy.ops.export_scene.gltf(filepath=str(OUT/name),**common,**options)
 print('SAMPLE_EXPORT',name,(OUT/name).stat().st_size,flush=True)
(OUT/'lossless-sample-export.json').write_text(json.dumps({'native':'outputs/MAZ543A_Textured.blend','nativeSaved':False,'selected':names,'compressedQuantizationBits':{'position':0,'normal':0,'texcoord':0,'color':0,'generic':0},'blenderVersion':bpy.app.version_string},indent=2),encoding='utf8')
