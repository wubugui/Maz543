import fs from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
await fs.mkdir('work/hydraulics',{recursive:true});
for(const name of ['cooling','starting','suspension','transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics','mechanics']){
  let js=ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");await fs.writeFile(`work/hydraulics/${name}.mjs`,js);
}
const {INITIAL,INITIAL_TELEMETRY,advance}=await import('../work/hydraulics/mechanics.mjs');
const {initialTransmissionDynamics,stepTransmission,transmissionMass,CLUTCH_SLIP}=await import('../work/hydraulics/transmissionDynamics.mjs');
const {HYDRAULIC_FIT}=await import('../work/hydraulics/transmissionHydraulics.mjs');
const M=transmissionMass(20550,.75,'high');
const energy=s=>(M.aa*s.inputOmega**2+2*M.ac*s.inputOmega*s.outputOmega+M.cc*s.outputOmega**2)/2;
let decay={...initialTransmissionDynamics(),inputOmega:100};
for(let j=0;j<240;j++){
  const next=stepTransmission(decay,0,0,'high',0,20550,.75,1/240);
  assert.ok(energy(next)<=energy(decay)+1e-8,'unpowered passive coupling must not add rotational energy');decay=next;
}
let warm={...INITIAL_TELEMETRY};const control={...INITIAL,running:true,throttle:50};
for(let j=0;j<360;j++)warm=advance(warm,control,1/60);
console.log('warm',{rpm:warm.rpm,speed:warm.speed,pressure:warm.transmission.hydraulics.mainPressure,stage:warm.starting.stage,input:warm.transmission.inputOmega});
assert.ok(warm.starting.combustion>.5);assert.ok(Math.abs(warm.speed)<1e-5);
const originalFriction=HYDRAULIC_FIT.frictionCoefficient;HYDRAULIC_FIT.frictionCoefficient=0;
let frictionless=warm;for(let j=0;j<600;j++)frictionless=advance(frictionless,{...control,gear:1},1/60);
HYDRAULIC_FIT.frictionCoefficient=originalFriction;
assert.ok(frictionless.transmission.hydraulics.boosters.first.normalForce>100,'hydraulics must still clamp');
assert.ok(Math.abs(frictionless.speed)<1e-5,'without disc friction gear selection must not drive the wheels');
let regular=warm,slow=warm;
for(let j=0;j<600;j++){regular=advance(regular,{...control,gear:1},.035/60);slow=advance(slow,{...control,gear:1,slow:true},1/60);}
assert.ok(Math.abs(regular.speed-slow.speed)<1e-10,'slow must scale the coupled clock');
const rows=[],staticBalance=[];let worstFlow=0,worstConstraint=0,maxConstraintIterations=0;
const measure=s=>{worstConstraint=Math.max(worstConstraint,s.constraintResidual);maxConstraintIterations=Math.max(maxConstraintIterations,s.constraintIterations);};
// Independent virtual-work check at a brake-held stall. At zero acceleration,
// converter torque + b_input * clutch reaction must vanish, as must road torque
// + b_output * clutch reaction. This checks force transmission, not just ratios.
for(const [name,gear] of [['first',1],['second',2],['direct',3],['reverse',-1]]){
  let state=initialTransmissionDynamics();
  for(let j=0;j<1440;j++){state=stepTransmission(state,83.1,gear,'high',100,20550,.75,1/240);measure(state);}
  const b=CLUTCH_SLIP[name],lambda=state.clutchTorque[name];
  assert.ok(Math.abs(state.inputOmega)<1e-6&&Math.abs(state.outputOmega)<1e-6);
  const inputResidual=state.converterTorque+b[0]*lambda,outputResidual=state.roadTorque+b[1]*lambda;
  assert.ok(Math.abs(inputResidual)<1e-5&&Math.abs(outputResidual)<1e-5);
  staticBalance.push({name,converterTorque:state.converterTorque,clutchTorque:lambda,roadTorque:state.roadTorque,inputResidual,outputResidual});
}
let shifting=warm;
for(const gear of [1,2,3,0,-1,0,1])for(let j=0;j<120;j++){
  shifting=advance(shifting,{...control,gear},1/120);
  worstConstraint=Math.max(worstConstraint,shifting.transmission.constraintResidual);maxConstraintIterations=Math.max(maxConstraintIterations,shifting.transmission.constraintIterations);
  assert.ok(Number.isFinite(shifting.speed));worstFlow=Math.max(worstFlow,shifting.transmission.hydraulics.residual);
  for(const b of Object.values(shifting.transmission.hydraulics.boosters))assert.ok(b.pressure>=0&&b.normalForce>=0&&b.travel>=0);
}
for(const gear of [1,2,3,-1]){
  let t=warm;let firstMotion=null;
  for(let j=0;j<1200;j++){
    t=advance(t,{...control,gear},1/60);
    worstConstraint=Math.max(worstConstraint,t.transmission.constraintResidual);maxConstraintIterations=Math.max(maxConstraintIterations,t.transmission.constraintIterations);
    worstFlow=Math.max(worstFlow,t.transmission.hydraulics.residual);
    if(Math.abs(t.speed)>.01&&firstMotion===null)firstMotion=(j+1)/60;
    assert.ok(Number.isFinite(t.speed)&&Math.abs(t.speed)<40);
    for(const [name,torque] of Object.entries(t.transmission.clutchTorque))assert.ok(Math.abs(torque)<=t.transmission.hydraulics.boosters[name].capacity+1e-6);
    if(j%60===59)rows.push({gear,t:(j+1)/60,rpm:t.rpm,speed:t.speed,pressure:t.transmission.hydraulics.mainPressure,slip:t.transmission.clutchSlip,torque:t.transmission.clutchTorque,capacity:Object.fromEntries(Object.entries(t.transmission.hydraulics.boosters).map(([n,b])=>[n,b.capacity])),heat:t.transmission.clutchHeat});
  }
  console.log('gear',gear,{speed:t.speed*3.6,rpm:t.rpm,firstMotion,slip:t.transmission.clutchSlip,heat:t.transmission.clutchHeat});
  assert.ok(t.speed*gear>0,'wheel direction must follow applied clutch reaction');
  if(gear===3)assert.ok(Math.abs(t.transmission.clutchSlip.direct)<1e-6,'reconstructed broad piston must hold this documented 50 percent throttle case');
  let stopped=t;for(let j=0;j<900;j++){stopped=advance(stopped,{...control,gear,brake:100},1/60);measure(stopped.transmission);}
  console.log('brake',gear,stopped.speed);assert.ok(Math.abs(stopped.speed)<1e-4);
  const paused=advance(t,{...control,gear,enginePaused:true},.05);assert.equal(paused.transmission,t.transmission);assert.equal(paused.starting,t.starting);assert.equal(paused.distance,t.distance);
}
await fs.writeFile('outputs/transmission-dynamic-verification.json',JSON.stringify({rows,staticBalance,worstFlow,worstConstraint,maxConstraintIterations,limits:'Reduced converter approximation, fitted inertia/friction/vehicle resistance; no full vehicle or factory torque-map acceptance.'},null,2));
assert.ok(worstConstraint<1e-7,'friction complementarity must converge');
assert.ok(worstFlow<2e-8);console.log('PASS coupled transmission');
