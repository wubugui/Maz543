import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {DisplayBatches}=await import('../lib/displayBatches.ts');
const {DisplayInstances,AUTHORITATIVE_PART_LAYER}=await import('../lib/displayInstances.ts');
const {DisplayFrameCache}=await import('../lib/displayFrameCache.ts');
const {RenderResources}=await import('../lib/renderResources.ts');
// GLTFExporter uses FileReader for binary buffers even when images are absent.
globalThis.FileReader=class {readAsArrayBuffer(blob){blob.arrayBuffer().then(r=>{this.result=r;this.onloadend?.();});}readAsDataURL(blob){blob.arrayBuffer().then(r=>{this.result='data:application/octet-stream;base64,'+Buffer.from(r).toString('base64');this.onloadend?.();});}};
const results=[];
for(const Class of [DisplayInstances,DisplayBatches]){
  const root=new T.Group(),moving=new T.Group(),material=new T.MeshStandardMaterial(),geometry=new T.BoxGeometry(.2,.3,.4);
  root.name='vehicle';moving.name='door_joint';root.add(moving);root.position.set(1,2,3);
  const a=new T.Mesh(geometry,material),b=new T.Mesh(geometry,material);
  a.name='part_A';b.name='part_B';a.position.x=-.5;b.position.x=.5;a.userData.partId='A';b.userData.partId='B';moving.add(a,b);
  for(const m of [a,b]){m.castShadow=true;m.receiveShadow=true;}
  root.updateMatrixWorld(true);
  const rawPosition=Buffer.from(geometry.attributes.position.array.buffer).toString('hex'),rawIndex=Buffer.from(geometry.index.array.buffer).toString('hex');
  const exportedBefore=await new GLTFExporter().parseAsync(root,{binary:true});
  const presentation=new Class(root),scene=new T.Scene();scene.add(root,presentation.root);presentation.sync();
  assert.equal(presentation.stats.instances,2);assert.equal(presentation.stats.batches,1);
  const ray=new T.Raycaster(new T.Vector3(.5,2,5),new T.Vector3(0,0,-1));ray.layers.enable(AUTHORITATIVE_PART_LAYER);
  assert.equal(ray.intersectObject(root,true)[0].object,a,'selection keeps original object identity');
  assert.equal(root.getObjectByName('part_A'),a);assert.equal(a.geometry,geometry);assert.equal(a.parent,moving);
  const exportedAfter=await new GLTFExporter().parseAsync(root,{binary:true});
  assert.deepEqual(new Uint8Array(exportedAfter),new Uint8Array(exportedBefore),'actual GLB bytes unchanged by presentation');
  moving.rotation.y=.37;moving.position.z=.42;presentation.sync();
  const proxy=presentation.root.children.find(o=>o.visible),matrix=new T.Matrix4();
  if(Class===DisplayInstances)proxy.getMatrixAt(0,matrix);else proxy.getMatrixAt(0,matrix);
  assert.deepEqual(matrix.elements,a.matrixWorld.elements.map(Math.fround),'latest solved pose reaches display at existing GPU float precision');
  moving.visible=false;presentation.sync();assert.equal(presentation.stats.instances,0);assert.equal(a.visible,true);assert.equal(a.layers.mask,1);
  moving.visible=true;presentation.sync();assert.equal(presentation.stats.instances,2);
  b.material=material.clone();b.material.transparent=true;presentation.sync();assert.equal(b.layers.mask,1,'transparent original retained');
  b.material=material;material.clippingPlanes=[new T.Plane(new T.Vector3(0,0,1),0)];presentation.sync();assert.equal(presentation.stats.instances,0,'section original retained');
  material.clippingPlanes=null;moving.scale.x=-1;presentation.sync();assert.equal(presentation.stats.instances,0,'reflections use original');
  moving.scale.x=1;presentation.sync();assert.equal(presentation.stats.instances,2);
  assert.equal(Buffer.from(geometry.attributes.position.array.buffer).toString('hex'),rawPosition);
  assert.equal(Buffer.from(geometry.index.array.buffer).toString('hex'),rawIndex);
  let copy;
  if(Class===DisplayBatches){
    copy=presentation.auditGeometry();assert.equal(copy.mismatches,0);
    geometry.attributes.position.setX(0,.123);geometry.attributes.position.needsUpdate=true;presentation.sync();assert.equal(presentation.stats.instances,0,'changed geometry cannot use stale display copy');
  }
  let geometryDisposed=false,materialDisposed=false;geometry.addEventListener('dispose',()=>geometryDisposed=true);material.addEventListener('dispose',()=>materialDisposed=true);
  presentation.dispose();assert.equal(a.layers.mask,1);assert.equal(b.layers.mask,1);assert.equal(geometryDisposed,false);assert.equal(materialDisposed,false);
  results.push({class:Class.name,selection:true,actualGlbBytesIdentical:true,pose:true,parentVisibility:true,transparentFallback:true,sectionFallback:true,reflectionFallback:true,sourceBuffersUntouched:true,disposalDoesNotDestroySources:true,geometryCopy:copy});
}
// Different shapes share a material batch without merging their identities.
{
  const root=new T.Group(),mat=new T.MeshStandardMaterial();root.add(new T.Mesh(new T.BoxGeometry(),mat),new T.Mesh(new T.SphereGeometry(),mat));
  const d=new DisplayBatches(root);d.sync();assert.equal(d.stats.instances,2);assert.equal(d.auditGeometry().mismatches,0);d.dispose();
}
{
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(),root=new T.Group(),m=new T.Mesh(new T.BoxGeometry(),new T.MeshStandardMaterial()),cache=new DisplayFrameCache(),revision={};scene.add(root);root.add(m);
  assert.equal(cache.needsRender(scene,camera,revision),true);assert.equal(cache.needsRender(scene,camera,revision),false);
  m.position.x=1e-30;assert.equal(cache.needsRender(scene,camera,revision),true,'no motion epsilon');assert.equal(cache.needsRender(scene,camera,revision),false);
  root.visible=false;assert.equal(cache.needsRender(scene,camera,revision),true);m.position.x=42;assert.equal(cache.needsRender(scene,camera,revision),false,'hidden mechanical poses do not redraw');
  root.visible=true;assert.equal(cache.needsRender(scene,camera,revision),true,'reveal uses latest pose');
  const a=m.geometry.attributes.position.clone();a.array[0]=.123;m.geometry.setAttribute('position',a);assert.equal(cache.needsRender(scene,camera,revision),true,'replacement attributes detected');
  a.needsUpdate=true;assert.equal(cache.needsRender(scene,camera,revision),true);assert.equal(cache.needsRender(scene,camera,revision),false);
  m.material.emissiveIntensity=2;assert.equal(cache.needsRender(scene,camera,revision),true);
  camera.position.z=1;assert.equal(cache.needsRender(scene,camera,revision),true);
  cache.invalidate();assert.equal(cache.needsRender(scene,camera,revision),true);
  results.push({class:'DisplayFrameCache',exactNumericInvalidation:true,hiddenPoseContinues:true,revealLatestPose:true,attributeReplacement:true,attributeUpdate:true,materialUpdate:true,cameraUpdate:true,explicitInvalidation:true});
}
{
  const resources=new RenderResources(),root=new T.Group(),geometry=new T.BoxGeometry(),material=new T.MeshStandardMaterial(),texture=new T.Texture();material.map=texture;material.normalMap=texture;
  root.add(new T.Mesh(geometry,material),new T.Mesh(geometry,material));
  const counts={geometry:0,material:0,texture:0};geometry.addEventListener('dispose',()=>counts.geometry++);material.addEventListener('dispose',()=>counts.material++);texture.addEventListener('dispose',()=>counts.texture++);
  resources.track(root);resources.track(root);resources.dispose();resources.dispose();assert.deepEqual(counts,{geometry:1,material:1,texture:1});
  const late=new T.Mesh(new T.BoxGeometry(),new T.MeshStandardMaterial()),lateTexture=new T.Texture();late.material.map=lateTexture;let released=0;lateTexture.addEventListener('dispose',()=>released++);resources.track(late);assert.equal(released,1);
  results.push({class:'RenderResources',sharedResourcesDisposedOnce:true,materialTexturesDisposed:true,lateAsyncLoadDisposed:true});
}
const report={passed:true,results,limits:'Small constructed scene invariants and actual GLB byte equality. Whole vehicle pixels and performance require separate real-browser evidence.'};
await fs.mkdir('outputs/render-performance-evidence',{recursive:true});await fs.writeFile('outputs/render-performance-evidence/presentation-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
