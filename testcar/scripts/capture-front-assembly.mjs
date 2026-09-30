import fs from 'node:fs/promises';
import {chromium} from 'file:///E:/Maz543/external/codex-dependencies/node/node_modules/playwright/index.mjs';
const dir=process.argv[2]??'outputs/front-assembly-20260930/cover-mirror-after';await fs.mkdir(dir,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
try{const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
const response=await page.goto('http://localhost:3000/?quality=full&debug-handle=1',{timeout:120000});
await page.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500&&window.__maz.root()?.getObjectByName('BL_Front_center_cover_NURBS'),null,{timeout:180000});await page.waitForTimeout(10000);
const parts=()=>page.evaluate(()=>{const {root,T,renderer}=window.__maz;root().updateMatrixWorld(true);const a=[];root().traverse(o=>{if(o.name.startsWith('BL_Front_')){const b=new T.Box3().setFromObject(o);a.push({name:o.name,parent:o.parent?.name,min:b.min.toArray(),max:b.max.toArray()});}});const doors=['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007'].map(name=>{const o=root().getObjectByName(name);return {name,rotation:o.rotation.toArray(),matrixWorld:o.matrixWorld.elements.slice()};});const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {parts:a,doors,meshCount:window.__maz.nativeMeshes.length,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)};});
const evidence={http:response.status(),errors,closed:await parts(),views:[]};
for(const [name,position,target]of [['front',[-12,2.05,0],[-4.4,1.75,0]],['frontoblique',[-10,4,6],[-4.1,1.8,0]],['top',[-4.1,9,0],[-4.1,1.7,0]],['side',[-4.2,2.25,8],[-4.2,1.8,0]],['center-port',[-6.8,4.1,1.6],[-4.6,2.25,.2]]]){
 await page.evaluate(({position,target})=>{const {camera,orbit,frameCache}=window.__maz;camera.position.fromArray(position);orbit.target.fromArray(target);orbit.update();frameCache.invalidate();},{position,target});await page.waitForTimeout(2500);
 evidence.views.push(await page.evaluate(name=>({name,camera:window.__maz.camera.matrixWorld.elements.slice(),projection:window.__maz.camera.projectionMatrix.elements.slice()}),name));await page.screenshot({path:dir+'/'+name+'.png'});
}
for(const label of ['右舱前门','右舱后门','左舱前门','左舱后门']){await page.getByRole('button').filter({hasText:label}).click();await page.waitForTimeout(2200);}
evidence.open=await parts();await page.evaluate(()=>{const {camera,orbit,frameCache}=window.__maz;camera.position.set(-10,4,6);orbit.target.set(-4.1,1.8,0);orbit.update();frameCache.invalidate();});await page.waitForTimeout(2500);await page.screenshot({path:dir+'/four-doors-open.png'});
await fs.writeFile(dir+'/browser-evidence.json',JSON.stringify(evidence,null,2));console.log(JSON.stringify({http:evidence.http,errors,parts:evidence.closed.parts.length,meshCount:evidence.closed.meshCount,renderer:evidence.closed.renderer}));}finally{await browser.close();}
