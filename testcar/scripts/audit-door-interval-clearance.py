"""Read-only conditional interval bounds for the real current native doors.

Never saves a blend or replaces a test object. Uses actual evaluated vertices
at frame zero; reports both conservative interval results and independent
actual-pose comparisons. Other whole-vehicle surfaces remain outside scope.
"""
import bpy, json, hashlib, math, sys, os
from pathlib import Path
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from door_interval_bounds import swept_bounds, certify_pair, controls

SOURCE = ROOT / 'testcar/outputs/MAZ543A_Master.blend'
OUT = ROOT / 'testcar/work/cloud-door-continuous-20260930'
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = '0391bfde5b7474a5f1ac4eac955f2fd8dbbb6febd33fb7d772a2cd18575edec3'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE) == EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def descendants(o):
    for child in o.children:
        yield child
        yield from descendants(child)


def vertices(o):
    ev = o.evaluated_get(dg)
    mesh = ev.to_mesh()
    if not mesh or not len(mesh.vertices):
        raise ValueError('Empty evaluated object: ' + o.name)
    local = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', local)
    local = local.reshape(-1, 3)
    matrix = np.array(ev.matrix_world, dtype=np.float64)
    result = local @ matrix[:3, :3].T + matrix[:3, 3]
    ev.to_mesh_clear()
    return result


moving_hierarchy = set()
for hinge_name in ['cab_pivot_002', 'cab_pivot_003', 'cab_pivot_006', 'cab_pivot_007']:
    h = bpy.data.objects[hinge_name]
    moving_hierarchy.update(x.name for x in [h, *descendants(h)])
dependency_details = []


def potential_nonrigidity(o, hinge, visited=None):
    issues = []
    visited = set() if visited is None else set(visited)
    if o.name in visited:
        return [o.name + ': cyclic modifier dependency']
    visited.add(o.name)
    current = o
    while current and current != hinge:
        if current.constraints:
            issues.append(current.name + ': constraints')
        if current.animation_data:
            issues.append(current.name + ': animation data')
        current = current.parent
    if o.data and getattr(o.data, 'animation_data', None):
        issues.append(o.name + ': animated data')
    if getattr(o.data, 'shape_keys', None):
        issues.append(o.name + ': shape keys')
    for attr in ['bevel_object', 'taper_object']:
        if getattr(o.data, attr, None):
            issues.append(o.name + ': external curve ' + attr)
    intrinsic = {'BEVEL', 'WEIGHTED_NORMAL', 'TRIANGULATE', 'SUBSURF', 'WELD', 'SOLIDIFY', 'EDGE_SPLIT'}
    for mod in o.modifiers:
        if not mod.show_viewport or mod.type in intrinsic:
            continue
        if mod.type == 'BOOLEAN' and hinge is None and mod.operand_type == 'OBJECT' and mod.object:
            operand = mod.object
            if operand.name in moving_hierarchy:
                issues.append(o.name + ': Boolean operand in moving door hierarchy')
            else:
                nested = potential_nonrigidity(operand, None, visited)
                issues.extend(nested)
                dependency_details.append({'object': o.name, 'modifier': mod.name, 'static_boolean_operand': operand.name, 'issues': nested})
        elif mod.type == 'NODES' and mod.node_group:
            group = mod.node_group
            # The inspected current slope mapping is local position arithmetic;
            # reject any future scene/object input, group nesting or animation.
            allowed = {'GeometryNodeInputPosition', 'GeometryNodeSetPosition', 'NodeGroupInput', 'NodeGroupOutput', 'ShaderNodeCombineXYZ', 'ShaderNodeMath', 'ShaderNodeSeparateXYZ'}
            node_types = sorted(set(n.bl_idname for n in group.nodes))
            if group.animation_data or not set(node_types).issubset(allowed):
                issues.append(o.name + ': unproven/animated geometry node group')
            for item in group.interface.items_tree:
                if item.item_type == 'SOCKET' and item.socket_type not in {'NodeSocketGeometry', 'NodeSocketFloat', 'NodeSocketInt', 'NodeSocketBool', 'NodeSocketVector'}:
                    issues.append(o.name + ': external/unknown geometry node interface')
            dependency_details.append({'object': o.name, 'modifier': mod.name, 'local_node_group': group.name, 'node_types': node_types})
        else:
            issues.append(o.name + ': unproven modifier ' + mod.type)
    return issues


fixed_objects = [o for o in bpy.data.objects if o.parent and o.name.startswith('BL_Front_') and o.type in {'MESH', 'CURVE'}]
assert fixed_objects
padding = 2e-5
fixed_vertices = {o.name: vertices(o) for o in fixed_objects}
fixed_bounds = {name: (pts.min(axis=0) - padding, pts.max(axis=0) + padding) for name, pts in fixed_vertices.items()}
report = {
    'status': 'IN_PROGRESS', 'all16VehicleGates': 'OPEN', 'source_sha256': EXPECTED,
    'scope': 'Current four real door descendants against the same BL_Front_* set used by the retained 3-degree audit. No original cab/frame/interior or other vehicle surfaces are added.',
    'mathematics': 'Closed-interval extrema of every actual evaluated vertex C+A*cos(theta)+B*sin(theta). Mesh triangle interiors lie inside the resulting axis-aligned boxes. Strictly disjoint outward-padded boxes are sufficient for separation of these frozen rigid snapshots throughout the stated angle interval, including possible contained volumes. Overlapping boxes are unresolved, not collisions or passes.',
    'numerics': 'Float64 analytic evaluation with 20 micrometres outward padding on each moving/fixed box; critical-angle membership widened by 1e-12 radians. Not an interval-arithmetic proof of every Blender/WebGL floating-point operation.',
    'native_dependency_limit': 'A dependency inventory and independent pose comparisons are reported separately. Any unproven modifier, constraint, animation or pose error prevents a native-rigid eligibility claim; frozen-snapshot bounds are not substituted for the full evaluated scene.',
    'padding_m_per_box': padding, 'synthetic_controls': controls(),
    'fixed_objects': [{'name': name, 'vertices': len(fixed_vertices[name]), 'bounds': [x.tolist() for x in bounds]} for name, bounds in fixed_bounds.items()],
    'fixed_dependency_inventory': [{'name': o.name, 'potential_nonrigidity': potential_nonrigidity(o, None)} for o in fixed_objects],
    'doors': []}

for name, side in [('cab_pivot_002', -1), ('cab_pivot_003', -1), ('cab_pivot_006', 1), ('cab_pivot_007', 1)]:
    hinge = bpy.data.objects[name]
    base = hinge.matrix_basis.copy()
    world = np.array(hinge.matrix_world, dtype=np.float64)
    inv = np.linalg.inv(world)
    parts = [o for o in descendants(hinge) if o.type in {'MESH', 'CURVE'}]
    assert parts and not any(o.name in fixed_bounds for o in parts)
    coefficients = {}
    inventory = []
    for part in parts:
        pts = vertices(part)
        loc = pts @ inv[:3, :3].T + inv[:3, 3]
        va = np.column_stack((loc[:, 0], loc[:, 1], np.zeros(len(loc))))
        vb = np.column_stack((-loc[:, 1], loc[:, 0], np.zeros(len(loc))))
        vc = np.column_stack((np.zeros(len(loc)), np.zeros(len(loc)), loc[:, 2]))
        a, b, c = va @ world[:3, :3].T, vb @ world[:3, :3].T, vc @ world[:3, :3].T + world[:3, 3]
        coefficients[part.name] = (a, b, c)
        inventory.append({'name': part.name, 'vertices': len(pts), 'potential_nonrigidity': potential_nonrigidity(part, hinge)})
    comparisons = []
    for deg in [0., .731, 14.37, 48.125, 83.61, 99.]:
        angle = -side * math.radians(deg)
        hinge.matrix_basis = base @ Matrix.Rotation(angle, 4, 'Z')
        bpy.context.view_layer.update()
        for part in parts:
            pts = vertices(part)
            a, b, c = coefficients[part.name]
            same = pts.shape == a.shape
            error = float(np.max(np.linalg.norm(pts - (c + a * math.cos(angle) + b * math.sin(angle)), axis=1))) if same else None
            comparisons.append({'part': part.name, 'degrees': deg, 'vertex_count_equal': same, 'maximum_corresponding_vertex_error_m': error})
    hinge.matrix_basis = base
    bpy.context.view_layer.update()
    pairs = []
    lo, hi = sorted((0., -side * math.radians(99)))
    for part in parts:
        a, b, c = coefficients[part.name]
        for other, bounds in fixed_bounds.items():
            result = certify_pair(a, b, c, bounds, lo, hi, max_depth=8, max_cells=511, padding=padding)
            result.update({'moving_part': part.name, 'fixed_part': other})
            pairs.append(result)
    max_error = max((x['maximum_corresponding_vertex_error_m'] or 0.) for x in comparisons)
    eligible = not hinge.constraints and not hinge.animation_data and not any(x['potential_nonrigidity'] for x in inventory) and all(x['vertex_count_equal'] for x in comparisons) and max_error < padding
    entry = {'hinge': name, 'side': side, 'basis': [list(x) for x in base], 'world_at_zero': world.tolist(), 'parts': inventory,
             'independent_actual_pose_comparisons': comparisons, 'maximum_actual_pose_error_m': max_error,
             'native_rigid_inventory_eligible': eligible, 'pairs': pairs,
             'certified_snapshot_pairs': sum(x['status'].startswith('CERTIFIED') for x in pairs),
             'unresolved_pairs': sum(x['status'] == 'UNRESOLVED' for x in pairs)}
    report['doors'].append(entry)
    print('DOOR_INTERVAL', name, entry['certified_snapshot_pairs'], entry['unresolved_pairs'], 'eligible', eligible, flush=True)
    (OUT / 'interval-report.partial.json').write_text(json.dumps(report, indent=2))

report['fixed_geometry_unchanged_after_door_trials'] = all(np.array_equal(vertices(o), fixed_vertices[o.name]) for o in fixed_objects)
report['source_sha256_after'] = sha(SOURCE)
assert report['source_sha256_after'] == EXPECTED
report['status'] = 'LIMITED_RIGID_SNAPSHOT_INTERVAL_RESULTS; NOT_WHOLE_VEHICLE_ACCEPTANCE'
report['certified_snapshot_pairs'] = sum(d['certified_snapshot_pairs'] for d in report['doors'])
report['unresolved_pairs'] = sum(d['unresolved_pairs'] for d in report['doors'])
report['all_native_dependency_inventories_eligible'] = all(d['native_rigid_inventory_eligible'] for d in report['doors']) and not any(x['potential_nonrigidity'] for x in report['fixed_dependency_inventory']) and report['fixed_geometry_unchanged_after_door_trials']
report['dependency_details'] = dependency_details
(OUT / 'interval-report.json').write_text(json.dumps(report, indent=2))
print('DONE', report['certified_snapshot_pairs'], report['unresolved_pairs'], flush=True)
