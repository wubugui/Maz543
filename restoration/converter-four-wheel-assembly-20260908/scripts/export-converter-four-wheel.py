"""Export the saved four-wheel assembly with native vertex evidence."""
import bpy,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'outputs/MAZ543A_Converter_FourWheelAssembly.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.view_layer.update()
parts=[];offset=0
with (ROOT/'work/transmission/converter-four-wheel-reference.bin').open('wb') as ref:
    for ob in bpy.data.objects:
        if ob.type!='MESH':continue
        points=[ob.matrix_world@v.co for v in ob.data.vertices]
        for p in points:ref.write(struct.pack('<fff',p.x,p.z,-p.y))
        parts.append({'name':ob.name,'vertices':len(points),'byteOffset':offset,'parent':ob.parent.name if ob.parent else None});offset+=len(points)*12
target=ROOT/'public/models/maz543a-converter-assembly.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_animations=False,export_extras=True,export_yup=True)
notes=json.loads((ROOT/'work/transmission/converter-four-wheel-assembly.json').read_text())
data={**notes,'parts':parts,'kind':'source-topology-assembly-inspection','nativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modelSha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(ROOT/'public/models/maz543a-converter-assembly.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
print(json.dumps({'bytes':target.stat().st_size,'meshes':len(parts),'nativeVertices':offset//12,'sha256':data['modelSha256']}),flush=True)
