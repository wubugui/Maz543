const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
const cross = (ay, az, by, bz) => ay * bz - az * by;
function solve4(A, rhs) {
    const rows = A.map((r, i) => [...r, rhs[i]]);
    for (let i = 0; i < 4; i++) {
        let pivot = i;
        for (let j = i + 1; j < 4; j++)
            if (Math.abs(rows[j][i]) > Math.abs(rows[pivot][i]))
                pivot = j;
        if (Math.abs(rows[pivot][i]) < 1e-12)
            return null;
        [rows[i], rows[pivot]] = [rows[pivot], rows[i]];
        const d = rows[i][i];
        for (let k = i; k <= 4; k++)
            rows[i][k] /= d;
        for (let j = 0; j < 4; j++)
            if (j !== i) {
                const c = rows[j][i];
                for (let k = i; k <= 4; k++)
                    rows[j][k] -= c * rows[i][k];
            }
    }
    return rows.map(r => r[4]);
}
export function freewheelSpringRate(f) { return f.shearModulus * (2 * f.springWireRadius) ** 4 / (8 * (2 * f.springRadius) ** 3 * f.springTurns); }
export function freewheelSpringLength(distance, f) {
    const w = f.springWireRadius, r = f.rollerRadius, reference = -f.springBaseZ - r - w;
    const wireLength = Math.hypot(reference, 2 * Math.PI * f.springTurns * f.springRadius);
    let length = distance - r - w, derivative = 1;
    // The terminal wire skin, rather than its centre plane, touches the roller.
    // Keeping helix centreline length fixed sets the pitch/radius relationship.
    for (let i = 0; i < 5; i++) {
        const sine = length / wireLength, cosine = Math.sqrt(1 - sine * sine), radial = Math.sqrt(r * r - w * w * sine * sine);
        derivative = 1 - w * w * length / (wireLength * wireLength * radial) - w * length / (wireLength * wireLength * cosine);
        length -= (length + radial + w * cosine - distance) / derivative;
    }
    return { length, dLengthDdistance: 1 / derivative, wireLength };
}
function spring(q, v, f) {
    const [y, z, , a] = q, [vy, vz, , w] = v, co = Math.cos(a), si = Math.sin(a), rho = f.innerRadius + f.rollerRadius;
    const by = rho * co - f.springBaseZ * si, bz = rho * si + f.springBaseZ * co;
    const dy = y - by, dz = z - bz, length = Math.hypot(dy, dz), ny = dy / length, nz = dz / length;
    const geometry = freewheelSpringLength(length, f), coilLength = geometry.length;
    const compression = Math.max(0, f.springFreeLength - coilLength), k = freewheelSpringRate(f);
    const rate = ny * (vy + w * bz) + nz * (vz - w * by);
    const axialForce = Math.max(0, k * compression - f.springDamping * rate * geometry.dLengthDdistance);
    const force = axialForce * geometry.dLengthDdistance, fy = force * ny, fz = force * nz, N = f.rollerCount;
    return { generalized: [N * fy, N * fz, 0, -N * cross(by, bz, fy, fz)], force,
        energy: N * .5 * k * compression * compression, coilLength, axialForce };
}
export function initialFreewheel(f) {
    const q = [f.innerRadius + f.rollerRadius, 0, 0, 0], v = [0, 0, 0, 0], s = spring(q, v, f);
    return { q, v, impulse: [0, 0, 0, 0], time: 0, inputWork: 0, gaps: [0, 0], normalForce: [0, 0], frictionForce: [0, 0], springForce: s.force, springAxialForce: s.axialForce, springLength: s.coilLength, iterations: 0, residual: 0, kinetic: 0, springEnergy: s.energy };
}
export function stepFreewheel(old, torque, h, f) {
    if (h <= 0)
        return old;
    const N = f.rollerCount, r = f.rollerRadius, R0 = Math.hypot(old.q[0], old.q[1]), phi0 = Math.atan2(old.q[1], old.q[0]);
    const co = Math.cos(phi0), si = Math.sin(phi0), radial = co * old.v[0] + si * old.v[1], orbital = (-si * old.v[0] + co * old.v[1]) / R0;
    const polarQ = [R0, phi0, old.q[2], old.q[3]], polarV = [radial, orbital, old.v[2], old.v[3]];
    const inv = [1 / (N * f.rollerMass), 1 / (N * f.rollerMass * R0 * R0), 1 / (N * f.rollerInertia), 1 / f.outerInertia];
    const a = old.q[3], s = spring(old.q, old.v, f), force = [
        co * s.generalized[0] + si * s.generalized[1] + N * f.rollerMass * R0 * orbital * orbital,
        cross(old.q[0], old.q[1], s.generalized[0], s.generalized[1]) - 2 * N * f.rollerMass * R0 * radial * orbital,
        0, s.generalized[3] + torque
    ];
    // Polar radial/orbital coordinates retain steady circular motion without
    // applying a dissipative Cartesian redirection at every contact step.
    const freeVelocity = polarV.map((x, i) => x + h * inv[i] * force[i]);
    let v = [...freeVelocity], lambda = [0, 0, 0, 0], residual = Infinity, iterations = 0;
    // Resolve normals on the end-of-step geometry. A single old-geometry
    // linearization lets fast rotation penetrate the ramp despite a tiny linear
    // residual; this nonlinear loop enforces the actual circle/plane gaps.
    for (let nonlinear = 0; nonlinear < 24; nonlinear++) {
        const trial = polarQ.map((x, i) => x + h * v[i]);
        const [R, phi, , angle] = trial, delta = phi - angle - f.wedgeAngle, cd = Math.cos(delta), sd = Math.sin(delta);
        const gaps = [R - f.innerRadius - r, (f.innerRadius + r) * Math.cos(f.wedgeAngle) - R * cd];
        const J = [[1, 0, 0, 0], [-cd, R * sd, 0, -R * sd],
            [0, R, -r, 0], [sd, R * cd, r, -(R * cd + r)]];
        const target = gaps.map((g, i) => dot(J[i], v) - g / h);
        // Two contacts permit exhaustive open/stick/slip(+/-) mode enumeration.
        // Solve each mode directly instead of accepting a poorly converged shallow-
        // wedge Gauss-Seidel iteration. The angular velocity is never sign-clamped.
        const K = J.map(j => J.map(k => j.reduce((sum, x, i) => sum + x * inv[i] * k[i], 0))), free = J.map(j => dot(j, freeVelocity));
        let best = null;
        for (let m0 = 0; m0 < 4; m0++)
            for (let m1 = 0; m1 < 4; m1++) {
                iterations++;
                const modes = [m0, m1], A = Array.from({ length: 4 }, () => [0, 0, 0, 0]), rhs = [0, 0, 0, 0];
                for (let c = 0; c < 2; c++) {
                    const m = modes[c], t = c + 2;
                    if (m === 0) {
                        A[c][c] = 1;
                        A[t][t] = 1;
                    }
                    else {
                        A[c] = [...K[c]];
                        rhs[c] = target[c] - free[c];
                        if (m === 1) {
                            A[t] = [...K[t]];
                            rhs[t] = -free[t];
                        }
                        else {
                            A[t][t] = 1;
                            A[t][c] = (m === 2 ? 1 : -1) * f.friction;
                        }
                    }
                }
                const candidate = solve4(A, rhs);
                if (candidate === null)
                    continue;
                const speed = free.map((x, i) => x + K[i].reduce((sum, k, j) => sum + k * candidate[j], 0));
                let valid = true, error = 0;
                for (let c = 0; c < 2; c++) {
                    const m = modes[c], n = candidate[c], t = candidate[c + 2], vn = speed[c] - target[c], vt = speed[c + 2];
                    const e = Math.max(0, -n * Math.max(K[c][c], K[c + 2][c + 2]), m === 0 ? -vn : Math.abs(vn), m === 1 ? Math.abs(vt) : m === 2 ? -vt : m === 3 ? vt : 0, (Math.abs(t) - f.friction * Math.max(0, n)) * K[c + 2][c + 2]);
                    error = Math.max(error, e);
                    if (e > 1e-8)
                        valid = false;
                }
                if (!valid)
                    continue;
                const velocity = freeVelocity.map((x, i) => x + inv[i] * J.reduce((sum, j, k) => sum + j[i] * candidate[k], 0));
                const energy = velocity.reduce((sum, x, i) => sum + .5 * x * x / inv[i], 0);
                if (best === null || energy < best.energy)
                    best = { lambda: candidate, velocity, energy, residual: error };
            }
        if (best === null)
            throw new Error('No admissible two-contact Coulomb mode');
        const change = Math.max(...v.map((x, i) => Math.abs(x - best.velocity[i]) * (i === 0 ? 1 : i === 2 ? r : R) * h));
        lambda = best.lambda;
        residual = best.residual;
        v = best.velocity;
        if (change < 1e-11)
            break;
        if (nonlinear === 23)
            throw new Error('Nonlinear freewheel contact did not converge');
    }
    const next = polarQ.map((x, i) => x + h * v[i]), cn = Math.cos(next[1]), sn = Math.sin(next[1]);
    const q = [next[0] * cn, next[0] * sn, next[2], next[3]], worldV = [v[0] * cn - next[0] * v[1] * sn, v[0] * sn + next[0] * v[1] * cn, v[2], v[3]];
    const after = spring(q, worldV, f);
    return { q, v: worldV, impulse: lambda, time: old.time + h, inputWork: old.inputWork + torque * (q[3] - a),
        gaps: [Math.hypot(q[0], q[1]) - f.innerRadius - r,
            (f.innerRadius + r) * Math.cos(f.wedgeAngle) - Math.cos(q[3] + f.wedgeAngle) * q[0] - Math.sin(q[3] + f.wedgeAngle) * q[1]],
        normalForce: [lambda[0] / h / N, lambda[1] / h / N], frictionForce: [lambda[2] / h / N, lambda[3] / h / N],
        springForce: after.force, springAxialForce: after.axialForce, springLength: after.coilLength, iterations, residual, kinetic: .5 * N * f.rollerMass * (worldV[0] ** 2 + worldV[1] ** 2) + .5 * N * f.rollerInertia * v[2] ** 2 + .5 * f.outerInertia * v[3] ** 2, springEnergy: after.energy };
}
