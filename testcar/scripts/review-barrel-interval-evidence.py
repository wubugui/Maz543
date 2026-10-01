#!/usr/bin/env python3
"""Read-only review of the measured barrel-axis frozen-interval evidence.

Requires Python 3 and NumPy, but not Blender. --root is the Maz543 repository.
This checks stored evidence and independently tests the analytic formulas; it
intentionally does not re-extract native geometry or prove floating-point error.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.dont_write_bytecode = True
EXPECTED_SOURCE = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
HINGES = ['cab_pivot_002', 'cab_pivot_003', 'cab_pivot_006', 'cab_pivot_007']
COUNT_KEYS = ('pairs', 'certified_frozen_pairs', 'unresolved_pairs',
              'prior261_unresolved', 'added145_unresolved',
              'retained_closed_surface_candidates')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path,
                        help='Path to the Maz543 repository')
    parser.add_argument('--output', required=True, type=Path,
                        help='Machine-readable JSON result path')
    parser.add_argument('--committed-input-ref', default='HEAD',
                        help='Git revision whose four published inputs must match (default: HEAD)')
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    tc = root / 'testcar'
    out = tc / 'work/cloud-barrel-axis-frozen-intervals-20261001'
    report_path = out / 'interval-report.json'
    report = load(report_path)
    source = tc / 'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
    bounds_path = tc / 'scripts/door_interval_bounds.py'
    generator_path = tc / 'scripts/audit-barrel-axis-frozen-intervals.py'
    input_paths = {
        'doors': tc / 'work/cloud-cab-door-dependencies-20261001/inventory.json',
        'original': tc / 'work/cloud-original-cab-contact-location-20261001/location-report.json',
        'axis': tc / 'work/cloud-door-barrel-axis-20261001/axis-report.json',
        'trial': tc / 'work/cloud-door-barrel-motion-trial-20261001/trial-report.json',
    }
    files = [source, bounds_path, generator_path, report_path, out / 'process.json', out / 'read.log', *input_paths.values()]
    files += [out / (hinge + '.json') for hinge in HINGES]
    initial_hashes = {str(p.relative_to(root)): sha(p) for p in files}
    data = {key: load(path) for key, path in input_paths.items()}
    committed_ref = subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', args.committed_input_ref], text=True).strip()
    for key, path in input_paths.items():
        require(sha(path) == report['input_sha256'][key], f'{key}: report hash mismatch')
        committed_bytes = subprocess.check_output(
            ['git', '-C', str(root), 'show', committed_ref + ':' + str(path.relative_to(root))])
        require(hashlib.sha256(committed_bytes).hexdigest() == sha(path), f'{key}: committed input mismatch')
        require(data[key]['source_sha256'] == EXPECTED_SOURCE, f'{key}: wrong source')
    require(sha(source) == report['source_sha256'] == report['source_sha256_after'] == EXPECTED_SOURCE,
            'Source blend hash mismatch')
    require(sha(bounds_path) == report['bounds_implementation_sha256'], 'Bounds implementation hash mismatch')
    require(data['trial']['axis_report_sha256'] == sha(input_paths['axis']), 'Trial/axis link mismatch')
    require(data['trial']['original_location_report_sha256'] == sha(input_paths['original']), 'Trial/original link mismatch')
    require(not data['trial']['violations'] and data['trial']['all_44_closed_parts_restored_exact'],
            'Published trial did not restore all closed parts')
    require(data['trial']['all_stationary_matrices_restored_exact'], 'Published trial did not restore stationary matrices')
    require(data['trial']['source_sha256_after'] == EXPECTED_SOURCE, 'Trial source changed')
    require(report['status'] == 'CONDITIONAL_BARREL_AXIS_FROZEN_INTERVAL_LOCALIZATION_ONLY', 'Wrong claim scope')
    require(report['frame'] == 0 and report['blender_version'] == '4.5.13 LTS', 'Wrong extraction environment')
    require(report['padding_m_per_box'] == 2e-5 and report['max_depth'] == 6 and report['max_cells_per_pair'] == 127,
            'Changed bounding configuration')
    require(report['source_saved'] is False and report['native_continuous_clearance_accepted'] is False
            and report['whole_vehicle_acceptance'] == '16 OPEN', 'Unexpected promotion/acceptance claim')
    require([x['hinge'] for x in report['doors']] == HINGES, 'Wrong report door order')
    require([x['hinge'] for x in data['doors']['doors']] == HINGES, 'Wrong inventory door order')
    require([x['hinge'] for x in data['trial']['doors']] == HINGES, 'Wrong trial door order')
    prior = [x['name'] for x in data['doors']['fixed_geometry']]
    added = data['original']['fixed_names']
    fixed = prior + added
    require(len(prior) == 261 and len(added) == 145 and not set(prior) & set(added), 'Wrong fixed groups')
    require(fixed == report['fixed_names'] and len(fixed) == len(set(fixed)) == 406, 'Wrong fixed-name scope')
    require(report['fixed_groups'] == {'prior_cab': [0, 261], 'original_cab_added': [261, 406]}, 'Wrong fixed indices')

    rng = np.random.default_rng(913)
    all_names, retained, summaries = [], [], []
    total = {key: 0 for key in COUNT_KEYS}
    refined_pairs = 0
    interval_leaves = 0
    max_formula_error = 0.0
    point_angle_comparisons = 0
    unknown_fixed_distribution = {}
    unresolved_reasons = {}
    for idx, entry in enumerate(report['doors']):
        path = out / entry['detail_file']
        require(path == out / (HINGES[idx] + '.json'), 'Unexpected detail path')
        require(sha(path) == entry['detail_sha256'], 'Detail hash mismatch')
        d = load(path)
        inventory = data['doors']['doors'][idx]
        trial = data['trial']['doors'][idx]
        require(d['hinge'] == inventory['hinge'] == trial['hinge'] == entry['hinge'], 'Door identity mismatch')
        require(d['fixed_names'] == fixed, 'Detail fixed order mismatch')
        require(d['moving_names'] == [x['name'] for x in inventory['parts']], 'Moving order mismatch')
        require(len(d['moving_names']) == len(set(d['moving_names'])) == 11, 'Moving names not unique')
        all_names += d['moving_names']
        rows = d['rows']
        pairs = {(r[0], r[1]) for r in rows}
        require(len(rows) == len(pairs) == 4466 and pairs == {(i, j) for i in range(11) for j in range(406)},
                'Missing/duplicate Cartesian pair')
        expected = sorted([0.0, (-1 if idx > 1 else 1) * math.radians(99)])
        require(d['angle_radians'] == expected, 'Wrong signed closed angle domain')
        lo, hi = expected
        refinements = {(r['moving_index'], r['fixed_index']): r for r in d['refined_intervals']}
        require(len(refinements) == len(d['refined_intervals']), 'Duplicate refinement')
        require(set(refinements) == {(r[0], r[1]) for r in rows if r[3] != 1 or not r[2]}, 'Missing refinement')
        for mi, fi, certified, cells, gap in rows:
            require(type(certified) is bool and 1 <= cells <= 127, 'Invalid row type/budget')
            if not certified:
                name = fixed[fi]
                unknown_fixed_distribution[name] = unknown_fixed_distribution.get(name, 0) + 1
            if (mi, fi) not in refinements:
                require(certified and cells == 1 and math.isfinite(gap) and gap > 0, 'Invalid one-cell separation')
            else:
                r = refinements[(mi, fi)]
                require(r['cells'] == cells and certified == (not r['unresolved_intervals']), 'Refinement status mismatch')
                require(r['status'] == ('CERTIFIED_RIGID_SNAPSHOT_BOX_SEPARATION' if certified else 'UNRESOLVED'),
                        'Unexpected refinement status')
                leaves = sorted(r['clear_intervals'] + r['unresolved_intervals'], key=lambda x: x['lo'])
                require(leaves[0]['lo'] == lo and leaves[-1]['hi'] == hi, 'Domain endpoints missing')
                require(all(x['lo'] < x['hi'] for x in leaves), 'Nonpositive leaf interval')
                require(all(a['hi'] == b['lo'] for a, b in zip(leaves, leaves[1:])), 'Gap/overlap in interval partition')
                require(all(0 <= x['axis'] <= 2 and math.isfinite(x['padded_gap_m']) and x['padded_gap_m'] > 0
                            for x in r['clear_intervals']), 'Invalid positive-gap witness')
                gaps = [x['padded_gap_m'] for x in r['clear_intervals']]
                require(gap == (min(gaps) if gaps else None), 'Row minimum differs from clear leaves')
                for x in r['unresolved_intervals']:
                    require(x['reason'] in ('OVERLAPPING_BOUNDS', 'CELL_BUDGET'), 'Unexpected unresolved reason')
                    unresolved_reasons[x['reason']] = unresolved_reasons.get(x['reason'], 0) + 1
                refined_pairs += 1
                interval_leaves += len(leaves)
        require([x['degrees'] for x in trial['poses']] == [0.0, 15.0, 45.0, 75.0, 99.0], 'Trial angle order changed')
        require(trial['poses'][0]['closed_geometry_exact'] is True, 'Trial closed geometry not exact')
        expected_candidates = {(d['moving_names'].index(x['moving']), fixed.index(x['fixed']))
                               for x in trial['poses'][0]['trial_surface_overlap_candidates']}
        require(expected_candidates == {(x['moving_index'], x['fixed_index'])
                                        for x in d['retained_closed_surface_candidates']}, 'Closed candidate set changed')
        require(all(x['zero_angle_unresolved'] is True for x in d['retained_closed_surface_candidates']),
                'Missing retained zero-angle flag')
        for mi, fi in sorted(expected_candidates):
            require(any(x['lo'] <= 0 <= x['hi'] for x in refinements[(mi, fi)]['unresolved_intervals']),
                    'Closed-pose candidate incorrectly certified')
            retained.append({'hinge': d['hinge'], 'moving': d['moving_names'][mi], 'fixed': fixed[fi],
                             'zero_angle_unresolved': True})
        counts = {'pairs': len(rows), 'certified_frozen_pairs': sum(x[2] for x in rows),
                  'unresolved_pairs': sum(not x[2] for x in rows),
                  'prior261_unresolved': sum(not x[2] and x[1] < 261 for x in rows),
                  'added145_unresolved': sum(not x[2] and x[1] >= 261 for x in rows),
                  'retained_closed_surface_candidates': len(expected_candidates)}
        require(all(entry[k] == v for k, v in counts.items()), 'Door summary mismatch')
        require(entry['max_cells'] == max(r[3] for r in rows), 'Maximum cell count mismatch')
        for key, value in counts.items():
            total[key] += value
        w = np.asarray(d['closed_hinge_world_matrix'])
        p = np.asarray(d['local_axis_point'])
        require(np.array_equal(p, trial['measured_local_axis_point']), 'Trial axis point mismatch')
        measured = next(x for x in data['axis']['doors'] if x['hinge'] == d['hinge'])
        center = np.mean([x['center'] for x in measured['barrels']], axis=0)
        independent_p = (np.linalg.inv(w) @ np.r_[center, 1.0])[:3]
        independent_p[2] = 0
        require(np.array_equal(p, independent_p), 'Axis point reconstruction mismatch')
        require(measured['barrel_axes_mutual_offset_m'] < 1e-6
                and all(abs(x - 1) < 1e-8 for x in measured['barrel_axis_dot_pivot_axis']), 'Measured axis alignment changed')
        local = rng.uniform(-2, 2, (300, 3))
        rel = local - p
        a = np.c_[rel[:, :2], np.zeros(len(rel))] @ w[:3, :3].T
        b = np.c_[-rel[:, 1], rel[:, 0], np.zeros(len(rel))] @ w[:3, :3].T
        c = np.c_[np.full(len(rel), p[0]), np.full(len(rel), p[1]), local[:, 2]] @ w[:3, :3].T + w[:3, 3]
        for angle in np.linspace(lo, hi, 123):
            cs, sn = math.cos(angle), math.sin(angle)
            rotation = np.array([[cs, -sn, 0], [sn, cs, 0], [0, 0, 1]])
            direct = (p + rel @ rotation.T) @ w[:3, :3].T + w[:3, 3]
            coefficients = c + a * cs + b * sn
            error = float(np.abs(direct - coefficients).max())
            require(error < 1e-12, 'Direct formula and coefficient formula differ')
            max_formula_error = max(max_formula_error, error)
            point_angle_comparisons += len(local)
        require(d['closed_coefficient_max_error_m'] < 1e-12, 'Stored closed reconstruction error exceeds limit')
        summaries.append({'hinge': d['hinge'], 'angle_radians': expected, 'counts': counts,
                          'refined_pairs': len(refinements),
                          'certified_refined_pairs': sum(r['status'] == 'CERTIFIED_RIGID_SNAPSHOT_BOX_SEPARATION'
                                                       for r in refinements.values()),
                          'minimum_gap_among_certified_pairs_m': min(r[4] for r in rows if r[2]),
                          'stored_closed_reconstruction_error_m': d['closed_coefficient_max_error_m']})
    require(len(set(all_names)) == len(all_names) == 44, 'Global moving scope not 44 unique names')
    require(all(report[k] == v for k, v in total.items()), 'Overall summary mismatch')
    require(total['pairs'] == 17864 and len(retained) == 6, 'Unexpected total scope/candidate count')

    spec = importlib.util.spec_from_file_location('reviewed_door_interval_bounds', bounds_path)
    bounds = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bounds)
    max_bound_difference = 0.0
    for case in range(1000):
        a, b, c = (rng.normal(size=(7, 3)) for _ in range(3))
        lo = float(rng.uniform(-20, 20))
        hi = lo + float(rng.uniform(0, 15))
        lower, upper = bounds.swept_bounds(a, b, c, lo, hi)
        scalar_lower, scalar_upper = np.full(3, np.inf), np.full(3, -np.inf)
        for i in range(7):
            for axis in range(3):
                values = [c[i, axis] + a[i, axis] * math.cos(t) + b[i, axis] * math.sin(t) for t in (lo, hi)]
                phase = math.atan2(b[i, axis], a[i, axis])
                for k in range(math.floor((lo - phase) / math.pi) - 1, math.ceil((hi - phase) / math.pi) + 2):
                    t = phase + k * math.pi
                    if lo <= t <= hi:
                        values.append(c[i, axis] + a[i, axis] * math.cos(t) + b[i, axis] * math.sin(t))
                scalar_lower[axis] = min(scalar_lower[axis], min(values))
                scalar_upper[axis] = max(scalar_upper[axis], max(values))
        require((lower <= scalar_lower).all() and (upper >= scalar_upper).all(), f'Enclosure failure in case {case}')
        max_bound_difference = max(max_bound_difference,
                                   float(np.abs(lower - (scalar_lower - 2e-5)).max()),
                                   float(np.abs(upper - (scalar_upper + 2e-5)).max()))
    controls = bounds.controls()
    require(all(controls[k] is True for k in controls if k != 'note'), 'Stock synthetic control failed')
    process = load(out / 'process.json')
    require(process['exit_code'] == 0 and process['python_exit_code_enabled'] is True
            and process['absolute_script_path'] is True, 'Formal run did not satisfy execution guards')
    require('BARREL_INTERVAL_FINISHED 17864 17812 52' in (out / 'read.log').read_text(), 'Missing formal terminal marker')
    require(all(sha(root / rel) == digest for rel, digest in initial_hashes.items()), 'Review input changed during run')
    result = {
        'status': 'PASS_READ_ONLY_FORMULA_AND_STORED_EVIDENCE_REVIEW',
        'checker_sha256': sha(Path(__file__).resolve()),
        'numpy_version': np.__version__, 'python_version': sys.version.split()[0],
        'committed_input_ref': committed_ref, 'input_sha256': initial_hashes,
        'input_hashes_match_reports_and_four_published_inputs': True,
        'source_sha256_verified': EXPECTED_SOURCE,
        'complete_cartesian_rows': 17864, 'unique_moving_names': 44, 'unique_fixed_names': 406,
        'all_signed_domains_match_trial': True,
        'refined_interval_partitions_checked': refined_pairs,
        'refined_interval_leaves_checked': interval_leaves,
        'all_refined_partitions_exactly_cover_closed_request': True,
        'all_separation_witness_gaps_strictly_positive': True,
        'counts': total, 'doors': summaries,
        'retained_closed_candidates': retained,
        'closed_and_stationary_restore_claims_verified_against_committed_trial': True,
        'unknown_fixed_distribution': unknown_fixed_distribution,
        'unresolved_interval_reasons': unresolved_reasons,
        'formula_random_check': {'rng_seed': 913, 'points_per_door': 300, 'angles_per_door': 123,
                                 'point_angle_comparisons': point_angle_comparisons,
                                 'maximum_absolute_difference_m': max_formula_error,
                                 'description': 'Direct p+Rz(local-p) compared with analytic coefficients using saved hinge transforms and axis points'},
        'independent_scalar_extrema_check': {'cases': 1000, 'vertices_per_case': 7,
                                            'rng_stream': 'Continuation of the seed-913 formula-check RNG',
                                            'lo_domain_radians': [-20, 20], 'width_domain_radians': [0, 15],
                                            'all_enclosed': True, 'maximum_bound_difference_m': max_bound_difference,
                                            'description': 'Independently enumerate phase+k*pi interior stationary points and endpoints per scalar coordinate'},
        'stock_synthetic_controls': controls,
        'formal_run_terminal_marker_verified': True,
        'limits': ['No Blender was executed; native evaluated vertices or all pairwise gaps were not independently re-extracted',
                   'Formula random tests use synthetic points and saved actual hinge transforms; they are regression evidence, not native clearance tests',
                   'Analytic enclosure reasoning applies to frozen frame-zero rigid vertex/triangle geometry',
                   '20 micrometre padding is not proved to bound all Blender floating-point error',
                   'Strict dependency eligibility of the previous261fixed parts is not extended to the added145',
                   'Unresolved pairs are not collision counts; no containment test, native promotion, runtime change or whole-vehicle acceptance'],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(output),
                      'checker_sha256': result['checker_sha256'], 'result_sha256': sha(output),
                      'pairs': total['pairs'], 'scalar_extrema_cases': 1000,
                      'maximum_formula_difference_m': max_formula_error}, indent=2))


if __name__ == '__main__':
    main()
