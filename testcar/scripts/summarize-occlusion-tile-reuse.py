from pathlib import Path
import json,statistics
root=Path(__file__).resolve().parents[1];folder=root/'outputs/occlusion-tile-reuse'
profile=json.loads((folder/'engine-12frames.json').read_text(encoding='utf8'));samples=profile['samples'];assert len(samples)==12
pairs=[]
for name in ['warm-verified','engine-verified','side-door-pair','first-gear-pair','section-pair','post-budget-pair']:
 data=json.loads((folder/(name+'.json')).read_text(encoding='utf8'));assert data['differentPixels']==0 and data['optimizedReadbackError']==0 and data['baselineReadbackError']==0,name
 pairs.append({'file':name+'.json','skipped':data['occlusionPrefix']['skipped'],'savedTriangles':data['occlusionPrefix']['savedTriangles'],'differentPixels':data['differentPixels'],'candidate':data['optimized'],'baseline':data['baseline']})
report={'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','pairs':pairs,'engineProfile':{'frames':len(samples),'meanFrameWorkMs':statistics.mean(s['frameWorkMs'] for s in samples),'meanStartGapMs':statistics.mean(b['startMs']-a['startMs'] for a,b in zip(samples,samples[1:])),'skippedRange':[min(s['occlusionPrefix']['skipped'] for s in samples),max(s['occlusionPrefix']['skipped'] for s in samples)],'queryTotal':sum(s['occlusionPrefix']['queried'] for s in samples),'epochResets':sum(s['occlusionPrefix']['epochReset'] for s in samples),'maxBacklogSeconds':max(s['simulationBacklog'] for s in samples),'maxPrefixNodes':max(s['occlusionPrefix']['prefixNodes'] for s in samples)},'limits':'Finite diagnostic samples, not sustained performance acceptance. Paired readbacks are synchronized; 12-frame profile contains no readback and has no contemporaneous baseline series. Exact model/display/solver precision retained, optimization remains default OFF.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
