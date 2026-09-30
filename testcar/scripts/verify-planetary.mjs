import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {planetaryPose,gearboxRatio,advancePlanetary} from '../work/transmission/transmission.mjs';
import {validateBytes} from 'gltf-validator';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-10,`${a} != ${b}`);
const constraints=[];
for(const gear of [1,2,3,-1]){
  const ratio=gearboxRatio(gear),a=planetaryPose(.42,.27,gear),b=planetaryPose(.42+.001,.27+.001/ratio,gear);
  const rates=Object.fromEntries(Object.keys(a).map(k=>[k,(b[k].rx-a[k].rx)/.001]));
  if(gear===1)near(rates.TX_ring40,0);
  if(gear===2)near(rates.TX_sun21,0);
  if(gear===-1)near(rates.TX_ring18,0);
  if(gear===3){for(const key of ['TX_sun41','TX_sun21','TX_ring18','TX_ring40','TX_carrier'])near(rates[key],1);for(let j=0;j<3;j++){near(rates[`TX_long43_${j}`],0);near(rates[`TX_short20_${j}`],0);}}
  // No slip at both bearing races: centre translation +/- ball surface speed.
  const R=.109,r=.0015,cage=rates.TX_feed_bearing_cage,spin=rates.TX_feed_ball_0+cage;
  near(cage*R+spin*r,0);
  near(cage*R-spin*r,rates.TX_ring18*(R-r));
  constraints.push({gear,ratio,rates});
}
const old={inputAngle:7,carrierAngle:2};assert.deepEqual(advancePlanetary(old,100,2,.75,1,'low',0),old);
const neutral=advancePlanetary(old,100,2,.75,0,'low',.01);near(neutral.inputAngle,old.inputAngle);assert.ok(neutral.carrierAngle>old.carrierAngle);
const bytes=await fs.readFile('public/models/maz543a-transmission.glb'),g=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
for(const name of Object.keys(planetaryPose(0,0,0)))assert.ok(g.nodes.some(n=>n.name===name),'missing '+name);
assert.equal(g.nodes.filter(n=>/TX_.*_disc_\d+$/.test(n.name)).length,50);
const r=await validateBytes(new Uint8Array(bytes),{uri:'maz543a-transmission.glb',maxIssues:100});
await fs.writeFile('outputs/transmission-glb-validation.json',JSON.stringify(r,null,2));
assert.equal(r.issues.numErrors,0);assert.equal(r.issues.numWarnings,0);
const report={constraints,bytes:bytes.length,nodes:g.nodes.length,discCount:50,errors:0,warnings:0,limits:'Rigid gearing and asset checks; no claim of complete hydraulic, clutch contact, bearing or installed driveline behavior.'};
await fs.writeFile('outputs/planetary-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
