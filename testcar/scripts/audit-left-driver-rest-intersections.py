"""Read-only rest-pose surface diagnostic for the relocated controls.

Triangle intersections identify failures; absence is not a volume-clearance proof.
The comparison pose puts the same retained controls back in their old right-cab
positions in memory. Neither pose is saved into the source model.
"""
import bpy, hashlib, json, itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/cloud-left-driver-side-20261001/MAZ543A_Master.blend'
OUT = ROOT / 'outputs/cloud-left-driver-rest-audit-20261001'
OUT.mkdir(exist_ok=True)
assert not (OUT / 'rest-intersections.json').exists(), 'Keep prior diagnostic outputs'
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
expected = json.loads((SOURCE.parent / 'build-report.json').read_text())[0]
assert source_hash == expected['candidate_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
moving = [bpy.data.objects[x['name']] for x in expected['separated_parts']]
wheel = bpy.data.objects['cab_pivot_004']
moving += [o for o in wheel.children_recursive if o.type == 'MESH']
names = {o.name for o in moving}
assert len(names) == 10
roots = [wheel] + [o for o in moving if o.name.startswith('BL_Left_driver_')]
original_matrices = {o.name: o.matrix_world.copy() for o in roots}

def bounds(points):
    return [[min(v[i] for v in points), max(v[i] for v in points)] for i in range(3)]

def intersect_bounds(a, b):
    return all(a[i][0] <= b[i][1] and b[i][0] <= a[i][1] for i in range(3))

def mesh_bvh(obj, dg):
    evaluated = obj.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    assert vertices and triangles
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=0.0), bounds(vertices), len(triangles)

results = []
for pose, shift in [('candidate_left_rest', 0.0), ('old_right_position_comparison', 2.05)]:
    for o in roots:
        matrix = original_matrices[o.name].copy()
        matrix.translation.y += shift
        o.matrix_world = matrix
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    moving_meshes = {o.name: mesh_bvh(o, dg) for o in moving}
    candidates = []
    for o in bpy.context.scene.objects:
        if o.name in names or o.type != 'MESH' or o.hide_render:
            continue
        e = o.evaluated_get(dg)
        box = bounds([e.matrix_world @ Vector(p) for p in e.bound_box])
        near = [n for n, (_, b, _) in moving_meshes.items() if intersect_bounds(b, box)]
        if near:
            candidates.append((o, near))
    overlaps = []
    checked = 0
    for o, near in candidates:
        fixed, _, count = mesh_bvh(o, dg)
        for n in near:
            checked += 1
            hits = moving_meshes[n][0].overlap(fixed)
            if hits:
                overlaps.append({'moving': n, 'fixed': o.name, 'triangle_pairs': len(hits), 'first_triangle_pairs': hits[:10], 'fixed_triangles': count})
    results.append({'pose': pose, 'moving_meshes': len(moving_meshes), 'fixed_mesh_candidates': len(candidates), 'narrow_phase_pairs': checked, 'surface_intersections': overlaps})
    print('DRIVER_REST_DIAGNOSTIC', pose, checked, len(overlaps), flush=True)
for o in roots:
    o.matrix_world = original_matrices[o.name]
bpy.context.view_layer.update()
assert all(o.matrix_world == original_matrices[o.name] for o in roots)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
left = {(r['moving'], r['fixed']) for r in results[0]['surface_intersections']}
right = {(r['moving'], r['fixed']) for r in results[1]['surface_intersections']}
report = {'source_sha256': source_hash, 'source_file_unchanged': True,
          'scope': 'Saved native Master rest pose; fixed mesh objects with own hide_render false; collection visibility not separately filtered',
          'comparison': 'Same retained controls translated back +2.05 m in Blender Y; no source save',
          'results': results, 'left_only_surface_pairs': sorted(left-right),
          'limitations': ['No full-containment test', 'No swept-motion or steering-angle test', 'No factory dimensions or intended joint-contact classification', 'Not an assembly pass'],
          'all16VehicleGates': 'OPEN'}
(OUT / 'rest-intersections.json').write_text(json.dumps(report, indent=2)+'\n')
