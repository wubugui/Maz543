import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {NormalOcclusionCache,containsVolume,queryCertificate}=await import('../lib/normalOcclusionCache.ts');
const base={left:10,right:20,bottom:10,top:20,nearDepth:.5};
assert.ok(containsVolume(base,{...base,left:11,nearDepth:.6}));
for(const v of [{left:9},{right:21},{bottom:9},{top:21},{nearDepth:.49},{left:NaN}])assert.equal(containsVolume(base,{...base,...v}),false);
assert.equal(queryCertificate({...base,nearDepth:0},100,80),null);
assert.equal(queryCertificate({...base,left:110,right:120},100,80),null);
assert.ok(containsVolume(queryCertificate(base,100,80),base));
function fixture(){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1.25,.05,100),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),mesh=new T.Mesh(geometry,material),normal=new T.MeshNormalMaterial({blending:T.NoBlending});scene.add(mesh);camera.position.z=10;
 const state={target:null,active:null,lost:false,available:true,depthMask:false,colorMask:true,clearDepth:1,created:0,deleted:0,targets:0,disposedTargets:0,readResults:0,fail:false,badControls:false,draws:0,sourceDisposals:0};
 const depths=new WeakMap(),seen=new WeakSet(),clearColor=new T.Color(.2,.3,.4);let clearAlpha=.7;
 const keys=['DEPTH_WRITEMASK','COLOR_WRITEMASK','DEPTH_CLEAR_VALUE','SAMPLES','DEPTH_BITS','VIEWPORT','ANY_SAMPLES_PASSED','ANY_SAMPLES_PASSED_CONSERVATIVE','CURRENT_QUERY','QUERY_RESULT_AVAILABLE','QUERY_RESULT'];const gl=Object.fromEntries(keys.map(k=>[k,k]));
 Object.assign(gl,{drawingBufferWidth:100,drawingBufferHeight:80,isContextLost:()=>state.lost,getError:()=>0,getParameter(k){return {DEPTH_WRITEMASK:state.depthMask,COLOR_WRITEMASK:[state.colorMask,state.colorMask,state.colorMask,state.colorMask],DEPTH_CLEAR_VALUE:state.clearDepth,SAMPLES:state.target?.samples??0,DEPTH_BITS:24,VIEWPORT:[0,0,100,80]}[k];},getQuery:()=>state.active,createQuery(){state.created++;return {samples:false};},deleteQuery(q){assert.ok(!q.deleted);q.deleted=true;state.deleted++;},beginQuery(_t,q){assert.equal(state.active,null);state.active=q;},endQuery(){assert.ok(state.active);state.active=null;},getQueryParameter(q,k){assert.ok(!q.deleted);if(k==='QUERY_RESULT_AVAILABLE')return state.available;assert.ok(state.available);state.readResults++;return q.samples;}});
 const renderer={getContext:()=>gl,capabilities:{precision:'highp'},clippingPlanes:[],shadowMap:{autoUpdate:true,needsUpdate:true},autoClear:true,getRenderTarget:()=>state.target,getActiveCubeFace:()=>0,getActiveMipmapLevel:()=>0,getClearColor(t){return t.copy(clearColor);},getClearAlpha:()=>clearAlpha,setClearColor(v,a){clearColor.set(v);clearAlpha=a;},setRenderTarget(t){state.target=t;if(t&&!seen.has(t)){seen.add(t);state.targets++;t.addEventListener('dispose',()=>state.disposedTargets++);}},state:{buffers:{depth:{setMask(v){state.depthMask=v;},setClear(v){state.clearDepth=v;}},color:{setMask(v){state.colorMask=v;}}}},clear(_c,d){if(d&&state.depthMask)depths.set(state.target,state.clearDepth);},render(s,c){for(const o of s.children){if(o.material instanceof T.MeshNormalMaterial){assert.equal(o.material,normal,'Snapshot borrows exact pass material');if(state.fail)throw new Error('depth fixture failure');depths.set(state.target,.5);}this.renderBufferDirect(c,s,o.geometry,o.material,o,null);}},renderBufferDirect(_c,_s,_g,m){state.draws++;state.depthMask=m.depthWrite;state.colorMask=m.colorWrite;if(state.active)state.active.samples=state.target.width===1&&state.badControls?false:m.uniforms.closestDepth.value<=depths.get(state.target);}};
 const original=renderer.renderBufferDirect;for(const resource of [geometry,material,normal])resource.addEventListener('dispose',()=>state.sourceDisposals++);
 const cache=new NormalOcclusionCache(renderer,normal);
 const draw=()=>{scene.overrideMaterial=normal;try{renderer.renderBufferDirect(camera,scene,geometry,normal,mesh,null);}finally{scene.overrideMaterial=null;}renderer.renderBufferDirect(camera,scene,geometry,material,mesh,null);};
 const run=(allowed=true)=>cache.render(scene,camera,allowed,draw);
 const restored=()=>{assert.equal(renderer.renderBufferDirect,original);assert.equal(state.target,null);assert.equal(normal.colorWrite,true);assert.equal(renderer.autoClear,true);assert.equal(renderer.shadowMap.autoUpdate,true);assert.equal(renderer.shadowMap.needsUpdate,true);assert.equal(state.clearDepth,1);assert.deepEqual(clearColor.toArray(),[.2,.3,.4]);assert.equal(clearAlpha,.7);assert.equal(state.sourceDisposals,0);};
 const close=()=>{cache.dispose();cache.dispose();assert.equal(state.created,state.deleted);assert.equal(state.targets,state.disposedTargets);restored();};
 const warm=()=>{run();run();const r=run();assert.equal(r.skipped,1);assert.equal(r.savedTriangles,12);assert.equal(r.queried,0);restored();return r;};
 return {state,cache,scene,camera,mesh,geometry,normal,renderer,original,run,draw,restored,close,warm};
}
{
 const f=fixture();f.state.available=false;f.run();f.run();f.run();assert.equal(f.state.readResults,0);f.state.available=true;assert.equal(f.run().skipped,1);f.restored();f.close();
}
for(const change of [f=>f.mesh.position.x+=1,f=>f.geometry.attributes.position.needsUpdate=true,f=>f.geometry.boundingSphere.radius+=1,f=>f.mesh.layers.mask=2,f=>f.scene.remove(f.mesh),f=>f.camera.position.x+=.1]){
 const f=fixture();f.warm();change(f);assert.equal(f.run().skipped,0);f.close();
}
{
 const f=fixture(),occluder=new T.Mesh(f.geometry,f.mesh.material);f.scene.add(occluder);f.run();f.mesh.position.x+=.001;f.run();f.mesh.position.x+=.001;assert.equal(f.run().skipped,1,'Moving candidate can reuse a contained proof without becoming an occluder');
 f.mesh.position.x+=.001;const before=f.state.draws;assert.equal(f.run().skipped,1);assert.equal(f.state.draws-before,1,'Original color draw remains');
 f.mesh.position.x+=1;assert.equal(f.run().skipped,0,'Leaving certified region restores original draw immediately');f.close();
}
{
 const f=fixture();f.scene.add(new T.Mesh(f.geometry,f.mesh.material));f.run();f.mesh.position.x+=.001;f.run();assert.equal(f.run().certificates,2);f.scene.remove(f.mesh);assert.equal(f.run().certificates,1,'Removed moving candidates are not retained by certificate map');f.close();
}
{
 const f=fixture();f.warm();assert.equal(f.run(false).skipped,0);f.run();f.normal.alphaTest=.1;assert.equal(f.run().skipped,0);f.close();
}
{
 const f=fixture();f.warm();f.geometry.dispose();assert.equal(f.state.sourceDisposals,1);f.state.sourceDisposals=0;assert.equal(f.run().skipped,0);f.close();
}
{
 const f=fixture();f.state.badControls=true;f.run();f.run();const r=f.run();assert.equal(r.controlsFailed,true);assert.equal(r.skipped,0);f.close();
}
{
 const f=fixture();f.state.fail=true;f.run();const r=f.run();assert.match(r.error,/depth fixture failure/);assert.equal(r.skipped,0);f.restored();f.close();
}
{
 const f=fixture();f.state.available=false;f.run();f.run();f.state.lost=true;assert.equal(f.run().skipped,0);f.close();
}
{
 const f=fixture();f.warm();assert.throws(()=>f.cache.render(f.scene,f.camera,true,()=>{throw new Error('product draw failed');}),/product draw failed/);assert.equal(f.renderer.renderBufferDirect,f.original);f.close();
}
const report={passed:true,conservativeContainmentAndNearPlaneFallback:true,exactNormalMaterialBorrowed:true,unavailableQueriesNeverRead:true,controlsRequired:true,poseGeometrySphereLayersVisibilityCameraChangesRestoreDrawing:true,unsupportedPassFallback:true,drawExceptionsRestoreHookAndInvalidate:true,ownedResourcesReleasedOnFailureContextLossAndDisposal:true,sourceResourcesRetained:true,limits:'Real Three objects with controlled WebGL query transport; no claim of actual raster equality or speed without browser evidence.'};
await fs.mkdir('outputs/normal-occlusion-cache',{recursive:true});await fs.writeFile('outputs/normal-occlusion-cache/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
