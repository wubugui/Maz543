from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];folder=root/'outputs/ordered-batches';summary={}
for path in sorted(folder.glob('whole-*-ax.txt')):
    text=path.read_text(encoding='utf-8');start=text.index('text {')+5
    report,_=json.JSONDecoder().raw_decode(text[start:]);name=path.name.removesuffix('-ax.txt')
    (folder/(name+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    summary[name]={key:report[key] for key in ['displayInstances','geometryCopy','baseline','optimized','differentPixels','maxChannelDifference','optimizedReadbackError','baselineReadbackError']}
summary['limits']='Each paired capture uses identical pose and original complete scene, candidate before baseline. Initial captures include shader compilation and every synchronized time includes readback. No steady-state FPS claim.'
(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
