import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {OriginalReplayDepthQueries}=await import('../lib/originalReplayDepthQueries.ts');
const {createTriangleRangeProxies}=await import('../lib/triangleRangeProxies.ts');
function fixture(){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1.25,.05,100),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),mesh=new T.Mesh(geometry,material);mesh.name='query candidate';scene.add(mesh);camera.position.z=10;camera.updateMatrixWorld(true);scene.updateMatrixWorld(true);
 const state={target:null,active:null,available:false,lost:false,created:0,deleted:0,read:0,clearDepth:1,controls:0,disposedControls:0,badControls:false,wrongSamples:false,sourceDisposals:0,prepared:false,initializations:0};
 const depths=new WeakMap(),seen=new WeakSet();const keys=['SAMPLES','DEPTH_BITS','ANY_SAMPLES_PASSED','ANY_SAMPLES_PASSED_CONSERVATIVE','CURRENT_QUERY','QUERY_RESULT_AVAILABLE','QUERY_RESULT'];const gl=Object.fromEntries(keys.map(k=>[k,k]));
 Object.assign(gl,{isContextLost:()=>state.lost,getError:()=>0,getParameter(k){return k==='SAMPLES'?(state.target?.samples??0)+(state.wrongSamples&&state.target.width===1?1:0):24;},getQuery:()=>state.active,createQuery(){state.created++;return {samples:false};},deleteQuery(q){assert.ok(!q.deleted);q.deleted=true;state.deleted++;},beginQuery(_kind,q){assert.equal(state.active,null);state.active=q;},endQuery(){assert.ok(state.active);state.active=null;},getQueryParameter(q,k){assert.ok(!q.deleted);if(k==='QUERY_RESULT_AVAILABLE')return state.available;assert.ok(state.available);state.read++;return q.samples;}});
 const renderer={getContext:()=>gl,capabilities:{precision:'highp'},autoClear:true,shadowMap:{autoUpdate:true,needsUpdate:true},render(s){assert.notEqual(s,scene);assert.equal(this.autoClear,false);assert.equal(this.shadowMap.autoUpdate,false);assert.equal(this.shadowMap.needsUpdate,false);assert.equal(s.children[0].material.depthWrite,false);assert.equal(s.children[0].material.colorWrite,false);assert.deepEqual(s.children[0].material.uniforms.rectangle.value.toArray(),[0,0,0,0]);state.prepared=true;state.initializations++;},setRenderTarget(t){state.target=t;if(t.width===1&&!seen.has(t)){seen.add(t);state.controls++;t.addEventListener('dispose',()=>state.disposedControls++);}},state:{buffers:{depth:{setMask(){},setClear(v){state.clearDepth=v;}}}},clear(){depths.set(state.target,state.clearDepth);}};
 const probe=new OriginalReplayDepthQueries(renderer,scene,camera),snapshots=[4,2,0].map(samples=>new T.WebGLRenderTarget(100,80,{samples}));
 const direct=(_camera,_scene,_geometry,m)=>{assert.ok(state.active);assert.equal(state.prepared,true,'Vertex upload must precede direct queries');state.active.samples=state.badControls&&state.target.width===1?false:m.uniforms.closestDepth.value<=(depths.get(state.target)??.5);};
 let rangeSet;const consume=(certificates=false,withRanges=false)=>{rangeSet=withRanges?createTriangleRangeProxies(geometry,2):null;probe.begin([{mesh,stableFrames:2,triangles:12,values:[]}],certificates,rangeSet?new Map([[mesh,rangeSet.ranges]]):new Map());for(const t of snapshots){renderer.setRenderTarget(t);depths.set(t,.5);probe.consume(t,{samples:t.samples,depthBits:24,viewport:[0,0,100,80],normalOverride:t.samples===0},direct);}probe.finish();};
 for(const r of [geometry,material,...snapshots])r.addEventListener('dispose',()=>state.sourceDisposals++);
 const close=()=>{probe.dispose();probe.dispose();rangeSet?.dispose();assert.equal(state.created,state.deleted);assert.equal(state.controls,state.disposedControls);assert.equal(state.sourceDisposals,0);assert.equal(renderer.autoClear,true);assert.equal(renderer.shadowMap.autoUpdate,true);assert.equal(renderer.shadowMap.needsUpdate,true);geometry.dispose();material.dispose();snapshots.forEach(t=>t.dispose());};
 return {state,probe,consume,close};
}
{
 const f=fixture();f.consume();assert.equal(f.state.created,9);assert.equal(f.state.initializations,1);assert.equal(f.probe.poll(),null);assert.equal(f.state.read,0);f.state.available=true;const r=f.probe.poll();assert.equal(r.summary.controlsPassed,true);assert.equal(r.results.length,9);assert.deepEqual(r.summary.passes.map(p=>[p.samples,p.zeroVolumes,p.zeroTriangles]),[[4,1,12],[2,1,12],[0,1,12]]);assert.equal(f.probe.poll(),null);f.close();
}
{
 const f=fixture();f.state.badControls=true;f.consume();f.state.available=true;assert.equal(f.probe.poll().summary.controlsPassed,false);f.close();
}
{
 const f=fixture();f.consume();f.state.lost=true;assert.match(f.probe.poll().summary.error,/Context lost/);assert.equal(f.state.read,0);f.close();
}
{
 const f=fixture();f.state.wrongSamples=true;assert.throws(f.consume,/Control sample\/depth mismatch/);f.close();
}
{
 const f=fixture();f.consume();f.close();assert.equal(f.state.read,0);
}
{
 const f=fixture();f.consume(true);f.state.available=true;const result=f.probe.poll();assert.equal(result.summary.controlsPassed,true);const rows=result.results.filter(r=>r.controlExpected===undefined);assert.equal(rows.length,3);assert.ok(rows.every(r=>r.meshUuid&&r.volume&&r.volume.nearDepth>0&&r.volume.right>r.volume.left));f.close();
}
{
 const f=fixture();f.consume(true,true);f.state.available=true;const result=f.probe.poll();assert.ok(result.summary.controlsPassed);assert.equal(result.results.length,27);assert.ok(result.summary.passes.every(p=>p.rangeQueried===6&&p.zeroCountsOverlap));const ranges=result.results.filter(r=>r.rangeStart!==undefined);assert.equal(ranges.length,18);assert.ok(ranges.every(r=>r.meshUuid&&r.volume&&r.rangeCount===6&&r.triangles===2));f.close();
}
const report={passed:true,exactSampleConfigurationsAndControlsChecked:true,unavailableQueriesNeverRead:true,failedControlsNotAccepted:true,contextLossAndPartialSubmissionCleaned:true,allQueriesAndControlTargetsDisposed:true,sourceResourcesNeverDisposed:true,limits:'Real Three geometry/resources and conservative bounds with controlled WebGL query results. Actual original-program snapshot occlusion must be measured in browser.'};
await fs.mkdir('outputs/original-pass-depth-replay',{recursive:true});await fs.writeFile('outputs/original-pass-depth-replay/query-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
