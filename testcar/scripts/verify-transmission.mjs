import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
import ts from 'typescript';

const out=path.resolve('work/verify-transmission');
await fs.mkdir(out,{recursive:true});
for(const name of ['cooling','starting','suspension','transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics','mechanics']){
  const source=await fs.readFile(`lib/${name}.ts`,'utf8');
  let js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");
  await fs.writeFile(path.join(out,`${name}.mjs`),js);
}
const {gearboxRatio,totalDriveRatio,synchronousRoadSpeed,transmissionSpeeds}=await import(pathToFileURL(path.join(out,'transmission.mjs')));
const {INITIAL,INITIAL_TELEMETRY,SPECS,advance}=await import(pathToFileURL(path.join(out,'mechanics.mjs')));
const near=(a,b,epsilon=1e-10)=>assert.ok(Math.abs(a-b)<=epsilon,`${a} != ${b}`);
const omega=2000*Math.PI/30, samples=[];
near(totalDriveRatio(3,'high'),8.137152);
near(totalDriveRatio(3,'low'),15.0537312);
near(totalDriveRatio(-1,'high'),-13.0194432);
for(const range of ['high','low'])for(const gear of [-1,1,2,3]){
  const speed=synchronousRoadSpeed(omega,gear,range,.75);
  const s=transmissionSpeeds(omega,speed,.75,gear,range);
  near(s.pump,s.turbine);
  near(s.slipOmega,0);
  near(s.gearboxOutput/s.propeller,range==='high'?1:1.85);
  near(s.propeller/s.halfshaft,1.92);
  near(s.halfshaft/s.wheel,5.1);
  assert.equal(Math.sign(speed),Math.sign(gear));
  samples.push({gear,range,totalRatio:totalDriveRatio(gear,range),synchronousKmh:speed*3.6});
}
near(synchronousRoadSpeed(omega,-1,'high',.75),-2*synchronousRoadSpeed(omega,1,'high',.75));
near(synchronousRoadSpeed(omega,2,'high',.75)/synchronousRoadSpeed(omega,2,'low',.75),1.85);
for(const gear of [0,4,-2,NaN,1.5]){
  assert.equal(gearboxRatio(gear),null);
  assert.equal(synchronousRoadSpeed(omega,gear,'high',.75),null);
}
const neutral=transmissionSpeeds(omega,5,.75,0,'low');
assert.equal(neutral.turbine,null);
assert.equal(neutral.slipOmega,null);
assert.ok(neutral.gearboxOutput>0,'neutral must not stop the coasting wheel-side shafts');
const rolling={...INITIAL_TELEMETRY,transmission:{...INITIAL_TELEMETRY.transmission,outputOmega:5/.75*1.92*5.1},speed:5,wheel:12,distance:8};
const coast=advance(rolling,INITIAL,.05);
assert.ok(coast.speed>0&&coast.speed<5&&coast.wheel>12);
const paused=advance(rolling,{...INITIAL,enginePaused:true,brake:100},.05);
for(const key of ['speed','wheel','distance'])near(paused[key],rolling[key]);
assert.equal(paused.starting,rolling.starting);
const slow=advance(rolling,{...INITIAL,slow:true},.05);
const short=advance(rolling,INITIAL,.05*.035);near(slow.speed,short.speed);
near(slow.wheel-rolling.wheel,slow.speed/SPECS.tireRadius*.05*.035);
// A real start / engage / brake path through the shared application advance().
let t={...INITIAL_TELEMETRY};
const started={...INITIAL,running:true,throttle:70};
for(let j=0;j<360;j++)t=advance(t,started,1/60);
assert.ok(t.starting.combustion>.5,'guided start must complete');
let forward=t,reverse=t,low=t;
for(let j=0;j<600;j++){
  forward=advance(forward,{...started,gear:1},1/60);
  reverse=advance(reverse,{...started,gear:-1},1/60);
  low=advance(low,{...started,gear:1,transferRange:'low'},1/60);
}
assert.ok(forward.speed>low.speed&&low.speed>0&&reverse.speed < -forward.speed);
assert.equal(forward.starting.warning,'','already running in gear must not show a starting-neutral warning');
const waiting=advance(INITIAL_TELEMETRY,{...INITIAL,running:true,gear:1},.05);
assert.equal(waiting.starting.warning,'引导流程等待空挡');
let stopped=forward;
for(let j=0;j<900;j++)stopped=advance(stopped,{...started,gear:1,brake:100},1/60);
near(stopped.speed,0);
const report={samples,neutral,application:{forwardKmh:forward.speed*3.6,reverseKmh:reverse.speed*3.6,lowKmh:low.speed*3.6,brakeHeldSpeed:stopped.speed},pauseAndSlow:true,errors:0,
  limits:'Checks cover published ratios, straight-running shaft-speed arithmetic and application controls. A separate coupled-dynamics suite covers hydraulic clutch motion and torque constraints; factory converter/traction maps and dimensional validation remain open.'};
await fs.writeFile('outputs/transmission-verification.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
