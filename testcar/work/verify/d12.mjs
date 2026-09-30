import { createTimingLayout } from './d12-timing.mjs';
// D12 family architecture from the engine manual, figs. 12–18; transport
// configuration from MAZ-543 Technical Description (1977) and KMZ 525A photos.
// Bore and main-bank stroke are published values. Rod lengths, articulation
// coordinates, cylinder pitch and cam profiles are reconstruction parameters,
// not measured factory dimensions. Keep that distinction in the source register.
export const D12 = {
    bore: .15, crankRadius: .09, mainRod: .32, slaveRod: .242426207136857,
    earAlong: .03, earAcross: .072277122855636, pitch: .18, crankY: .07,
    bankAngle: Math.PI / 6, valveLift: .009, camBaseRadius: .024,
    camY: .6765, valveOffset: .032, springLength: .061,
    // MAZ-543 (1973), figures 7–9: counts and nominal events, not fitted geometry.
    camSpurTeeth: 22, camBevelTeeth: 24, camDriveTeeth: 12,
    camOuterSplines: 41, camInnerSplines: 10,
    intakeOpenDeg: 340, intakeCloseDeg: 588,
    exhaustOpenDeg: 132, exhaustCloseDeg: 380,
    fireOrder: ['L1', 'R6', 'L5', 'R2', 'L3', 'R4', 'L6', 'R1', 'L2', 'R5', 'L4', 'R3'],
};
export const D12_TIMING = createTimingLayout(D12.camY, D12.valveOffset, D12.bankAngle, D12.crankY);
// MAZ 1973 fig.28: six blades and two bearings. Dimensions and ball count fitted.
export const WATER_PUMP = { origin: [-.665, -.221, 0], rate: -1.5, ballRadius: .004, ballPitch: .0175, balls: 9, bearings: [.025, .060] };
const TAU = Math.PI * 2, CYCLE = TAU * 2;
export const wrapCycle = (a) => ((a % CYCLE) + CYCLE) % CYCLE;
export const cylinderX = (i) => (i - 2.5) * D12.pitch;
export const firingPhase = (bank, i) => D12.fireOrder.indexOf(`${bank}${i + 1}`) * Math.PI / 3;
export const crankPinPhase = (i) => -D12.bankAngle - firingPhase('L', i);
export function bankPoint(x, y, z, bank) {
    const a = bank === 'L' ? -D12.bankAngle : D12.bankAngle;
    return [x, D12.crankY + y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
}
export function rodPair(angle, i) {
    const theta = angle + crankPinPhase(i), py = D12.crankRadius * Math.cos(theta), pz = D12.crankRadius * Math.sin(theta);
    const c = Math.cos(D12.bankAngle), s = Math.sin(D12.bankAngle);
    const project = py * c - pz * s, cross = py * s + pz * c;
    const distance = project + Math.sqrt(D12.mainRod ** 2 - cross ** 2);
    const my = distance * c, mz = -distance * s;
    const vy = (my - py) / D12.mainRod, vz = (mz - pz) / D12.mainRod;
    const ey = py + D12.earAlong * vy - D12.earAcross * vz, ez = pz + D12.earAlong * vz + D12.earAcross * vy;
    const sr = ey * c + ez * s, sc = -ey * s + ez * c;
    const slaveDistance = sr + Math.sqrt(D12.slaveRod ** 2 - sc ** 2);
    const sy = slaveDistance * c, sz = slaveDistance * s, x = cylinderX(i);
    return { pin: [x, py + D12.crankY, pz],
        main: [x, my + D12.crankY, mz],
        ear: [x, ey + D12.crankY, ez],
        slave: [x, sy + D12.crankY, sz],
        mainAngle: Math.atan2(vz, vy), slaveAngle: Math.atan2(sz - ez, sy - ey), distance, slaveDistance };
}
// Nominal MAZ events: intake 20 BTDC / 48 ABDC; exhaust 48 BBDC / 20 ATDC.
// The manual permits ±3 degrees. The 9 mm peak and quartic lift curve
// remain reconstruction choices; lash, acceleration and valve float are not solved.
export function valveWindow(kind) {
    const open = kind === 'intake' ? D12.intakeOpenDeg : D12.exhaustOpenDeg;
    const close = kind === 'intake' ? D12.intakeCloseDeg : D12.exhaustCloseDeg;
    return { center: (open + close) * Math.PI / 360, half: (close - open) * Math.PI / 360 };
}
export function valveLift(angle, bank, i, kind) {
    const phase = wrapCycle(angle - firingPhase(bank, i));
    const { center, half } = valveWindow(kind);
    let delta = phase - center;
    delta = ((delta + 2 * Math.PI) % CYCLE + CYCLE) % CYCLE - 2 * Math.PI;
    // This C1 quartic retains a convex flat-follower envelope at the fitted base
    // radius. A cosine squared at the shorter documented duration would undercut.
    return Math.abs(delta) >= half ? 0 : D12.valveLift * (1 - (delta / half) ** 2) ** 2;
}
export function d12Pose(angle) {
    const pose = { D12_crankshaft: { p: [0, D12.crankY, 0], rx: angle }, D12_injection_cam: { p: [0, .59, 0], rx: angle * D12_TIMING.shafts.injection.rate } };
    for (const shaft of Object.values(D12_TIMING.shafts))
        if (!shaft.existing)
            pose[shaft.node] = { p: [0, 0, 0], rx: angle * shaft.rate };
    const waterAngle = angle * WATER_PUMP.rate;
    pose.D12_water_rotor = { p: [0, 0, 0], rx: waterAngle };
    const cageRatio = (1 - WATER_PUMP.ballRadius / WATER_PUMP.ballPitch) / 2;
    const spinRatio = -(WATER_PUMP.ballPitch ** 2 - WATER_PUMP.ballRadius ** 2) / (2 * WATER_PUMP.ballPitch * WATER_PUMP.ballRadius);
    WATER_PUMP.bearings.forEach((x, b) => {
        pose[`D12_water_cage_${b}`] = { p: [0, 0, 0], rx: waterAngle * cageRatio };
        for (let j = 0; j < WATER_PUMP.balls; j++) {
            const a = j * Math.PI * 2 / WATER_PUMP.balls;
            pose[`D12_water_ball_${b}_${j}`] = { p: [x, WATER_PUMP.ballPitch * Math.cos(a), WATER_PUMP.ballPitch * Math.sin(a)], rx: waterAngle * spinRatio };
        }
    });
    for (let i = 0; i < 6; i++) {
        const pair = rodPair(angle, i);
        pose[`D12_master_rod_${i + 1}`] = { p: pair.pin, rx: pair.mainAngle };
        pose[`D12_slave_rod_${i + 1}`] = { p: pair.ear, rx: pair.slaveAngle };
        for (const bank of ['L', 'R']) {
            const a = bank === 'L' ? -D12.bankAngle : D12.bankAngle;
            pose[`D12_piston_${bank}${i + 1}`] = { p: bank === 'L' ? pair.main : pair.slave, rx: a };
            for (const kind of ['intake', 'exhaust']) {
                const z = (kind === 'intake' ? 1 : -1) * (bank === 'L' ? 1 : -1) * D12.valveOffset;
                const lift = valveLift(angle, bank, i, kind);
                for (let j = 0; j < 2; j++) {
                    const name = `${bank}${i + 1}_${kind}_${j + 1}`, x = cylinderX(i) + (j === 0 ? -D12.valveOffset : D12.valveOffset);
                    pose[`D12_valve_${name}`] = { p: bankPoint(x, .525 - lift, z, bank), rx: a };
                    pose[`D12_spring_${name}`] = { p: bankPoint(x, .568, z, bank), rx: a, sy: 1 - lift / D12.springLength };
                }
            }
            // Central injection pump has one plunger for every cylinder.
            const k = D12.fireOrder.indexOf(`${bank}${i + 1}`), phase = wrapCycle(angle - firingPhase(bank, i));
            const lift = phase > 3.65 * Math.PI ? .006 * Math.sin((phase - 3.65 * Math.PI) / (.35 * Math.PI) * Math.PI) : 0;
            pose[`D12_pump_plunger_${bank}${i + 1}`] = { p: [-.275 + k * .05, .625 + lift, 0], rx: 0 };
        }
    }
    for (const bank of ['L', 'R'])
        for (const kind of ['intake', 'exhaust']) {
            const z = (kind === 'intake' ? 1 : -1) * (bank === 'L' ? 1 : -1) * D12.valveOffset;
            pose[`D12_cam_${bank}_${kind}`] = { p: bankPoint(0, D12.camY, z, bank), rx: angle * D12_TIMING.shafts[kind + '_' + bank].rate };
        }
    return pose;
}
