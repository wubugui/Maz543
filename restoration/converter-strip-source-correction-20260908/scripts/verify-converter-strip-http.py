"""Verify the running local preview serves the exact reviewed study assets."""
from pathlib import Path
import urllib.request,hashlib,json
ROOT=Path(__file__).resolve().parents[1];rows=[]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for name in ['maz543a-strip-study.glb','maz543a-strip-study.json']:
    with opener.open('http://localhost:3000/models/'+name,timeout=20) as response:
        data=response.read();status=response.status
    assert status==200 and data==(ROOT/'public/models'/name).read_bytes()
    rows.append({'file':name,'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'matchesLocal':True})
with opener.open('http://localhost:3000/strip-spring',timeout=20) as response:
    page=response.read().decode('utf8');assert response.status==200 and '弯带弹簧接触' in page
report={'assets':rows,'pageStatus':200,'headingPresent':True,'limits':'HTTP provenance check; actual interaction evidence is stored separately.'}
(ROOT/'outputs/converter-strip-http-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
