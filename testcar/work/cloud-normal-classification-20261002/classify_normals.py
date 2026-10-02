"""Read saved ten-target arrays; emit a diagnosis, never an acceptance result.

Run only with capture.json's bundled Python. No bpy, source evaluation, export,
buffer correction, legacy gate invocation or overwrite is performed.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
os.environ['OPENBLAS_NUM_THREADS'] = '2'
os.environ['OMP_NUM_THREADS'] = '2'
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAPTURE = HERE.parent / 'cloud-ten-normal-capture-20261002'
EXPORT = HERE.parent / 'cloud-native-static-export-20261002'
sys.path.insert(0, str(CAPTURE))
import replay_capture as replay

spec = importlib.util.spec_from_file_location('saved_uv_helpers', CAPTURE / 'uv-analysis-01/analyze_uv.py')
uv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uv)
GROUPS = ('position_only_independent', 'normal_refined_conditioned')
LEGACY_KEY = 'raw_to_official_normal_max_nonzero_error'


def summary(values):
    values = np.asarray(values, dtype=np.float64)
    finite = values[np.isfinite(values)]
    return {'count': int(values.size), 'finite_count': int(finite.size),
            'nonfinite_count': int(values.size - finite.size),
            'min': float(finite.min()) if finite.size else None,
            'max': float(finite.max()) if finite.size else None}


def directions(left, right, fallback=None, left_zero_reason='left_zero'):
    """Internal NaNs never become JSON zeros; excluded directions serialize null."""
    left, right = np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)
    a, b = np.linalg.norm(left, axis=1), np.linalg.norm(right, axis=1)
    reason = np.full(len(left), '', dtype=object)
    reason[b == 0] = 'right_zero'
    if fallback is not None:
        reason[np.asarray(fallback, dtype=bool)] = 'rounded_zero_fallback'
    reason[a == 0] = left_zero_reason
    reason[~(np.isfinite(left).all(axis=1) & np.isfinite(right).all(axis=1))] = 'nonfinite_vector'
    valid = reason == ''
    angle, chord = np.full(len(left), np.nan), np.full(len(left), np.nan)
    u, v = left[valid] / a[valid, None], right[valid] / b[valid, None]
    angle[valid] = np.degrees(np.arctan2(np.linalg.norm(np.cross(u, v), axis=1),
                                       np.einsum('ij,ij->i', u, v)))
    chord[valid] = np.linalg.norm(u - v, axis=1)
    return angle, chord, reason


def direction_summary(metrics):
    angle, chord, reason = metrics
    valid = reason == ''
    return {'valid_count': int(valid.sum()), 'excluded_count': int((~valid).sum()),
            'exclusion_reason_counts': dict(Counter(reason[~valid])),
            'angle_degrees': summary(angle[valid]), 'chord': summary(chord[valid]),
            'excluded_angle_and_chord': None}


def corner_direction(metrics, index):
    angle, chord, reason = metrics
    return {'angle_degrees': None if reason[index] else float(angle[index]),
            'chord': None if reason[index] else float(chord[index]),
            'exclusion_reason': reason[index] or None}


def raw_diagnosis(name, a, transformed, old_value, old_source):
    raw = a['raw_normals_native']
    rounded, converted, fallback, error = transformed
    r, c = raw.astype(np.float64), converted.astype(np.float64)
    lengths, clengths = np.linalg.norm(r, axis=1), np.linalg.norm(c, axis=1)
    metrics = directions(r, c, fallback, 'raw_zero')
    perturbation = np.linalg.norm(rounded.astype(np.float64) - r, axis=1)

    def witness(index):
        index = int(index)
        direction = corner_direction(metrics, index)
        amplitude = float((lengths[index] - clengths[index]) ** 2)
        angular = None if direction['chord'] is None else float(lengths[index] * clengths[index] * direction['chord'] ** 2)
        memberships = np.argwhere(a['triangle_loop'] == index)
        return {'object': name, 'loop_index': index, 'vertex_index': int(a['loop_vertex'][index]),
                'r': raw[index].tolist(), 'q': rounded[index].tolist(), 'c': converted[index].tolist(),
                'raw_length': float(lengths[index]), 'converted_length': float(clengths[index]),
                'raw_to_reproduced_vector_error': float(error[index]), 'direction': direction,
                'triangle_references': [{'triangle': int(t), 'corner': int(k),
                                         'material_slot': int(a['triangle_material'][t])} for t, k in memberships],
                'same_corner_decomposition': {'D_squared': float(error[index] ** 2),
                                             'amplitude_squared': amplitude,
                                             'a_b_chord_squared': angular,
                                             'residual': None if angular is None else float(error[index] ** 2 - amplitude - angular)}}

    nonzero_max = float(error[~fallback].max(initial=0))  # Original ~zero mask, unchanged.
    assert nonzero_max == old_value
    valid_indices = np.flatnonzero(metrics[2] == '')
    worst_direction = witness(valid_indices[metrics[0][valid_indices].argmax()]) if valid_indices.size else None
    return {'native_raw': {'length': summary(lengths), 'distance_from_unit': summary(np.abs(lengths - 1)),
                           'zero_count': int((~raw.any(axis=1)).sum()),
                           'nonfinite_vector_count': int((~np.isfinite(raw).all(axis=1)).sum()),
                           'worst_distance_from_unit_corner': witness(np.abs(lengths - 1).argmax()),
                           'unit_length_acceptance_limit': None},
            'official_conversion': {'round4_vector_perturbation': summary(perturbation),
                                    'converted_length': summary(clengths),
                                    'raw_to_reproduced_vector_error': summary(error),
                                    'raw_to_reproduced_nonzero_max_vector_error': nonzero_max,
                                    'legacy_field_name': LEGACY_KEY, 'legacy_value': old_value,
                                    'legacy_source': old_source, 'legacy_mask': '~rounded_zero_after_normalization',
                                    'fallback_count': int(fallback.sum()), 'direction': direction_summary(metrics),
                                    'direction_acceptance_limit': None,
                                    'worst_vector_error_corner': witness(error.argmax()),
                                    'worst_direction_corner': worst_direction}}


def pair_triangles(fattrs, ftri, gattrs, gtri, fresh_material, glb_material):
    """Same rule as saved compare_bucket, reusing its exact grouping/value helpers.

    This exposes the pairing basis needed by the new report. UV is never read.
    Unresolved groups retain both cardinalities; there is no arbitrary fallback.
    """
    if fresh_material != glb_material:
        return [], [{'reason': 'material_mismatch', 'fresh_triangles': len(ftri), 'glb_triangles': len(gtri)}]
    fg, gg = uv.triangle_groups(fattrs, ftri), uv.triangle_groups(gattrs, gtri)
    pairs, unresolved = [], []
    for key in sorted(set(fg) | set(gg)):
        left, right = fg.get(key, []), gg.get(key, [])
        reason = None
        if len(left) != len(right) or not left or any(not t['rotation_unique'] for t in left + right):
            reason = 'position multiplicity or cyclic rotation ambiguity'
        elif len(left) == 1:
            pairs.append((left[0], right[0], GROUPS[0]))
        else:
            matches = [[j for j, b in enumerate(right)
                        if np.array_equal(uv.values(fattrs, a, 'NORMAL'), uv.values(gattrs, b, 'NORMAL'))]
                       for a in left]
            if all(len(m) == 1 for m in matches) and len({m[0] for m in matches}) == len(right):
                pairs.extend((a, right[m[0]], GROUPS[1]) for a, m in zip(left, matches))
            else:
                reason = 'exact numeric NORMAL does not uniquely resolve duplicates'
        if reason:
            unresolved.append({'position_key_sha256': hashlib.sha256(key).hexdigest(),
                               'fresh_triangles': len(left), 'glb_triangles': len(right), 'reason': reason})
    return pairs, unresolved


def transport(fresh, actual, fallback):
    fresh = np.ascontiguousarray(fresh, dtype='<f4').reshape(-1, 3)
    actual = np.ascontiguousarray(actual, dtype='<f4').reshape(-1, 3)
    # Numeric/bit comparison is on s/g themselves, BEFORE direction normalization.
    finite = np.isfinite(fresh) & np.isfinite(actual)
    eligible, nonfinite = int(finite.sum()), int((~finite).sum())
    fields = uv.field_comparison(fresh, actual) if not nonfinite else uv.field_comparison(fresh[finite], actual[finite])
    finite_max = fields['max_absolute_difference'] if eligible else None
    # Unknown/nonfinite components are counted separately, never silently equal.
    # The inherited helper sees only finite pairs; its historical code is intact.
    fields.update({'components': fresh.size, 'numeric_comparison_eligible_components': eligible,
                   'nonfinite_component_pairs': nonfinite,
                   'fresh_nonfinite_components': int((~np.isfinite(fresh)).sum()),
                   'glb_nonfinite_components': int((~np.isfinite(actual)).sum()),
                   'numeric_equal_eligible_components': eligible - fields['numeric_different_components'],
                   'numeric_comparison_scope': 'Finite component pairs only; nonfinite pairs are unknown, not equal',
                   'byte_different_components': int((fresh.view('<u4') != actual.view('<u4')).sum()),
                   'fresh_negative_zero_components': int(((fresh == 0) & np.signbit(fresh)).sum()),
                   'glb_negative_zero_components': int(((actual == 0) & np.signbit(actual)).sum()),
                   'finite_components_max_absolute_difference': finite_max,
                   'max_absolute_difference': None if nonfinite or not eligible else finite_max,
                   'max_ulp_distance': None if nonfinite or not eligible else fields['max_ulp_distance']})
    metrics = directions(fresh, actual, np.asarray(fallback).reshape(-1))
    finite_vectors = finite.all(axis=1)
    vector = np.full(len(fresh), np.nan)
    vector[finite_vectors] = np.linalg.norm(fresh[finite_vectors].astype(np.float64) - actual[finite_vectors].astype(np.float64), axis=1)
    return {'triangles': len(fresh) // 3, 'expanded_corners': len(fresh),
            **fields, 'vector_error': summary(vector),
            'max_vector_error': None if nonfinite else summary(vector)['max'],
            'direction': direction_summary(metrics),
            'max_direction_angle_degrees': direction_summary(metrics)['angle_degrees']['max'],
            'classification': ('NO_TRIANGLES_IN_GROUP' if not fresh.size else
                               'NONFINITE_COMPONENTS_NOT_NUMERICALLY_COMPARABLE' if nonfinite else
                               'NUMERIC_DIFFERENCE_OBSERVED' if fields['numeric_different_components'] else
                               'NUMERIC_EQUAL_WITH_ZERO_SIGN_DIFFERENCES'),
            'direction_acceptance_limit': None}


def preserved_qualification(cfg):
    old = json.loads((EXPORT / 'run-03/native/decoded-validation.json').read_text())
    limit = json.loads((EXPORT / 'inputs.json').read_text())['validation_limits']['normal_nonzero_vector_error']
    result = {**cfg['unchanged_qualification'], 'transport': old['status'], 'issues': len(old['issues']),
              'normal_nonzero_vector_error_limit': limit, 'legacy_raw_max': old[LEGACY_KEY],
              'legacy_report': str(EXPORT / 'run-03/native/decoded-validation.json'),
              'legacy_comparator': str(EXPORT / 'validate_export.py')}
    assert result['transport'] == 'FAIL_STATIC_NATIVE_TRANSPORT' and result['issues'] == 2299
    assert limit == 2e-4 and result['whole_vehicle'] == 'ALL_16_OPEN'
    return result


def input_paths(cfg):
    extra = [HERE / 'design.md', HERE / 'classify_normals.py', HERE / 'test_classification.py', HERE / 'run_bounded.py',
             ROOT / 'AGENTS.md', ROOT / 'CLOUD_CONTINUATION.md', ROOT / 'CLOUD_HANDOFF.md',
             ROOT / 'testcar/docs/ACCEPTANCE.md', CAPTURE / 'capture.json', CAPTURE / 'replay_capture.py',
             CAPTURE / 'run-01/replay-report.json', CAPTURE / 'run-01/result-summary.json',
             CAPTURE / 'uv-analysis-01/analyze_uv.py', CAPTURE / 'uv-analysis-01/analysis.json',
             EXPORT / 'inputs.json', EXPORT / 'validate_export.py', EXPORT / 'run-03/native/decoded-validation.json',
             HERE / 'attempt-01-preservation.json', *sorted((HERE / 'attempt-01').iterdir())]
    return list(dict.fromkeys([Path(v['path']) for v in cfg['inputs'].values()] + extra +
                             [CAPTURE / 'run-01' / (t['object'] + '.json') for t in cfg['targets']]))


def build_report():
    cfg = json.loads((CAPTURE / 'capture.json').read_text())
    assert replay.runtime_identity() == cfg['runtime'], 'Use the pinned official bundled runtime'
    paths = input_paths(cfg)
    before = [replay.file_record(p) for p in paths]
    assert {k: replay.file_record(v['path']) for k, v in cfg['inputs'].items()} == cfg['inputs']
    decoder = replay.load_decoder(cfg['inputs']['decoder']['path'])
    asset = decoder._GLB(Path(cfg['inputs']['glb']['path']).read_bytes())
    references = json.loads(Path(cfg['inputs']['references']['path']).read_text())
    prior = json.loads((CAPTURE / 'run-01/replay-report.json').read_text())
    uv_prior = json.loads((CAPTURE / 'uv-analysis-01/analysis.json').read_text())
    targets, global_arrays = [], {g: {'fresh': [], 'actual': [], 'fallback': []} for g in GROUPS}
    all_fuv, all_guv, unresolved_all = [], [], []
    loop_count = triangle_count = 0
    for target in cfg['targets']:
        name, ref_id = target['object'], target['reference_mesh_id']
        record_path = CAPTURE / 'run-01' / (name + '.json')
        record = json.loads(record_path.read_text())
        assert record['object'] == name and record['reference_mesh_id'] == ref_id and record['runtime'] == cfg['runtime']
        a, attrs, fresh, transformed = replay.attributes_and_legacy(record, decoder)
        saved = next(t for t in prior['targets'] if t['object'] == name)
        old = references['meshes'][ref_id]
        assert fresh == saved['fresh_legacy_record'] and old == saved['run03_record']
        assert references['nodes'][name] == ref_id
        nodes = [(i, n) for i, n in enumerate(asset.j['nodes']) if n.get('name') == name]
        assert len(nodes) == 1
        node_index, node = nodes[0]
        assert 'skin' not in node and not node.get('weights')
        mesh = asset.j['meshes'][node['mesh']]
        assert not mesh.get('weights')
        buckets, used_slots = [], set()
        for pi, primitive in enumerate(mesh['primitives']):
            assert primitive.get('mode', 4) == 4 and not primitive.get('targets')
            material = asset.j['materials'][primitive['material']]['name']
            slots = record['evaluated_material_slots']
            candidates = [int(i) for i in np.unique(a['triangle_material']) if slots[int(i)] == material]
            assert len(candidates) == 1, 'Ambiguous material identity: diagnosis cannot select a bucket'
            slot = candidates[0]
            assert slot not in used_slots
            used_slots.add(slot)
            gat = {k: asset.accessor(v)[0] for k, v in primitive['attributes'].items()}
            assert set(gat) == set(attrs) == {'POSITION', 'NORMAL', 'TEXCOORD_0'}
            gtri = asset.accessor(primitive['indices'])[0].reshape(-1, 3)
            ftri = a['triangle_loop'][a['triangle_material'] == slot]
            pairs, unresolved = pair_triangles(attrs, ftri, gat, gtri, slots[slot], material)
            old_bucket = next(t for t in uv_prior['targets'] if t['object'] == name)['buckets'][pi]
            assert len(pairs) == old_bucket['matched_triangles'] and unresolved == old_bucket['unresolved_groups']
            group_rows, counts = {}, Counter(basis for _, _, basis in pairs)
            assert counts[GROUPS[0]] == old_bucket['position_unique_pairs']
            assert counts[GROUPS[1]] == old_bucket['pairs_resolved_by_exact_numeric_normal']
            for basis in GROUPS:
                group_pairs = [(f, g) for f, g, b in pairs if b == basis]
                fn = np.asarray([uv.values(attrs, f, 'NORMAL') for f, _ in group_pairs], dtype='<f4').reshape(-1, 3)
                gn = np.asarray([uv.values(gat, g, 'NORMAL') for _, g in group_pairs], dtype='<f4').reshape(-1, 3)
                fb = np.asarray([np.roll(transformed[2][f['corners']], -f['rotation']) for f, _ in group_pairs]).reshape(-1)
                group_rows[basis] = transport(fn, gn, fb)
                for key, data in [('fresh', fn), ('actual', gn), ('fallback', fb)]:
                    global_arrays[basis][key].append(data)
            fn = np.asarray([uv.values(attrs, f, 'NORMAL') for f, _, _ in pairs], dtype='<f4')
            gn = np.asarray([uv.values(gat, g, 'NORMAL') for _, g, _ in pairs], dtype='<f4')
            fu = np.asarray([uv.values(attrs, f, 'TEXCOORD_0') for f, _, _ in pairs], dtype='<f4')
            gu = np.asarray([uv.values(gat, g, 'TEXCOORD_0') for _, g, _ in pairs], dtype='<f4')
            assert uv.field_comparison(fn, gn) == old_bucket['paired_normal']
            assert uv.field_comparison(fu, gu) == old_bucket['uv']
            all_fuv.append(fu.reshape(-1, 2)); all_guv.append(gu.reshape(-1, 2))
            actual_signatures = decoder.oriented_signature(gat, gtri)['signatures']
            assert actual_signatures == old_bucket['glb_signatures']
            assert next(p for p in old['parts'] if p['source_material_slot'] == slot)['signature']['signatures'] == old_bucket['run03_signatures']
            buckets.append({'material_name': material, 'source_material_slot': slot, 'glb_primitive': pi,
                            'fresh_triangles': len(ftri), 'glb_triangles': len(gtri),
                            'transport_by_correspondence': group_rows, 'unresolved_groups': unresolved,
                            'attribute_binding': {k: old_bucket[k] for k in
                                                  ('run03_signatures', 'glb_signatures', 'fresh_signatures', 'glb_vs_run03_signature_equal')},
                            'uv': uv.field_comparison(fu, gu)})
            unresolved_all.extend({'object': name, 'material_name': material, **u} for u in unresolved)
        assert used_slots == set(map(int, np.unique(a['triangle_material'])))
        loop_count += len(a['loop_vertex']); triangle_count += len(a['triangle_loop'])
        targets.append({'object': name, 'reference_mesh_id': ref_id, 'raw_evidence': str(record_path),
                        'original_loops': len(a['loop_vertex']), 'triangles': len(a['triangle_loop']),
                        'glb_node': node_index, 'glb_mesh': node['mesh'],
                        'legacy_record_status': saved['correspondence'],
                        **raw_diagnosis(name, a, transformed, old[LEGACY_KEY], cfg['inputs']['references']['path'] + '#/meshes/' + ref_id),
                        'buckets': buckets})
    groups = {g: transport(*(np.concatenate(global_arrays[g][k]) for k in ('fresh', 'actual', 'fallback'))) for g in GROUPS}
    for g, values in groups.items():
        values['basis'] = 'Exact material and oriented POSITION, unique triangle' if g == GROUPS[0] else 'Exact material/POSITION, duplicates selected by exact numeric NORMAL'
        values['independent_normal_evidence'] = g == GROUPS[0]
        values['interpretation'] = 'Measured after POSITION-only pairing' if g == GROUPS[0] else 'Equality is a pairing condition; not independent NORMAL validation'
    uv_total = uv.field_comparison(np.concatenate(all_fuv), np.concatenate(all_guv))
    diagnosis = {'status': 'DIAGNOSIS_ONLY_NOT_ACCEPTANCE',
                 'scope': {'measurement': 'fresh_run01', 'objects': len(targets), 'original_loops': loop_count,
                           'triangles': triangle_count, 'expanded_triangle_corners': triangle_count * 3,
                           'normal_component_occurrences': triangle_count * 9, 'uv_component_occurrences': triangle_count * 6,
                           'occurrence_warning': 'Expanded corners/components may repeat the same raw loop; not independent loop or vertex counts'},
                 'preserved_qualification': preserved_qualification(cfg),
                 'correspondence': {'legacy_record_status': prior['correspondence'],
                                    'position_only_triangles': groups[GROUPS[0]]['triangles'],
                                    'normal_refined_triangles': groups[GROUPS[1]]['triangles'],
                                    'unresolved_groups': unresolved_all, 'uv_used_for_pairing': False},
                 'converted_glb_transport': groups,
                 'attribute_binding': {'uv': uv_total,
                                       'glb_uv_exact_run03_all_ten': all(b['attribute_binding']['glb_vs_run03_signature_equal']['TEXCOORD_0'] for t in targets for b in t['buckets']),
                                       'formal_signed_zero_gate': prior['signed_zero_comparison']['status'],
                                       'full_attribute_fidelity': 'NOT_ESTABLISHED'},
                 'targets': targets, 'direction_acceptance_limit': None,
                 'limits': ['Fresh raw does not recover missing historical raw; old raw-length inference remains conditional.',
                            'Native direction correctness, non-unit magnitude eligibility, UV cause, tangent/shader/render equivalence and all remaining vehicle meshes remain unqualified.',
                            'No aggregate normal PASS, new angle gate, epsilon change or acceptance result is generated.',
                            'Same-corner squared-error decomposition is explanatory; maxima from different corners are never combined.']}
    after = [replay.file_record(p) for p in paths]
    assert before == after, 'Input bytes changed'
    return {'schema': 'maz-normal-classification-v1', 'normal_diagnosis': diagnosis,
            'runtime': replay.runtime_identity(), 'cpu_affinity': sorted(os.sched_getaffinity(0)),
            'input_records_before': before, 'input_records_after': after, 'inputs_unchanged': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.parent == HERE / 'attempt-02' and not output.exists(), 'New file in attempt-02 only'
    report = build_report()
    replay.write_json(output, report)
    print(json.dumps({'status': report['normal_diagnosis']['status'], 'output': str(output),
                      'inputs_unchanged': report['inputs_unchanged'], 'scope': report['normal_diagnosis']['scope']}))


if __name__ == '__main__':
    main()
