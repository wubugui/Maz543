import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {registerHooks} from 'node:module';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {OcclusionPrefixReuse}=await import('../lib/occlusionPrefixReuse.ts');

function fixture(spatial=false){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial();
 geometry.computeBoundingSphere();
 const blocker=new T.Mesh(geometry,material),hidden=new T.Mesh(geometry,material);blocker.name='blocker';hidden.name='hidden';scene.add(blocker,hidden);
 const state={active:null,available:true,samples:2,lost:false,scissor:false,throwOn:null,created:0,deleted:0,reads:0,draws:[]};
 const gl={};for(const name of ['ANY_SAMPLES_PASSED','ANY_SAMPLES_PASSED_CONSERVATIVE','CURRENT_QUERY','QUERY_RESULT_AVAILABLE','QUERY_RESULT','DEPTH_WRITEMASK','DEPTH_CLEAR_VALUE','SCISSOR_TEST','SAMPLE_COVERAGE','RASTERIZER_DISCARD','SAMPLES','DEPTH_BITS','VIEWPORT'])gl[name]=name;
 Object.assign(gl,{
  isContextLost:()=>state.lost,isEnabled:name=>name==='SCISSOR_TEST'&&state.scissor,getError:()=>0,
  getParameter(name){return ({DEPTH_WRITEMASK:true,DEPTH_CLEAR_VALUE:1,SAMPLES:state.samples,DEPTH_BITS:24,VIEWPORT:new Int32Array([0,0,1280,720])})[name];},
  getQuery:()=>state.active,createQuery(){state.created++;return {samples:false};},deleteQuery(query){assert.ok(!query.deleted);query.deleted=true;state.deleted++;},
  beginQuery(_kind,query){assert.equal(state.active,null);state.active=query;},endQuery(){assert.ok(state.active);state.active=null;},
  getQueryParameter(query,kind){assert.ok(!query.deleted);if(kind==='QUERY_RESULT_AVAILABLE')return state.available;assert.equal(state.available,true,'Never read a pending result');state.reads++;return query.samples;},
 });
 const target=new T.WebGLRenderTarget(1280,720,{samples:2});
 const renderer={getContext:()=>gl,getRenderTarget:()=>target,capabilities:{precision:'highp'},clippingPlanes:[],clear(){},
  renderBufferDirect(_camera,_scene,_geometry,_material,object){if(state.throwOn===object)throw new Error('draw fixture');state.draws.push(object.name);if(state.active)state.active.samples=object!==hidden;}};
 const drawOriginal=renderer.renderBufferDirect,clearOriginal=renderer.clear,reuse=new OcclusionPrefixReuse(renderer,{spatial});
 const frame=(clear=true)=>{state.draws=[];scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
  return reuse.render(renderer,scene,camera,()=>{if(clear)renderer.clear();for(const object of scene.children)if(object.visible){object.modelViewMatrix.multiplyMatrices(camera.matrixWorldInverse,object.matrixWorld);renderer.renderBufferDirect(camera,scene,object.geometry,object.material,object,null);}});};
 const close=()=>{reuse.dispose();assert.equal(state.created,state.deleted);assert.equal(renderer.clear,clearOriginal);assert.equal(renderer.renderBufferDirect,drawOriginal);target.dispose();geometry.dispose();for(const value of new Set([material,...scene.children.map(object=>object.material)]))value.dispose();};
 return {scene,camera,geometry,material,blocker,hidden,state,renderer,reuse,frame,close,drawOriginal,clearOriginal};
}
const cases=[];
for(const [name,change] of [
 ['preceding object matrix',f=>f.blocker.position.x=Number.EPSILON],
 ['target matrix',f=>f.hidden.position.y=Number.EPSILON],
 ['camera projection',f=>f.camera.projectionMatrix.elements[0]+=Number.EPSILON],
 ['attribute version',f=>f.geometry.attributes.position.needsUpdate=true],
 ['preceding depth write',f=>{f.blocker.material=f.material.clone();f.blocker.material.depthWrite=false;}],
 ['morph influence',f=>f.hidden.morphTargetInfluences=[Number.EPSILON]],
 ['MSAA samples',f=>f.state.samples=4],
 ['scissor clear',f=>f.state.scissor=true],
 ['global clipping',f=>f.renderer.clippingPlanes=[new T.Plane()]],
 ['custom shader callback',f=>f.material.onBeforeCompile=()=>{}],
 ['custom shader define',f=>f.material.defines.CUSTOM_POSITION=1],
 ['shader precision',f=>f.material.precision='mediump'],
 ['missing preceding draw',f=>f.blocker.visible=false],
 ['nonfinite transform',f=>f.hidden.position.x=Infinity],
 ]){
  const f=fixture();assert.equal(f.frame().queried,0);assert.equal(f.frame().queried,2);assert.equal(f.frame().skipped,1);change(f);assert.equal(f.frame().skipped,0,name);assert.ok(f.state.draws.includes('hidden'));cases.push(name);f.close();
 }
{
 const f=fixture();f.frame();f.frame();assert.equal(f.frame().skipped,1);f.material.color.set('#ff0000');assert.equal(f.frame().skipped,1,'Depth-independent color changes redraw blocker, preserve zero-depth proof');assert.deepEqual(f.state.draws,['blocker']);f.close();
}
{
 const f=fixture();f.state.available=false;f.frame();f.frame();assert.equal(f.frame().skipped,0);assert.equal(f.state.reads,0);assert.equal(f.state.created,2,'No duplicate query while pending');f.state.available=true;assert.equal(f.frame().skipped,1);assert.equal(f.frame(false).skipped,0);f.close();
}
{
 const f=fixture();f.frame();f.state.throwOn=f.hidden;assert.throws(()=>f.frame(),/draw fixture/);assert.equal(f.state.active,null);assert.equal(f.renderer.renderBufferDirect,f.drawOriginal);assert.equal(f.renderer.clear,f.clearOriginal);f.close();
}
{
 const f=fixture();f.frame();f.frame();assert.equal(f.frame().skipped,1);f.state.lost=true;assert.equal(f.frame().skipped,0);f.state.lost=false;assert.equal(f.frame().skipped,0);f.close();
}
{
 const f=fixture();for(let i=0;i<32;i++)f.frame();assert.ok(f.state.created<=6,'Epoch reset is bounded, not per-frame requery');f.close();
}
{
 const f=fixture();for(let i=0;i<12;i++){f.blocker.position.x=i;const result=f.frame();assert.equal(result.queried,0);assert.equal(result.skipped,0);}assert.equal(f.state.created,0,'Continuously changing prefixes do not spam queries');f.close();
}
const report={passed:true,invalidations:cases,pendingResultsNeverRead:true,queriesAndHooksReleasedOnFailure:true,colorOnlyDepthProofSafe:true,missingDepthClearFallsBack:true,contextLossInvalidates:true,epochStorageBounded:true,changingPrefixesAvoidQuerySpam:true,
 limits:'Actual Three scene objects with deterministic WebGL query/coverage transport. Tests proof invalidation and lifecycle; actual complete-frame raster pixels and performance require browser evidence.'};
await fs.writeFile('outputs/occlusion-prefix-reuse/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));

const spatialCases=[];
for(const [name,change,expected] of [
 ['disjoint moving predecessor',f=>f.blocker.position.x-=.1,1],
 ['predecessor enters target tiles',f=>f.blocker.position.x=3,0],
 ['exact target motion inside same tile',f=>f.hidden.position.y=Number.EPSILON,0],
 ['unknown predecessor shader covers every tile',f=>{f.blocker.material=f.material.clone();f.blocker.material.onBeforeCompile=()=>{};},0],
 ['mediump predecessor bounds cover every tile',f=>{f.blocker.material=f.material.clone();f.blocker.material.precision='mediump';f.blocker.position.x-=.1;},0],
 ['camera change invalidates local proof',f=>f.camera.position.x=.1,0],
 ]){
 const f=fixture(true);f.camera.position.z=10;f.blocker.position.x=-3;f.hidden.position.x=3;
 f.frame();f.frame();assert.equal(f.frame().skipped,1);change(f);const result=f.frame();assert.equal(result.skipped,expected,name);spatialCases.push({name,skipped:result.skipped,spatialBounds:result.spatialBounds,fullViewportBounds:result.fullViewportBounds});f.close();
}
const spatialReport={passed:true,cases:spatialCases,limits:'Deterministic proof transport, not actual rasterization. Full browser pixels tested separately.'};
{
 const f=fixture(true);for(let i=0;i<400;i++){const mesh=new T.Mesh(f.geometry,f.material);mesh.name='wide-'+i;f.scene.add(mesh);}
 const result=f.frame();assert.ok(result.spatialBudgetFallback>0);assert.ok(result.tileTouches<=250000);assert.equal(f.state.draws.length,402,'Budget fallback retains every original draw');assert.equal(result.skipped,0);spatialReport.perFrameBudgetPreservesAllDraws=true;f.close();
}
await fs.writeFile('outputs/occlusion-tile-reuse/dependencies-tests.json',JSON.stringify(spatialReport,null,2));console.log(JSON.stringify(spatialReport,null,2));
