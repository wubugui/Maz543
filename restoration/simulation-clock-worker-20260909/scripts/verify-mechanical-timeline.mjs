import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {registerHooks} from 'node:module';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {MechanicalTimeline,MECHANICAL_HZ}=await import('../lib/mechanicalTimeline.ts');
const {INITIAL,INITIAL_TELEMETRY,advance}=await import('../lib/mechanics.ts');
const controls={...INITIAL,running:true,terrain:25,doorTargets:[100,0,100,0]};
const direct=new MechanicalTimeline(0,controls),delayed=new MechanicalTimeline(0,controls);
for(const runner of [direct,delayed]){
  runner.setControls({...controls,throttle:20},2000);
  runner.setControls({...controls,running:false},4500);
}
for(let i=1;i<=360;i++)direct.advanceTo(i*1000/60);
for(const ms of [35,170,1550,2000,5000,6000])while(delayed.advanceTo(ms,60).backlogSeconds>0){}
assert.equal(direct.tick,1440);assert.equal(delayed.tick,1440);assert.deepEqual(delayed.state,direct.state,'same complete states despite different callback delays and budgets');
const reference=new MechanicalTimeline(0,controls);reference.advanceTo(2000,Infinity);
let state=structuredClone(INITIAL_TELEMETRY);for(let i=0;i<480;i++)state=advance(state,controls,1/MECHANICAL_HZ);
assert.deepEqual(reference.state,state,'calls the unchanged mechanical solver at its fixed step');
const paused=new MechanicalTimeline(0);paused.advanceTo(1000);paused.setPaused(true,1000);paused.advanceTo(11000);assert.equal(paused.tick,240);paused.setPaused(false,11000);paused.advanceTo(12000);assert.equal(paused.tick,480);
const backlog=new MechanicalTimeline(0);const pending=backlog.advanceTo(10000,60);assert.equal(backlog.tick,60);assert.equal(pending.backlogSeconds,9.75);while(backlog.advanceTo(10000,60).backlogSeconds>0){}assert.equal(backlog.tick,2400);
const boundary=new MechanicalTimeline(0);boundary.setControls({...INITIAL,doorTargets:[100,0,0,0]},1);boundary.advanceTo(4.2);assert.equal(boundary.state.doorOpenings[0],0,'control cannot change the preceding integration interval');boundary.advanceTo(8.4);assert.equal(boundary.state.doorOpenings[0],65/240);
// Actual worker-thread test: deliberately block this main thread for 1.2 s.
// The worker executes the same browser worker module, via a thin message shim.
const worker=new Worker(new URL('./mechanics-worker-node.mjs',import.meta.url));
let latest=null;
worker.on('message',data=>{if(data.generation===1)latest=data.telemetry;});
const ready=new Promise((resolve,reject)=>{worker.once('error',reject);worker.once('message',resolve);});
await ready;worker.postMessage({type:'reset',generation:1,controls:INITIAL,paused:false});
await new Promise(resolve=>setTimeout(resolve,100));assert.ok(latest,'worker initialized');
const before=latest.time;
Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,1200);
await new Promise(resolve=>setTimeout(resolve,150));
const after=latest.time;
let resetState=null;worker.on('message',data=>{if(data.generation===2)resetState=data.telemetry;});
worker.postMessage({type:'reset',generation:2,controls:INITIAL,paused:true});worker.postMessage({type:'controls',generation:1,controls:{...INITIAL,running:true}});
await new Promise(resolve=>setTimeout(resolve,100));assert.ok(resetState);assert.equal(resetState.time,0);assert.equal(resetState.rpm,0,'reset ignores obsolete control generations');
await worker.terminate();
assert.ok(after-before>1.1,`worker advanced ${after-before} s while main thread stalled`);
assert.equal(latest.simulationStats.mode,'worker');assert.equal(latest.simulationStats.stepHz,240);assert.equal(latest.simulationStats.backlogSeconds,0);
const report={passed:true,stepHz:MECHANICAL_HZ,delayedCallbacks:{ticks:delayed.tick,exactStateEquality:true},unchangedSolverEquality:true,hiddenPause:true,controlsAtNextBoundary:true,resetGenerationIsolation:true,retainedBacklog:{initialSeconds:9.75,completedTicks:backlog.tick},actualWorker:{mainThreadBlockedMs:1200,simulationBefore:before,simulationAfter:after,advancedSeconds:after-before,...latest.simulationStats},limits:'No geometry changes. Existing mechanical parameter/fidelity limits remain. Browser integration requires its own evidence.'};
await fs.mkdir('outputs/simulation-worker-evidence',{recursive:true});await fs.writeFile('outputs/simulation-worker-evidence/timeline-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
