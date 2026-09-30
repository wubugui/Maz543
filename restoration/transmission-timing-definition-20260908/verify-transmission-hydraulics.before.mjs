import fs from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
await fs.mkdir('work/hydraulics',{recursive:true});
for(const name of ['transmission','clutchSurfaceMetrics','transmissionHydraulics']){
  let js=ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");await fs.writeFile(`work/hydraulics/${name}.mjs`,js);
}
const {initialHydraulics,stepHydraulics,CLUTCH_NAMES,HYDRAULIC_SOURCE,pistonArea,BOOSTER_MECHANICAL_FIT}=await import('../work/hydraulics/transmissionHydraulics.mjs');
const {CLUTCH_PACKS,clutchContactTravel}=await import('../work/hydraulics/transmission.mjs');
const pump=600*Math.PI/30/.831,h=1/240,rows=[];let worst=0,maxIterations=0;
function step(s,g,p=pump,o=0){const n=stepHydraulics(s,g,p,o,h);worst=Math.max(worst,n.residual);maxIterations=Math.max(maxIterations,n.iterations);assert.ok(Number.isFinite(n.mainPressure));return n;}
for(const name of CLUTCH_NAMES){
  const gear=CLUTCH_PACKS[name].gear;let s=initialHydraulics();
  for(let j=0;j<240;j++)s=step(s,gear,0);
  assert.equal(s.boosters[name].travel,0,'no supply must not press selected pack');
  for(let j=0;j<240;j++)s=step(s,0);
  assert.ok(s.mainPressure>HYDRAULIC_SOURCE.boosterRange[0]&&s.mainPressure<HYDRAULIC_SOURCE.boosterRange[1]);
  let contactTime=null,fullTime=null;
  for(let j=0;j<1440;j++){
    s=step(s,gear);const b=s.boosters[name];
    if(b.normalForce>0&&contactTime===null)contactTime=(j+1)*h;
    if(b.pressure>.95*s.mainPressure&&fullTime===null)fullTime=(j+1)*h;
    for(const other of CLUTCH_NAMES)if(other!==name)assert.ok(s.boosters[other].normalForce===0);
    if(j%24===0)rows.push({pack:name,t:(j+1)*h,main:s.mainPressure,pressure:b.pressure,travel:b.travel,normal:b.normalForce,capacity:b.capacity,soft:b.softSpool});
  }
  assert.ok(contactTime!==null&&fullTime!==null,name+' must engage');
  assert.equal(s.boosters[name].travel,clutchContactTravel(name));
  console.log(name,{contactTime,fullTime,pressure:s.boosters[name].pressure,capacity:s.boosters[name].capacity});
  // The second gear's air vessel continues discharging after the plates have
  // unloaded; the manual gives no two-second full-drain requirement.
  for(let j=0;j<960;j++)s=step(s,0);
  assert.ok(s.boosters[name].travel<1e-7&&s.boosters[name].pressure<100,'neutral must drain and return '+name);
}
let tow=initialHydraulics();for(let j=0;j<240;j++)tow=step(tow,0,0,100);
assert.ok(tow.mainPressure>HYDRAULIC_SOURCE.boosterRange[0]);assert.equal(tow.frontFlow,0);assert.ok(tow.rearFlow>0);
assert.equal(pistonArea('first'),pistonArea('reverse'));
assert.deepEqual(BOOSTER_MECHANICAL_FIT.first,BOOSTER_MECHANICAL_FIT.reverse);
let first=initialHydraulics(),reverse=initialHydraulics(),sharedDifference={pressure:0,travel:0,normalForce:0,capacity:0};
for(let j=0;j<2400;j++){
  first=step(first,j<1440?1:0);reverse=step(reverse,j<1440?-1:0);
  for(const k of Object.keys(sharedDifference))sharedDifference[k]=Math.max(sharedDifference[k],Math.abs(first.boosters.first[k]-reverse.boosters.reverse[k]));
}
assert.ok(sharedDifference.pressure<.01&&sharedDifference.travel<1e-8&&sharedDifference.normalForce<.001&&sharedDifference.capacity<.001,'identical large boosters must respond equally to identical supply');
await fs.writeFile('outputs/transmission-hydraulic-verification.json',JSON.stringify({rows,maxFlowResidual:worst,maxIterations,sharedDifference,limits:'Fitted hydraulic volumes, spring loads, oil and orifice parameters; factory thresholds/topology only. No vehicle-load acceptance.'},null,2));
console.log({worst,maxIterations});assert.ok(worst<2e-8,'network flow balance');
