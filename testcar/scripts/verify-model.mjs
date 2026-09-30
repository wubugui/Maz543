import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import ts from 'typescript';
import {validateBytes} from 'gltf-validator';
const out=path.resolve('work/verify');await fs.mkdir(out,{recursive:true});
for(const name of ['cardan','cooling','d12-timing','d12','starting','suspension','transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics','mechanics','maz543']){
 const code=await fs.readFile(`lib/${name}.ts`,'utf8');let js=ts.transpileModule(code,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;js=js.replace("from './cooling'","from './cooling.mjs'").replace("from './transmission'","from './transmission.mjs'").replace("from './transmissionHydraulics'","from './transmissionHydraulics.mjs'").replace("from './clutchSurfaceMetrics'","from './clutchSurfaceMetrics.mjs'").replace("from './transmissionDynamics'","from './transmissionDynamics.mjs'").replace("from './mechanics'","from './mechanics.mjs'").replace("from './suspension'","from './suspension.mjs'").replace("from './starting'","from './starting.mjs'").replace("from './d12-timing'","from './d12-timing.mjs'");await fs.writeFile(path.join(out,`${name}.mjs`),js);
}
const {SPECS,INITIAL,INITIAL_TELEMETRY,advance,pistonPosition,steeringAngles}=await import(pathToFileURL(path.join(out,'mechanics.mjs')));
const {createMAZ543}=await import(pathToFileURL(path.join(out,'maz543.mjs')));
const near=(a,b,eps=1e-5)=>assert.ok(Math.abs(a-b)<eps,`${a} should be ${b}`);
near(SPECS.axles[3]-SPECS.axles[0],7.7);near(SPECS.axles[1]-SPECS.axles[0],2.2);near(SPECS.axles[2]-SPECS.axles[1],3.3);
near(pistonPosition(0)-pistonPosition(Math.PI),.18);
for(const steering of [-30,-10,10,30]){
 const angles=steeringAngles(steering),pivot=(SPECS.axles[2]+SPECS.axles[3])/2,radius=(pivot-SPECS.axles[0])/Math.tan(steering*Math.PI/180);
 for(let i=0;i<4;i++)near((pivot-SPECS.axles[Math.floor(i/2)])/Math.tan(angles[i])+(i%2?1:-1)*SPECS.track/2,radius);
}
let state={...INITIAL,running:true,gear:0,throttle:70},t={...INITIAL_TELEMETRY};
for(let i=0;i<360;i++)t=advance(t,state,1/60);state={...state,gear:1};
for(let i=0;i<1200;i++)t=advance(t,state,1/60);assert.ok(t.speed>1,'engaged drive should accelerate');
state={...state,brake:100};for(let i=0;i<600;i++)t=advance(t,state,1/60);near(t.speed,0);const held=t.distance;
for(let i=0;i<120;i++)t=advance(t,state,1/60);near(t.distance,held);
const model=createMAZ543();assert.equal(model.wheels.length,8);assert.equal(model.pistons.length,12);assert.equal(model.doors.length,4);
let doorState={...INITIAL_TELEMETRY};const oneDoor={...INITIAL,doorTargets:[100,0,0,0]};
doorState=advance(doorState,oneDoor,1/60);assert.ok(doorState.doorOpenings[0]>0&&doorState.doorOpenings[0]<2,'door should move continuously rather than teleport');
for(let i=0;i<180;i++)doorState=advance(doorState,oneDoor,1/60);
assert.deepEqual(doorState.doorOpenings,[100,0,0,0],'independent door operation');
for(let i=0;i<180;i++)doorState=advance(doorState,INITIAL,1/60);
assert.deepEqual(doorState.doorOpenings,[0,0,0,0],'door must close completely');
for(let frame=0;frame<72;frame++){
 model.update({...INITIAL,terrain:80},{...INITIAL_TELEMETRY,time:frame/12,crank:frame/72*Math.PI*4});
 for(const piston of model.pistons)near(piston.rod.scale.y,.32);
 model.root.traverse(o=>assert.ok(o.matrixWorld.elements.every(Number.isFinite),`non-finite transform: ${o.name}`));
}
model.update({...INITIAL,steering:25},{...INITIAL_TELEMETRY,time:0});model.update({...INITIAL,steering:25},{...INITIAL_TELEMETRY,time:1,wheel:1});assert.ok(model.wheels[0].spin.rotation.z>model.wheels[1].spin.rotation.z,'outside front wheel should travel farther');
model.update(INITIAL,INITIAL_TELEMETRY);
const bytes=await fs.readFile('public/models/maz543a-blender.glb');assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());const nodes=new Map(json.nodes.map(n=>[n.name,n]));
for(const part of model.parts)assert.ok(nodes.has(part.id),`missing assembly ${part.id}`);
for(const wheel of model.wheels){const n=nodes.get(wheel.carrier.name);assert.ok(n);near(n.translation[0],wheel.x);near(n.translation[2],wheel.side*SPECS.track/2);}
for(const door of model.doors)assert.ok(nodes.has(door.group.name));
assert.ok(!nodes.has('D12A_525A'),'D12 engine must remain a separate web asset');
assert.ok(!nodes.has('S543_SUSPENSION'),'detailed suspension must remain a separate web asset');
assert.ok(!nodes.has('S543_COOLING'),'cooling must remain a separate web asset');
near(nodes.get('engine').translation[0],-4.05);
assert.ok(!model.pistons.some(p=>nodes.has(p.piston.name)),'superseded generic engine must be removed from body asset');
assert.ok(json.textures.length>=3,'baked textures must be embedded');assert.ok(json.extensionsUsed.includes('KHR_draco_mesh_compression'));assert.ok(json.meshes.some(m=>m.name?.startsWith('BL_')));
const result=await validateBytes(new Uint8Array(bytes),{uri:'maz543a-blender.glb',maxIssues:50});
await fs.writeFile('outputs/gltf-validation.json',JSON.stringify(result,null,2));assert.equal(result.issues.numErrors,0,JSON.stringify(result.issues.messages));
const report={checks:['axle dimensions','legacy control-rig consistency (not rendered engine acceptance)','common steering centre','outside wheel speed','acceleration and brake hold','finite transforms','eight wheels and four doors','independent continuous door opening and closing','Blender body pivot bindings','separate engine asset without obsolete engine meshes','embedded PBR textures','glTF validation'],glbBytes:bytes.length,nodes:json.nodes.length,meshes:json.meshes.length,errors:result.issues.numErrors,warnings:result.issues.numWarnings};
await fs.writeFile('outputs/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));model.dispose();
const infoPath='public/models/model-info.json';const info=JSON.parse(await fs.readFile(infoPath,'utf8'));
info.bytes=bytes.length;info.objects=json.nodes.length;info.mesh_objects=json.nodes.filter(n=>n.mesh!==undefined).length;
info.triangles=json.nodes.filter(n=>n.mesh!==undefined).reduce((sum,n)=>sum+json.meshes[n.mesh].primitives.reduce((total,p)=>total+(p.indices!==undefined?json.accessors[p.indices].count:json.accessors[p.attributes.POSITION].count)/3,0),0);
const baked=JSON.parse(await fs.readFile('work/animation-keyframes.json','utf8'));
info.body_motion_nodes=baked.nodes.filter(n=>nodes.has(n.name)&&!nodes.get(n.name).extras?.coolingLegacyAux).length;
const {d12Pose}=await import(pathToFileURL(path.join(out,'d12.mjs')));
const {startingPose,initialStarting}=await import(pathToFileURL(path.join(out,'starting.mjs')));
info.engine_joint_count=Object.keys(d12Pose(0)).length;info.starting_joint_count=Object.keys(startingPose(initialStarting())).length;
const {coolingPose,initialCooling}=await import(pathToFileURL(path.join(out,'cooling.mjs')));
info.cooling_module='maz543a-cooling.glb';info.cooling_joint_count=Object.keys(coolingPose(initialCooling(),0)).length;
info.cooling_native_piece_count=JSON.parse(await fs.readFile('outputs/cooling-parts-register.json','utf8')).length;
info.cooling_scope='Original twin 12-blade fan/clutch topology; photo-guided lower gearbox with fitted 32:20 gears; uncalibrated thermal model; upper local gears/bearings rebuilt; four-hole interfaces corrected with fitted dimensions; installed Cardan drive and complete passages remain incomplete';
info.mesh_definitions=json.meshes.length;
const {cardanPose}=await import(pathToFileURL(path.join(out,'cardan.mjs')));
info.cardan_module='maz543a-cardan.glb';info.cardan_joint_count=Object.keys(cardanPose(0)).length;
info.cardan_native_piece_count=JSON.parse(await fs.readFile('outputs/cardan-parts-register.json','utf8')).length;
info.cardan_scope='Independent double-Cardan inspection module: 408-family bearing envelope, fitted forks/splines/length, ideal rolling kinematics. Vehicle installation and loads remain unverified.';
info.module_bytes[info.cardan_module]=(await fs.stat('public/models/'+info.cardan_module)).size;
info.module_bytes[info.cooling_module]=(await fs.stat('public/models/'+info.cooling_module)).size;
info.native_motion_nodes=info.body_motion_nodes+info.engine_joint_count+80+info.starting_joint_count+info.cooling_joint_count;
info.suspension_module='maz543a-suspension.glb';info.suspension_joint_count=80;info.suspension_scope='Source-guided double-torsion geometry and uncalibrated vertical force model';
info.engine_module='d12a525a-engine.glb';info.engine_scope='Source-guided reconstruction; dimensions and physical simulation incomplete';
info.engine_native_piece_count=JSON.parse(await fs.readFile('outputs/d12-parts-register.json','utf8')).length;
info.engine_cam_authored_objects=JSON.parse(await fs.readFile('outputs/cam-native-verification.json','utf8')).camAuthoredObjects;
for(const name of Object.keys(info.module_bytes))info.module_bytes[name]=(await fs.stat('public/models/'+name)).size;
await fs.writeFile(infoPath,JSON.stringify(info,null,2)+'\n');
