"""Archive current surface-contact mechanics with its failed trials and limitations."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'restoration/converter-strip-surface-contact-20260908'
files=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
       'docs/CONVERTER_STRIP_SURFACE_CONTACT_20260908.md','docs/CONVERTER_STRIP_POCKET_CONTACT_20260908.md',
       'docs/CONVERTER_STRIP_SOURCE_CORRECTION_20260908.md',
       'outputs/MAZ543A_Converter_CurvedStripStudy.blend','outputs/MAZ543A_Converter_StripSurfaceStudy.blend',
       'outputs/MAZ543A_Converter_StripSurfaceStudy.first-readback-failed.blend',
       'work/reference-docs/transmission/000-0687.jpg','work/reference-docs/transmission/catalog-converter-pump-reactors.gif',
       'work/reference-docs/transmission/converter-assembly-findings.json']
for directory,pattern in [('scripts','*strip*.py'),('outputs','converter-strip-*.json'),('outputs','converter-surface-strip-*.png'),
                          ('work/freewheel-contact','strip-*.json'),('work/transmission','converter-strip-*.log')]:
    files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/directory).glob(pattern)) if p.is_file())
assert len(files)==len(set(files))
for name in files:assert (ROOT/name).is_file(),name
assert not target.exists(),'Do not overwrite a stage archive'
target.mkdir(parents=True);manifest=[]
for name in files:
    source=ROOT/name;destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
    content=source.read_bytes();assert destination.read_bytes()==content
    manifest.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
report={'stage':'Full ribbon/roller surface contact, saved static study, and incomplete integration diagnostics',
        'wholeGoal':'active; all 16 gates OPEN',
        'status':'38 saved static states checked; fitted stress reaches 9.364 GPa. Continuous run incomplete after 1.187 s. Polar excess energy and Cartesian step-dependent dissipation unresolved.',
        'files':manifest,'fileCount':len(manifest),'totalBytes':sum(r['bytes'] for r in manifest)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
