// C5 / MZN-2 topology and operating limits: MAZ technical descriptions, 1973
// figs.24/122 and 1977 pp.231,238–239. All lumped electrical, fluid, inertia,
// friction, combustion and installation parameters below remain uncalibrated.
// This is a reduced dynamical reconstruction, not a validated engine test map.
import {initialCooling,copyCooling,stepCooling,type CoolingState,type CoolingInputs} from './cooling';
export const STARTING={pinionTeeth:11,ringTeeth:132,module:.0047,
  travel:.0325,axialRestGap:.0035,gearWidth:.027,helixLead:.072,engineInertia:8,rotorInertia:.015,
  driveInertia:.004,preoilDisplacement:3.5e-6,oilThreshold:2.5*98066.5,
  starterLimit:5,retryInterval:30,preoilLimit:60,batteryAh:280,
  starterPosition:[.3455,.163,-Math.sqrt((.0047*(132+11)/2)**2-.093**2)] as [number,number,number],
  pumpPosition:[-2.72,.90,-.47] as [number,number,number]};
export type StartInputs=CoolingInputs&{running:boolean;startMode:'guided'|'manual';batteryOn:boolean;preoilHeld:boolean;starterHeld:boolean;fuelEnabled:boolean;throttle:number;gear:number;transmissionLoad?:number};
export type StartingState={cooling:CoolingState;omega:number;angle:number;rotorOmega:number;rotorAngle:number;pinionOmega:number;pinionAngle:number;
  shift:number;mesh:boolean;overrun:boolean;meshPhase:number;pumpOmega:number;pumpAngle:number;
  oilPressure:number;oilFlow:number;current:number;pumpCurrent:number;voltage:number;soc:number;
  combustion:number;firingTravel:number;crankTorque:number;starterTorque:number;preoilTime:number;starterTime:number;restTime:number;
  battery:boolean;preoil:boolean;starter:boolean;fuel:boolean;guidedFailed:boolean;request:boolean;
  stage:'off'|'preoil'|'cranking'|'running'|'coasting'|'rest'|'failed';warning:string};
export function initialStarting():StartingState{return {cooling:initialCooling(),omega:0,angle:0,rotorOmega:0,rotorAngle:0,pinionOmega:0,pinionAngle:0,shift:0,mesh:false,overrun:false,meshPhase:0,pumpOmega:0,pumpAngle:0,oilPressure:0,oilFlow:0,current:0,pumpCurrent:0,voltage:0,soc:1,combustion:0,firingTravel:0,crankTorque:0,starterTorque:0,preoilTime:0,starterTime:0,restTime:30,battery:false,preoil:false,starter:false,fuel:false,guidedFailed:false,request:false,stage:'off',warning:''};}
const TAU=2*Math.PI,ratio=STARTING.ringTeeth/STARTING.pinionTeeth,lead=STARTING.helixLead/TAU;
const clamp=(x:number,a:number,b:number)=>Math.min(b,Math.max(a,x));
export function advanceStarting(previous:StartingState,c:StartInputs,dt:number):StartingState{
  const s={...previous,cooling:copyCooling(previous.cooling)};const steps=Math.max(1,Math.ceil(dt*1200)),h=dt/steps;
  if(c.running&&!s.request)s.guidedFailed=false;
  for(let step=0;step<steps;step++){
    const rpm=s.omega*60/TAU,guided=c.startMode==='guided';
    s.battery=guided?(c.running||s.omega>0):c.batteryOn;
    s.fuel=guided?c.running&&c.fuelEnabled:c.fuelEnabled;
    // Guided operation reproduces the driver's sequence. These are NOT claimed
    // to be original pressure/neutral electronic interlocks. Manual buttons
    // feed their contactors even with inadequate pressure or an engaged gear.
    s.preoil=s.battery&&(guided?c.running&&!s.guidedFailed&&rpm<450:c.preoilHeld);
    s.starter=s.battery&&(guided?c.running&&!s.guidedFailed&&rpm<450&&s.oilPressure>=STARTING.oilThreshold&&c.gear===0&&(s.starterTime>0||s.restTime>=STARTING.retryInterval):c.starterHeld);
    s.voltage=s.battery?Math.max(0,24+1.2*s.soc-.0025*(s.current+s.pumpCurrent+s.cooling.coilCurrent[0]+s.cooling.coilCurrent[1])):0;
    const flux=.096*(1-Math.exp(-Math.max(0,s.current)/300));
    // Series motor: current sets field flux, flux supplies torque and back EMF.
    const di=s.starter?(s.voltage-.012*s.current-flux*s.rotorOmega)/.0003:-s.current/.003;
    s.current=clamp(s.current+di*h,0,2200);
    const motorTorque=flux*s.current-.018*s.rotorOmega;
    s.starterTorque=Math.max(0,flux*s.current);
    s.pumpCurrent=s.preoil?clamp((s.voltage-.05*s.pumpOmega)/.15,0,100):0;
    const pumpLoad=s.oilPressure*STARTING.preoilDisplacement/(TAU*.78)+.04+.001*s.pumpOmega;
    s.pumpOmega=Math.max(0,s.pumpOmega+(s.pumpCurrent*.05-pumpLoad)/.0015*h);
    // Positive-displacement pump, gallery compliance, leakage and a lumped
    // system pressure relief. Check valves prevent reverse flow into either
    // inactive pump. The relief is a system approximation, not an invented MZN valve.
    const electricFlow=STARTING.preoilDisplacement*s.pumpOmega/TAU;
    const mechanicalFlow=45e-6*s.omega/TAU;
    s.oilFlow=electricFlow+mechanicalFlow;
    s.oilPressure=Math.max(0,s.oilPressure+(s.oilFlow-5.2e-10*s.oilPressure-Math.max(0,s.oilPressure-9*98066.5)*1e-8)/1.2e-9*h);
    s.pumpAngle+=s.pumpOmega*h;
    if(s.fuel&&rpm>80)s.firingTravel+=s.omega*h;else if(rpm<40)s.firingTravel=0;
    const firing=s.fuel&&rpm>80&&s.firingTravel>TAU*2;
    s.combustion=clamp(s.combustion+(firing?3:-8)*h,0,1);
    const target=550+clamp(c.throttle,0,100)/100*1450;
    const friction=55+1.2*s.omega+.003*s.omega*s.omega;
    const rack=clamp(friction/1800+(target-rpm)*.002,0,1);
    // Averaged governor torque with a 12-cylinder/720-degree firing ripple.
    // No claim of solved cylinder thermodynamics or a measured fuel-pump map.
    const burning=1800*rack*s.combustion*(1+.12*Math.sin(s.angle*6));
    const coolingLoad=stepCooling(s.cooling,c,s.omega,s.voltage,burning*s.omega,h);
    const engineTorque=burning-friction-coolingLoad-(c.transmissionLoad??0);
    s.crankTorque=engineTorque;
    let advancedPartial=false;
    if(s.mesh&&!s.overrun&&s.shift<STARTING.travel-1e-10){
      advancedPartial=true;
      const coupling=(12+420*s.shift)*lead+.008*(s.rotorOmega-s.pinionOmega);
      s.omega=Math.max(0,s.omega+(engineTorque+coupling*ratio*.88)/(STARTING.engineInertia+STARTING.driveInertia*ratio*ratio)*h);
      s.rotorOmega=Math.max(0,s.rotorOmega+(motorTorque-coupling)/STARTING.rotorInertia*h);
      s.pinionOmega=ratio*s.omega;
      s.shift=clamp(s.shift+lead*(s.rotorOmega-s.pinionOmega)*h,0,STARTING.travel);
      // The sleeve can also withdraw from partial engagement. Clamping it at
      // the first-contact gap traps the pinion after a held manual start.
      if(s.shift<STARTING.axialRestGap){s.mesh=false;s.overrun=false;}
      if(s.shift>=STARTING.travel-1e-10){
        const j=STARTING.engineInertia+STARTING.driveInertia*ratio*ratio,jr=STARTING.rotorInertia*ratio*ratio;
        s.omega=(j*s.omega+jr*s.rotorOmega/ratio)/(j+jr);s.rotorOmega=s.pinionOmega=ratio*s.omega;
      }
    }else if(s.mesh&&!s.overrun){
      const inertia=STARTING.engineInertia+(STARTING.rotorInertia+STARTING.driveInertia)*ratio*ratio;
      const acceleration=(engineTorque+motorTorque*ratio*.88)/inertia;
      // Negative spline reaction means the firing engine is now driving the
      // pinion faster than the armature can accelerate: inertia drive withdraws.
      if(s.combustion>.25&&motorTorque-STARTING.rotorInertia*ratio*acceleration<0)s.overrun=true;
      else {s.omega=Math.max(0,s.omega+acceleration*h);s.rotorOmega=s.pinionOmega=ratio*s.omega;}
    }
    if((!s.mesh||s.overrun)&&!advancedPartial){
      s.omega=Math.max(0,s.omega+engineTorque/STARTING.engineInertia*h);
      const spring=s.shift>0?(12+420*s.shift)*lead:0;
      const coupling=s.overrun?0:spring+.008*(s.rotorOmega-s.pinionOmega);
      s.rotorOmega=Math.max(0,s.rotorOmega+(motorTorque-coupling)/STARTING.rotorInertia*h);
      if(s.mesh)s.pinionOmega=ratio*s.omega;
      else s.pinionOmega=Math.max(0,s.pinionOmega+(coupling-.002*s.pinionOmega-.12)/STARTING.driveInertia*h);
      const dx=lead*(s.rotorOmega-s.pinionOmega)*h;
      s.shift=clamp(s.shift+dx,0,STARTING.travel);
      if(!s.starter&&!s.mesh&&s.rotorOmega<1&&s.pinionOmega<1)s.shift=Math.max(0,s.shift-.08*h);
      if(s.overrun&&s.shift<STARTING.axialRestGap){s.mesh=false;s.overrun=false;}
      if(!s.mesh&&!s.overrun&&s.shift>=STARTING.axialRestGap&&s.starter){
        // Inelastic engagement impulse; the friction drive absorbs the kinetic
        // mismatch. Ring count, pitch, clutch law and inertias need measurement.
        const jd=STARTING.driveInertia*ratio*ratio;
        s.omega=(STARTING.engineInertia*s.omega+jd*s.pinionOmega/ratio)/(STARTING.engineInertia+jd);
        s.pinionOmega=s.omega*ratio;s.mesh=true;
        const phi=Math.atan2(STARTING.starterPosition[2],STARTING.starterPosition[1]-.07);
        const phase=-((ratio+1)*phi+Math.PI-Math.PI/STARTING.pinionTeeth),pitch=TAU/STARTING.pinionTeeth;
        s.meshPhase=phase+Math.round((s.pinionAngle-ratio*s.angle-phase)/pitch)*pitch;
      }
    }
    s.angle+=s.omega*h;s.rotorAngle+=s.rotorOmega*h;
    s.pinionAngle=s.mesh?ratio*s.angle+s.meshPhase:s.pinionAngle+s.pinionOmega*h;
    s.soc=clamp(s.soc-(s.current+s.pumpCurrent+s.cooling.coilCurrent[0]+s.cooling.coilCurrent[1])*h/(STARTING.batteryAh*3600),0,1);
    if(s.preoil)s.preoilTime+=h;else s.preoilTime=0;
    if(s.starter){s.starterTime+=h;s.restTime=0;}else{s.restTime+=h;s.starterTime=0;}
    if(guided&&(s.starterTime>=STARTING.starterLimit||s.preoilTime>=STARTING.preoilLimit))s.guidedFailed=true;
    s.stage=s.combustion>.5&&rpm>450?'running':s.starter?'cranking':s.omega>1?'coasting':s.guidedFailed?'failed':s.preoil?'preoil':s.restTime<STARTING.retryInterval?'rest':'off';
    s.warning=guided&&c.running&&c.gear!==0&&rpm<450?'引导流程等待空挡':s.starter&&s.oilPressure<STARTING.oilThreshold?'未达到原车规定的预润滑压力':s.starterTime>5?'已超过原车规定的 5 秒操作时限':s.preoilTime>60?'已超过预润滑泵 1 分钟操作时限':s.guidedFailed?'引导流程已松开按钮；检查后再试':'';
  }
  s.request=c.running;return s;
}
export type StartingPose={p:[number,number,number];rx:number;sx?:number};
export function startingPose(s:StartingState):Record<string,StartingPose>{
  return {
    C5_rotor:{p:[0,0,0],rx:-s.rotorAngle},
    C5_drive:{p:[s.shift,0,0],rx:-s.rotorAngle+s.shift/lead},
    C5_pinion:{p:[s.shift,0,0],rx:-s.pinionAngle},
    C5_return_spring:{p:[.192,0,0],rx:0,sx:1-s.shift/.10},
    C5_FLYWHEEL_RING:{p:[.669,.07,0],rx:s.angle},
    MZN_rotor:{p:[0,0,0],rx:s.pumpAngle},
    MZN_driven:{p:[0,.034,0],rx:-s.pumpAngle+Math.PI/12},
  };
}
