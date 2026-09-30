from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/partitioned-shadow'
results={}
for path in sorted(folder.glob('whole-*-ax.txt')):
    text=path.read_text(encoding='utf8');start=text.index('{\n  "gpu"')
    data,_=json.JSONDecoder().raw_decode(text[start:])
    name=path.name.removesuffix('-ax.txt');results[name]=data
    (folder/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
(folder/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for name,row in results.items():
    print(json.dumps({'name':name,'partition':row['partitionedShadow'],'candidate':row['optimized'],'baseline':row['baseline'],'differentPixels':row['differentPixels'],'errors':[row['optimizedReadbackError'],row['baselineReadbackError']]},ensure_ascii=False))
