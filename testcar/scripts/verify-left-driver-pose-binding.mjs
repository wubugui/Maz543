// Execute the real binding-loop statement against actual exported steering-node transforms.
import fs from 'node:fs/promises';import assert from 'node:assert/strict';import ts from 'typescript';import * as T from 'three';
const root=new URL('../',import.meta.url),source=await fs.readFile(new URL('lib/reviewVehicleAsset.ts',root),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {selectReviewVehicleAsset,applyReviewNativePoseOffset}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
async function node(path){const b=await fs.readFile(new URL(path,root)),j=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));return j.nodes.find(n=>n.name==='cab_pivot_004');}
const original=await node('public/models/maz543a-blender.glb'),candidate=await node('public/models/review/maz543a-left-driver-v1.glb');assert.ok(original&&candidate);
function object(n){const o=new T.Object3D();o.name=n.name;o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);return o;}
const runtime=await fs.readFile(new URL('lib/vehicleViewport.ts',root),'utf8');const line=runtime.split('\n').find(l=>l.includes('for(const {source,target} of bindings)'));assert.ok(line?.includes('applyReviewNativePoseOffset(target,reviewAsset)'));
const bind=new Function('bindings','applyReviewNativePoseOffset','reviewAsset',line);const rows=[];
for(const kind of ['production','tyre-v2','hood-tyre-v1','left-driver-v1']){
 const asset=selectReviewVehicleAsset(kind==='production'?'':'?asset-review='+kind,true),s=object(original),target=object(candidate),expectedOffset=kind==='left-driver-v1'?2.05:0;
 const initial=s.position.clone();
 for(let frame=0;frame<120;frame++){
  s.rotation.y=Math.sin(frame*.13)*Math.PI;s.visible=frame%3!==0;
  const before=s.matrix.clone(),sourcePosition=s.position.clone(),sourceQuaternion=s.quaternion.clone();
  bind([{source:s,target}],applyReviewNativePoseOffset,asset);
  assert.ok(target.position.distanceTo(sourcePosition.clone().add(new T.Vector3(0,0,expectedOffset)))<1e-12);
  assert.ok(target.quaternion.equals(sourceQuaternion));assert.ok(target.scale.equals(s.scale));assert.equal(target.visible,s.visible);assert.ok(s.position.equals(initial));assert.ok(s.matrix.equals(before));
 }
 if(kind==='left-driver-v1')assert.ok(target.position.distanceTo(object(candidate).position)<5e-7,'Actual native and bound wheel positions differ');
 rows.push({kind,frames:120,sourceUnaffected:true,accumulation:false,offsetZ:expectedOffset});
}
const unrelated=new T.Object3D();unrelated.name='cab_pivot_006';unrelated.position.set(1,2,3);applyReviewNativePoseOffset(unrelated,selectReviewVehicleAsset('?asset-review=left-driver-v1',true));assert.deepEqual(unrelated.position.toArray(),[1,2,3]);
const report={status:'PASS_ACTUAL_BINDING_STATEMENT_ONLY',rows,otherPivotUnaffected:true,sourceLegacyPivotNamesUnchanged:true,nativeRestPoseAgreementToleranceM:5e-7,scope:'Actual viewport binding statement on real GLB steering transforms with 120 synthetic steering poses per asset. No browser, complete vehicle motion, controls UX or continuous clearance acceptance.',all16VehicleGates:'OPEN'};
await fs.mkdir(new URL('outputs/cloud-left-driver-side-20261001/browser-entry/',root),{recursive:true});await fs.writeFile(new URL('outputs/cloud-left-driver-side-20261001/browser-entry/pose-binding.json',root),JSON.stringify(report,null,2)+'\n');console.log(report.status,rows.length*120);
