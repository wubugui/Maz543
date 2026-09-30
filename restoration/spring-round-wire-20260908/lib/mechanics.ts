import {advanceSuspension,initialSuspension,type SuspensionState} from './suspension';
import {advanceStarting,initialStarting,type StartingState} from './starting';
// SI units. Reference reconstruction and simplified kinematics, not factory CAD.
export const SPECS = {
  length: 11.165, width: 3.05, cabinHeight: 2.67,
  axles: [-3.08, -.88, 2.42, 4.62], track: 2.375,
  tireRadius: .75, tireWidth: .61, mass: 20550,
  bore: .15, stroke: .18, bankAngle: Math.PI / 3,
  maxRPM: 2000, idleRPM: 600,
};
export type Controls = {
  latchButtons:boolean;startMode:'guided'|'manual';batteryOn:boolean;preoilHeld:boolean;starterHeld:boolean;fuelEnabled:boolean;
  startingView:'assembled'|'internals'|'stator';startingComponent:'all'|'starter'|'preoil';
  running: boolean; throttle: number; brake: number; steering: number;
  gear: number; terrain: number; slow: boolean; explode: number;
  mode: 'solid' | 'xray' | 'section'; focus: string; doors: number;
  engineView: 'assembled' | 'valvetrain' | 'internals' | 'camdrive' | 'timing' | 'waterpump';
  waterCutaway:boolean;
  fanLeft:boolean;fanRight:boolean;shutter:number;heaterLeft:boolean;heaterRight:boolean;ambient:number;coolingInternals:boolean;coolingView:'assembly'|'clutch'|'lower'|'upper'|'cardan';
  cardanBend:number;cardanExtension:number;
  engineBank:'L'|'R'|'both';
  enginePaused: boolean;
  suspensionWheel:number; suspensionInternals:boolean; suspensionPaused:boolean;
  doorTargets?: [number,number,number,number];
  lights: boolean; labels: boolean; wireframe: boolean;
};
export const INITIAL: Controls = {
  running: false, throttle: 0, brake: 0, steering: 0, gear: 0,
  latchButtons:false,startMode:'guided',batteryOn:false,preoilHeld:false,starterHeld:false,fuelEnabled:true,startingView:'assembled',startingComponent:'all',
  terrain: 0, slow: false, explode: 0, mode: 'solid', focus: '',
  doors: 0, lights: false, labels: false, wireframe: false,
  engineView: 'assembled', engineBank:'L', enginePaused: false,waterCutaway:true,
  fanLeft:true,fanRight:true,shutter:100,heaterLeft:false,heaterRight:false,ambient:25,coolingInternals:false,coolingView:'assembly',
  cardanBend:18,cardanExtension:15,
  suspensionWheel:-1,suspensionInternals:false,suspensionPaused:false,
};
export type Telemetry = { starting:StartingState; rpm: number; speed: number; distance: number; crank: number; wheel: number; time: number; doorOpenings:[number,number,number,number]; suspension:SuspensionState; viewScale?:{metres:number;pixels:number};renderStats?: {fps:number;drawCalls:number;triangles:number;gpu:string;gpuMs?:number} };
export const INITIAL_TELEMETRY: Telemetry = { starting:initialStarting(),rpm: 0, speed: 0, distance: 0, crank: 0, wheel: 0, time: 0, doorOpenings:[0,0,0,0],suspension:initialSuspension() };
export function steeringAngles(degrees: number) {
  const a = degrees * Math.PI / 180;
  if (Math.abs(a) < 1e-6) return [0, 0, 0, 0];
  const pivot = (SPECS.axles[2] + SPECS.axles[3]) / 2, radius = (pivot - SPECS.axles[0]) / Math.tan(a);
  return SPECS.axles.slice(0, 2).flatMap(x => [-1, 1].map(s => Math.atan((pivot - x) / (radius - s * SPECS.track / 2))));
}
export function pistonPosition(angle: number, rod = .32, crank = SPECS.stroke / 2) {
  return crank * Math.cos(angle) + Math.sqrt(rod * rod - (crank * Math.sin(angle)) ** 2);
}
export function advance(t: Telemetry, c: Controls, dt: number): Telemetry {
  const h = Math.max(0, Math.min(dt, .05));
  const starting=c.enginePaused?t.starting:advanceStarting(t.starting,c,h*(c.slow?.035:1));
  const rpm=starting.omega*60/(Math.PI*2);
  const ratio = [0, 3.2, 1.8, 1][Math.max(0, c.gear)] || 3.2;
  const targetSpeed = starting.combustion>.5 && c.gear !== 0 ? Math.sign(c.gear) * rpm / 60 / ratio / 10.5 * Math.PI * 2 * SPECS.tireRadius : 0;
  const drive = starting.combustion>.5 && c.gear !== 0 ? (targetSpeed - t.speed) * .24 * (.18 + c.throttle / 100) : 0;
  const resistance = Math.abs(t.speed) > .002 ? Math.sign(t.speed) * (.045 + c.brake / 100 * 3.8) : 0;
  let speed = t.speed + (drive - resistance) * h;
  if (Math.abs(t.speed)<.01 && c.brake/100*3.8 >= Math.abs(drive)) speed=0;
  if (Math.sign(speed) !== Math.sign(t.speed) && Math.abs(drive) < Math.abs(resistance)) speed = 0;
  if (Math.abs(speed) < .002) speed = 0;
  // Door joints move continuously toward manual inspection targets. Each cabin
  // door can be operated independently; these are not powered doors on the vehicle.
  const doorOpenings=t.doorOpenings.map((value,i)=>{
    const target=Math.max(0,Math.min(100,c.doorTargets?.[i]??c.doors));
    return value+Math.sign(target-value)*Math.min(Math.abs(target-value),h*65);
  }) as Telemetry['doorOpenings'];
  return { starting,rpm, speed, distance: t.distance + speed * h,
    crank: starting.angle % (Math.PI * 4),
    wheel: t.wheel + speed / SPECS.tireRadius * h, time: t.time + h, doorOpenings,
    suspension:c.suspensionPaused?t.suspension:advanceSuspension(t.suspension,h,c.terrain/100) };
}
