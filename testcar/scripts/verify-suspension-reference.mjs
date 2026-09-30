import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as revised from '../lib/suspension.ts';
import * as baseline from '../work/suspension-reference/baseline-suspension.ts';
const P=revised.SUSPENSION,dt=1/240;
assert.deepEqual(P,baseline.SUSPENSION);assert.deepEqual(revised.BAR_STIFFNESS,baseline.BAR_STIFFNESS);
const travels=[-.15,-.07,-1e-12,0,1e-12,.04,.12,.17];
assert.deepEqual(revised.suspensionPose(travels),baseline.suspensionPose(travels),'mechanical geometry and pose formulas unchanged');
assert.equal(revised.suspensionElastic(0).force,0);assert.equal(revised.suspensionElastic(0).energy,0);
let rest=revised.initialSuspension();for(let i=0;i<24000;i++)rest=revised.advanceSuspension(rest,dt,0);
for(const key of ['heave','pitch','roll','heaveVelocity','pitchVelocity','rollVelocity'])assert.equal(rest[key],0,`exact rest: ${key}`);
for(const key of ['wheel','velocity','travel','damperForce'])assert.ok(rest[key].every(value=>value===0),`exact rest: ${key}`);
const perturbations=[];
for(const displacement of [-1e-12,1e-12]){
 const initial=revised.initialSuspension();initial.wheel[0]=displacement;
 const next=revised.advanceSuspension(initial,1/480,0);
 assert.ok(next.velocity[0]*displacement<0,'tiny wheel displacement has a restoring response');assert.ok(next.heaveVelocity*displacement>0,'tiny spring force reaches the body');
 perturbations.push({displacement,wheelVelocity:next.velocity[0],bodyVelocity:next.heaveVelocity});
}
const tinyRoad=revised.advanceSuspension(revised.initialSuspension(),1/480,1e-12);assert.ok(tinyRoad.velocity.some(value=>value!==0),'tiny road excitation is not frozen');
const airborne=revised.initialSuspension();airborne.wheel.fill(.1);
const nextAirborne=revised.advanceSuspension(airborne,1/480,0);assert.ok(nextAirborne.normal.every(value=>value===0),'unilateral contact still releases');
const momentum=P.sprungMass*nextAirborne.heaveVelocity+P.unsprungMass*nextAirborne.velocity.reduce((sum,value)=>sum+value,0);
const gravityImpulse=-(P.sprungMass+8*P.unsprungMass)*9.81/480;
assert.ok(Math.abs(momentum-gravityImpulse)<Math.abs(gravityImpulse)*32*Number.EPSILON,'internal spring forces cancel in total vertical momentum');
let old=baseline.initialSuspension(),current=revised.initialSuspension();
const maximumDifference={heave:0,pitch:0,roll:0,wheel:0,normal:0};
for(let i=0;i<1200;i++){
 old=baseline.advanceSuspension(old,dt,.65);current=revised.advanceSuspension(current,dt,.65);
 for(const key of ['heave','pitch','roll'])maximumDifference[key]=Math.max(maximumDifference[key],Math.abs(old[key]-current[key]));
 for(let wheel=0;wheel<8;wheel++){maximumDifference.wheel=Math.max(maximumDifference.wheel,Math.abs(old.wheel[wheel]-current.wheel[wheel]));maximumDifference.normal=Math.max(maximumDifference.normal,Math.abs(old.normal[wheel]-current.normal[wheel]));assert.ok(Number.isFinite(current.wheel[wheel])&&current.normal[wheel]>=0);}
}
// This is a regression bound on an intentionally corrected force origin, not
// a factory suspension acceptance tolerance or an assertion of equal physics.
assert.ok(maximumDifference.heave<1e-6&&maximumDifference.wheel<1e-6,'reference correction must not introduce micrometre-scale drift in this finite trajectory');
const report={passed:true,parametersAndStiffnessUnchanged:true,poseGeometryExactlyUnchanged:true,neutralBefore:baseline.suspensionElastic(0),neutralAfter:revised.suspensionElastic(0),exactStaticSeconds:100,exactStaticDofs:true,perturbations,tinyRoadRetained:true,airborneMomentum:{measured:momentum,gravityImpulse,difference:momentum-gravityImpulse},dynamicRegression:{seconds:5,amplitude:.65,maximumDifference},limits:'Numerical neutral reference and force-balance tests. Full vehicle response, visual cache behavior, catalog dimensions and physical parameter calibration require separate evidence.'};
await fs.writeFile('outputs/suspension-reference/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
