"""Read-only neutral-pose wheel geometry; no rig changes or saved blend.

PCA extracts each existing tyre profile's symmetry axis. Sidewall rays are
restricted to horizontal axle axes, so their 520 mm radial datum is also at
wheel-axis height. These simultaneous static rays are NOT the manual's rolling,
loaded tyre measurement. No acceptance is inferred from the diagnostic.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/MAZ543A_Master.blend'
OUT = ROOT / 'outputs/cloud-wheel-alignment-20261001'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    expected = '0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3'
    assert sha(SOURCE) == expected
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for index in range(4):
        obj = bpy.data.objects[f'BL_Tyre_{index}_VI203_profile']
        spin = bpy.data.objects[f'wheels_pivot_{2 + 7 * index:03d}']
        ev = obj.evaluated_get(dg)
        mesh = ev.to_mesh()
        mesh.calc_loop_triangles()
        verts = [ev.matrix_world @ v.co for v in mesh.vertices]
        triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
        ev.to_mesh_clear()
        xyz = np.array([tuple(v) for v in verts], dtype=float)
        mean = xyz.mean(axis=0)
        values, vectors = np.linalg.eigh(np.cov(xyz - mean, rowvar=False))
        axis = Vector(vectors[:, 0])
        centre = spin.evaluated_get(dg).matrix_world.translation.copy()
        if axis.y * centre.y < 0:
            axis.negate()
        assert values[1] > values[0] * 1.5, (index, values.tolist())
        bvh = BVHTree.FromPolygons(verts, triangles, all_triangles=True)
        row = {'index': index, 'side': 'right' if centre.y > 0 else 'left',
               'tyre_object': obj.name, 'spin_object': spin.name,
               'centre_world_m': list(centre), 'outward_axis': list(axis),
               'pca_eigenvalues': values.tolist(),
               'profile_centroid_offset_m': float(np.linalg.norm(mean-np.array(centre))),
               'camber_magnitude_degrees': math.degrees(math.asin(abs(axis.z))),
               'axis_horizontal_gate': abs(axis.z) < 1e-6,
               'sidewall_points': {}}
        if row['axis_horizontal_gate']:
            forward = Vector((0, 0, 1)).cross(axis).normalized()
            if forward.x > 0:
                forward.negate()
            for name, sign in [('front', 1), ('rear', -1)]:
                datum = centre + forward * (.520 * sign)
                hit, normal, face, distance = bvh.ray_cast(datum-axis, axis, 2.0)
                assert hit is not None, (index, name)
                assert abs(hit.z-centre.z) < 2e-6
                assert (hit-centre).dot(axis) < 0, 'Must hit inboard sidewall first'
                row['sidewall_points'][name] = list(hit)
        rows.append(row)
    pairs = []
    for axle in range(2):
        right, left = rows[2*axle:2*axle+2]
        if not (right['axis_horizontal_gate'] and left['axis_horizontal_gate']):
            pairs.append({'axle': axle+1, 'status': 'HEIGHT_DATUM_UNRESOLVED'})
            continue
        distances = {key: (Vector(right['sidewall_points'][key])-Vector(left['sidewall_points'][key])).length
                     for key in ['front', 'rear']}
        pairs.append({'axle': axle+1, 'static_distances_m': distances,
                      'simultaneous_static_rear_minus_front_mm': 1000*(distances['rear']-distances['front']),
                      'status': 'STATIC_GEOMETRY_ONLY_NOT_ROLLING_LOADED_MEASUREMENT'})
    result = {'source_sha256': expected, 'source_sha256_after': sha(SOURCE),
              'saved_blend': False, 'object_count': len(bpy.data.objects),
              'wheels': rows, 'axles': pairs, 'whole_vehicle_acceptance': '16 OPEN',
              'limits': ['No applied tyre pressure, load, deformation or rolling protocol.',
                         'PCA assumes the retained rotational tyre profile; eigenvalues and centroid residual are exposed.',
                         'No steering linkage or suspension assembly fit is validated.',
                         'No production geometry or control was modified.']}
    assert result['source_sha256_after'] == expected
    OUT.mkdir(exist_ok=True)
    (OUT/'native-neutral-geometry.json').write_text(json.dumps(result, indent=2)+'\n')
    print('WHEEL_ALIGNMENT_DIAGNOSTIC', json.dumps({'camber_degrees':[r['camber_magnitude_degrees'] for r in rows], 'axles':pairs}))

if __name__ == '__main__':
    main()
