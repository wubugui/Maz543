// MAZ 1973 figs.45/46/52/53: selector drains non-selected boosters;
// 1/R use series soft-engagement valves, 2 uses a parallel air vessel.
// Source thresholds are separated from fitted geometry/fluid parameters below.
import {CLUTCH_PACKS,CLUTCH_CONTACT,DIRECT_BOOSTER,clutchContactTravel,type ClutchName} from './transmission';
import {CLUTCH_SURFACE_METRICS} from './clutchSurfaceMetrics';
export const CLUTCH_NAMES=Object.keys(CLUTCH_PACKS) as ClutchName[];
export const HYDRAULIC_SOURCE={kgf:98066.5,softStart:98066.5,softClosed:1.6*98066.5,softStop:2.4*98066.5,boosterRange:[8*98066.5,15*98066.5]};
export const HYDRAULIC_FIT={bulk:1.3e9,density:860,discharge:.62,frontDisplacement:30e-6,rearDisplacement:30e-6,
  pumpDriveRatio:1,mainCompliance:2e-12,frontUnload:11*98066.5,relief:12*98066.5,
  lubricationLeak:8e-11,sealLeak:1e-12,jetArea:.3e-6,bypassArea:18e-6,portArea:10e-6,
  spoolVolume:30e-6,airVolume:200e-6,atmosphere:101325,airExponent:1.4,
  steelShear:79e9,pistonDamping:500,frictionCoefficient:.12};
const largeMechanicalFit={preload:1800,mass:3};
export const BOOSTER_MECHANICAL_FIT={first:largeMechanicalFit,reverse:largeMechanicalFit,
  second:{preload:150,mass:1},direct:{preload:50,mass:.8}};
export function pistonArea(n:ClutchName){
  const pack=CLUTCH_PACKS[n];
  const [ro,ri]=n==='direct'?[DIRECT_BOOSTER.outerSealRadius,DIRECT_BOOSTER.innerSealRadius]:[pack.outer+.001,pack.inner+.0035];
  return Math.PI*(ro*ro-ri*ri);
}
export function springRate(){const s=CLUTCH_CONTACT;return 8*HYDRAULIC_FIT.steelShear*(2*s.springWire)**4/(8*(2*s.springRadius)**3*s.springTurns);}
export type BoosterState={pressure:number;travel:number;velocity:number;normalForce:number;capacity:number;flow:number;softSpool:number};
export type HydraulicState={mainPressure:number;frontFlow:number;rearFlow:number;returnFlow:number;residual:number;iterations:number;boosters:Record<ClutchName,BoosterState>};
export function initialHydraulics():HydraulicState{return {mainPressure:0,frontFlow:0,rearFlow:0,returnFlow:0,residual:0,iterations:0,
  boosters:Object.fromEntries(CLUTCH_NAMES.map(n=>[n,{pressure:0,travel:0,velocity:0,normalForce:0,capacity:0,flow:0,softSpool:0}])) as Record<ClutchName,BoosterState>};}
const clamp=(v:number,a:number,b:number)=>Math.max(a,Math.min(b,v));
function flow(dp:number,area:number){const f=HYDRAULIC_FIT;return f.discharge*area*Math.sqrt(2/f.density)*dp/(dp*dp+100**2)**.25;}
function stored(n:ClutchName,p:number){
  const f=HYDRAULIC_FIT,s=HYDRAULIC_SOURCE;
  if(n==='second')return f.airVolume*(1-(f.atmosphere/(f.atmosphere+p))**(1/f.airExponent));
  if(n==='first'||n==='reverse')return f.spoolVolume*clamp((p-s.softStart)/(s.softStop-s.softStart),0,1);
  return 0;
}
function solve(matrix:number[][],rhs:number[]){
  const a=matrix.map((row,i)=>[...row,rhs[i]]),n=rhs.length;
  for(let i=0;i<n;i++){
    let pivot=i;for(let j=i+1;j<n;j++)if(Math.abs(a[j][i])>Math.abs(a[pivot][i]))pivot=j;
    [a[i],a[pivot]]=[a[pivot],a[i]];const d=a[i][i];
    if(Math.abs(d)<1e-20)throw new Error('Singular hydraulic network');
    for(let k=i;k<=n;k++)a[i][k]/=d;
    for(let j=0;j<n;j++)if(j!==i){const m=a[j][i];for(let k=i;k<=n;k++)a[j][k]-=m*a[i][k];}
  }
  return a.map(row=>row[n]);
}
// One backward-Euler network step. Chamber flow, piston inertia, springs and
// unilateral travel stops are solved together; no gear-triggered time ramp.
export function stepHydraulics(old:HydraulicState,gear:number,pumpOmega:number,outputOmega:number,h:number):HydraulicState{
  if(h<=0)return old;
  const f=HYDRAULIC_FIT,s=HYDRAULIC_SOURCE,k=springRate();
  const qFront=Math.max(0,pumpOmega)*f.pumpDriveRatio*f.frontDisplacement/(2*Math.PI);
  // Fixed port orientation: reverse-driven rear pump does not feed its check valve.
  const qRear=Math.max(0,outputOmega)*f.rearDisplacement/(2*Math.PI);
  function evaluate(p:number[]){
    const front=Math.max(0,qFront-2e-11*p[0]-3e-9*Math.max(0,p[0]-f.frontUnload));
    const rear=Math.max(0,qRear-2e-11*p[0]);
    const relief=5e-9*Math.max(0,p[0]-f.relief),lube=f.lubricationLeak*p[0];
    const residual=[f.mainCompliance*(p[0]-old.mainPressure)/h-front-rear+relief+lube];
    const boosters={} as Record<ClutchName,BoosterState>;
    for(let i=0;i<4;i++){
      const name=CLUTCH_NAMES[i],o=old.boosters[name],pressure=p[i+1],A=pistonArea(name),m=BOOSTER_MECHANICAL_FIT[name].mass,L=clutchContactTravel(name);
      const preload=BOOSTER_MECHANICAL_FIT[name].preload;
      const free=(m*o.velocity+h*(A*pressure-preload-k*o.travel))/(m+h*f.pistonDamping+h*h*k);
      const travel=clamp(o.travel+h*free,0,L),velocity=(travel-o.travel)/h;
      const selected=gear===CLUTCH_PACKS[name].gear,soft=name==='first'||name==='reverse';
      const aperture=soft?f.jetArea+f.bypassArea*clamp((s.softClosed-pressure)/(s.softClosed-s.softStart),0,1):f.portArea;
      const incoming=selected?flow(p[0]-pressure,p[0]<pressure?f.bypassArea:aperture):0;
      const drain=selected?0:flow(pressure,f.bypassArea);
      const C=(A*(.0045+o.travel)+30e-6)/f.bulk;
      residual.push(C*(pressure-o.pressure)/h+A*velocity+(stored(name,pressure)-stored(name,o.pressure))/h+f.sealLeak*pressure+drain-incoming);
      residual[0]+=incoming;
      const normalForce=travel===L?Math.max(0,A*pressure-preload-k*travel-f.pistonDamping*velocity-m*(velocity-o.velocity)/h):0;
      const pack=CLUTCH_PACKS[name],meanRadius=CLUTCH_SURFACE_METRICS[pack.family].meanRadius;
      boosters[name]={pressure,travel,velocity,normalForce,capacity:(pack.count-1)*f.frictionCoefficient*meanRadius*normalForce,flow:incoming-drain,
        softSpool:soft?clamp((pressure-s.softStart)/(s.softStop-s.softStart),0,1):0};
    }
    return {residual,boosters,front,rear,returnFlow:relief+lube};
  }
  let p=[old.mainPressure,...CLUTCH_NAMES.map(n=>old.boosters[n].pressure)],iterations=0;
  const norm=(v:number[])=>Math.max(...v.map(Math.abs));
  for(;iterations<30;iterations++){
    const base=evaluate(p);if(norm(base.residual)<2e-10)break;
    const jac=Array.from({length:5},()=>Array(5).fill(0));
    for(let col=0;col<5;col++){
      const trial=[...p],eps=Math.max(.1,Math.abs(p[col])*1e-6);trial[col]+=eps;
      const r=evaluate(trial).residual;for(let row=0;row<5;row++)jac[row][col]=(r[row]-base.residual[row])/eps;
    }
    const delta=solve(jac,base.residual.map(v=>-v));let factor=1;
    for(let line=0;line<16;line++){
      const candidate=p.map((v,i)=>Math.max(0,v+factor*delta[i]));
      if(norm(evaluate(candidate).residual)<norm(base.residual)){p=candidate;break;}
      factor*=.5;
    }
  }
  const result=evaluate(p);
  return {mainPressure:p[0],frontFlow:result.front,rearFlow:result.rear,returnFlow:result.returnFlow,
    residual:norm(result.residual),iterations,boosters:result.boosters};
}
