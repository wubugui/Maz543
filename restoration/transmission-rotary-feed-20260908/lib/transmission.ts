// MAZ-543A technical description (1977), printed pp.20–22.
// Ratios are input speed / output speed; reverse carries the direction sign.
// This is the engaged, straight-running kinematic chain, not a converter map,
// shifting-clutch transient, differential locking law or traction simulation.
export const TRANSMISSION = {
  stepUp: .831,
  forward: [3.2, 1.8, 1] as const,
  reverse: -1.6,
  transfer: { high: 1, low: 1.85 },
  finalDrive: 1.92,
  wheelReduction: 5.1,
} as const;
export type TransferRange = keyof typeof TRANSMISSION.transfer;
export const CLUTCH_PACKS={first:{gear:1,count:15,direction:-1,start:.212,inner:.144,outer:.179},
  second:{gear:2,count:11,direction:1,start:-.213,inner:.043,outer:.082},
  direct:{gear:3,count:9,direction:1,start:-.173,inner:.045,outer:.096},
  reverse:{gear:-1,count:15,direction:1,start:-.134,inner:.169,outer:.207}} as const;
export type ClutchName=keyof typeof CLUTCH_PACKS;
export const CLUTCH_CONTACT={plateThickness:.0018,plateGap:.0003,pistonGap:.0021,
  springLength:.018,springRadius:.003,springWire:.00065,springTurns:5};
export function clutchContactTravel(name:ClutchName){return CLUTCH_CONTACT.pistonGap+(CLUTCH_PACKS[name].count-1)*CLUTCH_CONTACT.plateGap;}
export function clutchPlateShift(name:ClutchName,index:number,travel:number){
  const pack=CLUTCH_PACKS[name],ordinal=pack.direction===1?index:pack.count-1-index;
  const shift=Math.min((pack.count-1-ordinal)*CLUTCH_CONTACT.plateGap,Math.max(0,travel-CLUTCH_CONTACT.pistonGap-ordinal*CLUTCH_CONTACT.plateGap));
  return pack.direction*shift;
}
export function transmissionSpringWeights(name:ClutchName,travel:number):[number,number]{
  const s=CLUTCH_CONTACT,max=clutchContactTravel(name),x=Math.max(0,Math.min(max,travel)),sweep=s.springTurns*2*Math.PI;
  const arc2=s.springLength**2+(s.springRadius*sweep)**2;
  const radius=Math.sqrt(arc2-(s.springLength-x)**2)/sweep,end=Math.sqrt(arc2-(s.springLength-max)**2)/sweep;
  return [x/max,(radius-s.springRadius)/(end-s.springRadius)];
}
// One three-planet tooth-count solution derived from all four published ratios.
// These are NOT transcribed factory tooth counts. Module and axial dimensions
// remain fitted to the manual section and the current provisional installation.
export const PLANETARY={sun41:60,sun21:48,ring40:132,ring18:156,long43:36,short20:54,module:.0025,
  longRadius:.12,shortRadius:.1275,
  planetOffset:Math.acos((.12**2+.1275**2-.1125**2)/(2*.12*.1275)),
  position:[-.36,1.05,0] as [number,number,number]};
export type PlanetaryState={inputAngle:number;carrierAngle:number};
export const initialPlanetary=():PlanetaryState=>({inputAngle:0,carrierAngle:0});
export function advancePlanetary(previous:PlanetaryState,engineOmega:number,roadSpeed:number,tireRadius:number,gear:number,range:TransferRange,dt:number):PlanetaryState{
  const speeds=transmissionSpeeds(engineOmega,roadSpeed,tireRadius,gear,range);
  return {inputAngle:previous.inputAngle+(speeds.turbine??0)*dt,carrierAngle:previous.carrierAngle+speeds.gearboxOutput*dt};
}
export function planetaryPose(inputAngle:number,carrierAngle:number,gear:number){
  const s=PLANETARY,d=inputAngle-carrierAngle,phi=s.planetOffset;
  const longPhase=Math.PI-Math.PI/s.long43;
  const pairDirection=Math.atan2(s.shortRadius*Math.sin(phi),s.shortRadius*Math.cos(phi)-s.longRadius);
  const shortPhase=(1+s.long43/s.short20)*pairDirection+Math.PI-Math.PI/s.short20-s.long43/s.short20*longPhase;
  const sunPhase=((s.sun21+s.short20)*phi+s.short20*Math.PI-Math.PI-s.short20*shortPhase)/s.sun21;
  const ringPhase=((s.ring18-s.short20)*phi+s.short20*shortPhase-Math.PI)/s.ring18;
  const pose:Record<string,{rx:number;p?:[number,number,number];springTravel?:number;springPack?:ClutchName}>= {
    TX_carrier:{rx:carrierAngle}, TX_sun41:{rx:inputAngle},
    TX_sun21:{rx:carrierAngle-s.sun41/s.sun21*d+sunPhase},
    TX_ring40:{rx:carrierAngle-s.sun41/s.ring40*d},
    TX_ring18:{rx:carrierAngle+s.sun41/s.ring18*d+ringPhase},
  };
  for(let j=0;j<3;j++){
    const a=j*Math.PI*2/3;
    pose[`TX_long43_${j}`]={rx:-(s.sun41/s.long43)*d+longPhase+(1+s.sun41/s.long43)*a};
    pose[`TX_short20_${j}`]={rx:s.sun41/s.short20*d+shortPhase+(1+s.sun21/s.short20)*a};
  }
  // Sequential unilateral plate contact. Hydraulic forces and shifting slip
  // are still open; an engaged selection requests the measured closed stack.
  for(const name of Object.keys(CLUTCH_PACKS) as ClutchName[]){
    const pack=CLUTCH_PACKS[name],travel=gear===pack.gear?clutchContactTravel(name):0;
    pose[`TX_piston_${name}`]={rx:0,p:[pack.direction*travel,0,0]};
    for(let j=0;j<pack.count;j++)pose[`TX_disc_slide_${name}_${j}`]={rx:0,p:[clutchPlateShift(name,j,travel),0,0]};
    const pistonX=pack.start+(pack.direction===1?-.005:.005),radius=pack.outer+.014;
    for(let j=0;j<8;j++){
      const a=j*Math.PI/4;
      pose[`TX_spring_mount_${name}_${j}`]={rx:0,p:[pistonX+pack.direction*(.003+travel),radius*Math.cos(a),radius*Math.sin(a)],springTravel:travel,springPack:name};
    }
  }
  return pose;
}
export function gearboxRatio(gear: number): number | null {
  if (gear === -1) return TRANSMISSION.reverse;
  if (Number.isInteger(gear) && gear >= 1 && gear <= 3) return TRANSMISSION.forward[gear - 1];
  return null;
}
export function totalDriveRatio(gear: number, range: TransferRange): number | null {
  const gearbox = gearboxRatio(gear);
  return gearbox === null ? null : TRANSMISSION.stepUp * gearbox *
    TRANSMISSION.transfer[range] * TRANSMISSION.finalDrive * TRANSMISSION.wheelReduction;
}
// Equal converter pump/turbine speed is a reference for the existing fitted
// speed controller. It is NOT a request to engage the converter lock-up clutch.
export function synchronousRoadSpeed(engineOmega: number, gear: number, range: TransferRange, tireRadius: number) {
  const ratio = totalDriveRatio(gear, range);
  return ratio === null ? null : engineOmega / ratio * tireRadius;
}
export function transmissionSpeeds(engineOmega: number, roadSpeed: number, tireRadius: number, gear: number, range: TransferRange) {
  const wheel = roadSpeed / tireRadius;
  const halfshaft = wheel * TRANSMISSION.wheelReduction;
  const propeller = halfshaft * TRANSMISSION.finalDrive;
  const gearboxOutput = propeller * TRANSMISSION.transfer[range];
  const ratio = gearboxRatio(gear);
  const turbine = ratio === null ? null : gearboxOutput * ratio;
  const pump = engineOmega / TRANSMISSION.stepUp;
  return { pump, turbine, gearboxOutput, propeller, halfshaft, wheel,
    slipOmega: turbine === null ? null : pump - turbine };
}
