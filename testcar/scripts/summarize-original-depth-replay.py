from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];folder=root/'outputs/original-pass-depth-replay';measurements=[]
for name in ['still-queries','engine-queries','side-door-queries']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));raw=json.loads((folder/(name+'-raw.json')).read_text(encoding='utf8'))
 replay=data['originalDepthReplay'];query=data['depthQueries'];results=raw['results']
 assert data['differentPixels']==0 and data['maxChannelDifference']==0 and data['identicalPixels'],name
 assert data['optimizedReadbackError']==0 and data['baselineReadbackError']==0,name
 assert not replay['errors'] and replay['programMismatches']==0 and replay['matrixMismatches']==0,name
 assert replay['programMatches']==replay['recordedDraws']==replay['replayedDraws'],name
 assert [p['actualSamples'] for p in replay['passes']]==[4,2,0],name
 assert all(p['actualDepthBits']==24 and p['originalDepthBits']==24 for p in replay['passes']),name
 assert query['controlsPassed'] and query['queryError']==0 and raw['summary']==query,name
 assert [p['samples'] for p in query['passes']]==[4,2,0]
 for i,p in enumerate(query['passes']):
  controls=[r for r in results if r['pass']==i and 'controlExpected' in r]
  volumes=[r for r in results if r['pass']==i and 'controlExpected' not in r];zero=[r for r in volumes if not r['anySamplesPassed']]
  assert len(controls)==2 and all(r['anySamplesPassed']==r['controlExpected'] for r in controls)
  assert len(volumes)==p['queried'] and len(zero)==p['zeroVolumes']
  assert sum(r['triangles'] for r in zero)==p['zeroTriangles']
  assert sum(not r['stable'] for r in zero)==p['movingZeroVolumes']
 extra_query_draws=len(results)+query['initializationDraws']
 assert data['optimized']['calls']==data['baseline']['calls']+replay['replayedDraws']+extra_query_draws,name
 assert data['optimized']['triangles']==data['baseline']['triangles']+replay['replayedTriangles']+extra_query_draws*2,name
 if name=='side-door-queries':assert replay['threeRevision']=='183'
 measurements.append({'file':name+'.json','eligibleStaticMeshes':replay['eligibleMeshes'],'programMatches':replay['programMatches'],'pixelsDifferent':data['differentPixels'],'queryPasses':query['passes'],'baseline':data['baseline'],'diagnostic':data['optimized']})
failed=json.loads((folder/'still-query-uninitialized-geometry-raw.json').read_text(encoding='utf8'))
assert failed['summary']['controlsPassed'] is False
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'measurements':measurements,'rejectedSample':'still-query-uninitialized-geometry-raw.json','limits':'Finite actual original-program depth replay plus conservative occlusion potential only. No product draw skipped, no cross-frame cache validity or steady-state FPS gain established. Controls rejected the uninitialized query-geometry attempt.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'passed':True,'measurements':len(measurements),'goal':'ACTIVE','wholeVehicleGates':'16 OPEN'},ensure_ascii=False))
