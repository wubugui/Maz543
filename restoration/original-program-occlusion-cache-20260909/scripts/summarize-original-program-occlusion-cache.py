from pathlib import Path
import json,statistics
root=Path(__file__).resolve().parents[1];folder=root/'outputs/original-program-occlusion-cache'
measurements=[]
for name in ['still','engine','side-door','section']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));cache=data['originalOcclusion']
 assert data['identicalPixels'] and data['differentPixels']==0 and data['maxChannelDifference']==0,name
 assert data['optimizedReadbackError']==data['baselineReadbackError']==0,name
 assert data['baseline']['calls']-data['optimized']['calls']==cache['skipped'],name
 assert data['baseline']['triangles']-data['optimized']['triangles']==cache['savedTriangles'],name
 assert not cache['error'],name
 if name!='section':
  assert cache['ready'] and cache['depthControls']['controlsPassed'] and cache['depthControls']['queryError']==0,name
  assert [p['samples'] for p in cache['passes']]==[4,2,0]
  assert sum(p['skipped'] for p in cache['passes'])==cache['skipped']
  assert sum(p['savedTriangles'] for p in cache['passes'])==cache['savedTriangles']
 else:assert cache['skipped']==0
 measurements.append({'file':name+'.json','skipped':cache['skipped'],'savedTriangles':cache['savedTriangles'],'differentPixels':data['differentPixels'],'baseline':data['baseline'],'candidate':data['optimized']})
profiles=[]
for name in ['engine-profile','engine-baseline-profile']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));rows=data['samples'];assert len(rows)==12,name
 assert all(row['simulationBacklog']==0 for row in rows),name
 gaps=[b['startMs']-a['startMs'] for a,b in zip(rows,rows[1:])]
 profiles.append({'file':name+'.json','frames':len(rows),'meanFrameGapMs':statistics.mean(gaps),'medianFrameGapMs':statistics.median(gaps),'meanWorkMs':statistics.mean(r['frameWorkMs'] for r in rows),'callsRange':[min(r['drawCalls'] for r in rows),max(r['drawCalls'] for r in rows)],'skippedRange':[min((r.get('originalOcclusion') or {}).get('skipped',0) for r in rows),max((r.get('originalOcclusion') or {}).get('skipped',0) for r in rows)],'allBacklogZero':True})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'measurements':measurements,'profiles':profiles,'limits':'DEV-only candidate; finite actual pixel pairs and consecutive profile windows. Full mechanical fidelity and usable dynamic performance remain unfinished. No quality or mechanical computation reduction.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
