"""Conditional whole-angle localization for the measured barrel-axis trial.

Every pair is retained. Overlapping swept boxes are unresolved, never a contact
or a pass. Evaluated frame-zero snapshots are frozen under the trial formula;
this is not a floating-point implementation proof or native-asset promotion.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from door_interval_bounds import certify_pair, controls

SOURCE = ROOT / 'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
INPUTS = {
    'doors': ROOT / 'work/cloud-cab-door-dependencies-20261001/inventory.json',
    'original': ROOT / 'work/cloud-original-cab-contact-location-20261001/location-report.json',
    'axis': ROOT / 'work/cloud-door-barrel-axis-20261001/axis-report.json',
    'trial': ROOT / 'work/cloud-door-barrel-motion-trial-20261001/trial-report.json',
}
OUT = ROOT / 'work/cloud-barrel-axis-frozen-intervals-20261001'
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE) == EXPECTED and bpy.app.version[:3] == (4, 5, 13)
data = {k: json.loads(p.read_text()) for k, p in INPUTS.items()}
assert all(d['source_sha256'] == EXPECTED for d in data.values())
assert data['trial']['axis_report_sha256'] == sha(INPUTS['axis'])
assert data['trial']['original_location_report_sha256'] == sha(INPUTS['original'])
assert not data['trial']['violations'] and data['trial']['all_44_closed_parts_restored_exact']
assert data['trial']['source_sha256_after'] == EXPECTED
hinges = ['cab_pivot_002', 'cab_pivot_003', 'cab_pivot_006', 'cab_pivot_007']
assert [d['hinge'] for d in data['doors']['doors']] == hinges
assert [d['hinge'] for d in data['trial']['doors']] == hinges
prior = [d['name'] for d in data['doors']['fixed_geometry']]
added = data['original']['fixed_names']
assert len(prior) == 261 and len(added) == 145 and not set(prior) & set(added)
fixed_names = prior + added
assert len(set(fixed_names)) == 406

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def points(o):
    ev = o.evaluated_get(dg)
    m = ev.to_mesh()
    try:
        assert m and len(m.vertices)
        xyz = np.empty(len(m.vertices) * 3, dtype=np.float64)
        m.vertices.foreach_get('co', xyz)
        xyz = xyz.reshape(-1, 3)
        w = np.asarray(ev.matrix_world, dtype=np.float64)
        return xyz @ w[:3, :3].T + w[:3, 3]
    finally:
        ev.to_mesh_clear()

padding = 2e-5
fixed = []
for name in fixed_names:
    xyz = points(bpy.data.objects[name])
    fixed.append((xyz.min(0) - padding, xyz.max(0) + padding))
report = {
    'status': 'CONDITIONAL_BARREL_AXIS_FROZEN_INTERVAL_LOCALIZATION_ONLY',
    'source_sha256': EXPECTED,
    'input_sha256': {k: sha(p) for k, p in INPUTS.items()},
    'bounds_implementation_sha256': sha(ROOT / 'scripts/door_interval_bounds.py'),
    'blender_version': bpy.app.version_string, 'frame': 0,
    'motion_formula': 'world @ (p + Rz(theta) @ (local-p)), p from exact published trial',
    'padding_m_per_box': padding, 'max_depth': 6, 'max_cells_per_pair': 127,
    'fixed_names': fixed_names, 'fixed_groups': {'prior_cab': [0, 261], 'original_cab_added': [261, 406]},
    'synthetic_bounds_controls': controls(), 'doors': [],
    'source_saved': False, 'native_continuous_clearance_accepted': False,
    'whole_vehicle_acceptance': '16 OPEN',
    'limits': [
        'Frozen frame-zero evaluated vertices and triangle convex hulls only, under the recorded rigid formula',
        'No claim that 20 micrometre padding is a proved whole-angle Blender floating-point error bound',
        'Prior strict dependency eligibility covers261fixedparts; newly added145parts not automatically eligible',
        'Overlapping bounds are unresolved, not collision; no hidden parts, other moving doors or outside-root geometry',
        'Existing six closed-pose surface candidates are retained and cannot pass a full closed interval',
        'No native save, runtime change, factory axis coordinates, containment test or vehicle acceptance',
    ],
}
for door, trial, side in zip(data['doors']['doors'], data['trial']['doors'], [-1, -1, 1, 1]):
    hinge = bpy.data.objects[door['hinge']]
    w = np.asarray(hinge.matrix_world, dtype=np.float64)
    inv = np.linalg.inv(w)
    measured = next(d for d in data['axis']['doors'] if d['hinge'] == hinge.name)
    center = np.mean([x['center'] for x in measured['barrels']], axis=0)
    derived = inv[:3, :3] @ center + inv[:3, 3]
    derived[2] = 0
    p = np.asarray(trial['measured_local_axis_point'], dtype=np.float64)
    assert np.array_equal(derived, p), 'Changed trial axis'
    assert measured['barrel_axes_mutual_offset_m'] < 1e-6
    assert all(abs(x-1) < 1e-8 for x in measured['barrel_axis_dot_pivot_axis'])
    lo, hi = sorted((0., -side * math.radians(99)))
    part_names = [x['name'] for x in door['parts']]
    assert len(part_names) == len(set(part_names)) == 11
    closed_candidates = trial['poses'][0]['trial_surface_overlap_candidates']
    assert [x['degrees'] for x in trial['poses']] == [0., 15., 45., 75., 99.]
    rows, refined = [], []
    closed_coefficient_error = 0.
    for moving_index, name in enumerate(part_names):
        xyz = points(bpy.data.objects[name])
        local = xyz @ inv[:3, :3].T + inv[:3, 3]
        rel = local - p
        a = np.column_stack((rel[:, 0], rel[:, 1], np.zeros(len(rel)))) @ w[:3, :3].T
        b = np.column_stack((-rel[:, 1], rel[:, 0], np.zeros(len(rel)))) @ w[:3, :3].T
        c = np.column_stack((np.full(len(rel), p[0]), np.full(len(rel), p[1]), local[:, 2])) @ w[:3, :3].T + w[:3, 3]
        closed_coefficient_error = max(closed_coefficient_error, float(np.max(np.linalg.norm(a+c-xyz, axis=1))))
        for fixed_index, box in enumerate(fixed):
            r = certify_pair(a, b, c, box, lo, hi, max_depth=6, max_cells=127, padding=padding)
            certified = not r['unresolved_intervals']
            gaps = [x['padded_gap_m'] for x in r['clear_intervals']]
            rows.append([moving_index, fixed_index, certified, r['cells'], min(gaps) if gaps else None])
            if r['cells'] != 1 or not certified:
                refined.append({'moving_index': moving_index, 'fixed_index': fixed_index, **r})
    assert closed_coefficient_error < 1e-12
    assert len(rows) == 4466 and {(r[0], r[1]) for r in rows} == {(i,j) for i in range(11) for j in range(406)}
    retained = []
    for contact in closed_candidates:
        mi, fi = part_names.index(contact['moving']), fixed_names.index(contact['fixed'])
        row = next(r for r in rows if r[:2] == [mi,fi])
        assert not row[2], 'Known closed-pose candidate incorrectly separated'
        intervals = next(r for r in refined if r['moving_index']==mi and r['fixed_index']==fi)['unresolved_intervals']
        assert any(r['lo'] <= 0 <= r['hi'] for r in intervals)
        retained.append({'moving_index':mi, 'fixed_index':fi, 'zero_angle_unresolved':True})
    detail = {
        'hinge':hinge.name, 'angle_radians':[lo,hi], 'local_axis_point':p.tolist(),
        'closed_hinge_world_matrix':w.tolist(), 'moving_names':part_names, 'fixed_names':fixed_names,
        'row_columns':['moving_index','fixed_index','frozen_separation_certified','cells','minimum_proved_padded_gap_m'],
        'rows':rows, 'refined_intervals':refined,
        'single_cell_rows':'Certified one-cell rows cover the complete closed angle_radians interval',
        'closed_coefficient_max_error_m':closed_coefficient_error,
        'retained_closed_surface_candidates':retained,
    }
    path = OUT / (hinge.name+'.json')
    path.write_text(json.dumps(detail, ensure_ascii=False, separators=(',',':'))+'\n')
    entry = {
        'hinge':hinge.name, 'pairs':len(rows),
        'certified_frozen_pairs':sum(r[2] for r in rows), 'unresolved_pairs':sum(not r[2] for r in rows),
        'prior261_unresolved':sum(not r[2] for r in rows if r[1]<261),
        'added145_unresolved':sum(not r[2] for r in rows if r[1]>=261),
        'retained_closed_surface_candidates':len(retained), 'max_cells':max(r[3] for r in rows),
        'detail_file':path.name, 'detail_sha256':sha(path),
    }
    report['doors'].append(entry)
    print('BARREL_INTERVAL', entry, flush=True)
report.update({k:sum(d[k] for d in report['doors']) for k in ['pairs','certified_frozen_pairs','unresolved_pairs','prior261_unresolved','added145_unresolved','retained_closed_surface_candidates']})
report['source_sha256_after'] = sha(SOURCE)
assert report['source_sha256_after'] == EXPECTED and report['pairs'] == 17864
assert report['retained_closed_surface_candidates'] == 6
(OUT/'interval-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print('BARREL_INTERVAL_FINISHED', report['pairs'], report['certified_frozen_pairs'], report['unresolved_pairs'], flush=True)
