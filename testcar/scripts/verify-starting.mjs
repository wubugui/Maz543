import fs from 'node:fs/promises';import assert from 'node:assert/strict';import {validateBytes} from 'gltf-validator';
import {STARTING,initialStarting,advanceStarting,startingPose} from '../work/compiled/starting.mjs';
const TAU=2*Math.PI,base={running:true,startMode:'guided',batteryOn:false,preoilHeld:false,starterHeld:false,fuelEnabled:true,throttle:0,gear:0};
const run=(s,c,seconds,dt=1/60)=>{for(let i=0;i<Math.round(seconds/dt);i++)s=advanceStarting(s,c,dt);return s;};
let s=initialStarting(),meshSamples=0,maxMeshError=0,maxHelixError=0,minStartPressure=Infinity,previousAngle=0;
for(let i=0;i<600;i++){
 s=advanceStarting(s,base,1/60);const p=startingPose(s);
 assert.ok(Object.values(s).filter(v=>typeof v==='number').every(Number.isFinite));
 assert.ok(s.shift>=0&&s.shift<=STARTING.travel);assert.ok(s.angle>=previousAngle);previousAngle=s.angle;
 if(s.starter)minStartPressure=Math.min(minStartPressure,s.oilPressure);
 if(s.mesh){meshSamples++;maxMeshError=Math.max(maxMeshError,Math.abs(s.pinionAngle-12*s.angle-s.meshPhase));}
 maxHelixError=Math.max(maxHelixError,Math.abs((p.C5_drive.rx-p.C5_rotor.rx)*STARTING.helixLead/TAU-s.shift));
}
assert.ok(meshSamples>5);assert.ok(minStartPressure>=STARTING.oilThreshold-1);assert.ok(maxMeshError<1e-9);assert.ok(maxHelixError<1e-10);
assert.equal(s.stage,'running');assert.ok(s.omega*60/TAU>545&&s.omega*60/TAU<555);assert.equal(s.mesh,false);assert.ok(s.shift<1e-5);assert.ok(s.current<1);
const oneStep=advanceStarting(s,{...base,running:false},1/60);assert.ok(oneStep.omega>0&&oneStep.omega<s.omega,'fuel cut must coast rather than teleport to zero');
const stopped=run(s,{...base,running:false},15);assert.ok(stopped.omega<.01);assert.ok(stopped.combustion===0);
const noPower=run(initialStarting(),{...base,startMode:'manual',starterHeld:true,preoilHeld:true,batteryOn:false},5);assert.equal(noPower.omega,0);assert.equal(noPower.pumpOmega,0);assert.equal(noPower.current,0);
const dryCrank=run(initialStarting(),{...base,startMode:'manual',batteryOn:true,starterHeld:true,fuelEnabled:false},2);assert.ok(dryCrank.omega>10,'manual circuit must not invent an oil-pressure interlock');assert.equal(dryCrank.combustion,0);
const isolated=run(s,{...base,startMode:'manual',batteryOn:false,fuelEnabled:true},2);assert.ok(isolated.omega*60/TAU>540,'battery isolation must not stop a mechanically injected running diesel');
const failed=run(initialStarting(),{...base,fuelEnabled:false},10);assert.ok(failed.guidedFailed);assert.equal(failed.starter,false);assert.equal(failed.combustion,0);
const nonNeutral=run(initialStarting(),{...base,gear:1},7);assert.equal(nonNeutral.starter,false);assert.equal(nonNeutral.omega,0);assert.match(nonNeutral.warning,/空挡/);
const manual={...base,startMode:'manual',batteryOn:true,preoilHeld:true,starterHeld:false};
let hand=run(initialStarting(),manual,3);hand=run(hand,{...manual,starterHeld:true},4);
hand=run(hand,{...manual,starterHeld:false,preoilHeld:false},5);
assert.ok(hand.combustion>.99&&hand.omega*60/TAU>545,'manual release must leave the diesel running');
assert.ok(!hand.mesh&&hand.shift<1e-6,'partial engagement must withdraw after manual release');
const coarse=run(initialStarting(),base,10,1/30),fine=run(initialStarting(),base,10,1/120);assert.ok(Math.abs(coarse.omega-fine.omega)<.01,'substepping must be consistent across frame rates');
const report={meshSamples,maxMeshError,maxHelixError,minStartPressureKgf:minStartPressure/98066.5,idleRPM:s.omega*60/TAU,coastStopRPM:stopped.omega*60/TAU,unpoweredRPM:noPower.omega*60/TAU,manualNoFuelRPM:dryCrank.omega*60/TAU,failedAttemptReleased:failed.guidedFailed,frameRateDifferenceRPM:Math.abs(coarse.omega-fine.omega)*60/TAU};
for(const filename of ['maz543a-starting.glb','d12a525a-engine.glb']){
 const b=await fs.readFile('public/models/'+filename);const data=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());
 if(filename.includes('starting'))for(const key of Object.keys(startingPose(initialStarting())))assert.ok(data.nodes.some(n=>n.name===key),'missing joint '+key);
 const validation=await validateBytes(new Uint8Array(b),{uri:filename,maxIssues:5000});await fs.writeFile('outputs/'+filename+'-validation.json',JSON.stringify(validation,null,2));
 assert.equal(validation.issues.numErrors,0,JSON.stringify(validation.issues.messages));assert.equal(validation.issues.numWarnings,0,JSON.stringify(validation.issues.messages));
 report[filename]={bytes:b.length,nodes:data.nodes.length,errors:0,warnings:0};
}
await fs.writeFile('outputs/starting-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
