import fs from 'node:fs/promises';
import {chromium} from 'file:///E:/Maz543/external/codex-dependencies/node/node_modules/playwright/index.mjs';
const dir='outputs/front-assembly-20260930';await fs.mkdir(dir,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
try{const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
const res=await page.goto('http://localhost:3000/?quality=full&debug-handle=1');await page.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500,null,{timeout:180000});await page.waitForTimeout(10000);
for(const [name,position,target]of [['current-center-cover-gap',[-8,3.1,1.3],[-4.5,1.95,0]],['current-mirror-bumper-side',[-7,2.2,4],[-5.1,1.7,1.2]]]){
 await page.evaluate(({position,target})=>{const {camera,orbit,frameCache}=window.__maz;camera.position.fromArray(position);orbit.target.fromArray(target);orbit.update();frameCache.invalidate();},{position,target});await page.waitForTimeout(2500);await page.screenshot({path:dir+'/'+name+'.png'});
}
await fs.writeFile(dir+'/browser-current-baseline.json',JSON.stringify({http:res.status(),errors,state:'Production assets unchanged: candidate blocked by Hub runner permissions',meshCount:await page.evaluate(()=>window.__maz.nativeMeshes.length)},null,2));
console.log('Two current baseline screenshots saved.');}finally{await browser.close();}
