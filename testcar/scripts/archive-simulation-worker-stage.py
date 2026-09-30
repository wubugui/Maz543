from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];target=ROOT.parent/'restoration/simulation-clock-worker-20260909'
files=['AGENT_START_HERE.md','NEXT_AGENT_PROMPT.md','docs/CONTINUATION_20260908.md','docs/ACCEPTANCE.md',
 'docs/SIMULATION_DISPLAY_SCHEDULING_20260909.md','docs/PERFORMANCE_CAD_DISPLAY_20260908.md',
 'components/vehicle-viewer.tsx','components/workshop.tsx','lib/mechanics.ts','lib/mechanicalTimeline.ts','lib/mechanics.worker.ts',
 'lib/starting.ts','lib/suspension.ts','lib/transmission.ts','lib/transmissionDynamics.ts','lib/transmissionHydraulics.ts','lib/cooling.ts',
 'lib/compositedShadows.ts','lib/displayFrameCache.ts','lib/renderResources.ts','types/worker.d.ts',
 'scripts/verify-mechanical-timeline.mjs','scripts/mechanics-worker-node.mjs','scripts/archive-simulation-worker-stage.py',
 'work/simulation-worker-types.log','work/simulation-worker-build.log','work/simulation-worker-test.log']
files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'outputs/simulation-worker-evidence').glob('*')) if p.is_file())
files.extend(str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'dist/client').rglob('mechanics.worker-*.js')))
assert len(files)==len(set(files));assert not target.exists()
for name in files:assert (ROOT/name).is_file(),name
target.mkdir(parents=True);rows=[]
for name in files:
 src=ROOT/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);b=src.read_bytes();assert dst.read_bytes()==b
 rows.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
report={'stage':'Independent fixed-step mechanical clock','wholeGoal':'ACTIVE; all 16 gates OPEN','status':'Browser Worker and fixed-step tests passed; rendering remains slow and full physical fidelity unaccepted','files':rows,'fileCount':len(rows),'totalBytes':sum(r['bytes'] for r in rows)}
(target/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'directory':str(target),'fileCount':report['fileCount'],'totalBytes':report['totalBytes']},indent=2))
