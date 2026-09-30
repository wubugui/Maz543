// Reduced two-coordinate planetary dynamics. Published gearing is exact;
// inertias and the passive converter approximation remain fitted. In particular
// this does NOT yet reproduce the MAZ converter's single turbine and two reactors' torque map.
import { TRANSMISSION } from './transmission.mjs';
import { initialHydraulics, stepHydraulics, CLUTCH_NAMES } from './transmissionHydraulics.mjs';
export const TRANSMISSION_DYNAMIC_FIT = { inputInertia: 15, carrierInertia: 8, sun21Inertia: .7, ring40Inertia: 1.3, ring18Inertia: 3,
    converterSlipCoefficient: .08, rollingCoefficient: .012, brakeDeceleration: 3.8 };
export const CLUTCH_SLIP = { first: [-60 / 132, 1 + 60 / 132], second: [-60 / 48, 1 + 60 / 48],
    direct: [-60 / 48 - 60 / 156, 60 / 48 + 60 / 156], reverse: [60 / 156, 1 - 60 / 156] };
export function initialTransmissionDynamics() {
    return { inputOmega: 0, outputOmega: 0, inputAngle: 0, outputAngle: 0,
        hydraulics: initialHydraulics(), clutchTorque: { first: 0, second: 0, direct: 0, reverse: 0 }, clutchSlip: { first: 0, second: 0, direct: 0, reverse: 0 },
        clutchHeat: 0, converterHeat: 0, engineLoad: 0, converterTorque: 0, roadTorque: 0, range: 'high', constraintResidual: 0, constraintIterations: 0 };
}
export function outputReduction(range) { return TRANSMISSION.transfer[range] * TRANSMISSION.finalDrive * TRANSMISSION.wheelReduction; }
export function transmissionMass(mass, radius, range) {
    const f = TRANSMISSION_DYNAMIC_FIT;
    let aa = f.inputInertia, ac = 0, cc = f.carrierInertia + mass * radius * radius / outputReduction(range) ** 2;
    for (const [J, b] of [[f.sun21Inertia, CLUTCH_SLIP.second], [f.ring40Inertia, CLUTCH_SLIP.first], [f.ring18Inertia, CLUTCH_SLIP.reverse]]) {
        aa += J * b[0] * b[0];
        ac += J * b[0] * b[1];
        cc += J * b[1] * b[1];
    }
    return { aa, ac, cc };
}
export function stepTransmission(old, engineOmega, gear, range, brake, mass, radius, h) {
    if (h <= 0)
        return old;
    const f = TRANSMISSION_DYNAMIC_FIT, G = outputReduction(range), M = transmissionMass(mass, radius, range), det = M.aa * M.cc - M.ac * M.ac;
    const inv = (a, c) => [(M.cc * a - M.ac * c) / det, (M.aa * c - M.ac * a) / det];
    // Preserve wheel speed when changing the still-ideal transfer range. Shift
    // synchronization and its energy loss remain a separate unfinished mechanism.
    const beforeOutput = old.outputOmega * G / outputReduction(old.range), pump = engineOmega / TRANSMISSION.stepUp;
    const hydraulic = stepHydraulics(old.hydraulics, gear, pump, beforeOutput, h);
    const delta = pump - old.inputOmega;
    const converterTorque = f.converterSlipCoefficient * delta * Math.abs(delta);
    const rearPumpTorque = hydraulic.mainPressure * hydraulic.rearFlow / Math.max(1, beforeOutput);
    const ext = inv(converterTorque * h, -rearPumpTorque * h);
    let a = old.inputOmega + ext[0], c = beforeOutput + ext[1];
    const kinetic = (a, c) => (M.aa * a * a + 2 * M.ac * a * c + M.cc * c * c) / 2;
    const before = kinetic(a, c);
    const constraints = CLUTCH_NAMES.map(name => ({ name, b: CLUTCH_SLIP[name], cap: hydraulic.boosters[name].capacity * h, lambda: 0 }));
    constraints.push({ name: 'road', b: [0, 1], cap: mass * (9.80665 * f.rollingCoefficient + Math.max(0, brake) / 100 * f.brakeDeceleration) * radius / G * h, lambda: 0 });
    let roadHeat = 0, constraintResidual = 0, constraintIterations = 0;
    for (let pass = 0; pass < 48; pass++) {
        for (const row of constraints) {
            const [u, v] = row.b, d = inv(u, v), w = u * a + v * c, effective = u * d[0] + v * d[1];
            const next = Math.max(-row.cap, Math.min(row.cap, row.lambda - w / effective)), impulse = next - row.lambda;
            const startEnergy = kinetic(a, c);
            a += d[0] * impulse;
            c += d[1] * impulse;
            row.lambda = next;
            if (row.name === 'road')
                roadHeat += startEnergy - kinetic(a, c);
        }
        constraintIterations = pass + 1;
        constraintResidual = 0;
        // Projected complementarity residual in rad/s. Saturated sliding rows
        // may have slip; unsaturated static contacts must converge to zero slip.
        for (const row of constraints) {
            const [u, v] = row.b, d = inv(u, v), effective = u * d[0] + v * d[1], w = u * a + v * c;
            const projected = Math.max(-row.cap, Math.min(row.cap, row.lambda - w / effective));
            constraintResidual = Math.max(constraintResidual, Math.abs(projected - row.lambda) * effective);
        }
        if (constraintResidual < 1e-9)
            break;
    }
    const clutchTorque = {}, clutchSlip = {};
    for (const row of constraints)
        if (row.name !== 'road') {
            clutchTorque[row.name] = row.lambda / h;
            clutchSlip[row.name] = row.b[0] * a + row.b[1] * c;
        }
    const hydraulicPower = hydraulic.mainPressure * (hydraulic.frontFlow + hydraulic.rearFlow);
    // Pump/rear-shaft load separation is retained; unloading circulation losses
    // need pump maps. No arbitrary road-speed target drives these coordinates.
    const frontPower = hydraulicPower * hydraulic.frontFlow / Math.max(1e-12, hydraulic.frontFlow + hydraulic.rearFlow);
    return { inputOmega: a, outputOmega: c, inputAngle: old.inputAngle + a * h, outputAngle: old.outputAngle + c * h, hydraulics: hydraulic, clutchTorque, clutchSlip,
        clutchHeat: old.clutchHeat + Math.max(0, before - kinetic(a, c) - roadHeat), converterHeat: old.converterHeat + converterTorque * delta * h,
        engineLoad: converterTorque / TRANSMISSION.stepUp + frontPower / Math.max(1, engineOmega), converterTorque, roadTorque: constraints[4].lambda / h, range,
        constraintResidual, constraintIterations };
}
