import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {createStaticOcclusionProbe}=await import('../lib/staticOcclusionProbe.ts');
function fixture(){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(35,1,.05,100),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),mesh=new T.Mesh(geometry,material);scene.add(mesh);camera.position.z=10;camera.updateMatrixWorld();scene.updateMatrixWorld();
 const state={target:null,active:null,lost:false,available:true,depthMask:false,colorMask:true,clearDepth:1,storedDepth:1,created:0,deleted:0,targets:0,disposedTargets:0,readResults:0,fail:false};
 const constants=['DEPTH_WRITEMASK','COLOR_WRITEMASK','DEPTH_CLEAR_VALUE','SAMPLES','DEPTH_BITS','RGBA','UNSIGNED_BYTE','ANY_SAMPLES_PASSED','ANY_SAMPLES_PASSED_CONSERVATIVE','CURRENT_QUERY','QUERY_RESULT_AVAILABLE','QUERY_RESULT'];const gl=Object.fromEntries(constants.map(key=>[key,key]));
 Object.assign(gl,{drawingBufferWidth:800,drawingBufferHeight:600,isContextLost:()=>state.lost,getError:()=>0,readPixels(_x,_y,_w,_h,_format,_type,data){data.fill(20);},getParameter(key){return {DEPTH_WRITEMASK:state.depthMask,COLOR_WRITEMASK:[state.colorMask,state.colorMask,state.colorMask,state.colorMask],DEPTH_CLEAR_VALUE:state.clearDepth,SAMPLES:state.target?.samples??0,DEPTH_BITS:24}[key];},getQuery:()=>state.active,createQuery(){state.created++;return {samples:false};},deleteQuery(query){assert.ok(!query.deleted);query.deleted=true;state.deleted++;},beginQuery(_target,query){assert.equal(state.active,null);state.active=query;},endQuery(){assert.ok(state.active);state.active=null;},getQueryParameter(query,key){assert.ok(!query.deleted);if(key==='QUERY_RESULT_AVAILABLE')return state.available;assert.ok(state.available);state.readResults++;return query.samples;}});
 const seen=new WeakSet(),clearColor=new T.Color(.2,.3,.4);let clearAlpha=.7;
 const renderer={getContext:()=>gl,capabilities:{precision:'highp'},clippingPlanes:[],shadowMap:{autoUpdate:true,needsUpdate:true},autoClear:true,info:{render:{calls:0,triangles:0}},getRenderTarget:()=>state.target,getActiveCubeFace:()=>0,getActiveMipmapLevel:()=>0,getClearColor(target){return target.copy(clearColor);},getClearAlpha:()=>clearAlpha,setClearColor(value,alpha){clearColor.set(value);clearAlpha=alpha;},setRenderTarget(target){state.target=target;if(target&&!seen.has(target)){seen.add(target);state.targets++;target.addEventListener('dispose',()=>state.disposedTargets++);}},state:{buffers:{depth:{setMask(value){state.depthMask=value;},setClear(value){state.clearDepth=value;}},color:{setMask(value){state.colorMask=value;}}}},clear(_color,depth){if(depth&&state.depthMask)state.storedDepth=state.clearDepth;},render(scene,camera){for(const object of scene.children){if(object.material instanceof T.MeshNormalMaterial){if(state.fail)throw new Error('depth fixture failure');state.storedDepth=.5;}this.renderBufferDirect(camera,scene,object.geometry,object.material,object,null);}},renderBufferDirect(_camera,_scene,_geometry,material){this.info.render.calls++;this.info.render.triangles+=2;state.depthMask=material.depthWrite;state.colorMask=material.colorWrite;if(state.active)state.active.samples=material.uniforms.closestDepth.value<=state.storedDepth;}};
 const elements=[],host={appendChild(node){elements.push(node);}},document={createElement(tag){return {tag,style:{},textContent:'',setAttribute(){},remove(){this.removed=true;},onclick:null};}};
 let sourceDisposals=0;geometry.addEventListener('dispose',()=>sourceDisposals++);material.addEventListener('dispose',()=>sourceDisposals++);
 const drawBefore=renderer.renderBufferDirect,probe=createStaticOcclusionProbe(renderer,scene,camera,host,document),[button,output]=elements;
 probe.afterFrame(true,true);probe.afterFrame(true,true);
 const capture=()=>{button.onclick();probe.afterFrame(true,true);};
 const restored=()=>{assert.equal(renderer.renderBufferDirect,drawBefore);assert.equal(state.target,null);assert.equal(renderer.autoClear,true);assert.equal(renderer.shadowMap.autoUpdate,true);assert.equal(renderer.shadowMap.needsUpdate,true);assert.equal(state.depthMask,false);assert.equal(state.colorMask,true);assert.equal(state.clearDepth,1);assert.deepEqual(clearColor.toArray(),[.2,.3,.4]);assert.equal(clearAlpha,.7);assert.equal(sourceDisposals,0);};
 const close=()=>{probe.dispose();probe.dispose();assert.equal(state.created,state.deleted);assert.equal(state.targets,state.disposedTargets);assert.ok(elements.every(node=>node.removed));geometry.dispose();material.dispose();};
 return {state,probe,capture,restored,close,button,output};
}
{
 const f=fixture();f.state.available=false;f.capture();f.restored();f.probe.poll();assert.equal(f.state.readResults,0);assert.equal(f.state.targets,3);f.button.onclick();assert.equal(f.state.targets,3);f.state.available=true;f.probe.poll();const result=JSON.parse(f.output.textContent);assert.equal(result.controlsPassed,true);assert.equal(result.displayDifferentPixels,0);assert.equal(f.state.disposedTargets,3);f.close();
}
{
 const f=fixture();f.state.fail=true;f.capture();f.restored();assert.match(f.output.textContent,/depth fixture failure/);assert.equal(f.state.targets,1);assert.equal(f.state.disposedTargets,1);f.close();
}
{
 const f=fixture();f.state.available=false;f.capture();f.restored();f.state.lost=true;f.probe.poll();assert.equal(f.state.created,f.state.deleted);assert.equal(f.state.targets,f.state.disposedTargets);f.close();
}
{
 const f=fixture();f.state.available=false;f.capture();f.restored();f.close();
}
const result={passed:true,unavailableQueriesNeverRead:true,positiveAndNegativeControlsChecked:true,sourceGeometryAndMaterialsNeverDisposed:true,targetsAndQueriesReleasedOnSuccessFailureContextLossAndDisposal:true,rendererMasksClearStateTargetAndHooksRestored:true,limits:'Controlled WebGL transport with real Three resource objects; actual raster controls and potential occlusion counts require browser validation.'};
await fs.writeFile('outputs/static-occlusion-probe/lifecycle-tests.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
