import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {replayOriginalPassDepth}=await import('../lib/originalPassDepthReplay.ts');
function fixture(){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),normal=new T.MeshNormalMaterial(),mesh=new T.Mesh(geometry,material);scene.add(mesh);
 const a=new T.WebGLRenderTarget(100,80,{samples:4,type:T.HalfFloatType}),b=new T.WebGLRenderTarget(100,80,{samples:2,type:T.HalfFloatType}),n=new T.WebGLRenderTarget(100,80,{samples:0,type:T.HalfFloatType});n.depthTexture=new T.DepthTexture(100,80);
 const sources=new Set([a,b,n]),seen=new Set(),properties=new WeakMap(),programs=new WeakMap(),trace=[];
 const state={target:null,depthMask:true,colorMask:true,clearDepth:1,viewport:new T.Vector4(0,0,100,80),scissor:new T.Vector4(0,0,100,80),scissorTest:false,ownedTargets:0,disposedTargets:0,ownedDepths:0,disposedDepths:0,sourceDisposals:0,mismatch:false,matrixChange:false,worldChange:false,morphChange:false,handleChange:false,fail:false};
 const keys=['DEPTH_WRITEMASK','COLOR_WRITEMASK','DEPTH_CLEAR_VALUE','VIEWPORT','SCISSOR_BOX','SCISSOR_TEST','SAMPLES','DEPTH_BITS'];const gl=Object.fromEntries(keys.map(k=>[k,k]));
 Object.assign(gl,{isContextLost:()=>false,getError:()=>0,getParameter(k){return {DEPTH_WRITEMASK:state.depthMask,COLOR_WRITEMASK:[state.colorMask,state.colorMask,state.colorMask,state.colorMask],DEPTH_CLEAR_VALUE:state.clearDepth,VIEWPORT:state.viewport.toArray(),SCISSOR_BOX:state.scissor.toArray(),SCISSOR_TEST:state.scissorTest,SAMPLES:state.target?.samples??0,DEPTH_BITS:24}[k];}});
 const renderer={getContext:()=>gl,xr:{enabled:false},capabilities:{},clippingPlanes:[],properties:{get(m){if(!properties.has(m))properties.set(m,{});return properties.get(m);}},getRenderTarget:()=>state.target,getActiveCubeFace:()=>0,getActiveMipmapLevel:()=>0,setRenderTarget(t){state.target=t;if(t){state.viewport.copy(t.viewport);state.scissor.copy(t.scissor);state.scissorTest=t.scissorTest;}if(t&&!sources.has(t)&&!seen.has(t)){seen.add(t);state.ownedTargets++;t.addEventListener('dispose',()=>{state.disposedTargets++;t.depthTexture?.dispose();});if(t.depthTexture){state.ownedDepths++;t.depthTexture.addEventListener('dispose',()=>state.disposedDepths++);}}},state:{buffers:{depth:{setMask(v){state.depthMask=v;},setClear(v){state.clearDepth=v;}},color:{setMask(v){state.colorMask=v;}}},viewport(v){state.viewport.copy(v);},scissor(v){state.scissor.copy(v);},setScissorTest(v){state.scissorTest=v;}},clear(){},renderBufferDirect(...args){assert.equal(this,renderer);const m=args[3],owned=!sources.has(state.target);if(owned&&state.fail)throw new Error('fixture replay failure');if(!programs.has(m))programs.set(m,{id:programs.size??0,program:{}});this.properties.get(m).currentProgram=owned&&state.mismatch?{id:-1,program:{}}:programs.get(m);if(!owned)trace.push(args);state.colorMask=m.colorWrite;state.depthMask=m.depthWrite;}};
 const originalDraw=renderer.renderBufferDirect,originalAfter=scene.onAfterRender;
 const one=(target,m)=>{renderer.setRenderTarget(target);mesh.modelViewMatrix.identity();mesh.normalMatrix.identity();renderer.renderBufferDirect(camera,scene,geometry,m,mesh,null);};
 const end=()=>{if(state.matrixChange)mesh.modelViewMatrix.elements[12]=1;if(state.worldChange)mesh.matrixWorld.elements[12]=1;if(state.morphChange)mesh.morphTargetInfluences=[1];if(state.handleChange)renderer.properties.get(material).currentProgram.program={};scene.onAfterRender(renderer,scene,camera);};
 const draw=()=>{one(a,material);one(b,material);end();scene.overrideMaterial=normal;one(n,normal);end();scene.overrideMaterial=null;renderer.setRenderTarget(null);};
 for(const resource of [geometry,material,normal,a,b,n,n.depthTexture])resource.addEventListener('dispose',()=>state.sourceDisposals++);
 const run=()=>replayOriginalPassDepth(renderer,scene,camera,new Set([mesh]),draw);
 const restored=()=>{assert.equal(renderer.renderBufferDirect,originalDraw);assert.equal(scene.onAfterRender,originalAfter);assert.equal(material.colorWrite,true);assert.equal(normal.colorWrite,true);assert.equal(state.target,null);assert.equal(state.clearDepth,1);assert.equal(state.sourceDisposals,0);assert.equal(state.disposedTargets,state.ownedTargets);assert.equal(state.disposedDepths,state.ownedDepths);};
 const close=()=>{restored();for(const resource of [geometry,material,normal,a,b,n,n.depthTexture])resource.dispose();};
 return {scene,camera,geometry,material,normal,mesh,renderer,state,trace,draw,run,restored,close,originalDraw,originalAfter};
}
{
 const f=fixture();f.draw();const expected=f.trace.slice();f.trace.length=0;const r=f.run();assert.deepEqual(f.trace,expected);assert.equal(r.recordedDraws,3);assert.equal(r.replayedDraws,3);assert.equal(r.programMatches,3);assert.equal(r.programMismatches,0);assert.equal(r.replayedTriangles,36);assert.deepEqual(r.passes.map(p=>p.actualSamples),[4,2,0]);assert.deepEqual(r.errors,[]);f.close();
}
{
 const f=fixture();f.state.mismatch=true;const r=f.run();assert.equal(r.programMismatches,3);assert.equal(r.programMatches,0);f.close();
}
{
 const f=fixture();f.state.matrixChange=true;const r=f.run();assert.equal(r.matrixMismatches,3);assert.equal(r.replayedDraws,0);f.close();
}
for(const flag of ['worldChange','morphChange']){
 const f=fixture();f.state[flag]=true;const r=f.run();assert.equal(r.matrixMismatches,2);assert.equal(r.replayedDraws,1);f.close();
}
{
 const f=fixture();f.state.handleChange=true;const r=f.run();assert.equal(r.programMismatches,2);assert.equal(r.programMatches,1);f.close();
}
{
 const f=fixture();f.state.fail=true;const r=f.run();assert.equal(r.errors.length,3);assert.ok(r.errors.every(e=>e.includes('fixture replay failure')));assert.equal(f.trace.length,3);f.close();
}
{
 const f=fixture();const r=replayOriginalPassDepth(f.renderer,f.scene,f.camera,new Set([f.mesh]),f.draw,()=>{throw new Error('fixture snapshot consumer failed');});assert.equal(r.errors.length,3);assert.equal(f.trace.length,3);f.close();
}
{
 const f=fixture();assert.throws(()=>replayOriginalPassDepth(f.renderer,f.scene,f.camera,new Set([f.mesh]),()=>{throw new Error('source draw failed');}),/source draw failed/);f.close();
}
const report={passed:true,originalSourceDrawArgumentsAndOrderRetained:true,linkedProgramIdentityChecked:true,matrixMismatchStopsReplay:true,matchingSamplesAndDepthChecked:true,sourceDrawsContinueAfterSnapshotFailure:true,sourceGeometryMaterialsAndTargetsNeverDisposed:true,ownedTargetsAndDepthTexturesDisposedExactlyOnce:true,hooksAndMaterialStateRestoredOnSuccessAndFailure:true,limits:'Actual Three objects with controlled renderer/program transport. Actual driver program identity, target compatibility and unchanged product pixels require browser evidence.'};
await fs.mkdir('outputs/original-pass-depth-replay',{recursive:true});await fs.writeFile('outputs/original-pass-depth-replay/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
