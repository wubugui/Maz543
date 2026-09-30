import fs from 'node:fs/promises';
import {chromium} from 'file:///E:/Maz543/external/codex-dependencies/node/node_modules/playwright/index.mjs';
const b=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
try{const p=await b.newPage();await p.goto('http://localhost:3000/?quality=full&debug-handle=1');await p.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500,null,{timeout:180000});
const r=await p.evaluate(()=>{const {T,root}=window.__maz;const rows=[];root().updateMatrixWorld(true);root().traverse(o=>{
 if(!o.isMesh||!/^frame_000|BL_Merged_frame/.test(o.name))return;
 const a=o.geometry.attributes.position,ix=o.geometry.index;const adj=Array.from({length:a.count},()=>[]);
 for(let i=0;i<(ix?.count??a.count);i+=3){const ids=[0,1,2].map(k=>ix?ix.getX(i+k):i+k);for(const u of ids)for(const v of ids)if(u!==v)adj[u].push(v);}
 const seen=new Set(),parts=[];
 for(let i=0;i<a.count;i++){if(seen.has(i))continue;const stack=[i],ids=[];seen.add(i);while(stack.length){const n=stack.pop();ids.push(n);for(const j of adj[n])if(!seen.has(j)){seen.add(j);stack.push(j)}}
 const box=new T.Box3();for(const n of ids)box.expandByPoint(new T.Vector3().fromBufferAttribute(a,n).applyMatrix4(o.matrixWorld));
 if(box.min.x<-5.3)parts.push({vertices:ids.length,min:box.min.toArray(),max:box.max.toArray()});}
 rows.push({name:o.name,parts});});return rows;});await fs.writeFile('work/front-assembly-20260930/browser-frame-components.json',JSON.stringify(r,null,2));console.log(JSON.stringify(r));}finally{await b.close();}
