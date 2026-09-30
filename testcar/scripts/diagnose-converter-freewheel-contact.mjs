import fs from 'node:fs/promises';
import ts from 'typescript';
import assert from 'node:assert/strict';
const build=JSON.parse(await fs.readFile('outputs/converter-freewheel-build.json','utf8'));
const measured=JSON.parse(await fs.readFile('outputs/converter-freewheel-inertia.json','utf8'));
await fs.mkdir('work/freewheel-contact',{recursive:true});
await fs.writeFile('work/freewheel-contact/converterFreewheel.mjs',ts.transpileModule(await fs.readFile('lib/converterFreewheel.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const {initialFreewheel,stepFreewheel}=await import('../work/freewheel-contact/converterFreewheel.mjs');
const fit={...build.fit,rollerMass:measured.roller.massKg,rollerInertia:measured.roller.axialInertiaKgM2,
  outerInertia:measured.outerAssemblyInertiaKgM2,friction:.12,shearModulus:79e9,springFreeLength:.0085,springDamping:.2};
const hz=Number(process.argv.find(v=>v.startsWith('--hz='))?.split('=')[1]??4000);assert.ok([4000,8000,16000].includes(hz));
const h=1/hz;let state=initialFreewheel(fit);const initialEnergy=state.kinetic+state.springEnergy;
const rows=[];let worst=0,penetration=0,betaMin=0,betaMax=0,maxIterations=0,maximumEnergyExcess=0;
for(let i=0;i<2*hz;i++){
  const torque=i<.4*hz?-2:i<1.2*hz?2:-2;
  state=stepFreewheel(state,torque,h,fit);
  const beta=Math.atan2(Math.sin(Math.atan2(state.q[1],state.q[0])-state.q[3]),Math.cos(Math.atan2(state.q[1],state.q[0])-state.q[3]));
  worst=Math.max(worst,state.residual);penetration=Math.min(penetration,...state.gaps);betaMin=Math.min(betaMin,beta);betaMax=Math.max(betaMax,beta);maxIterations=Math.max(maxIterations,state.iterations);
  maximumEnergyExcess=Math.max(maximumEnergyExcess,state.kinetic+state.springEnergy-state.inputWork-initialEnergy);
  assert.ok(state.gaps.every(g=>g>=-1e-9)&&state.residual<1e-8,'actual nonlinear contact convergence');
  for(let c=0;c<2;c++)assert.ok(state.normalForce[c]>=-1e-8&&Math.abs(state.frictionForce[c])<=fit.friction*state.normalForce[c]+1e-7,'Coulomb cone');
  if(i%(hz/100)===(hz/100)-1)rows.push({...state,torque,beta});
  if(!state.q.every(Number.isFinite))throw new Error('Non-finite contact state');
}
assert.ok(Math.abs(rows[39].v[3])<1e-7&&Math.abs(rows.at(-1).v[3])<1e-7,'negative applied torque wedges naturally');
assert.ok(rows[119].v[3]>1,'positive torque overcomes spring preload and overruns');
assert.ok(maximumEnergyExcess<1e-6,'bench must not manufacture cumulative mechanical energy');
const locked=rows[39],supportBalance=-2+fit.rollerCount*fit.innerRadius*locked.frictionForce[0];
assert.ok(Math.abs(supportBalance)<1e-6,'independent fixed-inner-race torque balance');
const sweep=[];
if(hz===4000){
  for(const torque of [-2,0,.15,.3,.4,.6,1,2]){
    let x=initialFreewheel(fit);for(let i=0;i<hz/4;i++)x=stepFreewheel(x,torque,h,fit);
    sweep.push({torqueNm:torque,outerOmega:x.v[3],angle:x.q[3],innerReactionNm:fit.rollerCount*fit.innerRadius*x.frictionForce[0]});
  }
  let frictionless=initialFreewheel(fit);for(let i=0;i<hz/10;i++)frictionless=stepFreewheel(frictionless,-2,h,{...fit,friction:0});
  assert.ok(frictionless.v[3]<-1,'removing roller contact friction must remove directional torque holding');
  sweep.push({torqueNm:-2,friction:0,outerOmega:frictionless.v[3],angle:frictionless.q[3]});
}
const summary={worstResidual:worst,minimumGapM:penetration,betaRange:[betaMin,betaMax],maxIterations,maximumEnergyExcess,supportBalanceNm:supportBalance,
  at400ms:rows[39],at1200ms:rows[119],final:rows.at(-1)};
await fs.writeFile(`outputs/converter-freewheel-contact-diagnostic${hz===4000?'':`-${hz}hz`}.json`,JSON.stringify({fit,stepSeconds:h,summary,rows,torqueSweep:sweep,
 limits:'Experimental periodic-cell rigid contact/friction solver, not yet installed. Applied bench torque, fitted spring/friction/density, native outer-race inertia excluding reactor blades. Full pocket collision, fluid torque and factory performance not accepted.'},null,2));
console.log(JSON.stringify(summary,null,2));
