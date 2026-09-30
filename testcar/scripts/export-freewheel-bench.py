"""Export the saved neutral bench mesh; animation is reconstructed from its trace."""
import bpy,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'outputs/MAZ543A_Converter_Freewheel_ContactBench.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
data=json.loads((ROOT/'work/freewheel-contact/native-bench.json').read_text())
with (ROOT/'work/freewheel-contact/browser-coil-reference.bin').open('wb') as out:
    for sample in data['samples']:
        bpy.context.scene.frame_set(sample['frame']);bpy.context.view_layer.update()
        e=bpy.data.objects['CV_front_engagement_spring_0'].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
        for v in mesh.vertices:out.write(struct.pack('<fff',v.co.x,v.co.z,-v.co.y))
        e.to_mesh_clear()
bpy.context.scene.frame_set(0)
for ob in bpy.data.objects:
    ob.animation_data_clear()
    if ob.type=='MESH' and ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear();ob.shape_key_clear()
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
    if ob.name.startswith('CV_') or ob.name=='S543_CONVERTER_FREEWHEELS':ob.select_set(True)
target=ROOT/'public/models/maz543a-freewheel-bench.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_yup=True)
data['nativeBlendSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
data['modelSha256']=hashlib.sha256(target.read_bytes()).hexdigest()
(ROOT/'public/models/maz543a-freewheel-bench.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
print('EXPORTED',target.stat().st_size,data['modelSha256'],flush=True)
