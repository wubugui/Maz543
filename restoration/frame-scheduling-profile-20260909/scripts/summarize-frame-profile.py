from pathlib import Path
import json,statistics
root=Path(__file__).resolve().parents[1];folder=root/'outputs/frame-profile';rows=[]
def stats(values):return {'min':min(values),'median':statistics.median(values),'max':max(values)}
for path in sorted(folder.glob('*.json')):
 data=json.loads(path.read_text(encoding='utf8'))
 if data.get('kind')!='render-thread-wall-time':continue
 samples=data['samples'];gaps=[b['startMs']-a['startMs'] for a,b in zip(samples,samples[1:])]
 row={'file':path.name,'samples':len(samples),'focus':list(dict.fromkeys(s['focus'] for s in samples)),'mode':list(dict.fromkeys(s['mode'] for s in samples)),
 'frameSource':list(dict.fromkeys(s.get('frameSource','main-thread-bridge (original capture)') for s in samples)),
 'milliseconds':{key:stats([s[key] for s in samples]) for key in ['updateMs','queryPollMs','cacheMs','submitMs','frameWorkMs']},
 'frameStartGapMs':stats(gaps),'drawCalls':list(dict.fromkeys(s['drawCalls'] for s in samples)),'triangles':list(dict.fromkeys(s['triangles'] for s in samples)),
 'renderedFrames':sum(s['rendered'] for s in samples),'maxReportedSimulationBacklog':max(s['simulationBacklog'] for s in samples),'gpuTimersAvailable':any(s['gpuMs'] is not None for s in samples)}
 rows.append(row)
 ages=[s['stateAgeAtUpdateMs'] for s in samples if s.get('stateAgeAtUpdateMs') is not None]
 if ages:row['stateAgeAtUpdateMs']=stats(ages)
report={'rows':rows,'limits':'Finite same-application captures, not a controlled GPU benchmark. Frame start gaps include presentation and scheduling delays. Do not subtract clocks with different time origins or infer GPU duration from submission time.'}
(folder/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
