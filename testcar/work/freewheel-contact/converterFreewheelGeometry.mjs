export const FREEWHEEL_COIL_SEGMENTS = 160, FREEWHEEL_COIL_SIDES = 12;
export function freewheelCoilPositions(f, cy, cz, length) {
    const rho = f.innerRadius + f.rollerRadius, dy = cy - rho, dz = cz - f.springBaseZ, distance = Math.hypot(dy, dz), ay = dy / distance, az = dz / distance;
    const turns = 2 * Math.PI * f.springTurns, reference = -f.springBaseZ - f.rollerRadius - f.springWireRadius;
    const radius = Math.sqrt(f.springRadius ** 2 + (reference ** 2 - length ** 2) / turns ** 2), wire = f.springWireRadius;
    const out = new Float32Array((FREEWHEEL_COIL_SEGMENTS + 1) * FREEWHEEL_COIL_SIDES * 3);
    let index = 0;
    for (let i = 0; i <= FREEWHEEL_COIL_SEGMENTS; i++) {
        const t = i / FREEWHEEL_COIL_SEGMENTS, a = turns * t, ca = Math.cos(a), sa = Math.sin(a);
        const rx = ca, ry = sa * az, rz = -sa * ay;
        let tx = -turns * radius * sa, ty = length * ay + turns * radius * ca * az, tz = length * az - turns * radius * ca * ay;
        const tm = Math.hypot(tx, ty, tz);
        tx /= tm;
        ty /= tm;
        tz /= tm;
        let nx = ty * rz - tz * ry, ny = tz * rx - tx * rz, nz = tx * ry - ty * rx;
        const nm = Math.hypot(nx, ny, nz);
        nx /= nm;
        ny /= nm;
        nz /= nm;
        const x = radius * rx, y = rho + t * length * ay + radius * ry, z = f.springBaseZ + t * length * az + radius * rz;
        for (let j = 0; j < FREEWHEEL_COIL_SIDES; j++) {
            const b = 2 * Math.PI * j / FREEWHEEL_COIL_SIDES, c = Math.cos(b), s = Math.sin(b);
            out[index++] = x + wire * (c * rx + s * nx);
            out[index++] = y + wire * (c * ry + s * ny);
            out[index++] = z + wire * (c * rz + s * nz);
        }
    }
    return out;
}
