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
