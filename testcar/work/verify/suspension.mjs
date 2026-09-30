/** MAZ-543A topology from the 1973/1977 manuals. SI units.
 * Hard points, bar sizes, masses and force coefficients are reconstruction
 * parameters, not measured MAZ production or acceptance data.
 */
export const SUSPENSION = {
    axles: [-3.08, -.88, 2.42, 4.62], track: 2.375, wheelY: .75,
    lower: [.60, .55], upper: [1.025, .61],
    lowerEnd: [.60, 1.065], upperEnd: [.997, 1.015],
    wheelOffset: [.15, .1225],
    damperTop: [1.33, .86], damperFraction: .76,
    barLength: 1.70, lowerDiameter: .049, upperDiameter: .045,
    shearModulus: 79e9, sprungMass: 17910, unsprungMass: 330,
    compressionDamping: 18000, reboundDamping: 26000,
    tireStiffness: 1.8e6, tireDamping: 1500,
    compressionStop: .175, droopStop: -.16, stopStiffness: 1.2e6,
    minGeometryTravel: -.23, maxGeometryTravel: .24,
    // Packaging hypotheses pending a variant-specific installation drawing.
    anchorDirection: [1, -1, 1, -1],
};
const P = SUSPENSION, dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const lowerLength = dist(P.lower, P.lowerEnd), upperLength = dist(P.upper, P.upperEnd), uprightLength = dist(P.lowerEnd, P.upperEnd);
const upperZero = Math.atan2(P.upperEnd[0] - P.upper[0], P.upperEnd[1] - P.upper[1]);
const uprightZero = Math.atan2(P.upperEnd[1] - P.lowerEnd[1], P.upperEnd[0] - P.lowerEnd[0]);
function rotate(p, a) { return [p[0] * Math.cos(a) - p[1] * Math.sin(a), p[0] * Math.sin(a) + p[1] * Math.cos(a)]; }
function atAngle(a) {
    const lower = [P.lower[0] + lowerLength * Math.sin(a), P.lower[1] + lowerLength * Math.cos(a)];
    // Circle intersection closes upper arm and rigid upright simultaneously.
    const d = dist(P.upper, lower), dy = (lower[0] - P.upper[0]) / d, dz = (lower[1] - P.upper[1]) / d;
    const along = (upperLength ** 2 - uprightLength ** 2 + d * d) / (2 * d), across = Math.sqrt(Math.max(0, upperLength ** 2 - along ** 2));
    const upper = [P.upper[0] + along * dy + across * dz, P.upper[1] + along * dz - across * dy];
    const tilt = Math.atan2(upper[1] - lower[1], upper[0] - lower[0]) - uprightZero;
    const off = rotate(P.wheelOffset, tilt), wheel = [lower[0] + off[0], lower[1] + off[1]];
    const damperBottom = [P.lower[0] + (lower[0] - P.lower[0]) * P.damperFraction, P.lower[1] + (lower[1] - P.lower[1]) * P.damperFraction];
    return { lower, upper, wheel, tilt, lowerAngle: a, upperAngle: Math.atan2(upper[0] - P.upper[0], upper[1] - P.upper[1]) - upperZero, damperBottom, damperLength: dist(damperBottom, P.damperTop) };
}
export function wheelGeometry(travel) {
    const q = Math.max(P.minGeometryTravel, Math.min(P.maxGeometryTravel, travel));
    let lo = -.65, hi = .7;
    for (let i = 0; i < 28; i++) {
        const a = (lo + hi) / 2;
        if (atAngle(a).wheel[0] - P.wheelY < q)
            lo = a;
        else
            hi = a;
    }
    return atAngle((lo + hi) / 2);
}
const G0 = wheelGeometry(0);
const barK = (d) => P.shearModulus * Math.PI * d ** 4 / (32 * P.barLength);
export const BAR_STIFFNESS = [barK(P.lowerDiameter), barK(P.upperDiameter)];
export function suspensionElastic(travel) {
    const g = wheelGeometry(travel), h = .00001, a = wheelGeometry(travel - h), b = wheelGeometry(travel + h);
    const lowerRate = (b.lowerAngle - a.lowerAngle) / (2 * h), upperRate = (b.upperAngle - a.upperAngle) / (2 * h), damperRate = (b.damperLength - a.damperLength) / (2 * h);
    // The geometric inverse has a finite numerical residual. Elastic deflection
    // is relative to that same reconstructed neutral pose, not absolute angles.
    const lowerDeflection = g.lowerAngle - G0.lowerAngle, upperDeflection = g.upperAngle - G0.upperAngle;
    return { force: BAR_STIFFNESS[0] * lowerDeflection * lowerRate + BAR_STIFFNESS[1] * upperDeflection * upperRate,
        energy: .5 * (BAR_STIFFNESS[0] * lowerDeflection ** 2 + BAR_STIFFNESS[1] * upperDeflection ** 2), damperRate };
}
// Precompute force law; the physics solver performs no iterative linkage solve.
const tableMin = -.22, tableStep = .001;
const elasticTable = Array.from({ length: 451 }, (_, i) => suspensionElastic(tableMin + i * tableStep));
function forceLaw(q) {
    const f = Math.max(0, Math.min(elasticTable.length - 1.000001, (q - tableMin) / tableStep)), i = Math.floor(f), w = f - i;
    return { force: elasticTable[i].force * (1 - w) + elasticTable[i + 1].force * w, damperRate: elasticTable[i].damperRate * (1 - w) + elasticTable[i + 1].damperRate * w };
}
export function initialSuspension() { return { time: 0, heave: 0, pitch: 0, roll: 0, heaveVelocity: 0, pitchVelocity: 0, rollVelocity: 0, wheel: Array(8).fill(0), velocity: Array(8).fill(0), travel: Array(8).fill(0), road: Array(8).fill(0), normal: Array(8).fill((P.sprungMass / 8 + P.unsprungMass) * 9.81), damperForce: Array(8).fill(0) }; }
export function roadAt(time, index, amplitude) { const phase = Math.floor(index / 2) * .85 + (index % 2) * 1.7, w = 2 * Math.PI * .62; return { height: amplitude * .105 * Math.sin(w * time + phase), velocity: amplitude * .105 * w * Math.cos(w * time + phase) }; }
export function advanceSuspension(old, dt, amplitude) {
    const s = { ...old, wheel: [...old.wheel], velocity: [...old.velocity], travel: [...old.travel], road: [...old.road], normal: [...old.normal], damperForce: [...old.damperForce] };
    const steps = Math.max(1, Math.ceil(dt * 480)), h = dt / steps, g = 9.81, preload = P.sprungMass * g / 8, staticNormal = preload + P.unsprungMass * g;
    const cx = P.axles.reduce((a, b) => a + b, 0) / 4, pitchInertia = P.sprungMass * 11.165 ** 2 / 12, rollInertia = P.sprungMass * (3.05 ** 2 + 1.65 ** 2) / 12;
    for (let step = 0; step < steps; step++) {
        // Equal static preloads balance sprung gravity and their moments about cx.
        // Accumulate deviations directly, retaining tiny actual perturbations
        // instead of repeatedly subtracting large nearly equal static forces.
        let total = 0, pitchTorque = 0, rollTorque = 0;
        for (let i = 0; i < 8; i++) {
            const x = P.axles[Math.floor(i / 2)] - cx, z = (i % 2 ? 1 : -1) * P.track / 2;
            const body = s.heave + s.pitch * x + s.roll * z, bv = s.heaveVelocity + s.pitchVelocity * x + s.rollVelocity * z;
            const q = s.wheel[i] - body, qv = s.velocity[i] - bv, law = forceLaw(q);
            const damping = (qv > 0 ? P.compressionDamping : P.reboundDamping) * law.damperRate ** 2 * qv;
            const stop = P.stopStiffness * (Math.max(0, q - P.compressionStop) + Math.min(0, q - P.droopStop));
            const springDelta = law.force + damping + stop;
            const road = roadAt(s.time, i, amplitude), normalDelta = Math.max(-staticNormal, P.tireStiffness * (road.height - s.wheel[i]) + P.tireDamping * (road.velocity - s.velocity[i])), normal = staticNormal + normalDelta;
            s.velocity[i] += (normalDelta - springDelta) / P.unsprungMass * h;
            s.wheel[i] += s.velocity[i] * h;
            total += springDelta;
            pitchTorque += springDelta * x;
            rollTorque += springDelta * z;
            s.travel[i] = q;
            s.road[i] = road.height;
            s.normal[i] = normal;
            s.damperForce[i] = damping;
        }
        s.heaveVelocity += total / P.sprungMass * h;
        s.pitchVelocity += pitchTorque / pitchInertia * h;
        s.rollVelocity += rollTorque / rollInertia * h;
        s.heave += s.heaveVelocity * h;
        s.pitch += s.pitchVelocity * h;
        s.roll += s.rollVelocity * h;
        s.time += h;
    }
    for (let i = 0; i < 8; i++) {
        const x = P.axles[Math.floor(i / 2)] - cx, z = (i % 2 ? 1 : -1) * P.track / 2;
        s.travel[i] = s.wheel[i] - s.heave - s.pitch * x - s.roll * z;
    }
    return s;
}
export function suspensionPose(travel) {
    const pose = {};
    for (let i = 0; i < 8; i++) {
        const x = P.axles[Math.floor(i / 2)], s = i % 2 ? 1 : -1, g = wheelGeometry(travel[i] ?? 0), name = `S543_${i}`;
        pose[name + '_lower'] = { p: [x, P.lower[0], s * P.lower[1]], rx: -s * g.lowerAngle };
        pose[name + '_upper'] = { p: [x, P.upper[0], s * P.upper[1]], rx: -s * g.upperAngle };
        pose[name + '_upright'] = { p: [x, g.lower[0], s * g.lower[1]], rx: s * g.tilt };
        const dy = P.damperTop[0] - g.damperBottom[0], dz = s * (P.damperTop[1] - g.damperBottom[1]), rx = Math.atan2(dz, dy);
        pose[name + '_damper_body'] = { p: [x - .15, g.damperBottom[0], s * g.damperBottom[1]], rx };
        pose[name + '_damper_rod'] = { p: [x - .15, P.damperTop[0], s * P.damperTop[1]], rx };
        pose[name + '_wheel'] = { p: [x, g.wheel[0], s * g.wheel[1]], rx: s * g.tilt };
        const shaftInner = [x, .84, s * .18], shaftOuter = [x, g.wheel[0], s * (g.wheel[1] - .18)];
        const shaftAngle = Math.atan2(shaftOuter[2] - shaftInner[2], shaftOuter[1] - shaftInner[1]);
        pose[name + '_shaft_inner'] = { p: shaftInner, rx: shaftAngle };
        pose[name + '_shaft_outer'] = { p: shaftOuter, rx: shaftAngle };
        // The bar end is driven by the sleeve; its opposite end is frame-fixed.
        pose[name + '_lower_spline'] = { p: [x, P.lower[0], s * P.lower[1]], rx: -s * g.lowerAngle };
        pose[name + '_upper_spline'] = { p: [x, P.upper[0], s * P.upper[1]], rx: -s * g.upperAngle };
    }
    return pose;
}
export const SUSPENSION_NEUTRAL = G0;
