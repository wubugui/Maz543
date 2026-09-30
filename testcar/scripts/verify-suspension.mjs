import './prepare-suspension.mjs';
import {wheelGeometry,suspensionElastic,advanceSuspension,initialSuspension,SUSPENSION as P} from '../work/compiled/suspension.mjs';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]),near=(a,b,e=1e-7)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);
let maxClosure=0,maxEnergyError=0;
for(let i=0;i<=400;i++){
 const q=-.19+i/400*.40,g=wheelGeometry(q),e=suspensionElastic(q),h=1e-5;
 for(const [a,b,c,d] of [[g.lower,P.lower,P.lowerEnd,P.lower],[g.upper,P.upper,P.upperEnd,P.upper],[g.lower,g.upper,P.lowerEnd,P.upperEnd]]){maxClosure=Math.max(maxClosure,Math.abs(distance(a,b)-distance(c,d)));near(distance(a,b),distance(c,d));}
 near(g.wheel[0]-P.wheelY,q);assert.ok(g.damperLength>.48&&g.damperLength<.99);
 const energyDerivative=(suspensionElastic(q+h).energy-suspensionElastic(q-h).energy)/(2*h);maxEnergyError=Math.max(maxEnergyError,Math.abs(energyDerivative-e.force));near(energyDerivative,e.force,.02);
}
let rest=initialSuspension();for(let i=0;i<600;i++)rest=advanceSuspension(rest,1/60,0);near(rest.heave,0,1e-7);assert.ok(rest.travel.every(q=>Math.abs(q)<1e-7));
let s=initialSuspension(),maxTravel=0,minNormal=Infinity,maxBody=0;
for(let i=0;i<1200;i++){s=advanceSuspension(s,1/60,.85);maxTravel=Math.max(maxTravel,...s.travel.map(Math.abs));minNormal=Math.min(minNormal,...s.normal);maxBody=Math.max(maxBody,Math.abs(s.heave));assert.ok([...s.travel,s.heave,s.roll,s.pitch,...s.normal].every(Number.isFinite));assert.ok(s.normal.every(f=>f>=0));}
assert.ok(maxTravel>.015&&maxTravel<.24);assert.ok(maxBody>.005&&maxBody<.2);
const excited=Math.hypot(s.heave,...s.travel);for(let i=0;i<1800;i++)s=advanceSuspension(s,1/60,0);
assert.ok(Math.hypot(s.heave,...s.travel)<excited*.02,'free response must decay after removing road excitation');
// A wheel moved above its loaded radius loses unilateral road contact.
let airborne=initialSuspension();airborne.wheel[0]=.08;airborne=advanceSuspension(airborne,1/480,0);assert.equal(airborne.normal[0],0);
const report={checks:['rigid four-bar closure through 400 mm geometric envelope','torsion energy derivative equals wheel force','static gravitational equilibrium','8 unilateral tire contacts','heave pitch and roll force integration','response decays without road excitation','damper telescoping envelope'],maxClosure,maxEnergyError,maxTravel,minNormal,maxBody,remainingResponse:Math.hypot(s.heave,...s.travel),scope:'Numerical model validation only; MAZ geometry and force parameters remain uncalibrated'};
await fs.writeFile('outputs/suspension-verification.json',JSON.stringify(report,null,2));console.log(report);
