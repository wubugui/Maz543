// MAZ 1973 figs.27–31 / 1977 pp.73–80: circuit topology and two 12-blade fans.
// All dimensions, hydraulic resistance, heat capacities, curves and drive ratios
// below are fitted reconstruction parameters, NOT a measured MAZ cooling map.
const releaseSpringRate=79e9*.0014**4/(8*.049**3*5);
export const COOLING={enginePosition:[-4.05,1.32,0] as [number,number,number],fanPosition:[-5.02,1.56,.31] as [number,number,number],fanRadius:.292,fanRatio:1,fanInertia:.13,fanDrag:.00035,
  lowerOrigin:[-4.78,1.39,0] as [number,number,number],lowerTeeth:[32,20],lowerModule:.0038,
  upperApex:.18,upperTeeth:[20,32],
  upperBearings:[{shaft:'output',x:.1,bore:.0175,outer:.036,width:.017,pitch:.02675,ball:.0055},{shaft:'output',x:-.073,bore:.01,outer:.026,width:.015,pitch:.018,ball:.0045},
    ...[.088,.127].map(x=>({shaft:'input',x,bore:.0175,outer:.036,width:.017,pitch:.02675,ball:.0055}))],
  lowerBearings:[{shaft:'input',x:.093,bore:.025,outer:.055,width:.027,pitch:.04,ball:.0095},{shaft:'input',x:.146,bore:.025,outer:.055,width:.027,pitch:.04,ball:.0095},
    ...[0,1].flatMap(i=>[.090,.137].map(x=>({shaft:`output_${i}`,x,bore:.0175,outer:.04,width:.021,pitch:.02875,ball:.0065})))],
  pumpRatio:1.5,pumpRadius:.083,pumpHeadCoefficient:.22,pumpCurve:1.6e9,pumpEfficiency:.64,
  bankResistance:8e9,radiatorResistance:1.1e9,returnResistance:.2e9,heaterResistance:1.2e11,compressorResistance:2e11,
  coilResistance:8,coilInductance:.35,magnetCoefficient:450,clutchSpringForce:releaseSpringRate*.0045,clutchFriction:.32,clutchRadius:.075,clutchSlipStiffness:80,
  // Existing native faces: friction contact after 1.5 mm travel; magnetic
  // clearance decreases from 2.1 to 0.6 mm. Only the manual's engaged gap range
  // (0.1-1.0 mm) is source specified. Mass, force law and spring/damping fitted.
  clutchTravel:.0015,magneticGapReleased:.0021,axialMass:6,axialSpringRate:releaseSpringRate,axialDamping:20,
  releaseSpringLength:.010,releaseSpringRadius:.0245,releaseSpringWire:.0007,releaseSpringTurns:5,
  // Return, left block/head/manifold, right block/head/manifold, hot header,
  // three radiator passes, left/right heaters, compressor.
  masses:[8,12,7,5,12,7,5,4,10,10,10,3,3,4],cp:4180,metalCapacity:225000,
  names:['回水','左缸套','左缸盖','左排气夹套','右缸套','右缸盖','右排气夹套','热水总管','散热器一程','散热器二程','散热器三程','左舱暖风','右舱暖风','空压机'],
};
export type CoolingInputs={fanLeft?:boolean;fanRight?:boolean;shutter?:number;heaterLeft?:boolean;heaterRight?:boolean;ambient?:number};
export type CoolingState={temperature:number[];metal:number[];fanOmega:number[];fanAngle:number[];coilCurrent:number[];clutchPull:number[];clutchTorque:number[];
  axialPosition:number[];axialVelocity:number[];magnetForce:number[];clutchNormal:number[];clutchAirGap:number[];clutchSlipPower:number[];
  flow:number;bankFlow:number;radFlow:number;heaterFlow:number[];compressorFlow:number;pumpPressure:number;pumpPower:number;loadTorque:number;
  radiatorPower:number;heaterPower:number;heatInput:number;energyResidual:number;time:number};
export function initialCooling():CoolingState{return {temperature:COOLING.masses.map(()=>70),metal:[75,75],fanOmega:[0,0],fanAngle:[0,0],coilCurrent:[0,0],clutchPull:[0,0],clutchTorque:[0,0],axialPosition:[0,0],axialVelocity:[0,0],magnetForce:[0,0],clutchNormal:[0,0],clutchAirGap:[COOLING.magneticGapReleased,COOLING.magneticGapReleased],clutchSlipPower:[0,0],flow:0,bankFlow:0,radFlow:0,heaterFlow:[0,0],compressorFlow:0,pumpPressure:0,pumpPower:0,loadTorque:0,radiatorPower:0,heaterPower:0,heatInput:0,energyResidual:0,time:0};}
export function copyCooling(s:CoolingState):CoolingState{return {...s,temperature:[...s.temperature],metal:[...s.metal],fanOmega:[...s.fanOmega],fanAngle:[...s.fanAngle],coilCurrent:[...s.coilCurrent],clutchPull:[...s.clutchPull],clutchTorque:[...s.clutchTorque],axialPosition:[...s.axialPosition],axialVelocity:[...s.axialVelocity],magnetForce:[...s.magnetForce],clutchNormal:[...s.clutchNormal],clutchAirGap:[...s.clutchAirGap],clutchSlipPower:[...s.clutchSlipPower],heaterFlow:[...s.heaterFlow]};}
const clamp=(v:number,a:number,b:number)=>Math.max(a,Math.min(b,v));
export function coolingEnergy(s:CoolingState){return s.temperature.reduce((sum,t,i)=>sum+t*COOLING.masses[i]*COOLING.cp,0)+COOLING.metalCapacity*(s.metal[0]+s.metal[1]);}
// Called at the shared starting integrator's 1200 Hz step. Quasi-steady hydraulic
// network, dynamic fan/clutch and conservative lumped thermal transport.
export function stepCooling(s:CoolingState,c:CoolingInputs,omega:number,voltage:number,combustionPower:number,h:number):number{
  const ambient=c.ambient??25,shaft=omega*COOLING.fanRatio;
  let fanReaction=0;
  for(let i=0;i<2;i++){
    const enabled=i===0?(c.fanLeft??true):(c.fanRight??true),supply=enabled?voltage:0;
    s.coilCurrent[i]+=(supply-COOLING.coilResistance*s.coilCurrent[i])/COOLING.coilInductance*h;
    const closedGap=COOLING.magneticGapReleased-COOLING.clutchTravel;
    const forceAt=(x:number)=>COOLING.magnetCoefficient*s.coilCurrent[i]**2*(closedGap/(COOLING.magneticGapReleased-x))**2;
    let x=s.axialPosition[i],v=s.axialVelocity[i];
    const force=forceAt(x)-COOLING.clutchSpringForce-COOLING.axialSpringRate*x-COOLING.axialDamping*v;
    // Semi-implicit motion with unilateral, inelastic travel stops. Magnetic
    // attraction alone does not transmit dry friction across an open air gap.
    v+=force/COOLING.axialMass*h;x+=v*h;
    if(x<=0){x=0;v=Math.max(0,v);}
    if(x>=COOLING.clutchTravel){x=COOLING.clutchTravel;v=Math.min(0,v);}
    s.axialPosition[i]=x;s.axialVelocity[i]=v;s.clutchAirGap[i]=COOLING.magneticGapReleased-x;
    s.magnetForce[i]=forceAt(x);
    const normal=x>=COOLING.clutchTravel?Math.max(0,s.magnetForce[i]-COOLING.clutchSpringForce-COOLING.axialSpringRate*x):0;
    const capacity=COOLING.clutchFriction*normal*COOLING.clutchRadius,slip=shaft-s.fanOmega[i];
    const frictionTorque=clamp(slip*COOLING.clutchSlipStiffness,-capacity,capacity),torque=frictionTorque+.002*slip;
    s.clutchNormal[i]=normal;s.clutchSlipPower[i]=frictionTorque*slip;
    s.clutchPull[i]=x/COOLING.clutchTravel;s.clutchTorque[i]=torque;
    s.fanOmega[i]=Math.max(0,s.fanOmega[i]+(torque-COOLING.fanDrag*s.fanOmega[i]**2)/COOLING.fanInertia*h);
    s.fanAngle[i]+=s.fanOmega[i]*h;fanReaction+=torque*COOLING.fanRatio;
  }
  const conductance=[1/Math.sqrt(COOLING.radiatorResistance),c.heaterLeft?1/Math.sqrt(COOLING.heaterResistance):0,c.heaterRight?1/Math.sqrt(COOLING.heaterResistance):0,1/Math.sqrt(COOLING.compressorResistance)];
  const sum=conductance.reduce((a,b)=>a+b,0),parallel=1/(sum*sum),bank=COOLING.bankResistance/4;
  const pumpOmega=omega*COOLING.pumpRatio,head=1000*COOLING.pumpHeadCoefficient*(pumpOmega*COOLING.pumpRadius)**2;
  s.flow=Math.sqrt(head/(COOLING.pumpCurve+bank+parallel+COOLING.returnResistance));s.bankFlow=s.flow/2;
  s.radFlow=s.flow*conductance[0]/sum;s.heaterFlow=[s.flow*conductance[1]/sum,s.flow*conductance[2]/sum];s.compressorFlow=s.flow*conductance[3]/sum;
  s.pumpPressure=head-COOLING.pumpCurve*s.flow*s.flow;
  s.pumpPower=s.pumpPressure*s.flow/COOLING.pumpEfficiency;
  const pumpReaction=omega>1e-8?s.pumpPower/omega:0;
  s.loadTorque=fanReaction+pumpReaction;
  const before=coolingEnergy(s),dT=Array(14).fill(0) as number[],dm=[0,0];
  function transfer(from:number,to:number,flow:number){const power=1000*flow*COOLING.cp*s.temperature[from];dT[from]-=power;dT[to]+=power;}
  for(const first of [1,4]){transfer(0,first,s.bankFlow);transfer(first,first+1,s.bankFlow);transfer(first+1,first+2,s.bankFlow);transfer(first+2,7,s.bankFlow);}
  for(const [to,flow] of [[8,s.radFlow],[11,s.heaterFlow[0]],[12,s.heaterFlow[1]],[13,s.compressorFlow]])transfer(7,to,flow);
  transfer(8,9,s.radFlow);transfer(9,10,s.radFlow);transfer(10,0,s.radFlow);
  transfer(11,0,s.heaterFlow[0]);transfer(12,0,s.heaterFlow[1]);transfer(13,0,s.compressorFlow);
  s.heatInput=Math.max(0,combustionPower)*.8;let metalAir=0;
  for(let b=0;b<2;b++){
    dm[b]+=s.heatInput/2;
    for(let j=0;j<3;j++){const node=1+b*3+j,power=[500,800,700][j]*(s.metal[b]-s.temperature[node]);dm[b]-=power;dT[node]+=power;}
    const loss=25*(s.metal[b]-ambient);dm[b]-=loss;metalAir+=loss;
  }
  // All quasi-steady pump work eventually dissipates into the closed water loop.
  dT[0]+=s.pumpPower;
  const airFactor=clamp((c.shutter??100)/100,0,1),forced=(s.fanOmega[0]+s.fanOmega[1])/(2*2000*Math.PI/30);
  const ua=35+1600*Math.pow(Math.max(0,forced),.75)*(.015+.985*airFactor**2);
  s.radiatorPower=0;s.heaterPower=0;
  for(const i of [8,9,10]){const power=ua/3*(s.temperature[i]-ambient);dT[i]-=power;s.radiatorPower+=power;}
  for(const [i,on] of [[11,c.heaterLeft],[12,c.heaterRight]] as const){const power=(on?90:4)*(s.temperature[i]-ambient);dT[i]-=power;s.heaterPower+=power;}
  for(let i=0;i<14;i++)s.temperature[i]+=dT[i]/(COOLING.masses[i]*COOLING.cp)*h;
  for(let i=0;i<2;i++)s.metal[i]+=dm[i]/COOLING.metalCapacity*h;
  s.energyResidual+=coolingEnergy(s)-before-(s.heatInput+s.pumpPower-s.radiatorPower-s.heaterPower-metalAir)*h;s.time+=h;
  return s.loadTorque;
}
export function coolingPose(s:CoolingState,crank:number,shutter=100){
  const p:Record<string,{p:[number,number,number];rx:number;ry?:number;sx?:number}>={};
  for(let i=0;i<2;i++){
    const travel=s.axialPosition[i];
    p[`COOL_fan_${i}`]={p:[-travel,0,0],rx:-s.fanAngle[i]};
    p[`COOL_armature_${i}`]={p:[0,0,0],rx:-crank*COOLING.fanRatio};
    p[`COOL_spring_${i}`]={p:[-.0155,0,0],rx:-s.fanAngle[i],sx:(COOLING.releaseSpringLength-travel)/COOLING.releaseSpringLength};
    for(let j=0;j<2;j++)p[`COOL_brush_joint_${i}_${j}`]={p:[-travel,0,0],rx:0};
    const inner=-crank*COOLING.fanRatio,outer=-s.fanAngle[i],cage=(.0196*inner+.0244*outer)/.044;
    const roller=(.0244*outer-.0196*inner)/.0048;
    for(let k=0;k<2;k++)for(let j=0;j<24;j++){
      const a=cage+j*Math.PI/12;
      p[`COOL_needle_joint_${i}_${k}_${j}`]={p:[.007+k*.020-travel,.022*Math.cos(a),.022*Math.sin(a)],rx:roller};
    }
  }
  const shutterAngle=clamp(shutter/100,0,1)*Math.PI/2;
  for(let i=0;i<12;i++)p[`COOL_shutter_${i}`]={p:[-5.40,1.56,-.585+i*.1064],rx:0,ry:shutterAngle};
  p.COOL_shutter_link_joint={p:[-5.40+.029*Math.cos(shutterAngle),1.211,-.029*Math.sin(shutterAngle)],rx:0};
  p.COOL_lower_input={p:[0,0,0],rx:-crank};
  for(let i=0;i<2;i++)p[`COOL_lower_output_${i}`]={p:[0,0,0],rx:crank*COOLING.lowerTeeth[0]/COOLING.lowerTeeth[1]};
  for(let b=0;b<COOLING.lowerBearings.length;b++){
    const bearing=COOLING.lowerBearings[b],a=bearing.shaft==='input'?-crank:crank*COOLING.lowerTeeth[0]/COOLING.lowerTeeth[1],R=bearing.pitch,r=bearing.ball;
    p[`COOL_lower_cage_${b}`]={p:[0,0,0],rx:a*(1-r/R)/2};
    for(let j=0;j<8;j++){const angle=j*Math.PI/4;p[`COOL_lower_ball_${b}_${j}`]={p:[bearing.x,R*Math.cos(angle),R*Math.sin(angle)],rx:-a*(R*R-r*r)/(2*R*r)};}
  }
  p.COOL_lower_pump_drive={p:[-.198,0,0],rx:crank};
  p.COOL_lower_pump_driven={p:[-.198,-.04,0],rx:Math.PI-Math.PI/12-crank};
  for(let i=0;i<2;i++){
    // Upper output cone points toward the fan (-X). The sign follows the
    // authored bevel axes; Cardan installation / angular velocity is pending.
    p[`COOL_upper_output_${i}`]={p:[0,0,0],rx:crank};
    p[`COOL_upper_input_${i}`]={p:[0,0,0],rx:-crank*COOLING.lowerTeeth[0]/COOLING.lowerTeeth[1]};
    for(let b=0;b<COOLING.upperBearings.length;b++){
      const s=COOLING.upperBearings[b],a=s.shaft==='output'?crank:-crank*1.6,R=s.pitch,r=s.ball;
      p[`COOL_upper_cage_${i}_${b}`]={p:[0,0,0],rx:a*(1-r/R)/2};
      for(let j=0;j<8;j++){const angle=j*Math.PI/4;p[`COOL_upper_ball_${i}_${b}_${j}`]={p:[s.x,R*Math.cos(angle),R*Math.sin(angle)],rx:-a*(R*R-r*r)/(2*R*r)};}
    }
  }
  return p;
}
