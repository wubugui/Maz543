import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {Worker,MessageChannel} from 'node:worker_threads';
import {registerHooks} from 'node:module';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {INITIAL}=await import('../lib/mechanics.ts');
const physics=new Worker(new URL('./mechanics-worker-node.mjs',import.meta.url)),renderer=new Worker(new URL('./render-consumer-blocked.mjs',import.meta.url));
const wait=(worker,predicate)=>new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>finish(new Error('Timed out waiting for worker condition')),10000);
  const message=data=>{if(predicate(data))finish(null,data);},error=reason=>finish(reason);
  function finish(error,data){clearTimeout(timer);worker.off('message',message);worker.off('error',errorListener);if(error)reject(error);else resolve(data);}
  const errorListener=error;worker.on('message',message);worker.on('error',errorListener);
});
const channel=new MessageChannel(),mainStates=new Map();let unblocked=false;
physics.on('message',data=>{if(data.type==='state')mainStates.set(`${data.generation}/${data.telemetry.time}`,data);});
renderer.on('message',data=>{if(data.type==='unblocked')unblocked=true;});
try{
  const initial=wait(physics,data=>data.type==='state'&&data.generation===1);
  physics.postMessage({type:'reset',generation:1,controls:INITIAL,paused:false});await initial;
  const received=wait(renderer,data=>data.type==='render-state'&&data.state.generation===1);
  renderer.postMessage({type:'port',port:channel.port1},[channel.port1]);physics.postMessage({type:'connect-renderer',port:channel.port2},[channel.port2]);
  const first=await received;assert.deepEqual(first.state,mainStates.get(`1/${first.state.telemetry.time}`),'render channel receives exactly the same complete state');
  const blocked=wait(renderer,data=>data.type==='blocked');renderer.postMessage({type:'block'});await blocked;
  const controlTime=performance.now(),opening=wait(physics,data=>data.generation===1&&data.telemetry.doorOpenings[0]>40);
  physics.postMessage({type:'controls',generation:1,controls:{...INITIAL,doorTargets:[100,0,0,0]}});
  const moved=await opening,doorResponseMs=performance.now()-controlTime;
  assert.equal(unblocked,false,'real renderer worker is still blocked while controls and physics advance');assert.equal(moved.telemetry.simulationStats.stepHz,240);
  const reset=wait(physics,data=>data.generation===2&&data.telemetry.time===0);
  physics.postMessage({type:'reset',generation:2,controls:INITIAL,paused:true});physics.postMessage({type:'controls',generation:1,controls:{...INITIAL,running:true}});
  const cleared=await reset;assert.equal(unblocked,false);assert.equal(cleared.telemetry.doorOpenings[0],0);assert.equal(cleared.telemetry.rpm,0);
  const delivered=await wait(renderer,data=>data.type==='render-state'&&data.state.generation===2);
  assert.deepEqual(delivered.state,cleared,'paused reset is delivered intact when rendering becomes available');
  const report={passed:true,renderThreadBlockedMs:2000,directControlWhileRenderBlocked:true,doorReachedDegrees:moved.telemetry.doorOpenings[0],doorResponseMs,directResetWhileRenderBlocked:true,generationIsolation:true,fullStatePortEquality:true,stepHz:240,limits:'Real Node workers execute the browser mechanics module. This verifies scheduling and state equality, not browser GPU throughput or factory physics.'};
  await fs.mkdir('outputs/render-worker-evidence',{recursive:true});await fs.writeFile('outputs/render-worker-evidence/direct-mechanics-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{await physics.terminate();await renderer.terminate();channel.port1.close();channel.port2.close();}
