"""Copy the reviewed strip study stage into an immutable local evidence snapshot."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT.parent/'restoration/converter-strip-source-correction-20260908'
files=[
 'AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
 'docs/CONVERTER_STRIP_SOURCE_CORRECTION_20260908.md',
 'components/strip-spring-study.tsx','components/freewheel-bench.tsx','components/freewheel-bench.module.css','app/strip-spring/page.tsx',
 'scripts/blender-d12.py','scripts/converter_strip_spring.py','scripts/converter_strip_mesh.py','scripts/converter_strip_mount.py',
 'scripts/diagnose-converter-strip-spring.py','scripts/verify-converter-strip-formulation.py',
 'scripts/build-converter-strip-study.py','scripts/verify-converter-strip-native.py','scripts/render-converter-strip-study.py',
 'scripts/export-converter-strip-study.py','scripts/verify-converter-strip-browser.mjs','scripts/verify-converter-strip-mount.py',
 'scripts/verify-converter-strip-http.py','scripts/archive-converter-strip-stage.py',
 'work/freewheel-contact/strip-spring-study.json','work/freewheel-contact/strip-browser-reference.bin',
 'outputs/MAZ543A_Converter_CurvedStripStudy.blend',
 'public/models/maz543a-strip-study.glb','public/models/maz543a-strip-study.json']
files += ['work/reference-docs/transmission/'+n for n in ['009.htm','000-0687.jpg','000-3024.jpg','catalog-converter-016.htm','catalog-converter-016.txt',
 'catalog-converter-assembly.gif','catalog-converter-pump-reactors.gif','converter-assembly-findings.json','converter-assembly-source-index.json']]
files += ['outputs/'+n for n in ['converter-strip-formulation.json','converter-strip-native-verification.json','converter-strip-browser-verification.json',
 'converter-strip-mount-verification.json','converter-strip-http-verification.json',
 'converter-curved-strip-preloaded.png','converter-curved-strip-compressed.png','converter-curved-strip-limit-study.png']]
files += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'outputs/strip-browser-evidence').iterdir()) if p.is_file()]
files += ['work/transmission/'+n for n in ['converter-strip-spring.log','converter-strip-formulation.log','converter-strip-native-build.log',
 'converter-strip-native-verification.log','converter-strip-render.log','converter-strip-export.log','converter-strip-browser-verification.log',
 'converter-strip-browser-build.log','converter-strip-mount-verification.log','converter-strip-http-verification.log','converter-source-correction-build.log']]
assert len(files)==len(set(files))
for name in files:assert (ROOT/name).is_file(),name
assert not TARGET.exists(),'Archive already exists; do not overwrite an earlier evidence snapshot'
TARGET.mkdir(parents=True)
manifest=[]
for name in files:
    source=ROOT/name;dest=TARGET/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    content=source.read_bytes();assert dest.read_bytes()==content
    manifest.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
report={'stage':'Source correction, curved-strip study, static browser viewer and moving-mount force interface',
 'wholeGoal':'active; all 16 whole-vehicle gates OPEN','files':manifest,'fileCount':len(manifest),'totalBytes':sum(r['bytes'] for r in manifest)}
(TARGET/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(TARGET),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
