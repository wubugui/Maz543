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
  const pose:Record<string,{rx:number;p?:[number,number,number]}>= {
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
  // Kinematic selection only. Hydraulic filling, piston force and slip remain open.
  for(const [name,g,sign] of [['first',1,-1],['second',2,1],['direct',3,1],['reverse',-1,1]] as const)
    pose[`TX_piston_${name}`]={rx:0,p:[gear===g?sign*.0018:0,0,0]};
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
