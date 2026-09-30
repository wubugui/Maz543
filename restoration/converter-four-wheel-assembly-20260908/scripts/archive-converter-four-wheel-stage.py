"""Preserve the four-wheel assembly and actual app-check evidence together."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/converter-four-wheel-assembly-20260908'
files=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
       'docs/CONVERTER_FOUR_WHEEL_ASSEMBLY_20260908.md','docs/CONVERTER_STRIP_SURFACE_CONTACT_20260908.md',
       'scripts/blender-d12.py','scripts/converter_strip_mesh.py','components/converter-assembly.tsx','components/freewheel-bench.module.css',
       'components/workshop.tsx','app/converter/page.tsx','outputs/MAZ543A_Converter_FourWheelAssembly.blend',
       'outputs/converter-main-renderer-observation.json','public/models/maz543a-converter-assembly.glb','public/models/maz543a-converter-assembly.json',
       'work/transmission/converter-four-wheel-assembly.json','work/transmission/converter-four-wheel-reference.bin','work/freewheel-contact/strip-spring-study.json']
for directory,pattern in [('scripts','*converter-four-wheel*.py'),('scripts','*converter-four-wheel*.mjs'),('outputs','converter-four-wheel-*'),('work/transmission','converter-four-wheel-*.log'),('outputs/converter-browser-evidence','*')]:
    files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/directory).glob(pattern)) if p.is_file())
files+=['work/reference-docs/transmission/'+n for n in ['009.htm','000-3024.jpg','catalog-converter-pump-reactors.gif','catalog-converter-016.txt','converter-assembly-findings.json']]
assert len(files)==len(set(files))
for name in files:assert (ROOT/name).is_file(),name
assert not target.exists(),'Preserve existing archives'
target.mkdir(parents=True);manifest=[]
for name in files:
    src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);content=src.read_bytes();assert dst.read_bytes()==content
    manifest.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
report={'stage':'Four-wheel converter assembly with native/export/browser inspection','wholeGoal':'active; all 16 gates OPEN',
        'status':'180 fitted solids and app controls checked. Fluid/contact/lockup dynamics, factory fidelity, installation and main-scene performance incomplete.',
        'files':manifest,'fileCount':len(manifest),'totalBytes':sum(r['bytes'] for r in manifest)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
