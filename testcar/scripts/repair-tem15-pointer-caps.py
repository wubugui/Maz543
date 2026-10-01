"""Native conversion + Weld duplicate cap seams, retaining editable Curve source."""
import bpy,json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'outputs/cloud-tem15-face-study-20261001';OUT=BASE/'iteration-02';OUT.mkdir(exist_ok=True)
source=BASE/'study.blend';expected='5724611e2fcd763c0dffae5b5bc916d4b84b9b704937502147c9e5f572bb7eb9';assert hashlib.sha256(source.read_bytes()).hexdigest()==expected;assert not (OUT/'study.blend').exists()
bpy.ops.wm.open_mainfile(filepath=str(source));o=bpy.data.objects['POINTER — fitted uncalibrated photo pose'];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();before=[tuple(v.co) for v in m.vertices];e.to_mesh_clear()
s=o.copy();s.data=o.data.copy();s.name='HIDDEN POINTER EDITABLE CURVE SOURCE';bpy.context.scene.collection.objects.link(s);s.hide_render=True;s.hide_set(True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object
w=o.modifiers.new('Native Weld exact cap seam duplicates','WELD');w.merge_threshold=1e-7;bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();after=[tuple(v.co) for v in m.vertices];e.to_mesh_clear();assert set(before)==set(after) and len(before)==12 and len(after)==6
o['repair']='Native Curve conversion and Weld duplicate cap seams; exact vertex position set unchanged'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'study.blend'),compress=True);manifest=json.loads((BASE/'build.json').read_text());manifest['model_sha256']=hashlib.sha256((OUT/'study.blend').read_bytes()).hexdigest();manifest['previous_failed_source_sha256']=expected;manifest['pointer_cap_repair']={'before_vertices':len(before),'after_vertices':len(after),'position_set_exact':True,'editable_source_retained':s.name,'modifier':'Native Weld,1e-7m'};(OUT/'build.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');shutil.copyfile(BASE/'FONT-LICENSE.txt',OUT/'FONT-LICENSE.txt');assert hashlib.sha256(source.read_bytes()).hexdigest()==expected;print('TEM15_NATIVE_CAP_REPAIR_SAVED',flush=True)
