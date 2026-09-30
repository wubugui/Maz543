import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(error){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw error;}}});
const {PartitionedShadowCache}=await import('../lib/partitionedShadowCache.ts');
const scene=new T.Scene(),camera=new T.PerspectiveCamera(),light=new T.DirectionalLight();
light.position.set(3,8,4);light.castShadow=true;scene.add(light,light.target);
const material=new T.MeshStandardMaterial({transparent:true,side:T.DoubleSide}),a=new T.Mesh(new T.BoxGeometry(),material),b=new T.Mesh(new T.BoxGeometry(),material);
a.castShadow=b.castShadow=true;b.position.x=2;scene.add(a,b);
light.shadow.map=new T.WebGLRenderTarget(512,512,{depthTexture:new T.DepthTexture(512,512,T.UnsignedIntType)});
const sourceMap=light.shadow.map,depthSets=new WeakMap();let target=null,throwDraw=false;
const renderer={
 shadowMap:{enabled:true,autoUpdate:true,needsUpdate:false,type:T.PCFShadowMap,render(lights,s,c){
   if(!this.autoUpdate&&!this.needsUpdate)return;
   const before=target;target=light.shadow.map;renderer.clear();
   s.traverseVisible(o=>{if(o instanceof T.Mesh&&o.castShadow&&o.material.visible&&o.layers.test(c.layers))renderer.renderBufferDirect(light.shadow.camera,null,o.geometry,new T.MeshDepthMaterial(),o,null);});
   target=before;this.needsUpdate=false;light.shadow.needsUpdate=false;
 }},
 capabilities:{logarithmicDepthBuffer:false,reversedDepthBuffer:false},localClippingEnabled:true,clippingPlanes:[],
 renderBufferDirect(c,s,g,m,o){if(throwDraw)throw new Error('injected source draw failure');depthSets.get(target.depthTexture).add(o);},
 clear(){depthSets.set(target.depthTexture,new Set());},
 copyTextureToTexture(src,dst){depthSets.set(dst,new Set(depthSets.get(src)));target=null;},
 getRenderTarget(){return target;},getActiveCubeFace(){return 0;},getActiveMipmapLevel(){return 0;},setRenderTarget(t){target=t;},
};
const original={shadow:renderer.shadowMap.render,draw:renderer.renderBufferDirect,clear:renderer.clear};
const cache=new PartitionedShadowCache();
const draw=()=>{renderer.shadowMap.render([light],scene,camera);material.needsUpdate=true;material.needsUpdate=true;renderer.shadowMap.render([light],scene,camera);};
const run=()=>{
 const report=cache.render(scene,camera,light,renderer,draw);
 assert.equal(light.shadow.map,sourceMap);assert.equal(renderer.shadowMap.render,original.shadow);assert.equal(renderer.renderBufferDirect,original.draw);assert.equal(renderer.clear,original.clear);assert.equal(renderer.shadowMap.autoUpdate,true);
 assert.deepEqual([...depthSets.get(sourceMap.depthTexture)].sort((a,b)=>a.id-b.id),[a,b].filter(o=>o.visible&&o.material.visible).sort((a,b)=>a.id-b.id),'composed depth includes every current source caster');return report;
};
assert.equal(run().dynamicDraws,2,'first frame all source casters dynamic');
assert.equal(run().staticDraws,2,'unchanged poses enter static subset');
let stable=run();assert.equal(stable.staticRefreshed,false);assert.equal(stable.staticDraws,0);assert.equal(stable.dynamicDraws,0);assert.equal(stable.depthCopies,1);
b.position.x+=1e-12;let motion=run();assert.equal(motion.dynamicDraws,1);assert.equal(motion.staticDraws,1);assert.equal(motion.staticRefreshed,true,'moving mesh removed from old static map');
b.position.x+=1e-12;motion=run();assert.equal(motion.dynamicDraws,1);assert.equal(motion.staticDraws,0);assert.equal(motion.staticRefreshed,false,'continuous dynamic movement reuses unchanged source subset');
run();run();
a.geometry.attributes.position.needsUpdate=true;assert.equal(run().staticRefreshed,true,'geometry upload invalidates static depth');assert.equal(run().staticRefreshed,false);
light.position.x+=1e-12;assert.equal(run().staticRefreshed,true,'full precision light transform');assert.equal(run().staticRefreshed,false);
a.visible=false;assert.equal(run().staticRefreshed,true,'removed source clears its old cached depth');a.visible=true;assert.equal(run().staticRefreshed,true);
material.alphaTest=.2;assert.equal(run().staticRefreshed,true,'depth material input invalidates');
b.morphTargetInfluences=[1e-15];assert.equal(run().dynamicDraws,1,'morph weights compare at full precision');
sourceMap.depthTexture.dispose();assert.equal(run().staticRefreshed,true,'source depth disposal invalidates');
a.onBeforeShadow=()=>{};assert.equal(run().eligible,false,'unsupported callback falls back to original whole depth pass');a.onBeforeShadow=T.Object3D.prototype.onBeforeShadow;
run();throwDraw=true;cache.invalidate();assert.throws(()=>run(),/injected source draw failure/);
assert.equal(light.shadow.map,sourceMap);assert.equal(renderer.shadowMap.render,original.shadow);assert.equal(renderer.renderBufferDirect,original.draw);assert.equal(renderer.clear,original.clear);assert.equal(renderer.shadowMap.autoUpdate,true);assert.equal(target,null,'failed internal shadow draw restores the prior render target');
throwDraw=false;assert.equal(run().staticRefreshed,true);cache.dispose();cache.dispose();
const result={passed:true,firstFrameAllDynamic:true,continuousMotionReusesStaticSubset:true,subFloat32PoseAndMorphChecked:true,sourceDepthSetComplete:true,geometryMaterialLightVisibilityDisposalInvalidate:true,stockDoubleSideVersionsAccepted:true,originalHooksAndMapRestoredOnException:true,limits:'Real Three inputs and mocked stock submission/depth copy; actual WebGL pixel comparison is separate.'};
await fs.mkdir('outputs/partitioned-shadow',{recursive:true});await fs.writeFile('outputs/partitioned-shadow/tests.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
