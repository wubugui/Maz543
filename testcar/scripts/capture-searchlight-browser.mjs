import fs from 'node:fs/promises';
import {chromium} from 'file:///E:/Maz543/external/codex-dependencies/node/node_modules/playwright/index.mjs';
const phase=process.argv[2]??'before';
const dir=`outputs/searchlight-correction-20260930/${phase}`;
await fs.mkdir(dir,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
try{
  const page=await browser.newPage({viewport:{width:1600,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  const response=await page.goto('http://localhost:3000/?quality=full&debug-handle=1',{waitUntil:'domcontentloaded',timeout:120000});
  await page.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500,null,{timeout:180000});
  await page.waitForTimeout(1500);
  const evidence=await page.evaluate(()=>{
    const {T,root,renderer}=window.__maz;
    const r=root(),parts=[];
    r.updateMatrixWorld(true);
    r.traverse(o=>{if(o.name.startsWith('BL_Searchlight_')){
      const box=new T.Box3().setFromObject(o);
      parts.push({name:o.name,parent:o.parent?.name,min:box.min.toArray(),max:box.max.toArray()});
    }});
    const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');
    return {parts,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),meshCount:window.__maz.nativeMeshes.length};
  });
  for(const [name,position,target] of [
    ['front',[-12,2.05,0],[-4.4,1.75,0]],
    ['frontoblique',[-10,4,6],[-4.1,1.8,0]],
    ['top',[-4.1,9,0],[-4.1,1.7,0]]]){
    await page.evaluate(({position,target})=>{
      const {camera,orbit,frameCache}=window.__maz;
      camera.position.fromArray(position);orbit.target.fromArray(target);orbit.update();frameCache.invalidate();
    },{position,target});
    await page.waitForTimeout(2000);
    await page.screenshot({path:`${dir}/${name}.png`});
  }
  if(phase==='after'){
    await page.getByRole('button').filter({hasText:'左舱前门'}).click();
    await page.waitForTimeout(2500);
    evidence.openDoor=await page.evaluate(()=>{
      const r=window.__maz.root();const result=[];
      r.traverse(o=>{if(o.name.startsWith('BL_Searchlight_'))result.push({name:o.name,parent:o.parent.name,position:o.getWorldPosition(new window.__maz.T.Vector3()).toArray()});});
      return result;
    });
    await page.evaluate(()=>{const {camera,orbit,frameCache}=window.__maz;camera.position.set(-10,4,6);orbit.target.set(-4.1,1.8,0);orbit.update();frameCache.invalidate();});
    await page.waitForTimeout(2000);
    await page.screenshot({path:`${dir}/left-front-door.png`});
    const downloaded=page.waitForEvent('download',{timeout:120000});
    await page.getByRole('button',{name:/导出 GLB/}).click();
    const file=await downloaded;await file.saveAs(`${dir}/browser-current-pose.glb`);
    evidence.export={filename:file.suggestedFilename(),failure:await file.failure()};
  }
  await fs.writeFile(`${dir}/browser-evidence.json`,JSON.stringify({phase,url:page.url(),httpStatus:response.status(),errors,...evidence},null,2));
  console.log(JSON.stringify({phase,httpStatus:response.status(),errors,...evidence}));
}finally{await browser.close();}
