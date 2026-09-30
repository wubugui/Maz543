from pathlib import Path
import json,statistics
root=Path(__file__).resolve().parents[1];folder=root/'outputs/triangle-range-occlusion';measurements=[]
for name in ['still','engine','side-door','section']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));cache=data['originalOcclusion']
 assert data['differentPixels']==data['maxChannelDifference']==0 and data['identicalPixels'],name
 assert data['optimizedReadbackError']==data['baselineReadbackError']==0 and not cache['error'],name
 assert data['baseline']['calls']-data['optimized']['calls']==cache['skipped'],name
 assert data['baseline']['triangles']-data['optimized']['triangles']==cache['savedTriangles'],name
 if name!='section':
  assert cache['ready'] and cache['rangeMode'] and cache['rangeSavedTriangles']>0 and cache['rangeProxyBytes']>0,name
  assert cache['depthControls']['controlsPassed'] and cache['depthControls']['queryError']==0,name
  assert [p['samples'] for p in cache['passes']]==[4,2,0]
  assert sum(p['skipped'] for p in cache['passes'])==cache['skipped']
  assert sum(p['savedTriangles'] for p in cache['passes'])==cache['savedTriangles']
  assert all(p['rangeQueried']>0 and p['zeroCountsOverlap'] for p in cache['depthControls']['passes'])
 else:assert cache['skipped']==cache['savedTriangles']==0
 measurements.append({'file':name+'.json','skippedNetCalls':cache['skipped'],'savedTriangles':cache['savedTriangles'],'additionalRangeSavedTriangles':cache['rangeSavedTriangles'],'rangeSourceDraws':cache['rangeSourceDraws'],'rangeSubmittedDraws':cache['rangeSubmittedDraws'],'rangeProxyBytes':cache['rangeProxyBytes'],'differentPixels':data['differentPixels'],'baseline':data['baseline'],'candidate':data['optimized']})
profiles=[];sources=[];gpus=[]
for name in ['engine-range-profile','engine-whole-profile']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));rows=data['samples'];assert len(rows)==12,name
 assert all(row['simulationBacklog']==0 and row['originalOcclusion']['ready'] and not row['originalOcclusion']['error'] for row in rows),name
 assert all(row['originalOcclusion']['rangeMode']==(name=='engine-range-profile') for row in rows)
 sources.append(set(row['frameSource'] for row in rows));gpus.append(set(row['gpu'] for row in rows))
 gaps=[b['startMs']-a['startMs'] for a,b in zip(rows,rows[1:])]
 profiles.append({'file':name+'.json','frames':len(rows),'meanFrameGapMs':statistics.mean(gaps),'medianFrameGapMs':statistics.median(gaps),'meanWorkMs':statistics.mean(row['frameWorkMs'] for row in rows),'callsRange':[min(row['drawCalls'] for row in rows),max(row['drawCalls'] for row in rows)],'trianglesRange':[min(row['triangles'] for row in rows),max(row['triangles'] for row in rows)],'rangeSavedTrianglesRange':[min(row['originalOcclusion']['rangeSavedTriangles'] for row in rows),max(row['originalOcclusion']['rangeSavedTriangles'] for row in rows)],'allBacklogZero':True})
assert sources[0]==sources[1] and gpus[0]==gpus[1]
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'measurements':measurements,'profiles':profiles,'limits':'DEV-only exact original triangle-range submission reuse. Sequential finite samples, not universal performance or default enable acceptance. Complete geometry, original element order, materials and mechanical solver retained; usable preview and full product fidelity unfinished.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
