from pathlib import Path
import json,statistics
root=Path(__file__).resolve().parents[1];folder=root/'outputs/normal-occlusion-cache'
rows=[]
for name in ['still','engine','side-door','section','final-still']:
 raw=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));data=raw.get('audit',raw);cache=data['normalOcclusion']
 assert data['differentPixels']==0 and data['maxChannelDifference']==0 and data['identicalPixels'],name
 assert data['optimizedReadbackError']==0 and data['baselineReadbackError']==0,name
 assert not cache['error'] and not cache['controlsFailed'],name
 assert not cache['rebuilt'],name
 query_draws=cache['queried']+2 if cache['queried'] else 0
 assert data['optimized']['calls']==data['baseline']['calls']-cache['skipped']+query_draws,name
 assert data['optimized']['triangles']==data['baseline']['triangles']-cache['savedTriangles']+2*query_draws,name
 assert (cache['skipped']==0 if name=='section' else cache['skipped']>1000),name
 rows.append({'file':name+'.json','pixelsDifferent':data['differentPixels'],'baseline':data['baseline'],'candidate':data['optimized'],'cache':cache})
profiles=[]
for name in ['side-door-12frames','baseline-side-door-12frames']:
 raw=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));samples=raw['samples'];assert len(samples)==12
 assert all(row['simulationBacklog']==0 for row in samples)
 assert all(row['frameSource']=='native-worker' and row['rendered'] for row in samples)
 gaps=[b['startMs']-a['startMs'] for a,b in zip(samples,samples[1:])]
 caches=[row.get('normalOcclusion') for row in samples if row.get('normalOcclusion')]
 if caches:assert all(not r['error'] and not r['controlsFailed'] and not r['rebuilt'] and r['skipped']>1000 for r in caches)
 profiles.append({'file':name+'.json','frames':len(samples),'meanWorkMs':statistics.mean(r['frameWorkMs'] for r in samples),'meanFrameGapMs':statistics.mean(gaps),'meanSubmitMs':statistics.mean(r['submitMs'] for r in samples),'meanCalls':statistics.mean(r['drawCalls'] for r in samples),'meanTriangles':statistics.mean(r['triangles'] for r in samples),'meanPreparationMs':statistics.mean(r['prepareMs'] for r in caches) if caches else None,'skipRange':[min(r['skipped'] for r in caches),max(r['skipped'] for r in caches)] if caches else None,'totalQueries':sum(r['queried'] for r in caches),'backlogZero':True})
result={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'pairs':rows,'profiles':profiles,'limits':'Exact normal-material camera pass only. Source assets, main color, transmission, shadow passes and mechanics retained. Five same-pose pairs establish only tested pixel equality. Sequential 12-frame profiles are not randomized or identical-pose benchmarks, and do not establish final product performance. Default OFF.'}
(folder/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'passed':True,'profiles':profiles},ensure_ascii=False,indent=2))
