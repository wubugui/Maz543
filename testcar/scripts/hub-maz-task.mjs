// Task records are persisted before network writes. Never resubmit with a new key.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const base='http://denghong01:8765';
const headers={'X-Hub-App-ID':'codex','X-Hub-Project-ID':'maz543a'};
async function call(route,options={}){
  const r=await fetch(base+route,{...options,headers:{...headers,...options.headers}});
  if(!r.ok)throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
const dir='work/searchlight-correction-20260930';await fs.mkdir(dir,{recursive:true});
const recordPath=path.join(dir,'task-record.json');
const save=r=>fs.writeFile(recordPath,JSON.stringify(r,null,2));
let record;try{record=JSON.parse(await fs.readFile(recordPath,'utf8'));}catch{record={base_url:base,idempotency_key:'maz543a-searchlight-correction-'+crypto.randomUUID()};await save(record);}
if(process.argv[2]==='repair'){
  const id=record.response.task_id??record.response.task_ids[0];
  const task=await call('/v1/tasks/'+id);
  if(task.state!=='failed')throw Error('Only replace our confirmed failed task');
  await fs.writeFile(path.join(dir,'task-record-failed-'+id+'.json'),JSON.stringify(record,null,2));
  record={base_url:base,idempotency_key:'maz543a-searchlight-correction-repair-'+crypto.randomUUID()};await save(record);
  console.log('REPAIR_RECORD_READY; run submit');
}else if(process.argv[2]==='rebudget-4096'){
  const id=record.response.task_id??record.response.task_ids[0];
  const task=await call('/v1/tasks/'+id);
  if(task.state!=='queued')throw Error('Only replace our queued task');
  await call('/v1/tasks/'+id+'/cancel',{method:'POST'});
  const ended=await call('/v1/tasks/'+id);
  if(ended.state!=='cancelled')throw Error('Cancellation not terminal');
  await fs.writeFile(path.join(dir,'task-record-8192-cancelled.json'),JSON.stringify({...record,terminalState:ended.state},null,2));
  record={...record,idempotency_key:'maz543a-searchlight-correction-4096-'+crypto.randomUUID(),body:{...record.body,params:{...record.body.params,ram_mb:4096}},response:undefined};
  await save(record);
  record.response=await call('/v1/tasks',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':record.idempotency_key},body:JSON.stringify(record.body)});await save(record);
  console.log(JSON.stringify(record.response));
}else
if(process.argv[2]==='submit'){
  if(!record.script_file){
    const bytes=await fs.readFile('scripts/hub-searchlight-correction.py');
    const sha256=crypto.createHash('sha256').update(bytes).digest('hex');
    if(!record.upload){record.upload=await call('/v1/uploads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:'hub-searchlight-correction.py',size:bytes.length,sha256})});await save(record);}
    const id=record.upload.upload_id??record.upload.id;
    const status=await call('/v1/uploads/'+id);
    const offset=status.offset??0;
    if(offset<bytes.length)await call('/v1/uploads/'+id,{method:'PUT',headers:{'Content-Type':'application/octet-stream','Upload-Offset':String(offset)},body:bytes.subarray(offset)});
    record.script_file=await call('/v1/uploads/'+id+'/complete',{method:'POST'});await save(record);
  }
  if(!record.body){record.body={backend:'blender',name:'MAZ543A driver front searchlight correction',priority:50,params:{version:'4.5.13',project_file:'79701385-4164-4f93-bd1b-5c610f84213d',files:[{file_id:record.script_file.id,path:'correction.py'}],script:'correction.py',device:'cpu',threads:4,ram_mb:8192,timeout_seconds:900}};await save(record);}
  if(!record.response){record.response=await call('/v1/tasks',{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':record.idempotency_key},body:JSON.stringify(record.body)});await save(record);}
  console.log(JSON.stringify(record.response));
}else{
  const id=record.response.task_id??record.response.task_ids[0];
  const task=await call('/v1/tasks/'+id);await fs.writeFile(path.join(dir,'task-result.json'),JSON.stringify(task,null,2));
  console.log(JSON.stringify({id,state:task.state,error:task.error,files:task.result?.files}));
  if(process.argv[2]==='download'&&task.state==='succeeded'){
    for(const file of task.result.files){
      const r=await fetch(base+file.url,{headers});if(!r.ok)throw Error(r.status);
      const bytes=Buffer.from(await r.arrayBuffer());
      if(bytes.length!==file.size||crypto.createHash('sha256').update(bytes).digest('hex')!==file.sha256)throw Error('Output hash mismatch');
      await fs.writeFile(path.join(dir,file.relative_path),bytes);
    }
    console.log('ALL_OUTPUTS_SHA256_VERIFIED');
  }
}
