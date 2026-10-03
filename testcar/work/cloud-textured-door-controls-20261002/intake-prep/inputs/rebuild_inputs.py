"""Recreate only this new4.5.14 intake configuration from verified restored inputs."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
root=Path('/workspace/scratch/a29d03198654/Maz543')
out=root/'testcar/work/cloud-textured-door-controls-20261002/intake-prep'
work=root/'testcar/work'
ten=json.loads((work/'cloud-ten-normal-capture-20261002/capture.json').read_text())
graph=json.loads((work/'cloud-wheel-export-graph-20261002/inputs.json').read_text())
fixed=root.parent/'maz-canonical-remote-9816a330-20261002/fixed-evidence-restored'
official=root.parent/'tools-feiting/blender-4.5.14-linux-x64'
def record(p):
 p=Path(p); b=p.read_bytes()
 return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
inputs={k:ten['inputs'][k] for k in ['source','blender','bundled_python','numpy_version','legacy_export_helper','mesh_protection_helper']}
inputs.update({k:graph['inputs'][k] for k in ['helper','builder','saved_expected']})
inputs['blender']=record(official/'blender')
assert inputs['blender']['bytes']==163613240 and inputs['blender']['sha256']=='050c02562f81fe80ba616a80198fa02d381e60f8b61b8d39add881f4bca0d7d8'
inputs['bundled_python']=record(official/'4.5/python/bin/python3.11')
assert inputs['bundled_python']['bytes']==28653440 and inputs['bundled_python']['sha256']=='60b08089c60cbe81827b135c8fd9e206ba2ee6bf54aa1dbd0d6f56ac2d5914f6'
inputs['numpy_version']=record(official/'4.5/python/lib/python3.11/site-packages/numpy/version.py')
assert sys.version==ten['runtime']['python_version'] and np.__version__=='1.26.4'
assert Path(np.__file__).resolve()==official/'4.5/python/lib/python3.11/site-packages/numpy/__init__.py'
for key,p in {
 'graph_common':work/'cloud-wheel-export-graph-20261002/graph_common.py',
 'graph_inspector':work/'cloud-wheel-export-graph-20261002/inspect_native_graph.py',
 'array_helper':work/'cloud-ten-normal-capture-20261002/replay_capture.py',
 'original_runner':work/'cloud-ten-normal-capture-20261002/run_capture.py',
 'stations':work/'cloud-wheel-export-graph-20261002/run-02/native/stations.json',
 'inventory':work/'cloud-wheel-export-graph-20261002/run-02/native/object-inventory.json',
 'graph':work/'cloud-wheel-export-graph-20261002/run-02/native/native-graph.json',
 'graph_report':work/'cloud-wheel-export-graph-20261002/run-02/native/native-report.json',
 'static_findings':out.parent/'static-findings.json',
 'static_script':out.parent/'summarize_saved_doors.py',
 'scope_readme':out.parent/'README.md',
 'wheel_fresh_report':fixed/'fresh-01/native-report.json',
 'wheel_materials':fixed/'fixed-01/materials.json',
 'wheel_inputs':fixed/'fixed-01/inputs.json',
}.items(): inputs[key]=record(p)
assert all(record(v['path'])==v for v in inputs.values())
findings=json.loads((out.parent/'static-findings.json').read_text())
conf={
 'schema':'maz-textured-door-readonly-intake-v1',
 'phase':'MAZ_TEXT_TEXTURED_DOOR_INTAKE_4514',
 'prepared_at_head':'f0a0ca6221a8982075b61f1c19a67d24267b9156',
 'inputs':inputs,
 'runtime':{'python_version':sys.version,'numpy_version':np.__version__,'numpy_file':str(Path(np.__file__).resolve())},
 'doors':[{'hinge':d['hinge'],'source_side':d['source_side'],'door_index':d['door_index'],
           'children':d['current_children'],'green':d['merged_group_evidence'][0]['current_object']} for d in findings['doors']],
 'controls':['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007','cab','MAZ543_REFERENCE_CHASSIS'],
 'expected':{'objects':8522,'actions':552,'frame':0,'subframe':0,'blender_version':[4,5,14],'build_hash':'62c1db4208e8'},
 'execution':{'threads':2,'wall_seconds':120,'postflight_reserve_seconds':10,'minimum_native_seconds':60,
              'heartbeat_seconds':10,'term_grace_seconds':2,'kill_grace_seconds':3},
 'qualification':{'axes':'NOT_IDENTIFIED_REVIEW_SAVED_RAW','control_installation':'NOT_RUN',
                  'closed_contacts':'SIX_ORIGINAL_OPEN','whole_vehicle':'ALL_16_OPEN',
                  'global_timeline_nodes':'BLOCKED_NOT_EXECUTED'},
 'limits':[
  'Raw saved frame only; no frame_set, depsgraph evaluation, mesh changes, save/export/render or pose trial',
  'Only20 door mesh payloads; all8522 objects transform/binding records and552 original action records, no other geometry sweep',
  'Supported mesh signature fields and actually read action field inventories are explicit; original source is the recoverable full action archive. Unsupported or unenumerated RNA is not certified.',
  'Prior4.5.13 wheel132 raw/128 evaluated/7 material PASS records are historical only; no such acceptance is transferred to4.5.14',
  'Current before/after nonmutation protection is separate from historical4.5.13 baseline correspondence; save raw first and block axes/install on any mismatch',
  'No geometric acceptance thresholds or OEM dimension claim; all PCA axes and components remain candidates pending offline review'
 ]}
conf['inputs']['official_action_ui']=record(official/'4.5/scripts/startup/bl_ui/anim.py')
(out/'inputs').mkdir(exist_ok=True)
assert not (out/'inputs/intake.json').exists()
(out/'inputs/intake.json').write_text(json.dumps(conf,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
print('fixed inputs',len(inputs))
