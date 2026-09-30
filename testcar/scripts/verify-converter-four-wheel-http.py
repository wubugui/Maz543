"""Check localhost serves the exact verified native export and new route."""
from pathlib import Path
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parents[1];rows=[]
for relative in ['models/maz543a-converter-assembly.glb','models/maz543a-converter-assembly.json']:
    with urllib.request.urlopen('http://localhost:3000/'+relative,timeout=30) as response:
        content=response.read();assert response.status==200
    expected=(ROOT/'public'/relative).read_bytes();assert content==expected
    rows.append({'path':relative,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
with urllib.request.urlopen('http://localhost:3000/converter',timeout=30) as response:
    html=response.read().decode('utf8');assert response.status==200
assert '变矩器内部总成' in html and '轴向拆开' in html
report={'assets':rows,'route':'/converter','headingPresent':True,'limits':'HTTP byte equality and server-rendered markup. Actual WebGL and interactions are checked separately.'}
(ROOT/'outputs/converter-four-wheel-http.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
