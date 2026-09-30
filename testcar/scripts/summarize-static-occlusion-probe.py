from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];folder=root/'outputs/static-occlusion-probe'
rows=[]
for name in ['still-loose-depth','still-correlated','engine-correlated','side-door-correlated']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'))
 assert data['controlsPassed'] and data['displayDifferentPixels']==0,name
 assert data['beforeReadbackError']==0 and data['afterReadbackError']==0,name
 assert [p['actualSamples'] for p in data['passes']]==[4,2,0],name
 assert all(p['depthBits']==24 for p in data['passes']),name
 for p in data['visibility']:
  actual=[r for r in data['results'] if r['samples']==p['requestedSamples'] and not r.get('control')]
  zero=[r for r in actual if not r['anySamplesPassed']]
  assert len(actual)==p['queried'] and len(zero)==p['zeroVolumes']
  assert sum(r['triangles'] for r in zero)==p['zeroVolumeTriangles']
 rows.append({'file':name+'.json','bounds':data.get('boundsMode','independent-z-w'),'stableOccluders':data['stableOccluders'],'movingOrNew':data['movingOrNew'],'passes':data['passes'],'visibility':data['visibility'],'submitMs':data['snapshotAndQuerySubmitMs'],'displayDifferentPixels':data['displayDifferentPixels'],'controlsPassed':data['controlsPassed']})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','passed':True,'measurements':rows,'limits':'Finite isolated snapshot potential only. No actual product draw was skipped, no dynamic FPS improvement or cross-frame proof reuse established.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'passed':True,'measurements':len(rows),'goal':'ACTIVE','wholeVehicleGates':'16 OPEN'}))
