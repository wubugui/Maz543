from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'restoration/cad-display-performance-20260908'
files=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
 'docs/PERFORMANCE_CAD_DISPLAY_20260908.md','components/vehicle-viewer.tsx','components/workshop.tsx',
 'lib/compositedShadows.ts','lib/displayInstances.ts','lib/displayBatches.ts','lib/displayFrameCache.ts','lib/renderResources.ts',
 'lib/mechanics.ts','lib/export-model.ts','scripts/inventory-render-assets.py','scripts/verify-display-presentation.mjs',
 'scripts/summarize-render-performance.py','scripts/archive-render-performance-stage.py',
 'outputs/render-asset-inventory.json','outputs/render-performance-results.json','work/render-performance-build.log']
files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'outputs/render-performance-evidence').glob('*')) if p.is_file())
assert len(files)==len(set(files))
for name in files:assert (ROOT/name).is_file(),name
assert not target.exists(),'Preserve previous immutable checkpoint'
target.mkdir(parents=True);manifest=[]
for name in files:
    src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    content=src.read_bytes();assert dst.read_bytes()==content
    manifest.append({'path':name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
report={'stage':'CAD presentation optimization and software-rendering evidence','wholeGoal':'ACTIVE; all 16 gates OPEN',
 'status':'Safe shadow/cache/lifecycle improvements enabled. Full-vehicle dynamic performance not accepted. Experimental batching disabled by default.',
 'files':manifest,'fileCount':len(manifest),'totalBytes':sum(r['bytes'] for r in manifest)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
