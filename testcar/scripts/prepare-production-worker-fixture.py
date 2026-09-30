from pathlib import Path
import hashlib,json,shutil,urllib.request
root=Path(__file__).resolve().parents[1];folder=root/'public/__worker-validation';out=root/'outputs/production-worker-acceptance';out.mkdir(parents=True,exist_ok=True)
names=[]
for pattern in ['viewport.worker-*.js','mechanics.worker-*.js']:
 matches=list((root/'dist/client/_next/static').glob(pattern));assert len(matches)==1,(pattern,matches);names.append(matches[0].name)
rows=[]
folder.mkdir(exist_ok=True)
for name in names:
 source=root/'dist/client/_next/static'/name;dest=folder/name;data=source.read_bytes()
 if dest.exists():assert dest.read_bytes()==data,'Never overwrite a different fixture'
 else:shutil.copy2(source,dest)
 assert dest.read_bytes()==data
 url='http://localhost:3000/__worker-validation/'+name
 with urllib.request.urlopen(url,timeout=30) as response:
  served=response.read();assert served==data,'HTTP response must equal the compiled artifact'
  rows.append({'file':str(source.relative_to(root)),'fixture':str(dest.relative_to(root)),'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'httpStatus':response.status,'contentType':response.headers.get('Content-Type'),'httpByteEqual':True})
report={'kind':'exact-production-worker-fixtures','passed':True,'files':rows,'limits':'Byte-exact serving verified. Actual browser execution and product interactions still required. Same existing localhost:3000; no server/port/settings changes.'}
(out/'fixture-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
source="import type {RenderWorkerFactories} from './renderWorkerClient';\n\n/** Generated DEV acceptance entry; the script verifies actual HTTP bytes. */\nexport const productionWorkerFixture:RenderWorkerFactories={\n render:()=>new Worker('/__worker-validation/"+names[0]+"',{name:'MAZ production render acceptance'}),\n mechanics:()=>new Worker('/__worker-validation/"+names[1]+"',{name:'MAZ production mechanics acceptance'}),\n};\nexport const productionWorkerFixtureIdentity="+json.dumps(' + '.join(names))+";\n"
(root/'lib/productionWorkerFixture.ts').write_text(source,encoding='utf8')
