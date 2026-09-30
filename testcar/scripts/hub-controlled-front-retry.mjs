// One authorized retry through the normal Hub endpoint. Persist before POST.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const dir='work/front-controlled-retry-20260930',base='http://denghong01:8765',prior='6e95834d-f419-495b-9e5b-9e6b9b561d87';
const headers={'X-Hub-App-ID':'codex','X-Hub-Project-ID':'maz543a'};
async function get(p){const r=await fetch(base+p,{headers,signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error(`${r.status} ${await r.text()}`);return r.json();}
await fs.mkdir(dir,{recursive:true});const p=dir+'/task-record.json';let rec;
try{rec=JSON.parse(await fs.readFile(p,'utf8'));}catch{rec={base_url:base,prior_task_id:prior,idempotency_key:'maz-authorized-front-retry-'+crypto.randomUUID(),authorization:'User replaces prior clearance prerequisite; one controlled normal retry after terminal/no-output/service checks',endpoint:'/v1/tasks/'+prior+'/retry'};await fs.writeFile(p,JSON.stringify(rec,null,2));}
if(rec.response){console.log(JSON.stringify(rec.response));process.exit(0);}
const [old,health,blender]=await Promise.all([get('/v1/tasks/'+prior),get('/health'),get('/health/blender')]);
if(old.state!=='failed'||old.execution?.state!=='finished'||old.result?.files?.length!==0||old.resource_held||old.next_retry)throw Error('Prior task not confirmed terminal and empty');
if(health.status!=='ok'||blender.status!=='ready')throw Error('Hub not currently available');
rec.preflight={oldState:old.state,execution:old.execution.state,outputCount:0,resourceHeld:old.resource_held,health:health.status,blender:blender.status,pid:health.pid};
rec.originalParams=old.params;rec.scriptSha256=crypto.createHash('sha256').update(await fs.readFile('scripts/hub-front-assembly-model.py')).digest('hex');
await fs.writeFile(p,JSON.stringify(rec,null,2));
const r=await fetch(base+rec.endpoint,{method:'POST',headers:{...headers,'Idempotency-Key':rec.idempotency_key},signal:AbortSignal.timeout(90000)});
const t=await r.text();if(!r.ok)throw Error(`${r.status} ${t}`);rec.response=JSON.parse(t);await fs.writeFile(p,JSON.stringify(rec,null,2));console.log(JSON.stringify(rec.response));
