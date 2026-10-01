"""Export actual saved corrected driving controls world vertices for asset QA."""
import bpy,json,struct,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('MAZ_LETTERING_DIR',str(ROOT/'outputs/cloud-left-driver-side-20261001'))).resolve()
OUT=Path(os.environ.get('MAZ_OUTPUT_DIR',str(ROOT/'work/cloud-left-driver-export-20261001'))).resolve();OUT.mkdir(parents=True,exist_ok=True)
if OUT==ROOT/'public/models' or OUT==ROOT/'outputs':raise RuntimeError('Refusing production output directory')
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'MAZ543A_Textured.blend'));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();rows=[];offset=0
with (OUT/'driver-world-reference.bin').open('wb') as stream:
 for obj in sorted(bpy.data.objects,key=lambda x:x.name):
  if not (obj.name.startswith('BL_Left_driver_') or (obj.parent and obj.parent.name=='cab_pivot_004' and obj.type=='MESH')):continue
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();points=[ev.matrix_world@v.co for v in m.vertices]
  for p in points:stream.write(struct.pack('<fff',p.x,p.z,-p.y))
  rows.append({'name':obj.name,'byteOffset':offset,'vertices':len(points),'triangles':len(m.loop_triangles)});offset+=len(points)*12;ev.to_mesh_clear()
assert len(rows)==10
(OUT/'driver-world-reference.json').write_text(json.dumps({'coordinates':'glTF / browser Y-up world','parts':rows},indent=2));print('DRIVER_REFERENCE',len(rows),offset)
