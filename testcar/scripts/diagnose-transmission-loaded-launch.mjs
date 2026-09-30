// Fixed-speed bench: isolate load and gearing before claiming vehicle launch.
// This does not replace the engine governor, tire contact or source acceptance.
import fs from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
await fs.mkdir('work/loaded-launch',{recursive:true});
for(const name of ['transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics']){
  let js=ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");
  await fs.writeFile(`work/loaded-launch/${name}.mjs`,js);
}
const {initialTransmissionDynamics,stepTransmission,outputReduction,TRANSMISSION_DYNAMIC_FIT}=await import('../work/loaded-launch/transmissionDynamics.mjs');
const {HYDRAULIC_SOURCE}=await import('../work/loaded-launch/transmissionHydraulics.mjs');
const hz=Number(process.argv.find(v=>v.startsWith('--hz='))?.split('=')[1]??240);
assert.ok([240,480,960].includes(hz),'supported bounded time-step study');
const h=1/hz,radius=.75,engineRpm=600,engineOmega=engineRpm*Math.PI/30;
const cases=[];
for(const mass of [20550,21000,40600])for(const range of ['high','low'])for(const [pack,gear] of [['first',1],['reverse',-1]]){
  let state=initialTransmissionDynamics(),motionTime=null,contactTime=null,pressure95Time=null,peakAcceleration=0,peakState=null,worstConstraint=0,worstFlow=0;
  // The source shift begins with a running engine in neutral. Allow this
  // fitted neutral circuit and turbine to settle; hold brakes only in neutral.
  for(let i=0;i<5*hz;i++)state=stepTransmission(state,engineOmega,0,range,100,mass,radius,h);
  const samples=[];
  for(let i=0;i<12*hz;i++){
    const previousSpeed=state.outputOmega/outputReduction(range)*radius;
    state=stepTransmission(state,engineOmega,gear,range,0,mass,radius,h);
    const t=(i+1)*h,speed=state.outputOmega/outputReduction(range)*radius,b=state.hydraulics.boosters[pack];
    const acceleration=(speed-previousSpeed)/h;
    assert.ok(Number.isFinite(speed)&&Number.isFinite(acceleration));
    if(Math.abs(speed)>.01&&motionTime===null)motionTime=t;
    if(b.normalForce>0&&contactTime===null)contactTime=t;
    if(b.pressure>.95*state.hydraulics.mainPressure&&pressure95Time===null)pressure95Time=t;
    if(Math.abs(acceleration)>peakAcceleration){peakAcceleration=Math.abs(acceleration);
      peakState={t,speedMps:speed,previousSpeedMps:previousSpeed,accelerationMps2:acceleration,
        pressurePa:b.pressure,normalForceN:b.normalForce,capacityNm:b.capacity,
        clutchTorqueNm:state.clutchTorque[pack],slipRadPerSec:state.clutchSlip[pack],
        inputOmega:state.inputOmega,converterTorqueNm:state.converterTorque};}
    worstConstraint=Math.max(worstConstraint,state.constraintResidual);worstFlow=Math.max(worstFlow,state.hydraulics.residual);
    if(i%(hz/10)===(hz/10)-1)samples.push({t,speedMps:speed,accelerationMps2:acceleration,pressurePa:b.pressure,
      mainPressurePa:state.hydraulics.mainPressure,inputOmega:state.inputOmega,outputOmega:state.outputOmega,
      converterTorqueNm:state.converterTorque,clutchTorqueNm:state.clutchTorque[pack],capacityNm:b.capacity,
      slipRadPerSec:state.clutchSlip[pack],engineLoadNm:state.engineLoad});
  }
  assert.ok(worstConstraint<1e-7&&worstFlow<2e-8,'numerical convergence; no source performance pass');
  const last=samples.at(-1),caseSummary={massKg:mass,range,pack,firstPlateContactSeconds:contactTime,
    firstSpeedAbove001MpsSeconds:motionTime,pressure95MainSeconds:pressure95Time,
    peakSampleStepAccelerationMps2:peakAcceleration,peakState,finalSpeedMps:last.speedMps,
    motionDiagnosticWithin3s:motionTime!==null&&motionTime<=3,
    pressureDiagnosticWithin3s:pressure95Time!==null&&pressure95Time<=3,
    worstConstraint,worstFlow};
  cases.push({...caseSummary,samples});console.log(caseSummary);
}
const report={status:'DIAGNOSTIC_ONLY_SOURCE_ACCEPTANCE_OPEN',engineRpm,stepSeconds:h,tireRadiusM:radius,
  massSource:{url:'https://djvu.online/file/zjMdLY3MFjmTL',edition:1977,printedPage:12,
    currentRuntimeKg:20550,maz543ACurbTableKg:21000,maz543AFullTableKg:40600,
    limits:'Primary manual web transcription read; original table scan fetch returned 403/timeout. Nominal empty table has tolerance; this is not a measured specimen. No runtime mass changed by this diagnostic.'},
  launchSource:{url:'https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/011.htm',
    loadedMotionMaximumSeconds:3,fullPressureSeconds:[2,3],firstAccelerationMps2:.8,reverseAccelerationMps2:.7},
  assumptions:{fixedEngineSpeed:true,neutralWarmupSeconds:5,selectedDurationSeconds:12,brakeAfterShift:0,
    road:'horizontal; fitted Coulomb rolling resistance; no separate tire traction or breakaway model',
    motionDiagnosticThresholdMps:.01,pressureDiagnosticFractionOfMain:.95,fit:TRANSMISSION_DYNAMIC_FIT,
    boosterRangePa:HYDRAULIC_SOURCE.boosterRange},
  limits:'Fixed engine speed supplies whatever engine torque the fitted converter requests. This does not validate engine torque/governor behavior, factory two-reactor converter, loaded suspension, payload placement, tire traction, or factory launch. Diagnostic thresholds are not source instrument definitions. Peak acceleration includes discrete clutch engagement and needs physical compliance validation.',cases};
await fs.writeFile(`outputs/transmission-loaded-launch-diagnostic${hz===240?'':`-${hz}hz`}.json`,JSON.stringify(report,null,2));
