// Real delivered GLB door geometry + actual model.update/binding statement.
// This is a scoped data/kinematics test, not browser, GPU or cab-clearance QA.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire,registerHooks} from 'node:module';
import ts from 'typescript';
import * as T from 'three';

const out='work/cloud-barrel-axis-web-20261001';await fs.mkdir(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const assetPath='public/models/review/maz543a-cab-va180-v1.glb';
const bytes=await fs.readFile(assetPath),expectedSHA='fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e';
assert.equal(sha(bytes),expectedSHA);assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(8),bytes.length);
const length=bytes.readUInt32LE(12),gltf=JSON.parse(bytes.subarray(20,20+length)),bin=28+length;
assert.equal(new Set(gltf.nodes.map(n=>n.name)).size,gltf.nodes.length);
const moduleSource=await fs.readFile('lib/reviewVehicleAsset.ts','utf8');
const compiled=ts.transpileModule(moduleSource,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {selectReviewVehicleAsset,applyReviewNativePoseOffset,reviewCandidateMetadata}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const asset=selectReviewVehicleAsset('?asset-review=cab-va180-axis-v1',true),legacy=selectReviewVehicleAsset('?asset-review=cab-va180-v1',true);
assert.equal(asset.kind,'cab-va180-axis-v1');assert.equal(asset.url,legacy.url);assert.equal(asset.sha256,expectedSHA);
assert.ok(asset.notice.includes('未替换生产'));assert.notEqual(asset.exportFilename,legacy.exportFilename);
assert.equal(reviewCandidateMetadata(asset).id,'cab-va180-axis-v1');
const selectionCases=[
 ['?asset-review=cab-va180-axis-v1',true,'cab-va180-axis-v1'],
 ['?asset-review=cab-va180-axis-v1',false,'production'],
 ['?asset-review=cab-va180-axis-v1&render-worker=1',true,'production'],
 ['?asset-review=cab-va180-axis-v1&worker-build=1',true,'production'],
 ['?asset-review=cab-va180-axis-v1&asset-review=cab-va180-axis-v1',true,'production'],
 ['?asset-review=cab-va180-axis-v1&asset-review=cab-va180-v1',true,'production'],
 ['?asset-review=cab-va180-axis-v1&quality=full',true,'cab-va180-axis-v1'],
 ['',true,'production'],['?asset-review=cab-va180-v1',true,'cab-va180-v1'],
];
for(const [query,development,kind] of selectionCases)assert.equal(selectReviewVehicleAsset(query,development).kind,kind);
const runtime=await fs.readFile('lib/vehicleViewport.ts','utf8');
const statement=runtime.split('\n').find(l=>l.includes('for(const {source,target} of bindings)'));
assert.ok(statement.includes('applyReviewNativePoseOffset(target,reviewAsset)'));
// oxlint-disable-next-line typescript/no-implied-eval -- Replay the trusted in-repo statement being tested, not third-party input.
const bind=new Function('bindings','applyReviewNativePoseOffset','reviewAsset',statement);
registerHooks({resolve(s,c,next){try{return next(s,c)}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e}}});
const {createMAZ543}=await import('../lib/maz543.ts');
const {INITIAL,INITIAL_TELEMETRY}=await import('../lib/mechanics.ts');
const model=createMAZ543();model.update(INITIAL,INITIAL_TELEMETRY);

function graph(){
 const objects=gltf.nodes.map(n=>{const o=new T.Object3D();o.name=n.name;o.userData=structuredClone(n.extras??{});
  if(n.matrix)new T.Matrix4().fromArray(n.matrix).decompose(o.position,o.quaternion,o.scale);
  else{o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);}
  return o;});
 gltf.nodes.forEach((n,i)=>(n.children??[]).forEach(j=>objects[i].add(objects[j])));
 const scene=new T.Group();for(const i of gltf.scenes[gltf.scene??0].nodes)scene.add(objects[i]);
 const bindings=objects.flatMap(target=>{const source=model.root.getObjectByName(target.name);return source&&!target.userData.coolingLegacyAux?[{source,target}]:[]});
 return {scene,objects,bindings,index:new Map(objects.map((o,i)=>[o.name,i]))};
}
const now=graph(),before=graph();
const doors=model.doors.map(d=>({name:d.group.name,side:d.side,source:d.group}));
assert.deepEqual(doors.map(d=>d.name),['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007']);
const axisBytes=await fs.readFile('work/cloud-door-barrel-axis-20261001/axis-report.json');
const axis=JSON.parse(axisBytes);
const trialBytes=await fs.readFile('work/cloud-door-barrel-motion-trial-20261001/trial-report.json');
const trial=JSON.parse(trialBytes);assert.equal(trial.axis_report_sha256,sha(axisBytes));
assert.equal(trial.source_sha256,'8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70');
const inventoryBytes=await fs.readFile('work/cloud-cab-door-dependencies-20261001/inventory.json');
const inventory=JSON.parse(inventoryBytes);assert.equal(inventory.source_sha256,trial.source_sha256);
for(const d of doors){const p=trial.doors.find(x=>x.hinge===d.name).measured_local_axis_point;d.p=new T.Vector3(p[0],p[2],-p[1]);}
const moving=new Set();for(const d of doors)now.objects[now.index.get(d.name)].traverse(o=>moving.add(o.name));
assert.equal(moving.size,24); // Four pivots and 20 delivered merged/individual mesh children.
const stationary=now.objects.filter(o=>!moving.has(o.name));

// Decode delivered Draco positions and indices; no replacement geometry fixture.
const wrapper='/tmp/maz-barrel-axis-draco-wrapper.cjs';
await fs.writeFile(wrapper,await fs.readFile('public/draco/draco_wasm_wrapper.js'));
const draco=await createRequire(import.meta.url)(wrapper)({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
function decode(p,skipPositionTransform=false){
 const ext=p.extensions?.KHR_draco_mesh_compression;assert.ok(ext);
 const v=gltf.bufferViews[ext.bufferView],raw=bytes.subarray(bin+(v.byteOffset??0),bin+(v.byteOffset??0)+v.byteLength);
 const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(raw,raw.length);
 if(skipPositionTransform)decoder.SkipAttributeTransform(draco.POSITION);
 const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());
 const attr=decoder.GetAttributeByUniqueId(mesh,ext.attributes.POSITION),values=new draco.DracoFloat32Array();
 const quant=new draco.AttributeQuantizationTransform();
 const quantized=quant.InitFromAttribute(attr);
 const quantization=quantized?{bits:quant.quantization_bits(),range:quant.range(),min:[0,1,2].map(i=>quant.min_value(i))}:null;
 decoder.GetAttributeFloatForAllPoints(mesh,attr,values);const xyz=[];
 for(let i=0;i<values.size();i+=3)xyz.push(new T.Vector3(values.GetValue(i),values.GetValue(i+1),values.GetValue(i+2)));
 const face=new draco.DracoInt32Array(),tri=[];
 for(let i=0;i<mesh.num_faces();i++){assert.ok(decoder.GetFaceFromMesh(mesh,i,face));tri.push([face.GetValue(0),face.GetValue(1),face.GetValue(2)]);}
 for(const o of [quant,face,values,mesh,buffer,decoder])draco.destroy(o);
 return {xyz,tri,quantization:quantization??(!skipPositionTransform?decode(p,true).quantization:null)};
}
function components(xyz,tri){
 const parent=xyz.map((_,i)=>i),root=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
 const join=(a,b)=>{a=root(a);b=root(b);if(a!==b)parent[Math.max(a,b)]=Math.min(a,b)};
 for(const t of tri){join(t[0],t[1]);join(t[1],t[2]);}
 const same=new Map();xyz.forEach((p,i)=>{const k=p.toArray().join(',');if(same.has(k))join(i,same.get(k));else same.set(k,i)});
 const groups=new Map();xyz.forEach((_,i)=>{const r=root(i);if(!groups.has(r))groups.set(r,[]);groups.get(r).push(i)});
 return [...groups.values()];
}
const decoded=[];const barrels=[];const componentCandidates=[];let initialBoxFilterMatches=0;
for(const d of doors){
 const pivot=now.objects[now.index.get(d.name)],native=axis.doors.find(x=>x.hinge===d.name);
 for(const child of pivot.children){
  const ni=now.index.get(child.name),node=gltf.nodes[ni];assert.notEqual(node.mesh,undefined);
  const primitives=gltf.meshes[node.mesh].primitives;assert.equal(primitives.length,1);
  const data=decode(primitives[0]);child.updateMatrix();
  const local=data.xyz.map(v=>v.clone().applyMatrix4(child.matrix));
  decoded.push({node:child.name,door:d.name,vertices:data.xyz.length,triangles:data.tri.length});
  if(!child.name.includes('OD_green_aged_enamel'))continue;
  for(const ids of components(data.xyz,data.tri)){
   const box=new T.Box3().setFromPoints(ids.map(i=>local[i]));const center=box.getCenter(new T.Vector3()),size=box.getSize(new T.Vector3());
   const unique=[...new Map(ids.map(i=>[local[i].toArray().join(','),local[i]])).values()];
   const centroid=unique.reduce((a,p)=>a.add(p),new T.Vector3()).divideScalar(unique.length);
   const members=new Set(ids),triangleCount=data.tri.filter(t=>members.has(t[0])).length;
   componentCandidates.push({door:d.name,node:child.name,vertices:ids.length,uniqueVertices:unique.length,triangles:triangleCount,center:center.toArray(),centroid:centroid.toArray(),size:size.toArray(),quantization:data.quantization});
   for(const ref of native.barrels){
    const expected=new T.Vector3(ref.center[0],ref.center[2],-ref.center[1]).sub(new T.Vector3(...gltf.nodes[now.index.get(d.name)].translation));
    if(center.distanceTo(expected)<2e-5&&Math.abs(size.y-ref.length_m)<2e-5&&Math.abs(size.x-.036)<2e-5&&Math.abs(size.z-.036)<2e-5)
     initialBoxFilterMatches++;
    const sourceGeometry=inventory.doors.find(x=>x.hinge===d.name).parts.find(x=>x.name===ref.name);
    assert.equal(sourceGeometry.vertices,192);assert.equal(sourceGeometry.triangles,380);
    const evaluated=ref.evaluated_centroid;
    const expectedCentroid=new T.Vector3(evaluated[0],evaluated[2],-evaluated[1]).sub(new T.Vector3(...gltf.nodes[now.index.get(d.name)].translation));
    const q=data.quantization;assert.ok(q&&q.bits===14);const step=q.range/(2**q.bits-1);
    // A component-identification envelope derived from encoded grid spacing is
    // not a relaxed transport acceptance gate. The inherited 20um box test is
    // explicitly retained and still fails; the192unique-position centroid is
    // the matching metric for the native 192 evaluated vertices.
    if(unique.length===sourceGeometry.vertices&&triangleCount===sourceGeometry.triangles&&centroid.distanceTo(expectedCentroid)<2e-5&&Math.abs(size.y-ref.length_m)<2*step&&Math.abs(size.x-.036)<2*step&&Math.abs(size.z-.036)<2*step)
     barrels.push({door:d.name,sourceName:ref.name,node:child.name,vertices:ids.length,uniqueVertices:unique.length,triangles:triangleCount,
      center:centroid.toArray(),boxCenter:center.toArray(),size:size.toArray(),nativeCentroidErrorM:centroid.distanceTo(expectedCentroid),
      nativeBoxCenterErrorM:center.distanceTo(expected),nativeSizeErrorsM:[Math.abs(size.x-.036),Math.abs(size.y-ref.length_m),Math.abs(size.z-.036)],
      quantization:q,positionQuantizationStepM:step});
   }
  }
 }
}
await fs.writeFile(out+'/decoded-components.json',JSON.stringify(componentCandidates,null,2)+'\n');
assert.equal(decoded.length,20);assert.equal(barrels.length,12);assert.equal(new Set(barrels.map(b=>b.sourceName)).size,12);
assert.equal(initialBoxFilterMatches,0,'Retain the failed 20um AABB matching attempt, rather than silently declaring it passed');
let frames=0,stationaryMatrixComparisons=0,closedDoorChecks=0,maxMatrixError=0,maxBarrelCenterDrift=0,oldMaximumBarrelOrbit=0;
const expected=new T.Matrix4();
function apply(openings){
 model.update(INITIAL,{...INITIAL_TELEMETRY,doorOpenings:openings});
 const sourcePoses=doors.map(d=>({p:d.source.position.toArray(),q:d.source.quaternion.toArray()}));
 bind(now.bindings,applyReviewNativePoseOffset,asset);bind(before.bindings,applyReviewNativePoseOffset,legacy);
 now.scene.updateMatrixWorld(true);before.scene.updateMatrixWorld(true);
 for(let k=0;k<doors.length;k++){
  const d=doors[k],pivot=now.objects[now.index.get(d.name)],old=before.objects[before.index.get(d.name)];
  assert.deepEqual(d.source.position.toArray(),sourcePoses[k].p);assert.deepEqual(d.source.quaternion.toArray(),sourcePoses[k].q);
  const local=new T.Matrix4().makeTranslation(...d.source.position.toArray()).multiply(new T.Matrix4().makeTranslation(...d.p.toArray())).multiply(new T.Matrix4().makeRotationFromQuaternion(d.source.quaternion)).multiply(new T.Matrix4().makeTranslation(...d.p.clone().negate().toArray()));
  expected.multiplyMatrices(pivot.parent.matrixWorld,local);
  maxMatrixError=Math.max(maxMatrixError,...pivot.matrixWorld.elements.map((x,i)=>Math.abs(x-expected.elements[i])));
  assert.ok(maxMatrixError<2e-12);
  if(openings[k]===0){pivot.traverse(o=>{assert.deepEqual(o.matrixWorld.elements,before.objects[before.index.get(o.name)].matrixWorld.elements);closedDoorChecks++});}
  for(const b of barrels.filter(b=>b.door===d.name)){
   const center=new T.Vector3(...b.center),closed=center.clone().add(d.source.position).applyMatrix4(pivot.parent.matrixWorld);
   maxBarrelCenterDrift=Math.max(maxBarrelCenterDrift,center.clone().applyMatrix4(pivot.matrixWorld).distanceTo(closed));
   oldMaximumBarrelOrbit=Math.max(oldMaximumBarrelOrbit,center.clone().applyMatrix4(old.matrixWorld).distanceTo(closed));
  }
 }
 for(const o of stationary){const old=before.objects[before.index.get(o.name)];assert.deepEqual(o.matrixWorld.elements,old.matrixWorld.elements);assert.equal(o.visible,old.visible);stationaryMatrixComparisons++;}
 frames++;
}
try{
 apply([0,0,0,0]);
 for(let k=0;k<4;k++)for(let i=0;i<=396;i++){const a=[0,0,0,0];a[k]=i/396*100;apply(a);}
 for(let i=0;i<400;i++)apply([i%2?100:0,100*(.5+.5*Math.sin(i*.31)),100*(.5+.5*Math.cos(i*.17)),(i%101)]);
 for(let i=0;i<40;i++){apply([100,100,100,100]);apply([0,0,0,0]);}
 assert.ok(maxBarrelCenterDrift<2e-5,'Decoded barrel centers no longer stay on their fitted axes');
 assert.ok(oldMaximumBarrelOrbit>.106&&oldMaximumBarrelOrbit<.108,'Legacy orbit negative control not reproduced');
 // Legacy asset kinds retain their exact previous door binding, including zero.
 const legacyRows=[];
 for(const kind of ['production','tyre-v2','hood-tyre-v1','left-driver-v1','cab-va180-v1']){
  const selected=selectReviewVehicleAsset(kind==='production'?'':'?asset-review='+kind,true);
  for(let i=0;i<8;i++){
   model.update(INITIAL,{...INITIAL_TELEMETRY,doorOpenings:[i/7*100,100-i/7*100,i%2?100:0,0]});
   bind(before.bindings,applyReviewNativePoseOffset,selected);
   for(const d of doors){const p=before.objects[before.index.get(d.name)];assert.deepEqual(p.position.toArray(),d.source.position.toArray());assert.deepEqual(p.quaternion.toArray(),d.source.quaternion.toArray());}
  }
  legacyRows.push({kind,states:8,unchanged:true});
 }
 assert.equal(sha(await fs.readFile(assetPath)),expectedSHA);
 const report={status:'PASS_REVIEW_BARREL_AXIS_REAL_GLB_BINDING_ONLY',assetSHA256:expectedSHA,
  sourceAxisReportSHA256:sha(axisBytes),sourceTrialReportSHA256:sha(trialBytes),sourceDoorInventorySHA256:sha(inventoryBytes),
  selectorCases:selectionCases.length,frames,sourceModel:'Actual createMAZ543 and model.update; delivered GLB node graph and20 decoded door mesh payloads',
  bindingStatementSHA256:sha(statement),decoded,barrels,movingNodes:moving.size,stationaryNodes:stationary.length,
  stationaryMatrixComparisons,closedDoorChecks,maxMatrixError,maxBarrelCenterDrift,oldMaximumBarrelOrbit,
  legacyRows,initialBoxFilterMatches,inheritedDoorBoxTransport20umAccepted:false,centroidMotionGateM:2e-5,
  centroidMetric:'Exact-coordinate unique positions: 192 per decoded barrel, matching 192 native evaluated vertices; not a physical mass centroid',
  closedGeometryExactAgainstLegacyBinding:true,sourcePosesUnchanged:true,
  repeatedBindingAccumulates:false,assetBytesUnchanged:true,productionSelectionUnchanged:true,
  limits:['Numerical sampled actual source-update/binding regression; no browser, camera, render or full loaded-vehicle assembly test',
   'Twelve decoded barrel components identified by connectivity, 192 unique positions / 380 triangles, native centroid and recorded 14-bit quantization grid; inherited box/size transport 20um check remains failed',
   'The 20um sampled centroid-motion gate is unchanged and is not a formal whole-angle floating-point bound',
   'Six closed contact candidates and 52 unresolved frozen pairs remain; no collision or factory-axis acceptance',
   'Development-only same-GLB motion review; no native master replacement or new asset upload'],wholeVehicleAcceptance:'16 OPEN'};
 await fs.writeFile(out+'/binding-report.json',JSON.stringify(report,null,2)+'\n');console.log(report.status,{frames,maxBarrelCenterDrift,oldMaximumBarrelOrbit,stationaryMatrixComparisons});
}finally{model.dispose();}
