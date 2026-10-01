"""Reproduce the validated cab edits on the retained textured sibling.

Keeps the textured baseline's own seat UVs/materials via native Separate. Applies
the published steering matrices, then appends the same partial VA180 study.
Intermediate native files are reproducible pipeline outputs under work/.
"""
import ast
import bpy
import hashlib
import json
import numpy as np
import runpy
import sys
from pathlib import Path
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'outputs/cloud-left-driver-side-20261001/MAZ543A_Textured.blend'
BASE_SHA='171e7696421227fca28b8be3c555065381cbc6ca2a4b43ca94d18b83b5a167c7'
MASTER=ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
MASTER_SHA='8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
WORK=ROOT/'work/cloud-va180-textured-pipeline-20261001'
OUT=ROOT/'outputs/cloud-va180-textured-20261001'
WORK.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE)==BASE_SHA and sha(MASTER)==MASTER_SHA
panel=WORK/'panel-intermediate.blend';steering=WORK/'steering-intermediate.blend'
assert not panel.exists() and not steering.exists() and not (OUT/'MAZ543A_Textured.blend').exists()

def run_script(path,arguments):
    original=sys.argv[:]
    try:
        sys.argv=[str(path),'--']+[str(x) for x in arguments]
        return runpy.run_path(str(path),run_name='__main__')
    finally:sys.argv=original

run_script(ROOT/'scripts/build-cab-panel-fit-candidate.py',['--input',BASE,'--output',panel,'--anchor','rear-face'])
panel_report=json.loads(panel.with_suffix('.build.json').read_text())
assert panel_report['seat_bases_before']==panel_report['seat_bases_after']
assert panel_report['remaining_visible_seat_base_vertices']==3600

tree=ast.parse((ROOT/'scripts/build-va180-panel-fit.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'geometry','state'}],type_ignores=[]),'snapshot_helpers','exec'))
before={o.name:state(o) for o in bpy.data.objects}
reference=json.loads((MASTER.parent/'build.json').read_text())
assert reference['candidate_sha256']==MASTER_SHA
wheel=bpy.data.objects['cab_pivot_004'];column=bpy.data.objects['BL_Left_driver_steering_column_retained']
allowed={wheel.name,column.name}|{o.name for o in wheel.children_recursive};assert len(allowed)==5
for name in ['LEFT DISPLAY ROOT — not vehicle datum','RIGHT DISPLAY ROOT — not vehicle datum']:
    assert np.max(np.abs(np.array(bpy.data.objects[name].matrix_world)-np.array(reference['old_object_snapshot'][name]['world'])))<1e-6
for obj in [wheel,column]:obj.matrix_world=Matrix(reference['old_object_snapshot'][obj.name]['world'])
bpy.context.view_layer.update()
after={o.name:state(o) for o in bpy.data.objects};assert before.keys()==after.keys()
fail=[]
for name,prior in before.items():
    for key,value in prior.items():
        if name in allowed and key in {'world','local'}:continue
        if after[name][key]!=value:fail.append([name,key])
assert not fail,fail[:20]
pose_checks=[]
for name in sorted(allowed):
    expected=reference['old_object_snapshot'][name]['world']
    error=float(np.max(np.abs(np.array(after[name]['world'])-np.array(expected))))
    assert error<1e-6,(name,error)
    pose_checks.append({'name':name,'source_master_world':expected,'textured_world':after[name]['world'],'max_matrix_error':error})
for obj in [wheel,column]:
    obj['steering_pose_status']='PHOTO_CONSISTENT_HYPOTHESIS_NOT_CALIBRATED'
    obj['steering_mount_status']='OPEN: bottom X and column length refitted; unknown reducer hardpoint'
bpy.context.scene['cab_candidate_status']='Textured sibling of partial native cab candidate; existing contacts and all16 gates remain OPEN'
bpy.ops.wm.save_as_mainfile(filepath=str(steering),compress=True)
steering_sha=sha(steering)
run_script(ROOT/'scripts/build-va180-panel-fit.py',['--base',steering,'--base-sha',steering_sha,'--output',OUT,'--candidate-name','MAZ543A_Textured.blend'])
report={'status':'BUILT_TEXTURED_SIBLING_REQUIRES_FRESH_READBACK','baseline_textured_sha256':BASE_SHA,
        'reference_master_sha256':MASTER_SHA,'final_candidate_sha256':sha(OUT/'MAZ543A_Textured.blend'),
        'panel_stage':panel_report,'steering_intermediate_sha256':steering_sha,
        'steering_scope_identity_failures':fail,'steering_world_comparison':pose_checks,
        'changed_world_objects':sorted(allowed),'old_texture_material_nodes_modified':False,
        'scope':'Native Separate retains the textured baseline seat UVs/materials, then exact published Master steering poses and retained partial VA180 append. No factory dimensions or whole-vehicle acceptance.'}
assert sha(BASE)==BASE_SHA and sha(MASTER)==MASTER_SHA
(OUT/'textured-pipeline.json').write_text(json.dumps(report,indent=2)+'\n')
print('TEXTURED_CAB_CANDIDATE_BUILT',report['final_candidate_sha256'],flush=True)
