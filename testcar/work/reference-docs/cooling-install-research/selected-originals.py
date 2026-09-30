from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request
from PIL import Image
OUT=Path(__file__).resolve().parent
index=json.loads((OUT/'primeportal-source-index.json').read_text())
selected={'171','174','175','177','180','181','182','183'}
(OUT/'originals').mkdir(exist_ok=True)
def one(r):
    path=OUT/'originals'/f'{r["number"]}.jpg'
    result={'number':r['number'],'url':r['originalUrl'],'path':str(path.relative_to(OUT))}
    try:
        if not path.exists():
            with urllib.request.urlopen(r['originalUrl'],timeout=30) as res:
                data=res.read()
            if not data.startswith(b'\xff\xd8'): raise ValueError('Not JPEG')
            path.write_bytes(data)
        with Image.open(path) as im: result['size']=im.size; im.verify()
        result['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception as exc:result['error']=str(exc)
    print(json.dumps(result),flush=True)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records=list(pool.map(one,[r for r in index['records'] if r['number'] in selected]))
(OUT/'selected-originals-index.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
