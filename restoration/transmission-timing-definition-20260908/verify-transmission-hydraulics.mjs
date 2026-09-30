import fs from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
await fs.mkdir('work/hydraulics',{recursive:true});
for(const name of ['transmission','clutchSurfaceMetrics','transmissionHydraulics']){
  let js=ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");await fs.writeFile(`work/hydraulics/${name}.mjs`,js);
}
const {initialHydraulics,stepHydraulics,CLUTCH_NAMES,HYDRAULIC_SOURCE,pistonArea,springRate,BOOSTER_MECHANICAL_FIT}=await import('../work/hydraulics/transmissionHydraulics.mjs');
const {CLUTCH_PACKS,clutchContactTravel}=await import('../work/hydraulics/transmission.mjs');
const pump=600*Math.PI/30/.831,h=1/240,rows=[],timingDiagnostics=[];let worst=0,maxIterations=0;
function step(s,g,p=pump,o=0){const n=stepHydraulics(s,g,p,o,h);worst=Math.max(worst,n.residual);maxIterations=Math.max(maxIterations,n.iterations);assert.ok(Number.isFinite(n.mainPressure));return n;}
for(const name of CLUTCH_NAMES){
  const gear=CLUTCH_PACKS[name].gear;let s=initialHydraulics();
  for(let j=0;j<240;j++)s=step(s,gear,0);
  assert.equal(s.boosters[name].travel,0,'no supply must not press selected pack');
  for(let j=0;j<240;j++)s=step(s,0);
  assert.ok(s.mainPressure>HYDRAULIC_SOURCE.boosterRange[0]&&s.mainPressure<HYDRAULIC_SOURCE.boosterRange[1]);
  // First plate contact is not loaded chassis motion. The manual says full
  // booster pressure, without defining a 95%-of-main measurement convention.
  let contactTime=null,pressure95MainTime=null,atThreeSeconds=null;
  for(let j=0;j<1440;j++){
    s=step(s,gear);const b=s.boosters[name];
    if(b.normalForce>0&&contactTime===null)contactTime=(j+1)*h;
    if(b.pressure>.95*s.mainPressure&&pressure95MainTime===null)pressure95MainTime=(j+1)*h;
    if(j===719)atThreeSeconds={pressurePa:b.pressure,mainPressurePa:s.mainPressure,
      fractionOfMain:b.pressure/s.mainPressure,travelM:b.travel,normalForceN:b.normalForce};
    for(const other of CLUTCH_NAMES)if(other!==name)assert.ok(s.boosters[other].normalForce===0);
    if(j%24===0)rows.push({pack:name,t:(j+1)*h,main:s.mainPressure,pressure:b.pressure,travel:b.travel,normal:b.normalForce,capacity:b.capacity,soft:b.softSpool});
  }
  assert.ok(contactTime!==null&&pressure95MainTime!==null,name+' must engage');
  assert.equal(s.boosters[name].travel,clutchContactTravel(name));
  const A=pistonArea(name),preload=BOOSTER_MECHANICAL_FIT[name].preload,k=springRate(name),travel=clutchContactTravel(name);
  const staticContactPressure=(preload+k*travel)/A;
  const timing={pack:name,firstPlateContactSeconds:contactTime,pressure95MainSeconds:pressure95MainTime,
    atThreeSeconds,pressureAtSixSecondsPa:s.boosters[name].pressure,
    mainPressureAtSixSecondsPa:s.mainPressure,capacityAtSixSecondsNm:s.boosters[name].capacity,
    diagnostic95MainWithinThreeSeconds:pressure95MainTime<=3,
    softValveSpringDiagnostic:(name==='first'||name==='reverse')?{
      staticContactPressurePa:staticContactPressure,
      bypassClosesPressurePa:HYDRAULIC_SOURCE.softClosed,
      staticTravelAtBypassClosureM:Math.max(0,Math.min(travel,(A*HYDRAULIC_SOURCE.softClosed-preload)/k)),
      fullTravelM:travel,
      contactRequiresPressureAboveBypassClosure:staticContactPressure>HYDRAULIC_SOURCE.softClosed,
      limits:'Quasistatic spring/piston estimate; excludes damping and inertia. Explains fitted timing sensitivity, not factory dimensions or permission to retune.'}:null};
  timingDiagnostics.push(timing);console.log(timing);
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
const sourceTimingAcceptance={status:'OPEN',applicablePacks:['first','reverse'],
  sources:[
    {edition:1973,url:'https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/011.htm',section:'Soft engagement mechanism, following fig.53'},
    {edition:1977,url:'https://djvu.online/file/zjMdLY3MFjmTL',section:'Soft engagement mechanism; corroborating edition'}],
  conditions:{engineRpm:600,shiftFrom:'neutral',road:'horizontal, hard surface',chassis:'with load'},
  motionStartMaximumSeconds:3,fullBoosterPressureSeconds:[2,3],
  accelerationUpperMps2:{first:.8,reverse:.7},
  numericalTest:{engineRpm:600,outputOmega:0,neutralPrechargeSeconds:1,stepSeconds:h,
    chassisMotionSimulated:false,pressureDiagnostic:'First crossing above 95% of simultaneous main pressure'},
  limits:'Manual does not specify a 95% convention, exact load, oil temperature or instrument tolerance in this paragraph. Plate contact is not vehicle motion. This stationary fitted circuit cannot validate loaded launch. The 95%-of-main diagnostic is retained unchanged and is not a factory full-pressure pass.'};
await fs.writeFile('outputs/transmission-hydraulic-verification.json',JSON.stringify({rows,timingDiagnostics,sourceTimingAcceptance,maxFlowResidual:worst,maxIterations,sharedDifference,limits:'Fitted hydraulic volumes, spring loads, oil and orifice parameters; factory thresholds/topology only. No vehicle-load acceptance.'},null,2));
console.log({worst,maxIterations});assert.ok(worst<2e-8,'network flow balance');
