"""Preserve successful and incomplete contact evidence together, without overwrite."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/converter-strip-pocket-contact-20260908'
files=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
 'docs/CONVERTER_STRIP_POCKET_CONTACT_20260908.md','docs/CONVERTER_STRIP_SOURCE_CORRECTION_20260908.md',
 'scripts/converter_strip_spring.py','scripts/converter_strip_mesh.py','scripts/converter_strip_mount.py','scripts/converter_strip_pocket.py','scripts/converter_strip_dynamics.py',
 'scripts/diagnose-converter-strip-domain.py','scripts/verify-converter-strip-domain-native.py','scripts/diagnose-converter-strip-pocket.py',
 'scripts/verify-converter-strip-pocket.py','scripts/verify-converter-strip-pocket-refinement.py','scripts/verify-converter-strip-mount.py',
 'scripts/measure-converter-strip-inertia.py','scripts/diagnose-converter-strip-dynamics.py','scripts/diagnose-converter-strip-breakaway.py',
 'scripts/diagnose-converter-strip-exit-checkpoint.py','scripts/compare-converter-strip-dynamics.py','scripts/archive-converter-strip-pocket-stage.py',
 'outputs/MAZ543A_Converter_CurvedStripStudy.blend']
files+=['work/freewheel-contact/'+n for n in ['strip-spring-study.json','strip-domain.json','strip-pocket-domain.json','strip-domain-exit-checkpoint.json']]
files+=['outputs/'+n for n in ['converter-strip-domain-native.json','converter-strip-pocket-domain-native.json','converter-strip-pocket-verification.json',
 'converter-strip-pocket-refinement.json','converter-strip-mount-verification.json','converter-strip-inertia.json','converter-strip-static-torque-domain.json',
 'converter-strip-dynamics-4000hz-88segments.json','converter-strip-dynamics-4000hz-88segments-drive6.json',
 'converter-strip-dynamics-4000hz-88segments-drive10.json','converter-strip-dynamics-8000hz-88segments-drive10.json','converter-strip-dynamics-step-comparison.json']]
files+=['work/transmission/'+n for n in ['converter-strip-domain.log','converter-strip-domain-native.log','converter-strip-pocket.log',
 'converter-strip-pocket-verification.log','converter-strip-pocket-domain-native.log','converter-strip-pocket-refinement.log',
 'converter-strip-mount-verification.log','converter-strip-inertia.log','converter-strip-breakaway.log','converter-strip-exit-checkpoint.log',
 'converter-strip-dynamics-4000hz.log','converter-strip-dynamics-4000hz-drive6.log','converter-strip-dynamics-4000hz-drive10.log','converter-strip-dynamics-8000hz-drive10.log']]
files+=['work/reference-docs/transmission/'+n for n in ['000-0687.jpg','catalog-converter-pump-reactors.gif','converter-assembly-findings.json']]
assert len(files)==len(set(files))
for name in files:assert (ROOT/name).is_file(),name
assert not target.exists(),'Do not overwrite an existing evidence archive'
target.mkdir(parents=True);manifest=[]
for name in files:
    src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    content=src.read_bytes();assert dst.read_bytes()==content
    manifest.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
report={'stage':'Curved ribbon/wedge contact and offline continuous-load diagnostics','wholeGoal':'active; all 16 gates OPEN',
 'status':'Static contact checks and 2/6 Nm runs completed; 10 Nm trajectories incomplete at unexamined geometric boundary',
 'files':manifest,'fileCount':len(manifest),'totalBytes':sum(r['bytes'] for r in manifest)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
