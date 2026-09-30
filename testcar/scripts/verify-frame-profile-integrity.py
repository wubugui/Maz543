from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];base=ROOT.parent/'restoration/render-worker-and-blob-20260909'
rows=[]
for name in ['mechanics','starting','suspension','transmission','transmissionDynamics','transmissionHydraulics','cooling','mechanicalTimeline']:
 relative=f'lib/{name}.ts';current=(ROOT/relative).read_bytes();assert current==(base/relative).read_bytes(),relative
 rows.append({'file':relative,'sha256':hashlib.sha256(current).hexdigest(),'unchanged':True})
worker=(ROOT/'lib/mechanics.worker.ts').read_text(encoding='utf8')
worker=worker.replace('    // Transport age uses a shared epoch; never subtract unrelated worker clocks.\n    // This timestamp is metadata only and does not enter the mechanical solver.\n','')
worker=worker.replace('generation,publishedAtEpochMs:performance.timeOrigin+performance.now(),telemetry:','generation,telemetry:')
assert worker==(base/'lib/mechanics.worker.ts').read_text(encoding='utf8'),'Mechanical dispatch has unexpected changes beyond timestamp metadata'
report={'passed':True,'solverFiles':rows,'mechanicalDispatchOnlyChange':'Outer message timestamp and explanatory comments; solver, publication frequency and two-channel equality unchanged.'}
(ROOT/'outputs/frame-profile/source-integrity.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('8 solver files unchanged; mechanical dispatch differs only by timestamp metadata.')
