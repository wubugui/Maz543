from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];folder=root/'outputs/render-target-timing';measurements=[]
for name in ['still','engine-side-door']:
 raw=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));data=raw.get('audit',raw);timing=data['targetTiming'];segments=timing['segments']
 assert data['gpuTimerAvailable'] is False and timing['gpuCompletionProven'] is False
 assert data['differentPixels']==0 and data['maxChannelDifference']==0 and data['identicalPixels']
 assert data['optimizedReadbackError']==0 and data['baselineReadbackError']==0 and timing['glError']==0
 assert data['optimized']['calls']==data['baseline']['calls']==sum(s['draws'] for s in segments)
 assert data['optimized']['triangles']==data['baseline']['triangles']==sum(s['triangles'] for s in segments)
 assert abs(sum(s['synchronizedMs'] for s in segments)-timing['attributedMs'])<1e-5
 assert abs(timing['captureMs']-timing['attributedMs']-timing['unattributedMs'])<1e-5
 assert -.001<=timing['unattributedMs']<max(10,timing['captureMs']*.01)
 phases={}
 for s in segments:
  assert abs(s['submitAndFinishReturnMs']+s['stateReadWaitMs']-s['synchronizedMs'])<1e-5
  if not s['draws']:phase='target-setup'
  elif 'shadow-depth-camera' in s['kinds']:phase='shadow-depth'
  elif 'vehicle-color' in s['kinds']:phase='transmission-prepass' if s['requestedSamples']==4 else 'main-color'
  elif 'vehicle-override' in s['kinds']:phase='normal-buffer'
  else:phase=' + '.join(s['materials'])
  row=phases.setdefault(phase,{'wallMs':0,'stateReadWaitMs':0,'draws':0,'triangles':0});row['wallMs']+=s['synchronizedMs'];row['stateReadWaitMs']+=s['stateReadWaitMs'];row['draws']+=s['draws'];row['triangles']+=s['triangles']
 measurements.append({'file':name+'.json','captureMs':timing['captureMs'],'unattributedMs':timing['unattributedMs'],'pixelDifferences':data['differentPixels'],'phases':phases})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'measurements':measurements,'limits':'Intrusive command/state round-trip wall time only. Chromium finish is Flush, GPU timer extension unavailable, and GPU completion not proven. No pass skipped; no FPS optimization claimed. Earlier incomplete-boundary sample is excluded.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
