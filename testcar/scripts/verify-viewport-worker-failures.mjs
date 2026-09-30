import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
registerHooks({
 resolve(s,c,next){if(s==='./vehicleViewport')return {url:'mazmock:viewport',shortCircuit:true};try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}},
 load(url,c,next){if(url==='mazmock:viewport')return {format:'module',source:'export function createVehicleViewport(bindings){return globalThis.__viewportFactory(bindings);}',shortCircuit:true};return next(url,c);},
});
const {INITIAL}=await import('../lib/mechanics.ts');
const cases=[];
for(const mode of ['throws','no-disposer','asset-fatal','recoverable-error','normal-dispose','dispose-throws']){
 const sent=[],port={closed:0,onmessage:null,close(){this.closed++;}};let bindings,disposeCalls=0;
 globalThis.postMessage=message=>sent.push(message);
 globalThis.__viewportFactory=value=>{
  bindings=value;
  if(mode==='throws')throw new Error('WebGL setup fixture');
  if(mode==='no-disposer')return;
  value.simulationWorker.current=value.environment.createSimulation();
  return ()=>{disposeCalls++;if(mode==='dispose-throws')throw new Error('dispose fixture');};
 };
 await import('../lib/viewport.worker.ts?case='+mode);
 await globalThis.onmessage({data:{type:'init',canvas:{},simulation:port,metrics:{width:1212,height:773,left:0,top:0,innerWidth:1280,devicePixelRatio:1},hidden:false,search:'',controls:structuredClone(INITIAL),selection:'',contextAudit:mode==='normal-dispose'?true:mode==='recoverable-error'?'true':undefined}});
 assert.equal(bindings.environment.contextAudit,mode==='normal-dispose','Only explicit boolean true enables production audit inputs');
 if(mode==='throws'||mode==='no-disposer')assert.ok(sent.some(message=>message.type==='fatal'));
 else if(mode==='asset-fatal'){bindings.callbacks.current.onFatal('asset load failed');assert.equal(sent.at(-1).type,'fatal');}
 else if(mode==='recoverable-error'){bindings.callbacks.current.onError('context interrupted');assert.equal(sent.at(-1).type,'error');assert.ok(!sent.some(message=>message.type==='fatal'));}
 else{
  await globalThis.onmessage({data:{type:'dispose'}});assert.equal(disposeCalls,1);assert.equal(port.closed,1);assert.ok(sent.some(message=>message.type==='disposed'),'acknowledge even when renderer disposal throws');
 }
 cases.push({mode,messages:sent.map(message=>message.type),closedPorts:port.closed});
}
const report={passed:true,cases,limits:'Actual worker entry and host protocol with an injected viewport constructor; no WebGL allocation or whole-model browser performance is measured.'};
await fs.writeFile('outputs/worker-lifecycle/worker-failure-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
