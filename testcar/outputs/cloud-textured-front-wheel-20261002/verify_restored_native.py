"""Fresh-open the remotely restored exact candidate; no model save or render.

--evidence is a fresh restoration of the already published fixed-wheel text
package. The old cloud output model is not opened or read by this verifier.
"""
import argparse,ast,hashlib,json,math,sys,traceback
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);sha=lambda b:hashlib.sha256(b).hexdigest();attempt=a.evidence/'fixed-01'
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def ob(name):return bpy.data.objects[name]
def matrix(o):return np.asarray(o.matrix_world,dtype=np.float64)
def worlds():return {o.name:matrix(o).tolist() for o in bpy.data.objects}
report={'status':'FRESH_REMOTE_RESTORATION_CHECK_STARTED','saved_model':False,'rendered':False,'timeline_advanced':False,'all16_vehicle_gates':'OPEN'}
try:
    assert not a.output.exists()
    manifest=json.loads(a.manifest.read_text());assert manifest['bytes']==100052636 and manifest['sha256']=='48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea'
    artifact=a.artifact.resolve();assert artifact.stat().st_size==manifest['bytes'] and sha(artifact.read_bytes())==manifest['sha256']
    assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0' and not bpy.context.preferences.filepaths.use_scripts_auto_execute
    helper=attempt/'intake-helper-source.py';assert sha(helper.read_bytes())=='e093cb1f0d1f66d3c399b345daea9f6d563abceee940d0f64c8f49e7f97aa289'
    H=dict(bpy=bpy,np=np,json=json,math=math,hashlib=hashlib,sha=sha,issues=[])
    defs=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name!='main'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'),H)
    builder=attempt/'build-trial.py';assert sha(builder.read_bytes())=='892cf825ff6a0929ab576c502b0fbb59829ec9943b627161fa48de02bac80a1d'
    main=next(n for n in ast.parse(builder.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='main')
    extract=[n for n in main.body if isinstance(n,ast.FunctionDef) and n.name in {'action_record','mesh_record','snap'}];assert len(extract)==3
    exec(compile(ast.Module(body=extract,type_ignores=[]),str(builder),'exec'),globals())
    expected=json.loads((attempt/'saved-state-expected.json').read_text());I=json.loads((attempt/'inputs.json').read_text());before=json.loads((attempt/'native-report.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(artifact));bpy.context.view_layer.update()
    assert Path(bpy.data.filepath).resolve()==artifact and bpy.context.scene.frame_current==0 and bpy.context.scene.frame_subframe==0
    assert sorted(bpy.data.objects.keys())==expected['object_names'] and len(bpy.data.objects)==8522
    assert digest(worlds())==expected['world_matrices_sha256']
    assert digest({o.name:o.parent.name if o.parent else None for o in bpy.data.objects})==expected['parents_sha256']
    assert digest({x.name:digest(action_record(x)) for x in bpy.data.actions})==expected['actions_sha256']
    for n,sig in expected['raw_geometry'].items():assert mesh_record(ob(n).data)==sig,('raw',n)
    for n,sig in expected['moving_evaluated'].items():assert snap(n)[0]==sig,('evaluated',n)
    mats=json.loads((attempt/'materials.json').read_text());actual={name:{'use_nodes':bpy.data.materials[name].use_nodes,'node_tree':H['node_tree_record'](bpy.data.materials[name].node_tree),'diffuse_color':list(bpy.data.materials[name].diffuse_color),'roughness':bpy.data.materials[name].roughness,'metallic':bpy.data.materials[name].metallic} for name in mats};assert actual==mats
    for s in I['stations']:
        joint=ob(f"S543_{s['station']}_native_steering_joint_frame");assert joint.type=='EMPTY' and joint.parent==ob(s['upright'])
        assert ob(s['carrier']).parent==joint and ob(s['brake']).parent==joint and ob(s['drum']).parent==ob(s['spin']) and ob(s['spin']).rotation_mode=='XYZ'
    for row in before['detached_retained_actions']:
        assert ob(row['object']).animation_data.action is None and bpy.data.actions[row['action']].use_fake_user
    assert not H['issues'],H['issues']
    assert sha(artifact.read_bytes())==manifest['sha256']
    report.update(status='REMOTE_RESTORED_NATIVE_FRESH_OPEN_PASS',actual_opened_filepath=bpy.data.filepath,bytes=manifest['bytes'],sha256=manifest['sha256'],objects=8522,raw_meshes_exact=132,moving_evaluated_meshes_exact=128,materials_exact=len(mats),all_saved_world_matrices_exact=True,all_original_action_key_data_exact=True,source_file_unchanged=True,original_cloud_model_not_read=True)
except BaseException as exc:
    report.update(status='REMOTE_RESTORED_NATIVE_FRESH_OPEN_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc());a.output.write_text(json.dumps(report,indent=2)+'\n');raise
else:
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],flush=True)
