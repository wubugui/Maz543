"""Fresh-open the remotely restored existing door source, without replay/save.

Checks delivery/load fidelity and the saved closed native controls. The earlier
44-pose mechanical qualification is retained, not rerun or expanded here.
"""
import argparse, ast, hashlib, json, math, sys, traceback
from pathlib import Path
import bpy
import numpy as np

p=argparse.ArgumentParser()
for name in ('artifact','evidence','manifest','output'):
    p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':'REMOTE_DOOR_NATIVE_OPEN_STARTED','saved_model':False,'rendered':False,
        'timeline_advanced':False,'angle_property_changed':False,'mechanical_pose_retest':False,
        'all16_vehicle_gates':'OPEN','six_original_closed_contacts':'OPEN'}
try:
    assert not a.output.exists()
    manifest=json.loads(a.manifest.read_text())
    assert manifest['bytes']==67937160 and manifest['sha256']=='3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f'
    artifact=a.artifact.resolve()
    assert artifact.stat().st_size==manifest['bytes'] and sha(artifact)==manifest['sha256']
    assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0'
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    source=a.evidence/'verify-fresh-executed-script.py'
    assert sha(source)=='4390d1566fce69cff30e336ae21137d74b1927fff1067dedcbdd7b7ca71b95d9'
    wanted={'require','as_plain','scalar_rna','array','mesh_signature','driver_description',
            'animation_state','value_guard','property_guard','expressions','controls_guard'}
    defs=[n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in wanted]
    assert len(defs)==len(wanted)
    H=dict(bpy=bpy,np=np,json=json,hashlib=hashlib,math=math,PROP='open_angle_deg',META='maz_native_axis_control_v1')
    exec(compile(ast.Module(body=defs,type_ignores=[]),str(source),'exec'),H)
    prior=json.loads((a.evidence/'verify-report.json').read_text())
    assert prior['status']=='FRESH_REOPEN_DISABLE_AUTOEXEC_PASS' and prior['candidate_sha256']==manifest['sha256']
    signatures=a.evidence/'restored-signatures/verify-final_identity-mesh-signatures.json'
    assert sha(signatures)==prior['final_identity']['mesh_signature_manifest_sha256']=='77f22c327f85e4c2cf6e54c7840d5cec621ec01b344af207579d8c6e25c9ac2d'
    mesh_manifest=json.loads(signatures.read_text());expected_meshes=mesh_manifest['meshes']
    bpy.ops.wm.open_mainfile(filepath=str(artifact),load_ui=False)
    bpy.context.view_layer.update()
    assert Path(bpy.data.filepath).resolve()==artifact
    assert bpy.context.scene.frame_current==0 and bpy.context.scene.frame_subframe==0
    assert len(bpy.data.objects)==prior['final_identity']['object_count']==10434
    assert len(bpy.data.meshes)==prior['final_identity']['mesh_count']==7470
    assert sorted(bpy.data.meshes.keys())==sorted(expected_meshes)
    for name,row in expected_meshes.items():
        m=bpy.data.meshes[name]
        assert [len(m.vertices),len(m.edges),len(m.loops),len(m.polygons)]==row['counts'],name
    specs=prior['specifications']
    actual_controls=json.loads(json.dumps(H['controls_guard'](specs)))
    assert actual_controls==prior['final_driver_records']
    parts=[name for s in specs for name in s['parts']]
    assert len(parts)==len(set(parts))==44
    checked=set()
    for spec in specs:
        hinge=bpy.data.objects[spec['hinge']]
        assert hinge['open_angle_deg']==0 and hinge.type=='EMPTY'
        assert set(spec['parts'])=={o.name for o in hinge.children_recursive}
        for name in spec['parts']:
            obj=bpy.data.objects[name]
            assert obj.type=='MESH' and obj.parent==hinge
            sig=H['mesh_signature'](obj.data);expected=expected_meshes[obj.data.name]
            assert sig['sha256']==expected['sha256'] and sig['counts']==expected['counts'],name
            assert sig['fields']==mesh_manifest['field_schemas'][expected['field_schema']],name
            checked.add(obj.data.name)
    assert sha(artifact)==manifest['sha256']
    report.update(status='REMOTE_RESTORED_NATIVE_FRESH_OPEN_PASS',actual_opened_filepath=bpy.data.filepath,
                  bytes=manifest['bytes'],sha256=manifest['sha256'],objects=10434,mesh_name_count_topology_exact=7470,
                  door_part_bindings_exact=44,door_mesh_stored_signatures_exact=len(checked),
                  exact_valid_simple_native_drivers=16,closed_angle_properties=4,
                  source_file_unchanged=True,original_cloud_model_not_read=True,
                  full7470_mesh_payload_signatures_recomputed=False)
except BaseException as exc:
    report.update(status='REMOTE_RESTORED_NATIVE_FRESH_OPEN_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
    a.output.write_text(json.dumps(report,indent=2)+'\n');raise
else:
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],flush=True)
