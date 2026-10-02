// Read real GLB node graphs and execute the actual viewport wheel statements.
// No mesh decoding, rendering, Blender execution or candidate-asset fabrication.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {registerHooks} from 'node:module';
import * as T from 'three';

registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {createMAZ543}=await import('../lib/maz543.ts');
const {INITIAL,INITIAL_TELEMETRY}=await import('../lib/mechanics.ts');
const {suspensionPose}=await import('../lib/suspension.ts');
const {bindLegacyWheelStations,LEGACY_WHEEL_STATIONS}=await import('../lib/nativeWheelBindings.ts');
const {selectReviewVehicleAsset,applyReviewNativePoseOffset}=await import('../lib/reviewVehicleAsset.ts');
const out=process.env.MAZ_WHEEL_BINDING_REPORT_DIR??'work/cloud-wheel-binding-20261002';
await fs.mkdir(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const runtimeBytes=await fs.readFile('lib/vehicleViewport.ts'),runtime=runtimeBytes.toString();
const baselineCommit='3a7bd1322b6b72f3d8168ab16c935cdc55b5035f';
const baseline=execFileSync('git',['show',`${baselineCommit}:testcar/lib/vehicleViewport.ts`]);
assert.equal(sha(baseline),'d2423fe367cc9827b4f3b27f3b38bac9cb9f5bd9cd670f7ef8d165eb83efe17e');
function wheelStatement(source){
  const start=source.indexOf('      wheelBindings.forEach(');assert.ok(start>0);
  const end=source.indexOf('      });',start);assert.ok(end>start);
  return source.slice(start,end+'      });'.length);
}
const currentStatement=wheelStatement(runtime),oldStatement=wheelStatement(baseline.toString());
// oxlint-disable-next-line typescript/no-implied-eval -- Execute only pinned/local repository statements under test.
const runWheel=new Function('wheelBindings','suspension','latest','T',currentStatement);
// oxlint-disable-next-line typescript/no-implied-eval -- Execute the exact pinned historical wheel loop as a regression reference.
const runOldWheel=new Function('wheelBindings','suspension','latest','T',oldStatement);
const commonStatement=runtime.split('\n').find(l=>l.includes('for(const {source,target} of bindings)'));
assert.ok(commonStatement.includes('applyReviewNativePoseOffset(target,reviewAsset)'));
// oxlint-disable-next-line typescript/no-implied-eval -- Replay the current repository's shared pose-copy statement.
const runCommon=new Function('bindings','applyReviewNativePoseOffset','reviewAsset',commonStatement);

// Execute the real preflight block; assignment to renderedRoot must not happen
// on failure. The existing Promise.catch/fatal UI path is inspected, not run.
const preflightStart=runtime.indexOf('      const nativeRoot='),preflightEnd=runtime.indexOf("      if(reviewAsset.kind!=='production')",preflightStart);
assert.ok(preflightStart>0&&preflightEnd>preflightStart);
const preflightStatement=runtime.slice(preflightStart,preflightEnd);
assert.ok(preflightEnd<runtime.indexOf('      driveHolder=renderedRoot'));
assert.ok(preflightEnd<runtime.indexOf('for(const child of [...suspensionHolder.children])'));
assert.ok(preflightEnd<runtime.indexOf('scene.remove(model.root);scene.add(renderedRoot)'));
assert.ok(runtime.includes('      wheelBindings=nativeWheelBindings;'));
assert.ok(runtime.includes("console.error('MAZ native model loading or assembly failed:',error)"));
assert.ok(runtime.includes('(callbacks.current.onFatal??callbacks.current.onError)'));
// oxlint-disable-next-line typescript/no-implied-eval -- Execute the actual preflight, preserving its assignment order on rejection.
const preflight=new Function('gltf','model','bindLegacyWheelStations',`let renderedRoot=model.root;try{${preflightStatement.replace(' as T.Group','')}return {renderedRoot,bindings:nativeWheelBindings};}catch(error){return {renderedRoot,error};}`);
const model=createMAZ543();model.update(INITIAL,INITIAL_TELEMETRY);
assert.deepEqual(model.wheels.map(w=>[w.carrier.name,w.spin.name,w.brake.name]),LEGACY_WHEEL_STATIONS.map(s=>[s.carrier,s.spin,s.brake]));
const inputs=[
  {path:'public/models/maz543a-blender.glb',sha256:'4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698',kind:'production',nodes:371},
  {path:'public/models/review/maz543a-cab-va180-v1.glb',sha256:'fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e',kind:'cab-va180-v1',nodes:850},
];
function graph(gltf){
  const objects=gltf.nodes.map(n=>{
    const o=new T.Object3D();o.name=n.name;o.userData=structuredClone(n.extras??{});
    if(n.matrix)new T.Matrix4().fromArray(n.matrix).decompose(o.position,o.quaternion,o.scale);
    else{o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);}
    return o;
  });
  gltf.nodes.forEach((n,i)=>(n.children??[]).forEach(j=>objects[i].add(objects[j])));
  const scene=new T.Group();for(const i of gltf.scenes[gltf.scene??0].nodes)scene.add(objects[i]);
  const root=scene.getObjectByName('MAZ543_REFERENCE_CHASSIS');assert.ok(root);
  const common=objects.flatMap(target=>{const source=model.root.getObjectByName(target.name);return source&&!target.userData.coolingLegacyAux?[{source,target}]:[];});
  return {scene,root,objects,common};
}
function snapshot(g){return g.objects.map(o=>({id:o.uuid,name:o.name,parent:o.parent?.uuid,children:o.children.map(c=>c.uuid),p:o.position.toArray(),q:o.quaternion.toArray(),s:o.scale.toArray(),visible:o.visible}));}
const reports=[],rejections=[];
for(const input of inputs){
  const bytes=await fs.readFile(input.path);assert.equal(sha(bytes),input.sha256);assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(8),bytes.length);
  const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
  assert.equal(new Set(gltf.nodes.map(n=>n.name)).size,gltf.nodes.length);
  assert.equal(gltf.nodes.length,input.nodes);
  const before=graph(gltf),after=graph(gltf),reordered=graph(gltf);
  const initial=snapshot(after),prepared=preflight({scene:after.scene},model,bindLegacyWheelStations);
  assert.equal(prepared.renderedRoot,after.root);assert.ok(!prepared.error);assert.deepEqual(snapshot(after),initial);
  const bindings=prepared.bindings,permuted=bindLegacyWheelStations(reordered.root,[...model.wheels].reverse());
  assert.deepEqual(bindings.map(b=>b.station),[0,1,2,3,4,5,6,7]);
  assert.deepEqual(permuted.map(b=>b.source),bindings.map(b=>b.source));
  const oldBindings=model.wheels.map(w=>({carrier:before.root.getObjectByName(w.carrier.name),brake:before.root.getObjectByName(w.brake.name),source:w.carrier}));
  const asset=selectReviewVehicleAsset(input.kind==='production'?'':'?asset-review=cab-va180-v1',true);
  let comparedWorldMatrices=0,maxMatrixError=0,maxReorderedError=0;
  for(let frame=0;frame<97;frame++){
    const controls={...INITIAL,steering:Math.sin(frame*.17)*32,explode:frame%4===0?65:0,terrain:36};
    model.update(controls,{...structuredClone(INITIAL_TELEMETRY),time:frame/24,wheel:frame*.0731});
    const pose=suspensionPose(Array.from({length:8},(_,i)=>Math.sin(frame*.11+i*.37)*.13));
    for(const g of [before,after,reordered])runCommon(g.common,applyReviewNativePoseOffset,asset);
    runOldWheel(oldBindings,pose,{current:controls},T);
    runWheel(bindings,pose,{current:controls},T);
    // The frame loop must use the stored station even if binding order changes.
    runWheel([...permuted].reverse(),pose,{current:controls},T);
    for(const g of [before,after,reordered])g.scene.updateMatrixWorld(true);
    for(let i=0;i<gltf.nodes.length;i++){
      const a=before.objects[i].matrixWorld.elements,b=after.objects[i].matrixWorld.elements,c=reordered.objects[i].matrixWorld.elements;
      for(let k=0;k<16;k++){maxMatrixError=Math.max(maxMatrixError,Math.abs(a[k]-b[k]));maxReorderedError=Math.max(maxReorderedError,Math.abs(b[k]-c[k]));}
      comparedWorldMatrices++;
    }
  }
  assert.equal(maxMatrixError,0);assert.equal(maxReorderedError,0);
  function reject(label,mutate,sources=model.wheels){
    const g=graph(gltf);mutate(g);const previous=snapshot(g);
    const result=preflight({scene:g.scene},{root:model.root,wheels:sources},bindLegacyWheelStations);
    assert.ok(result.error instanceof Error,label);assert.ok(result.error.message.startsWith('Native wheel binding: '),result.error.message);
    assert.equal(result.renderedRoot,model.root,label);assert.equal(result.bindings,undefined,label);assert.deepEqual(snapshot(g),previous,label);
    rejections.push({asset:input.kind,test:label,error:result.error.message});
  }
  for(const s of LEGACY_WHEEL_STATIONS)for(const role of ['carrier','spin','brake'])reject(`missing ${role} station ${s.station}`,g=>g.root.getObjectByName(s[role]).removeFromParent());
  for(const name of ['wheels','brakes',...LEGACY_WHEEL_STATIONS.flatMap(s=>[s.carrier,s.spin,s.brake])])reject(`duplicate target ${name}`,g=>{const o=new T.Object3D();o.name=name;g.root.add(o);});
  for(const station of [0,3]){
    reject(`missing source station ${station}`,()=>{},model.wheels.filter((_,i)=>i!==station));
    const duplicate=[...model.wheels];duplicate[station]=model.wheels[7];reject(`duplicate source station ${station}`,()=>{},duplicate);
    const wrong=[...model.wheels];wrong[station]={...wrong[station],side:-wrong[station].side};reject(`wrong source side station ${station}`,()=>{},wrong);
  }
  // Explicitly synthetic candidate topology. It proves legacy rejection only,
  // and is never exported, rendered, or called a native repair candidate.
  reject('synthetic four-front-joint parent chain',g=>{
    const suspension=g.root.getObjectByName('suspension'),s543=new T.Object3D();s543.name='S543_SUSPENSION';suspension.add(s543);
    for(const s of LEGACY_WHEEL_STATIONS.slice(0,4)){
      const upright=new T.Object3D();upright.name=`S543_${s.station}_upright`;s543.add(upright);
      const joint=new T.Object3D();joint.name=`S543_${s.station}_native_steering_joint_frame`;upright.add(joint);
      joint.add(g.root.getObjectByName(s.carrier),g.root.getObjectByName(s.brake));
    }
  });
  // Witness the actual old failure: deleting the first or a middle carrier
  // shifts surviving stations onto the wrong suspension pose/side.
  const oldFailures=[];
  for(const missing of [0,3]){
    const g=graph(gltf);g.root.getObjectByName(LEGACY_WHEEL_STATIONS[missing].carrier).removeFromParent();
    const compact=model.wheels.flatMap(w=>{const carrier=g.root.getObjectByName(w.carrier.name);return carrier?[{carrier,brake:g.root.getObjectByName(w.brake.name),source:w.carrier}]:[];});
    const pose=suspensionPose(Array(8).fill(0));runOldWheel(compact,pose,{current:{explode:0}},T);
    const affected=missing+1,carrier=g.root.getObjectByName(LEGACY_WHEEL_STATIONS[affected].carrier);
    const wrongDistance=carrier.position.distanceTo(new T.Vector3(...pose[`S543_${affected}_wheel`].p));assert.ok(wrongDistance>2);
    oldFailures.push({missingStation:missing,observedWrongStation:affected,positionErrorM:wrongDistance});
  }
  assert.equal(sha(await fs.readFile(input.path)),input.sha256);
  reports.push({path:input.path,sha256:input.sha256,bytes:bytes.length,nodeCount:gltf.nodes.length,stationIdentities:bindings.map(b=>({station:b.station,carrier:b.carrier.name,spin:b.spin.name,brake:b.brake.name,parents:[b.carrier.parent.name,b.spin.parent.name,b.brake.parent.name]})),frames:97,comparedWorldMatrices,maxMatrixError,maxReorderedError,oldCompactArrayFailureWitnesses:oldFailures});
}
const mainViewer=await fs.readFile('components/vehicle-viewer.tsx','utf8'),workerClient=await fs.readFile('lib/renderWorkerClient.ts','utf8'),worker=await fs.readFile('lib/viewport.worker.ts','utf8');
assert.ok(mainViewer.includes('const callbacks=useRef({onReady,onSelect,onTelemetry,onError})'));
assert.ok(!mainViewer.includes('onFatal:'));
assert.ok(worker.includes("onFatal:message=>send({type:'fatal',message})"));
assert.ok(workerClient.includes("case 'fatal':fail(data.message);break;"));
assert.ok(workerClient.includes('stop(true,message);callbacks.current.onError(message)'));
const sourcePaths=['lib/nativeWheelBindings.ts','lib/vehicleViewport.ts','lib/maz543.ts','lib/suspension.ts','lib/reviewVehicleAsset.ts','lib/renderWorkerClient.ts','lib/viewport.worker.ts','components/vehicle-viewer.tsx','components/workshop.tsx','scripts/export-va180-cab-candidate.py','scripts/verify-native-wheel-bindings.mjs'];
const sources=await Promise.all(sourcePaths.map(async path=>({path,sha256:sha(await fs.readFile(path))})));
const report={status:'PASS_SCOPED_LEGACY_WHEEL_BINDING',baselineCommit,baselineViewportSHA256:sha(baseline),sources,assets:reports,rejectedCases:rejections.length,rejections,preflight:'Actual viewport block rejects before renderedRoot assignment or subtree replacement; no binding array is returned on failure.',failureUI:{evidence:'Source inspection only; no browser execution.',mainThread:'No onFatal callback is supplied. Existing onError displays the load error; the generated model.root remains in the scene and animation continues, with nativeLoaded=false and no native onReady. This is the existing provisional model, not an accepted native asset.',renderWorker:'Worker onFatal sends fatal. renderWorkerClient stops its workers, clears its owned API/canvas and forwards onError; no automatic main-thread retry for this asynchronous fatal. The synchronous worker-start fallback is a different existing path.'},limits:['Node transform graph/data test with actual createMAZ543, model.update and viewport pose statements. No GLTFLoader, Draco mesh decoding, browser, GPU or rendering.','Only production 4aa0a228 and cab VA180 fde04e48 asset bytes checked; older review assets not materialized here.','New joint-parent candidate is not integrated or activated. Export selection, suspension merge, candidate pose binding, native timeline, contacts and steering qualification remain open.','No geometry, acceptance thresholds, asset selector or asset bytes changed. All 16 whole-vehicle gates remain OPEN.']};
await fs.writeFile(`${out}/binding-report.json`,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,assets:reports.map(r=>({path:r.path,nodeCount:r.nodeCount,frames:r.frames,comparedWorldMatrices:r.comparedWorldMatrices,maxMatrixError:r.maxMatrixError,maxReorderedError:r.maxReorderedError})),rejectedCases:report.rejectedCases},null,2));
