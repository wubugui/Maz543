from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'outputs/render-performance-evidence'
audits={}
for name in ['shadow-audit','instance-initial','instance-door','batch-initial','batch-warm']:
    text=(folder/f'{name}-ax.txt').read_text(encoding='utf8')
    start=text.index('{\n  "gpu"')
    audits[name]=json.JSONDecoder().raw_decode(text[start:])[0]
assets={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (ROOT/'public/models').glob('*.glb') if p.stem in ['maz543a-blender','d12a525a-engine','maz543a-suspension','maz543a-starting','maz543a-cooling','maz543a-cardan','maz543a-transmission']}
report={'wholeGoal':'ACTIVE; all 16 gates OPEN',
 'enabled':['One shadow update per rendered frame','Exact visible-presentation invalidation','Exact-angle torsion buffer reuse','Elapsed-time camera easing','Explicit native texture/late-load/shadow-target cleanup'],
 'experimentalOnly':['DisplayInstances: inspect=instance-audit','DisplayBatches: inspect=batch-audit'],
 'audits':audits,'currentNativeAssetHashes':assets,
 'limits':['Full-vehicle software rendering remains slow. No frame-rate acceptance.',
 'Batch warm readback was 1546.8 ms vs 1553.5 ms baseline; insufficient benefit for 392645360 additional buffer bytes.',
 'Batch and instance pixels are not identical; neither enabled by default.',
 'Frame cache uses exact comparisons; continuous motion, including tiny body movement, correctly invalidates it.',
 'Existing mechanical timestep cap remains: physics still follows RAF with maximum 0.05 seconds. Separate accurate simulation scheduling remains to be done.',
 'chrome://gpu was blocked by browser security policy; no attempt to bypass. No OS, driver or Codex settings changed.']}
(ROOT/'outputs/render-performance-results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps({'audits':list(audits),'assets':len(assets)},ensure_ascii=False))
