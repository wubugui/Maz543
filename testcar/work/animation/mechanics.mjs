// SI units. Reference reconstruction and simplified kinematics, not factory CAD.
export const SPECS = {
    length: 11.165, width: 3.05, cabinHeight: 2.67,
    axles: [-3.08, -.88, 2.42, 4.62], track: 2.375,
    tireRadius: .75, tireWidth: .61, mass: 20550,
    bore: .15, stroke: .18, bankAngle: Math.PI / 3,
    maxRPM: 2000, idleRPM: 600,
};
export const INITIAL = {
    running: false, throttle: 25, brake: 0, steering: 0, gear: 0,
    terrain: 0, slow: true, explode: 0, mode: 'solid', focus: '',
    doors: 0, lights: false, labels: false, wireframe: false,
};
export const INITIAL_TELEMETRY = { rpm: 0, speed: 0, distance: 0, crank: 0, wheel: 0, time: 0 };
export function steeringAngles(degrees) {
    const a = degrees * Math.PI / 180;
    if (Math.abs(a) < 1e-6)
        return [0, 0, 0, 0];
    const pivot = (SPECS.axles[2] + SPECS.axles[3]) / 2, radius = (pivot - SPECS.axles[0]) / Math.tan(a);
    return SPECS.axles.slice(0, 2).flatMap(x => [-1, 1].map(s => Math.atan((pivot - x) / (radius - s * SPECS.track / 2))));
}
export function pistonPosition(angle, rod = .32, crank = SPECS.stroke / 2) {
    return crank * Math.cos(angle) + Math.sqrt(rod * rod - (crank * Math.sin(angle)) ** 2);
}
export function advance(t, c, dt) {
    const h = Math.max(0, Math.min(dt, .05));
    const targetRPM = c.running ? SPECS.idleRPM + c.throttle / 100 * (SPECS.maxRPM - SPECS.idleRPM) : 0;
    const rpm = t.rpm + (targetRPM - t.rpm) * (1 - Math.exp(-h * 3));
    const ratio = [0, 3.2, 1.8, 1][Math.max(0, c.gear)] || 3.2;
    const targetSpeed = c.running && c.gear !== 0 ? Math.sign(c.gear) * rpm / 60 / ratio / 10.5 * Math.PI * 2 * SPECS.tireRadius : 0;
    const drive = c.running && c.gear !== 0 ? (targetSpeed - t.speed) * .24 * (.18 + c.throttle / 100) : 0;
    const resistance = Math.abs(t.speed) > .002 ? Math.sign(t.speed) * (.045 + c.brake / 100 * 3.8) : 0;
    let speed = t.speed + (drive - resistance) * h;
    if (Math.abs(t.speed) < .01 && c.brake / 100 * 3.8 >= Math.abs(drive))
        speed = 0;
    if (Math.sign(speed) !== Math.sign(t.speed) && Math.abs(drive) < Math.abs(resistance))
        speed = 0;
    if (Math.abs(speed) < .002)
        speed = 0;
    const displayTime = h * (c.slow ? .035 : 1);
    return { rpm, speed, distance: t.distance + speed * h,
        crank: (t.crank + rpm / 60 * Math.PI * 2 * displayTime) % (Math.PI * 4),
        wheel: t.wheel + speed / SPECS.tireRadius * h, time: t.time + h };
}
