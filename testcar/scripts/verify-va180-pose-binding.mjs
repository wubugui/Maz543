// Execute the actual viewport binding statement. Static/native/data QA, not browser QA.
import fs from 'node:fs/promises';import assert from 'node:assert/strict';import ts from 'typescript';import * as T from 'three';
const src=await fs.readFile('lib/reviewVehicleAsset.ts','utf8');
const code=ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {selectReviewVehicleAsset,applyReviewNativePoseOffset}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
async function node(p){const b=await fs.readFile(p),j=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));return j.nodes.find(n=>n.name==='cab_pivot_004');}
const old=await node('public/models/maz543a-blender.glb'),now=await node('public/models/review/maz543a-cab-va180-v1.glb');
const nativeQ=new T.Quaternion(...now.rotation).normalize(),oldQ=new T.Quaternion(...old.rotation).normalize();
const normal=new T.Vector3(0,1,0).applyQuaternion(nativeQ);
const line=(await fs.readFile('lib/vehicleViewport.ts','utf8')).split('\n').find(l=>l.includes('for(const {source,target} of bindings)'));
assert.ok(line.includes('applyReviewNativePoseOffset(target,reviewAsset)'));
const bind=new Function('bindings','applyReviewNativePoseOffset','reviewAsset',line);
const modelSource=await fs.readFile('lib/maz543.ts','utf8');assert.ok(modelSource.includes('sw.rotation.z=.3'));assert.ok(modelSource.includes('sw.rotation.y=-c.steering*Math.PI/180*12'));
const source=new T.Object3D(),target=new T.Object3D();source.name=target.name='cab_pivot_004';source.position.fromArray(old.translation);source.quaternion.copy(oldQ);
const asset=selectReviewVehicleAsset('?asset-review=cab-va180-v1',true),spoke=new T.Vector3(.177,0,0);
let maxNormalError=0,maxQuaternionError=0,maxSpokeError=0;
for(let frame=0;frame<721;frame++){
 const steering=(frame-360)/10,spin=-steering*Math.PI/180*12;
 source.rotation.set(0,spin,.3,'XYZ');source.visible=frame%3!==0;
 const before=source.quaternion.clone();
 bind([{source,target}],applyReviewNativePoseOffset,asset);
 const expected=nativeQ.clone().multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,1,0),spin));
 maxNormalError=Math.max(maxNormalError,new T.Vector3(0,1,0).applyQuaternion(target.quaternion).distanceTo(normal));
 maxQuaternionError=Math.max(maxQuaternionError,1-Math.abs(target.quaternion.dot(expected)));
 maxSpokeError=Math.max(maxSpokeError,spoke.clone().applyQuaternion(target.quaternion).distanceTo(spoke.clone().applyQuaternion(expected)));
 assert.ok(target.position.distanceTo(new T.Vector3(...now.translation))<5e-7);assert.ok(source.quaternion.equals(before));assert.equal(source.visible,target.visible);
}
assert.ok(maxNormalError<1e-7);assert.ok(maxQuaternionError<1e-12);assert.ok(maxSpokeError<1e-7);
// Rest-pose native agreement and deliberate old-loop control: the prior binding
// must demonstrably fail the normal-axis invariant at a nonzero steering state.
source.quaternion.copy(oldQ);bind([{source,target}],applyReviewNativePoseOffset,asset);assert.ok(1-Math.abs(target.quaternion.dot(nativeQ))<1e-12);
const oldLoopNormal=new T.Vector3(0,1,0).applyQuaternion(new T.Quaternion().setFromEuler(new T.Euler(0,Math.PI/2,.3)));
assert.ok(oldLoopNormal.distanceTo(normal)>.1);
const unrelated=new T.Object3D();unrelated.name='cab_pivot_006';unrelated.position.set(1,2,3);unrelated.rotation.set(.1,.2,.3);const initial=unrelated.quaternion.clone();applyReviewNativePoseOffset(unrelated,asset);assert.ok(unrelated.quaternion.equals(initial));assert.deepEqual(unrelated.position.toArray(),[1,2,3]);
const r={status:'PASS_CANDIDATE_STEERING_BINDING_ONLY',frames:721,maxNormalError,maxQuaternionError,maxSpokeError,nativeRestRotation:now.rotation,sourceRestRotation:old.rotation,unrelatedPivotUnchanged:true,sourceUnaffected:true,accumulation:false,oldLoopNegativeControl:true,limits:'Synthetic actual binding-loop test with real GLB rest transforms. No browser, full steering linkage, collision, manufacturer geometry or whole-vehicle acceptance.',wholeVehicleAcceptance:'16 OPEN'};
await fs.writeFile('work/cloud-va180-web-20261001/pose-binding.json',JSON.stringify(r,null,2)+'\n');console.log(r);
