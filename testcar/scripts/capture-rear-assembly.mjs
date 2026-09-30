import fs from 'node:fs/promises';
// Use an installed Playwright module; allow an executor-provided module URL.
const {chromium}=await import(process.env.MAZ_PLAYWRIGHT_MODULE || 'playwright');
const dir=process.argv[2];
if(!dir)throw new Error('Usage: node scripts/capture-rear-assembly.mjs <evidence-directory>');
await fs.mkdir(dir,{recursive:true});
const browser=await chromium.launch({headless:true,...(process.env.MAZ_CHROMIUM_EXECUTABLE?{executablePath:process.env.MAZ_CHROMIUM_EXECUTABLE}:{}),args:process.env.MAZ_CHROMIUM_ARGS?JSON.parse(process.env.MAZ_CHROMIUM_ARGS):[]});
try{
 const page=await browser.newPage({viewport:{width:1600,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
 const response=await page.goto(new URL('/?quality=full&debug-handle=1',process.env.MAZ_PREVIEW_URL||'http://localhost:3000').href,{timeout:120000});await page.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500,null,{timeout:180000});await page.waitForTimeout(10000);
 const evidence={timeUTC:new Date().toISOString(),http:response.status(),errors,quality:'full',requestedUrl:page.url(),views:[],parts:await page.evaluate(()=>{const {root,T,renderer}=window.__maz;root().updateMatrixWorld(true);const a=[];root().traverse(o=>{if(o.name.startsWith('BL_RearRestoration_')||/^frame_000[234]$/.test(o.name)){const b=new T.Box3().setFromObject(o);a.push({name:o.name,parent:o.parent?.name,min:b.min.toArray(),max:b.max.toArray(),material:o.material?.name,color:o.material?.color?.toArray()});}});const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {objects:a,meshCount:window.__maz.nativeMeshes.length,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)};})};
 for(const [name,position,target]of [['left-side',[-.3,3.0,17],[-.1,1.4,0]],['right-side',[-.3,3.0,-17],[-.1,1.4,0]],['rear-oblique',[9,5,10],[2.5,1.1,0]],['rear-opposite',[9,5,-10],[2.5,1.1,0]],['rear-top',[3.3,9,0],[3.3,.9,0]],['box-mount',[4,2.4,7],[3.5,1.1,0]]]){
  await page.evaluate(({position,target})=>{const {camera,orbit,frameCache}=window.__maz;camera.position.fromArray(position);orbit.target.fromArray(target);orbit.update();frameCache.invalidate();},{position,target});await page.waitForTimeout(2500);
  evidence.views.push(await page.evaluate(name=>({name,camera:window.__maz.camera.matrixWorld.elements.slice(),projection:window.__maz.camera.projectionMatrix.elements.slice()}),name));await page.screenshot({path:dir+'/'+name+'.png'});
 }
 await fs.writeFile(dir+'/browser-evidence.json',JSON.stringify(evidence,null,2));console.log(JSON.stringify({http:evidence.http,errors,parts:evidence.parts.objects.length,meshCount:evidence.parts.meshCount,renderer:evidence.parts.renderer}));
}finally{await browser.close();}
