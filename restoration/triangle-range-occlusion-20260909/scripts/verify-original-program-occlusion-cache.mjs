import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {OriginalProgramOcclusionCache,materialDepthSignature}=await import('../lib/originalProgramOcclusionCache.ts');
const {ConservativeRasterBounds}=await import('../lib/conservativeRasterBounds.ts');
const {queryCertificate}=await import('../lib/normalOcclusionCache.ts');
const {createTriangleRangeProxies}=await import('../lib/triangleRangeProxies.ts');
function fixture(){
 const scene=new T.Scene(),camera=new T.PerspectiveCamera(40,1,.1,100),normal=new T.MeshNormalMaterial(),material=new T.MeshStandardMaterial(),geometry=new T.BoxGeometry(),mesh=new T.Mesh(geometry,material),target=new T.WebGLRenderTarget(100,100,{samples:2});
 mesh.position.z=-10;scene.add(mesh);scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
 const state={target:null,selected:{program:{}},prior:{program:{}},draws:0,trace:[],setup:0,fail:false,samples:2,viewport:[0,0,100,100]};
 const gl={TRIANGLES:4,UNSIGNED_SHORT:5123,UNSIGNED_INT:5125,SAMPLES:1,DEPTH_BITS:2,VIEWPORT:3,drawingBufferWidth:100,drawingBufferHeight:100,isContextLost:()=>false,getParameter(k){return k===1?state.samples:k===2?24:state.viewport;},drawElements(mode,count,type,offset){assert.equal(this,gl);state.draws++;state.trace.push({count,type,offset});},drawArrays(mode,first,count){assert.equal(this,gl);state.draws++;state.trace.push({first,count});}};
 const properties=new WeakMap();const renderer={xr:{enabled:false},capabilities:{precision:'highp'},clippingPlanes:[],localClippingEnabled:true,shadowMap:{enabled:true,type:T.PCFSoftShadowMap},toneMapping:T.AgXToneMapping,outputColorSpace:T.SRGBColorSpace,getContext:()=>gl,getRenderTarget:()=>state.target,properties:{get(m){if(!properties.has(m))properties.set(m,{currentProgram:state.prior});return properties.get(m);}},info:{render:{calls:0,triangles:0}},renderBufferDirect(...args){assert.equal(this,renderer);state.setup++;this.properties.get(args[3]).currentProgram=state.selected;if(state.fail)throw new Error('source failure');const count=state.count??36;if(state.useArrays)gl.drawArrays(gl.TRIANGLES,state.first??0,count);else gl.drawElements(gl.TRIANGLES,count,state.elementType??0,state.offset??0);this.info.render.calls++;this.info.render.triangles+=count/3;}};
 const original=renderer.renderBufferDirect,elements=gl.drawElements,arrays=gl.drawArrays;
 const cache=new OriginalProgramOcclusionCache(renderer,normal),bounds=new ConservativeRasterBounds(),matrix=new T.Matrix4().multiplyMatrices(camera.matrixWorldInverse,mesh.matrixWorld),volume=bounds.volume(geometry,matrix,camera.projectionMatrix,[0,0,100,100]),proof=queryCertificate(volume,100,100);
 assert.ok(proof);cache.global=cache.signature(scene,camera);assert.ok(cache.global,'Stock material configuration must be supported');
 const sig=t=>[t,t.width,t.height,t.depth,t.samples,t.depthBuffer,t.stencilBuffer,t.depthTexture,t.depthTexture?.type,t.depthTexture?.format,t.textures.length,...t.textures.flatMap(x=>[x,x.type,x.format,x.internalFormat,x.colorSpace]),...t.viewport.toArray(),...t.scissor.toArray(),t.scissorTest];
 cache.ready=true;cache.passes=[{target,signature:sig(target),samples:2,depthBits:24,viewport:[0,0,100,100],normalOverride:false,rangeProofs:new Map(),programs:new Map([[mesh,[{target,mesh,material,program:state.selected,linked:state.selected.program,normalOverride:false}]]]),proofs:new Map([[mesh,{volume:proof,zero:true}]])}];
 const source=(cam=camera,sc=scene,m=material)=>renderer.renderBufferDirect(cam,sc,geometry,m,mesh,null);
 const draw=()=>{state.target=target;try{source();}finally{state.target=null;}};
 const restored=()=>{assert.equal(renderer.renderBufferDirect,original);assert.equal(gl.drawElements,elements);assert.equal(gl.drawArrays,arrays);};
 return {cache,renderer,scene,camera,normal,material,geometry,mesh,target,state,gl,source,draw,restored,run:()=>cache.render(scene,camera,true,draw),close(){cache.dispose();geometry.dispose();material.dispose();normal.dispose();target.dispose();restored();}};
}
{
 const f=fixture(),r=f.run();assert.equal(r.skipped,1);assert.equal(r.savedTriangles,12);assert.equal(f.state.setup,1);assert.equal(f.state.draws,0);assert.equal(f.renderer.info.render.calls,0);assert.equal(f.renderer.info.render.triangles,0);f.close();
}
{
 const f=fixture();f.state.useArrays=true;const r=f.run();assert.equal(r.skipped,1);assert.equal(f.state.draws,0);assert.equal(f.state.setup,1);f.close();
}
{
 const f=fixture();f.state.selected={program:{}};const r=f.run();assert.equal(r.skipped,0);assert.equal(r.programFallbacks,1);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();f.mesh.position.x=5;const r=f.run();assert.equal(r.skipped,0);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();f.state.samples=4;const r=f.run();assert.equal(r.skipped,0);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();const transparent=new T.MeshPhysicalMaterial({transparent:true,opacity:.5});
 const report=f.cache.render(f.scene,f.camera,true,()=>{f.state.target=f.target;f.source(new T.PerspectiveCamera(),null);f.source(f.camera,f.scene,transparent);f.source();f.state.target=null;});
 assert.equal(report.skipped,1);assert.equal(f.state.draws,2);assert.equal(f.state.setup,3);assert.equal(f.renderer.info.render.calls,2);assert.equal(f.renderer.info.render.triangles,24);transparent.dispose();f.close();
}
{
 const f=fixture();f.state.fail=true;assert.throws(()=>f.run(),/source failure/);f.restored();assert.equal(f.cache.ready,false);f.close();
}
{
 const f=fixture();f.material.side=T.BackSide;const report=f.run();assert.equal(report.skipped,0);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();f.cache.retained.set(f.mesh,[]);const report=f.run();assert.equal(report.excludedChanged,1);assert.equal(report.skipped,0);f.close();
}
{
 const f=fixture();f.cache.watch(f.geometry);f.geometry.dispose();assert.equal(f.cache.ready,false);assert.equal(f.cache.watched.size,0);f.close();
}
{
 const f=fixture();f.target.setSize(120,100);assert.equal(f.run().skipped,0);f.close();
}
{
 const f=fixture();f.cache.ready=false;f.cache.pending=true;f.cache.queries={poll:()=>null,cancel(){},dispose(){}};assert.equal(f.run().skipped,0);assert.equal(f.state.draws,1);assert.equal(f.cache.pending,true);f.close();
}
{
 const f=fixture();f.cache.ready=false;f.cache.pending=true;f.cache.queries={poll:()=>({summary:{controlsPassed:false,queryError:0,passes:[]},results:[]}),cancel(){},dispose(){}};const report=f.run();assert.equal(report.skipped,0);assert.match(report.error,/controls failed/);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();f.state.selected.program={};assert.equal(f.run().skipped,0);assert.equal(f.state.draws,1);f.close();
}
{
 const f=fixture();const absent=new T.Mesh();f.cache.passes[0].programs.set(absent,[]);f.run();assert.equal(f.cache.passes[0].programs.has(absent),false);f.close();
}
{
 const m=new T.MeshPhysicalMaterial();assert.ok(materialDepthSignature(m));const before=materialDepthSignature(m);m.normalScale.x=2;assert.notDeepEqual(materialDepthSignature(m),before);m.displacementMap=new T.Texture();assert.equal(materialDepthSignature(m),null);m.displacementMap.dispose();m.dispose();
}
function seedRanges(f){
 const set=createTriangleRangeProxies(f.geometry,1);assert.ok(set);f.cache.rangeMode=true;f.cache.rangeSets.set(f.geometry,set);f.cache.meshRanges.set(f.mesh,set.ranges);f.cache.passes[0].proofs.get(f.mesh).zero=false;
 const bounds=new ConservativeRasterBounds(),matrix=new T.Matrix4().multiplyMatrices(f.camera.matrixWorldInverse,f.mesh.matrixWorld);f.cache.passes[0].rangeProofs.set(f.mesh,new Map(set.ranges.map((range,i)=>[range.start,{count:range.count,zero:i%2===1,volume:queryCertificate(bounds.volume(range.bounds,matrix,f.camera.projectionMatrix,[0,0,100,100]),100,100)}])));return set;
}
for(const bytes of [2,4]){
 const f=fixture();if(bytes===4)f.geometry.setIndex(new T.BufferAttribute(Uint32Array.from(f.geometry.index.array),1));f.state.elementType=bytes===2?5123:5125;seedRanges(f);
 const r=f.run();assert.equal(r.rangeSourceDraws,1);assert.equal(r.rangeSubmittedDraws,6);assert.equal(r.rangeSavedTriangles,6);assert.equal(r.skipped,-5);assert.equal(f.renderer.info.render.calls,6);assert.equal(f.renderer.info.render.triangles,6);assert.equal(f.state.setup,1);assert.deepEqual(f.state.trace.map(t=>[t.offset,t.count]),[0,6,12,18,24,30].map(start=>[start*bytes,3]));f.close();
}
{
 const f=fixture();f.geometry.setIndex(null);f.state.count=24;f.state.useArrays=true;seedRanges(f);const r=f.run();assert.equal(r.rangeSavedTriangles,4);assert.equal(r.rangeSubmittedDraws,4);assert.deepEqual(f.state.trace.map(t=>[t.first,t.count]),[[0,3],[6,3],[12,3],[18,3]]);assert.equal(f.renderer.info.render.calls,4);assert.equal(f.renderer.info.render.triangles,4);f.close();
}
{
 const f=fixture();f.state.elementType=5123;f.state.offset=2;f.state.count=33;seedRanges(f);const r=f.run();assert.equal(r.rangeSourceDraws,0);assert.equal(r.savedTriangles,0);assert.deepEqual(f.state.trace,[{offset:2,count:33,type:5123}]);f.close();
}
{
 const f=fixture();const set=seedRanges(f);f.geometry.attributes.position.needsUpdate=true;assert.equal(f.run().skipped,0);assert.equal(set.ranges.length,0);f.close();
}
const report={passed:true,originalProgramSelectedBeforeSkip:true,stalePriorProgramNotUsed:true,programMismatchFallsBack:true,originalUniformSetupRetained:true,volumeEscapeAndRasterMismatchFallBack:true,originalShadowAndTransparentDrawsRetained:true,submittedCallAndTriangleAccounting:true,sourceExceptionRestoresHooks:true,materialTargetOccluderChangesInvalidate:true,disposedGeometryReleasesCertificates:true,rangeIndexByteOffsetsAndArrayStartsPreserved:true,rangeAdditionalDrawsAndSavedTrianglesAccounted:true,unalignedPrimitiveAssemblyFallsBack:true,rangeResourcesReleasedOnAttributeChange:true,limits:'Actual Three objects and conservative bounds with controlled GL transport. Actual depth controls, pixels, animation and stable frame interval still require browser verification.'};
await fs.mkdir('outputs/original-program-occlusion-cache',{recursive:true});await fs.writeFile('outputs/original-program-occlusion-cache/tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
