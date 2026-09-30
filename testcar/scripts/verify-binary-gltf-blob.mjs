import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {registerHooks} from 'node:module';
import * as T from 'three';
import validator from 'gltf-validator';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
globalThis.FileReader=class {readAsArrayBuffer(blob){blob.arrayBuffer().then(result=>{this.result=result;this.onloadend?.();});}};
const {exportGLB,exportGLBBlob}=await import('../lib/export-model.ts');
const {assembleBinaryGltf}=await import('../lib/binaryGltfBlob.ts');
const root=new T.Group();root.name='MAZ543_REFERENCE_CHASSIS';root.position.set(.123456789,.987654321,-.125);
const material=new T.MeshStandardMaterial({color:0x657341,metalness:.4,roughness:.65});material.clippingPlanes=[new T.Plane(new T.Vector3(0,0,1),.21)];material.wireframe=true;
const glass=new T.MeshPhysicalMaterial({color:0xaaaaff,transmission:.82,roughness:.15,ior:1.42,thickness:.025});
const geometry=new T.BoxGeometry(.1234,.5678,.91011,2,3,4),shape=geometry.attributes.position.clone();
for(let i=0;i<shape.count;i++)shape.setY(i,shape.getY(i)*.81234);geometry.morphAttributes.position=[shape];
const a=new T.Mesh(geometry,material);a.name='spring';a.morphTargetInfluences[0]=.3456789;a.rotation.set(.1234,.9876,-.321);root.add(a);
const b=new T.Mesh(geometry,material);b.name='共享实体_02';b.position.set(-1.35,2.178,3.019);b.scale.set(-1,1.2,.7);b.morphTargetInfluences[0]=.8765432;root.add(b);
const transparent=new T.Mesh(new T.SphereGeometry(.3,12,8),glass);transparent.name='window';root.add(transparent);
const hidden=new T.Mesh(geometry,material);hidden.name='hidden';hidden.visible=false;root.add(hidden);
const originals=new Map([[a.name,material],[b.name,material],[transparent.name,glass],[hidden.name,material]]);
const animations=[new T.AnimationClip('弹簧压缩',1,[new T.NumberKeyframeTrack('spring.morphTargetInfluences[0]',[0,1],[0,1])])];
const results=[];
for(const clips of [[],animations]){
  const baseline=Buffer.from(await exportGLB(root,originals,clips)),blob=await exportGLBBlob(root,originals,clips),candidate=Buffer.from(await blob.arrayBuffer());
  assert.deepEqual(candidate,baseline,'stock exporter and Blob finalizer must be byte-for-byte identical');
  const validation=await validator.validateBytes(new Uint8Array(candidate),{maxIssues:0});assert.equal(validation.issues.numErrors,0);
  results.push({animations:clips.length,bytes:candidate.length,sha256:crypto.createHash('sha256').update(candidate).digest('hex'),byteIdentical:true,validationErrors:validation.issues.numErrors});
}
assert.equal(material.wireframe,true);assert.equal(material.clippingPlanes.length,1);assert.equal(hidden.visible,false);assert.equal(a.morphTargetInfluences[0],.3456789);
// Odd payload and UTF-8 JSON cover both alignment paddings explicitly.
const packed=Buffer.from(await assembleBinaryGltf({name:'中',buffers:[{byteLength:3}]},[new Uint8Array([12,34,56])]).arrayBuffer());
assert.equal(packed.length%4,0);assert.equal(packed.readUInt32LE(8),packed.length);assert.equal(packed.at(-1),0);
const report={passed:true,threeRevision:T.REVISION,cases:results,unalignedPayload:true,utf8Json:true,authoritativeSourcePreserved:true,limits:'Byte equality covers shared geometry/materials, transforms, visibility, morphs, animation and material extensions. Browser image encoding and full native vehicle export are verified separately.'};
await fs.writeFile('outputs/render-worker-evidence/blob-encoding-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
