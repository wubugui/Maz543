from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'outputs/occlusion-profile'
source=folder/'whole-actual-targets.json'
data=json.loads(source.read_text(encoding='utf8'))
assert data['kind']=='original-camera-pass-occlusion-query'
assert data['queryError']==0
passes=[]
for target in data['passes']:
 rows=[row for row in data['results'] if row['targetId']==target['id']]
 hidden=[row for row in rows if not row['anySamplesPassed']]
 assert len(rows)==target['draws'] and sum(row['triangles'] for row in rows)==target['triangles']
 assert len(hidden)==target['zeroSampleDraws']
 assert sum(row['triangles'] for row in hidden)==target['zeroSampleTriangles']
 passes.append({key:target[key] for key in ['id','kind','samples','actualSamples','viewport','draws','triangles','zeroSampleDraws','zeroSampleTriangles']})
 for entry in [passes[-1]]:entry['zeroSampleTriangleFraction']=target['zeroSampleTriangles']/target['triangles']
 passes[-1]['largestZeroSampleDraws']=sorted(hidden,key=lambda row:row['triangles'],reverse=True)[:12]
report={'passed':True,'source':source.name,'passes':passes,'queryError':data['queryError'],'drawsPreserved':True,'limits':data['limits']}
(folder/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
