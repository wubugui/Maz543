import fs from 'node:fs/promises';
import {createWriteStream,createReadStream} from 'node:fs';
import path from 'node:path';
import {Readable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import crypto from 'node:crypto';
const dir=process.argv[2],filter=process.argv[3]?new RegExp(process.argv[3]):null,base='http://denghong01:8765';
const rec=JSON.parse(await fs.readFile(dir+'/task-record.json','utf8')),id=rec.response.task_id??rec.response.task_ids[0],headers={'X-Hub-App-ID':'codex','X-Hub-Project-ID':'maz543a'};
const response=await fetch(base+'/v1/tasks/'+id,{headers,signal:AbortSignal.timeout(30000)});if(!response.ok)throw Error(response.status);const task=await response.json();
await fs.writeFile(dir+'/task-result.json',JSON.stringify(task,null,2));if(task.state!=='succeeded')throw Error('Only download succeeded complete candidates');
async function hash(file){const h=crypto.createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');}
for(const f of task.result.files){
 if(filter&&!filter.test(f.relative_path))continue;
 const dest=path.resolve(dir,f.relative_path),root=path.resolve(dir)+path.sep;if(!dest.startsWith(root))throw Error('Unsafe output path');await fs.mkdir(path.dirname(dest),{recursive:true});
 try{if((await fs.stat(dest)).size===f.size&&await hash(dest)===f.sha256){console.log('Already verified '+f.relative_path);continue;}}catch{}
 const part=dest+'.part';let offset=0;try{offset=(await fs.stat(part)).size;}catch{};if(offset>f.size)throw Error('Unexpected partial size');
 if(offset<f.size){const r=await fetch(base+f.url,{headers:{...headers,...(offset?{Range:'bytes='+offset+'-'}:{})}});if(!r.ok)throw Error(r.status);if(offset&&r.status!==206)throw Error('Server did not honor range');await pipeline(Readable.fromWeb(r.body),createWriteStream(part,{flags:offset?'a':'w'}));}
 if((await fs.stat(part)).size!==f.size||await hash(part)!==f.sha256)throw Error('Output integrity failed '+f.relative_path);
 await fs.rename(part,dest);console.log('SHA256 verified '+f.relative_path+' '+f.size);
}
