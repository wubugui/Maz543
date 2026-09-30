"""Export saved, independently equilibrated meshes; never interpolate them as dynamics."""
import bpy,json,hashlib,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
study=json.loads((ROOT/'work/freewheel-contact/strip-spring-study.json').read_text())
strip=bpy.data.objects['CS_curved_strip'];roller=bpy.data.objects['CS_roller_12_5x22'];rows=[];snapshots=[]
with (ROOT/'work/freewheel-contact/strip-browser-reference.bin').open('wb') as reference:
    for index,row in enumerate(study['rows']):
        bpy.context.scene.frame_set(index);bpy.context.view_layer.update()
        evaluated=strip.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=bpy.data.meshes.new_from_object(evaluated)
        ob=bpy.data.objects.new(f'CS_equilibrium_{index:02d}',mesh);bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world=evaluated.matrix_world.copy();ob['equilibrium_index']=index;snapshots.append(ob)
        for vertex in mesh.vertices:
            p=ob.matrix_world@vertex.co;reference.write(struct.pack('<fff',p.x,p.z,-p.y))
        p=roller.matrix_world.translation
        rows.append({'index':index,'betaRad':row['beta'],'forceN':row['forceN'],'energyJ':row['energyJ'],
          'stressPa':row['maximumIncrementalBendingStressPa'],'rollerPosition':[p.x,p.z,-p.y],
          'nativeVertexCount':len(mesh.vertices)})
bpy.context.scene.frame_set(0)
for ob in bpy.data.objects:ob.animation_data_clear()
bpy.ops.object.select_all(action='DESELECT')
for ob in snapshots+[roller,bpy.data.objects['CS_outer_pocket'],bpy.data.objects['CS_fixed_inner_section']]:ob.select_set(True)
target=ROOT/'public/models/maz543a-strip-study.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_yup=True)
data={'kind':'independent-static-equilibria','rows':rows,'fit':study['fit'],
  'nativeSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modelSha256':hashlib.sha256(target.read_bytes()).hexdigest(),
  'limits':study['limits']}
(ROOT/'public/models/maz543a-strip-study.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
print(json.dumps({'bytes':target.stat().st_size,'states':len(rows),'sha256':data['modelSha256']}),flush=True)
