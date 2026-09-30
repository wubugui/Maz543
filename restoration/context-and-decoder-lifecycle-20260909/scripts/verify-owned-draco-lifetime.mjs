import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {DRACOLoader} from 'three/addons/loaders/DRACOLoader.js';
import {protectDracoLifetime} from '../lib/ownedDracoLifetime.ts';
const originalWorker=globalThis.Worker,workers=[];let immediate=false;
class DecoderWorker{
 constructor(url){this.url=url;this.terminated=false;this.onmessage=null;workers.push(this);}
 postMessage(message){if(message.type==='decode'&&immediate)queueMicrotask(()=>this.onmessage?.({data:{type:'decode',id:message.id,geometry:{index:{array:new Uint32Array([0,1,2])},attributes:[{name:'position',array:new Float32Array([0,0,0,1,0,0,0,1,0]),itemSize:3,stride:3}]}}}));}
 terminate(){this.terminated=true;}
}
globalThis.Worker=DecoderWorker;
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const config={attributeIDs:{},attributeTypes:{},useUniqueIDs:false,vertexColorSpace:'srgb-linear'};
function delayedLoader(){const loader=new DRACOLoader().setDecoderConfig({type:'js'});let release;loader._loadLibrary=()=>new Promise(resolve=>release=resolve);return {loader,release:()=>release('/* controlled decoder library */')};}
try{
 // Reproduce the real installed implementation's late-worker race.
 const stock=delayedLoader(),stockTask=stock.loader.decodeGeometry(new ArrayBuffer(8),config);stockTask.catch(()=>{});
 stock.loader.dispose();stock.release();await tick();
 assert.equal(workers.length,1);assert.equal(workers[0].terminated,false,'stock creates a decoder after dispose');
 for(const callback of Object.values(workers[0]._callbacks))callback.reject(new Error('test cleanup'));
 await assert.rejects(stockTask,/test cleanup/);stock.loader.dispose();
 const countAfterStock=workers.length;
 // The guarded instance cancels immediately, then cleans up late initialization.
 const late=delayedLoader(),lifetime=protectDracoLifetime(late.loader);
 const pending=late.loader.decodeGeometry(new ArrayBuffer(8),config);pending.catch(()=>{});
 assert.equal(lifetime.pendingDecodes,1);late.loader.dispose();await assert.rejects(pending,/owning viewport has closed/);
 late.release();await tick();assert.equal(workers.length,countAfterStock,'no decoder created after late init settles');assert.equal(lifetime.pendingDecodes,0);
 await assert.rejects(late.loader.decodeGeometry(new ArrayBuffer(8),config),/owning viewport has closed/);late.loader.dispose();
 // An already-running stock task is also settled before its owned worker ends.
 const active=delayedLoader(),activeLife=protectDracoLifetime(active.loader),activeTask=active.loader.decodeGeometry(new ArrayBuffer(8),config);activeTask.catch(()=>{});
 active.release();await tick();const activeWorker=workers.at(-1);assert.equal(activeWorker.terminated,false);
 active.loader.dispose();await assert.rejects(activeTask,/owning viewport has closed/);await tick();
 assert.equal(activeWorker.terminated,true);assert.equal(activeWorker.onmessage,null);assert.equal(activeLife.pendingDecodes,0);assert.deepEqual(activeWorker._callbacks,{});
 // Dispose in the exact microtask gap after obtaining a worker but before
 // stock decodeGeometry registers and posts the decode callback.
 const gap=delayedLoader(),gapLife=protectDracoLifetime(gap.loader),get=gap.loader._getWorker;
 gap.loader._getWorker=function(...args){return get.apply(this,args).then(worker=>{queueMicrotask(()=>gap.loader.dispose());return worker;});};
 const gapTask=gap.loader.decodeGeometry(new ArrayBuffer(8),config);gapTask.catch(()=>{});gap.release();
 await assert.rejects(gapTask,/owning viewport has closed/);await tick();const gapWorker=workers.at(-1);
 assert.equal(gapWorker.terminated,true);assert.deepEqual(gapWorker._callbacks,{});assert.equal(gapLife.pendingDecodes,0);
 // Successful decoding still uses the actual stock geometry construction.
 immediate=true;const success=delayedLoader(),successLife=protectDracoLifetime(success.loader);
 const successTask=success.loader.decodeGeometry(new ArrayBuffer(8),config);success.release();const geometry=await successTask;
 assert.deepEqual([...geometry.attributes.position.array],[0,0,0,1,0,0,0,1,0]);assert.equal(geometry.attributes.position.count,3);assert.deepEqual([...geometry.index.array],[0,1,2]);assert.equal(successLife.pendingDecodes,0);
 success.loader.dispose();success.loader.dispose();geometry.dispose();assert.ok(workers.every(worker=>worker.terminated));
 const report={passed:true,actualStockCreatesWorkerAfterDispose:true,guardBlocksLateWorker:true,pendingAndActiveTasksRejectOnDispose:true,stockCallbacksReleased:true,workerToPostMicrotaskGapSettles:true,newTasksRejectedAfterDispose:true,idempotentDispose:true,stockGeometryConstructionUnchanged:true,
 limits:'Actual r183 DRACOLoader lifecycle and geometry construction with controlled library/Worker transport. Does not prove this race alone caused the observed 27 GiB process, real GPU memory release, full codec fidelity or stable frame rate.'};
 await fs.mkdir('outputs/owned-draco-lifetime',{recursive:true});await fs.writeFile('outputs/owned-draco-lifetime/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{globalThis.Worker=originalWorker;}
