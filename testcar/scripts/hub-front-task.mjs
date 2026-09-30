import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
const base='http://denghong01:8765',headers={'X-Hub-App-ID':'codex','X-Hub-Project-ID':'maz543a'};
const dir=process.argv[3]??'work/front-assembly-20260930';await fs.mkdir(dir,{recursive:true});
const recordPath=path.join(dir,'task-record.json');
const save=r=>fs.writeFile(recordPath,JSON.stringify(r,null,2));
async function call(route,opt={}){const r=await fetch(base+route,{...opt,headers:{...headers,...opt.headers},signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error(`${r.status} ${await r.text()}`);return r.json();}
let rec;try{rec=JSON.parse(await fs.readFile(recordPath,'utf8'));}catch{rec={idempotency_key:'maz-front-'+crypto.randomUUID()};await save(rec);}
if(process.argv[2]==='repair'){
 const id=rec.response.task_id??rec.response.task_ids[0],task=await call('/v1/tasks/'+id);
 if(task.state!=='failed')throw Error('Repair only a confirmed failed task');
 await fs.writeFile(path.join(dir,'failed-'+id+'.json'),JSON.stringify(rec,null,2));
 rec={idempotency_key:'maz-front-repair-'+crypto.randomUUID()};await save(rec);console.log('Repair record ready');
}else if(process.argv[2]==='submit'){
 const cfg=JSON.parse(await fs.readFile(path.join(dir,'config.json'),'utf8'));
 // Refresh the authorized Hub contract and readiness before each new job.
 for(const [i,route]of ['/health','/health/blender','/guide.md','/capabilities.json'].entries()){
  const response=await fetch(base+route,{headers,signal:AbortSignal.timeout(30000)});if(!response.ok)throw Error('Preflight '+route+' '+response.status);
  const body=await response.text();await fs.writeFile(path.join(dir,'preflight-'+i+'.txt'),body);
  if(route==='/health'&&JSON.parse(body).status!=='ok')throw Error('Hub is not healthy');
  if(route==='/health/blender'){const health=JSON.parse(body);if(health.status!=='ready'||!health.versions.some(v=>v.version==='4.5.13'&&v.available))throw Error('Required Blender version unavailable');}
 }
 if(!rec.script_file){
  const bytes=await fs.readFile(cfg.script),sha256=crypto.createHash('sha256').update(bytes).digest('hex');
  if(!rec.upload){rec.upload=await call('/v1/uploads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:path.basename(cfg.script),size:bytes.length,sha256})});await save(rec);}
  const id=rec.upload.upload_id??rec.upload.id,st=await call('/v1/uploads/'+id),offset=st.offset??0;
  if(offset<bytes.length)await call('/v1/uploads/'+id,{method:'PUT',headers:{'Content-Type':'application/octet-stream','Upload-Offset':String(offset)},body:bytes.subarray(offset)});
  rec.script_file=await call('/v1/uploads/'+id+'/complete',{method:'POST'});await save(rec);
 }
 if(!rec.body){rec.body={backend:'blender',name:cfg.name,priority:50,params:{version:'4.5.13',files:[...cfg.files,{file_id:rec.script_file.id,path:'main.py'}],script:'main.py',device:'cpu',threads:4,ram_mb:4096,timeout_seconds:900}};await save(rec);}
 if(!rec.response){rec.response=await call('/v1/tasks',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':rec.idempotency_key},body:JSON.stringify(rec.body)});await save(rec);}
 console.log(JSON.stringify(rec.response));
}else{
 const id=rec.response.task_id??rec.response.task_ids[0],task=await call('/v1/tasks/'+id);await fs.writeFile(path.join(dir,'task-result.json'),JSON.stringify(task,null,2));
 console.log(JSON.stringify({id,state:task.state,error:task.error,files:task.result?.files}));
 if(process.argv[2]==='download'&&task.state==='succeeded')for(const f of task.result.files){
  const dest=path.join(dir,f.relative_path);try{const b=await fs.readFile(dest);if(crypto.createHash('sha256').update(b).digest('hex')===f.sha256)continue;}catch{}
  const r=await fetch(base+f.url,{headers});if(!r.ok)throw Error(r.status);const b=Buffer.from(await r.arrayBuffer());
  if(b.length!==f.size||crypto.createHash('sha256').update(b).digest('hex')!==f.sha256)throw Error('Output hash mismatch');
  await fs.mkdir(path.dirname(dest),{recursive:true});await fs.writeFile(dest,b);console.log('verified '+f.relative_path);
 }
}
