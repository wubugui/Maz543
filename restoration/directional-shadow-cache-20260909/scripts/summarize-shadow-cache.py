from pathlib import Path
import json, statistics

root=Path(__file__).resolve().parents[1]
folder=root/'outputs/directional-shadow-cache'
summary={}
for name in ['whole-still','whole-side','whole-door','whole-suspension','whole-section','phase-baseline','phase-cached']:
    text=(folder/(name+'-ax.txt')).read_text(encoding='utf-8')
    start=text.index('text {')+5
    data,_=json.JSONDecoder().raw_decode(text[start:])
    (folder/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    if name.startswith('whole-'):
        assert data['differentPixels']==0 and data['optimizedReadbackError']==0 and data['baselineReadbackError']==0
        summary[name]={key:data[key] for key in ['shadowCache','baseline','optimized','differentPixels']}
    else:
        samples=data['samples'];assert len(samples)==12 and all(s['rendered'] for s in samples)
        gaps=[b['startMs']-a['startMs'] for a,b in zip(samples,samples[1:])]
        summary[name]={'sampleCount':len(samples),'meanStartGapMs':statistics.mean(gaps),'medianStartGapMs':statistics.median(gaps),
            'meanSubmitMs':statistics.mean(s['submitMs'] for s in samples),'meanUpdateMs':statistics.mean(s['updateMs'] for s in samples),
            'drawCalls':sorted(set(s['drawCalls'] for s in samples)),'triangles':sorted(set(s['triangles'] for s in samples)),
            'maxSimulationBacklog':max(s['simulationBacklog'] for s in samples)}
summary['limits']='Sequential 12-frame samples of forced complete rendering at fixed pose, same worker/native RAF and diagnostic overhead. Not a randomized benchmark or ordinary static-cache FPS. Pixel pairs are separate and include readback.'
(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
