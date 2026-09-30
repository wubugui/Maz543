// 543-1308586-A topology from the original parts catalog; 408-family envelope
// from MCB 2017. Fork dimensions, spline count, length and installation are fitted.
export const CARDAN = { capRadius: .014, crossSpan: .073, grooveSpan: .0425, pinRadius: .008,
    rollerRadius: .00125, rollerPitch: .00925, rollerCount: 22, rollerLength: .014,
    crossDistance: .230, maxExtension: .040, maxBend: 30, splineTeeth: 12, maleEnd: .170, femaleReach: .125 };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const d = Math.hypot(...a); return a.map(v => v / d); };
// Orthonormal, right-handed basis columns to a unit quaternion (glTF order).
function quaternion(x, y, z) {
    const m = [x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]], tr = m[0] + m[4] + m[8];
    let q;
    if (tr > 0) {
        const s = Math.sqrt(tr + 1) * 2;
        q = [(m[7] - m[5]) / s, (m[2] - m[6]) / s, (m[3] - m[1]) / s, s / 4];
    }
    else if (m[0] > m[4] && m[0] > m[8]) {
        const s = Math.sqrt(1 + m[0] - m[4] - m[8]) * 2;
        q = [s / 4, (m[1] + m[3]) / s, (m[2] + m[6]) / s, (m[7] - m[5]) / s];
    }
    else if (m[4] > m[8]) {
        const s = Math.sqrt(1 + m[4] - m[0] - m[8]) * 2;
        q = [(m[1] + m[3]) / s, s / 4, (m[5] + m[7]) / s, (m[2] - m[6]) / s];
    }
    else {
        const s = Math.sqrt(1 + m[8] - m[0] - m[4]) * 2;
        q = [(m[2] + m[6]) / s, (m[5] + m[7]) / s, s / 4, (m[3] - m[1]) / s];
    }
    return q;
}
const yRotation = (a) => [0, Math.sin(a / 2), 0, Math.cos(a / 2)];
export function cardanMechanism(angle, bendDegrees = 18, extensionMM = 15) {
    const beta = Math.max(0, Math.min(CARDAN.maxBend, bendDegrees)) * Math.PI / 180;
    const length = CARDAN.crossDistance + Math.max(0, Math.min(40, extensionMM)) / 1000;
    const u = [1, 0, 0], v = [Math.cos(beta), 0, Math.sin(beta)], a = [0, Math.cos(angle), Math.sin(angle)];
    // Both cross trunnions must remain perpendicular. The two central forks have
    // the same phase because the sliding spline admits translation, not rotation.
    const b = norm(cross(v, a)), a2 = norm(cross(b, u)), cx = norm(cross(a, b));
    const end = v.map(k => k * length);
    const inputTwist = Math.atan2(dot(a, cross(u, cx)), dot(u, cx));
    const middleTwist = Math.atan2(dot(b, cross(v, cx)), dot(v, cx));
    const outputAngle = Math.atan2(a2[2], a2[1]);
    const middleRatio = Math.cos(beta) / (Math.cos(angle) ** 2 + Math.cos(beta) ** 2 * Math.sin(angle) ** 2);
    return { u, v, a, b, a2, cx, end, length, inputTwist, middleTwist, outputAngle, middleRatio,
        splineOverlap: CARDAN.maleEnd - (length - CARDAN.femaleReach), splineEndGap: length - .044 - CARDAN.maleEnd };
}
export function cardanPose(angle, bendDegrees = 18, extensionMM = 15) {
    const m = cardanMechanism(angle, bendDegrees, extensionMM), poses = {};
    for (let end = 0; end < 2; end++) {
        const at = end ? m.end : [0, 0, 0];
        poses[`CJ_flange_${end}`] = { p: at, q: quaternion(m.u, end ? m.a2 : m.a, cross(m.u, end ? m.a2 : m.a)) };
        poses[`CJ_shaft_${end}`] = { p: at, q: quaternion(m.v, m.b, cross(m.v, m.b)) };
        poses[`CJ_cross_${end}`] = { p: at, q: quaternion(m.cx, m.a, m.b) };
        for (const kind of ['flange', 'shaft'])
            for (const side of [-1, 1]) {
                const twist = kind === 'flange' ? m.inputTwist : m.middleTwist;
                const R = CARDAN.rollerPitch, r = CARDAN.rollerRadius;
                poses[`CJ_needles_${end}_${kind}_${side}`] = { p: [0, 0, 0], q: yRotation(twist * (1 - r / R) / 2) };
                for (let j = 0; j < CARDAN.rollerCount; j++) {
                    const a = j * Math.PI * 2 / CARDAN.rollerCount;
                    // Relative to the orbiting carrier: both inner and outer rolling
                    // contacts have equal surface velocity at the fitted race radii.
                    const relativeSpin = -twist * (R * R - r * r) / (2 * R * r);
                    poses[`CJ_roller_${end}_${kind}_${side}_${j}`] = { p: [R * Math.cos(a), side * .0275, -R * Math.sin(a)], q: yRotation(relativeSpin) };
                }
            }
    }
    return poses;
}
