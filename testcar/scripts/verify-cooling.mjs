import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
import {COOLING,initialCooling,copyCooling,stepCooling,coolingPose} from '../work/compiled/cooling.mjs';
const h=1/1200,omega=1500*Math.PI/30;
function run(s,c,seconds,w=omega,v=24,power=60000){for(let i=0;i<seconds/h;i++)stepCooling(s,c,w,v,power,h);return s;}
const on=run(initialCooling(),{},10),leftOff=run(copyCooling(on),{fanLeft:false},8);
const pullIn=initialCooling();let contactTime=null,openSamples=0,maxOpenDryTorque=0;
for(let j=0;j<1200;j++){
  const slip=omega-pullIn.fanOmega[0];stepCooling(pullIn,{},omega,24,0,h);
  if(pullIn.axialPosition[0]<COOLING.clutchTravel){
    openSamples++;maxOpenDryTorque=Math.max(maxOpenDryTorque,Math.abs(pullIn.clutchTorque[0]-.002*slip));
    assert.equal(pullIn.clutchNormal[0],0);
  }else if(contactTime===null)contactTime=(j+1)*h;
  assert.ok(pullIn.clutchSlipPower[0]>=0);
  assert.ok(pullIn.clutchAirGap[0]>=.0006-1e-12&&pullIn.clutchAirGap[0]<=.0021+1e-12);
}
assert.ok(contactTime>h&&contactTime<1&&openSamples>1&&maxOpenDryTorque<1e-10,'dry clutch must wait for face contact');
assert.ok(on.axialPosition.every(x=>Math.abs(x-.0015)<1e-12));
assert.ok(leftOff.axialPosition[0]===0&&Math.abs(leftOff.clutchAirGap[0]-.0021)<1e-12,'release spring must return fan');
assert.ok(on.fanOmega.every(w=>Math.abs(w-omega)<.2),'energized fans must follow shafts under load');
assert.ok(leftOff.fanOmega[0]<leftOff.fanOmega[1]*.5,'separate switches must control separate clutches');
assert.ok(leftOff.fanOmega[0]>0,'deenergized fan must coast');
assert.ok(leftOff.coilCurrent[0]<1e-8&&leftOff.coilCurrent[1]>2.9);
assert.ok(on.loadTorque*omega>on.pumpPower,'fan load must be reflected at crankshaft');
const flow=on.flow,power=on.pumpPower,pressure=on.pumpPressure;
const half=run(initialCooling(),{},1,omega/2);
assert.ok(Math.abs(half.flow/flow-.5)<1e-10);
assert.ok(Math.abs(half.pumpPressure/pressure-.25)<1e-10);
assert.ok(Math.abs(half.pumpPower/power-.125)<1e-10);
const heaters=run(copyCooling(on),{heaterLeft:true,heaterRight:true},2);
assert.ok(Math.abs(2*heaters.bankFlow-heaters.flow)<1e-12);
assert.ok(Math.abs(heaters.radFlow+heaters.heaterFlow[0]+heaters.heaterFlow[1]+heaters.compressorFlow-heaters.flow)<1e-12);
assert.ok(heaters.heaterFlow.every(q=>q>0));
const open=run(initialCooling(),{shutter:100},180),closed=run(initialCooling(),{shutter:0},180);
assert.ok(closed.temperature[10]>open.temperature[10]+5,'closing shutters must reduce cooling');
assert.ok(Math.abs(open.energyResidual)<.01&&Math.abs(closed.energyResidual)<.01,'thermal graph must conserve energy');
const coasting=run(copyCooling(on),{},.01,0,0,0);assert.equal(coasting.flow,0);assert.ok(coasting.fanOmega[0]>1);
let rollingError=0;
for(const [wi,wo] of [[omega,0],[omega,omega],[0,omega],[omega,omega*.3]]){
  const wc=(.0196*wi+.0244*wo)/.044,wr=(.0244*wo-.0196*wi)/.0048;
  rollingError=Math.max(rollingError,Math.abs(.022*wc-.0024*wr-.0196*wi),Math.abs(.022*wc+.0024*wr-.0244*wo));
}assert.ok(rollingError<1e-12);
const bytes=await fs.readFile('public/models/maz543a-cooling.glb'),g=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
const poses=coolingPose(on,17,47);for(const n of Object.keys(poses))assert.ok(g.nodes.some(o=>o.name===n),'missing '+n);
const report=await validateBytes(new Uint8Array(bytes),{uri:'maz543a-cooling.glb',maxIssues:1000});
await fs.writeFile('outputs/cooling-glb-validation.json',JSON.stringify(report,null,2));assert.equal(report.issues.numErrors,0);assert.equal(report.issues.numWarnings,0);
const summary={coolingJoints:Object.keys(poses).length,bytes:bytes.length,fanRPM:on.fanOmega.map(w=>w*30/Math.PI),leftOffRPM:leftOff.fanOmega.map(w=>w*30/Math.PI),flowLmin:flow*60000,pumpWatts:power,openOutletC:open.temperature[10],closedOutletC:closed.temperature[10],maxThermalEnergyResidualJ:Math.max(Math.abs(open.energyResidual),Math.abs(closed.energyResidual)),rollingContactError:rollingError,errors:0,warnings:0,limits:'Fitted parameters. Checks verify numerical and assembly behavior, not original cooling performance.'};
await fs.writeFile('outputs/cooling-verification.json',JSON.stringify(summary,null,2));console.log(summary);
const contactReport={contactTimeSeconds:contactTime,openSamples,maxOpenDryTorque,engagedAirGapMM:on.clutchAirGap.map(x=>x*1000),releasedAirGapMM:leftOff.clutchAirGap[0]*1000,engagedNormalN:on.clutchNormal,limits:'Reduced fitted force law with unilateral friction contact; not measured pull-in timing, magnetic saturation, flux dynamics or thermal clutch acceptance.'};
await fs.writeFile('outputs/clutch-contact-verification.json',JSON.stringify(contactReport,null,2));console.log(contactReport);
