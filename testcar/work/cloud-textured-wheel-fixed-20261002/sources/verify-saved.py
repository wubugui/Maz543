"""Fresh-open fixed-frame artifact verification; no animation playback or render."""
import argparse,ast,hashlib,json,math,sys,traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--output',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);attempt=Path(a.attempt);out=Path(a.output)
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def ob(name):return bpy.data.objects[name]
def matrix(o):return np.asarray(o.matrix_world,dtype=np.float64)
def worlds():return {o.name:matrix(o).tolist() for o in bpy.data.objects}
report={'status':'FRESH_OPEN_IN_PROGRESS','timeline_status':'BLOCKED_NOT_EXECUTED','rendered':False,'asset_delivery':'LOCAL_ONLY_LFS_BLOCKED'}
try:
 I=json.loads((attempt/'inputs.json').read_text());before=json.loads((attempt/'native-report.json').read_text())
 assert before['status']=='FIXED_FRAME_NATIVE_BUILD_SAVED_FRESH_OPEN_PENDING' and before['saved_blend']
 artifact=Path(before['saved_path']);assert artifact.stat().st_size==before['saved_bytes'] and sha(artifact.read_bytes())==before['saved_sha256']
 assert sha(Path(I['source_path']).read_bytes())==I['source_sha256']
 assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0' and not bpy.context.preferences.filepaths.use_scripts_auto_execute
 helper=attempt/'intake-helper-source.py';assert sha(helper.read_bytes())==I['helper_sha256']
 H=dict(bpy=bpy,np=np,json=json,math=math,hashlib=hashlib,sha=sha,issues=[])
 tree=ast.parse(helper.read_bytes());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main'],type_ignores=[]),str(helper),'exec'),H)
 builder=attempt/'build-trial.py';prepared=json.loads((attempt/'PREPARATION-MANIFEST.json').read_text())
 assert sha(builder.read_bytes())==prepared['prepared_files']['build-trial.py']['sha256']
 main=next(n for n in ast.parse(builder.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
 extract=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in {'action_record','mesh_record','snap'}];assert len(extract)==3
 exec(compile(ast.Module(body=extract,type_ignores=[]),str(builder),'exec'),globals())
 expected=json.loads((attempt/'saved-state-expected.json').read_text())
 bpy.ops.wm.open_mainfile(filepath=str(artifact));bpy.context.view_layer.update()
 assert bpy.context.scene.frame_current==0 and bpy.context.scene.frame_subframe==0
 assert sorted(bpy.data.objects.keys())==expected['object_names'] and len(bpy.data.objects)==8522
 assert digest(worlds())==expected['world_matrices_sha256']
 assert digest({o.name:o.parent.name if o.parent else None for o in bpy.data.objects})==expected['parents_sha256']
 assert digest({x.name:digest(action_record(x)) for x in bpy.data.actions})==expected['actions_sha256']
 for n,sig in expected['raw_geometry'].items():assert mesh_record(ob(n).data)==sig,('raw',n)
 for n,sig in expected['moving_evaluated'].items():assert snap(n)[0]==sig,('evaluated',n)
 material_expected=json.loads((attempt/'materials.json').read_text())
 material_actual={name:{'use_nodes':bpy.data.materials[name].use_nodes,'node_tree':H['node_tree_record'](bpy.data.materials[name].node_tree),'diffuse_color':list(bpy.data.materials[name].diffuse_color),'roughness':bpy.data.materials[name].roughness,'metallic':bpy.data.materials[name].metallic} for name in material_expected}
 assert material_actual==material_expected, 'Fresh material shader values differ from original intake'
 report['selected_materials_exact']=len(material_expected)
 for s in I['stations']:
  joint=ob(f"S543_{s['station']}_native_steering_joint_frame")
  assert joint.type=='EMPTY' and joint.parent==ob(s['upright'])
  assert ob(s['carrier']).parent==joint and ob(s['brake']).parent==joint
  assert ob(s['drum']).parent==ob(s['spin']) and ob(s['spin']).rotation_mode=='XYZ'
 for row in before['detached_retained_actions']:
  assert ob(row['object']).animation_data.action is None
  assert bpy.data.actions[row['action']].use_fake_user
 assert not H['issues'],H['issues']
 assert sha(artifact.read_bytes())==before['saved_sha256'] and sha(Path(I['source_path']).read_bytes())==I['source_sha256']
 report.update(status='FIXED_FRAME_SAVED_ARTIFACT_FRESH_OPEN_PASS',artifact_sha256=before['saved_sha256'],artifact_bytes=before['saved_bytes'],original_source_unchanged=True,objects=8522,raw_meshes_exact=132,moving_evaluated_meshes_exact=128,all_saved_world_matrices_exact=True,all_original_action_key_data_exact=True,parent_and_mode_persistence=True)
except BaseException as exc:
 report.update(status='FRESH_OPEN_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc());out.write_text(json.dumps(report,indent=2)+'\n');raise
else:
 out.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],flush=True)
