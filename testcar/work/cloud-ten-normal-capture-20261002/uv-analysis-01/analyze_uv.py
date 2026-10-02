"""Read-only saved-array diagnosis; no Blender or formal signed-zero gate.

Use the Python pinned in ../capture.json. Output must be a new file here.
Triangle correspondence uses material and exact oriented POSITION bytes; only
duplicate POSITION groups may be refined by exact numeric NORMAL equality.
UV is never used to choose a pairing. All unresolved multiplicities stay open.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
os.environ['OPENBLAS_NUM_THREADS'] = '2'
os.environ['OMP_NUM_THREADS'] = '2'
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import replay_capture as replay


def triangle_groups(attrs, triangles):
    groups = defaultdict(list)
    for index, corners in enumerate(triangles):
        position = attrs['POSITION'][corners]
        rotations = [np.roll(position, -k, axis=0).tobytes() for k in range(3)]
        key = min(rotations)
        turns = [k for k, b in enumerate(rotations) if b == key]
        groups[key].append({'triangle': index, 'corners': corners,
                            'rotation': turns[0], 'rotation_unique': len(turns) == 1})
    return groups


def values(attrs, triangle, semantic):
    return np.roll(attrs[semantic][triangle['corners']], -triangle['rotation'], axis=0)


def ordered_bits(values):
    bits = np.ascontiguousarray(values, dtype='<f4').view('<u4').astype(np.int64)
    return np.where(bits & 0x80000000, 0xffffffff - bits, bits + 0x80000000)


def field_comparison(fresh, actual):
    difference = fresh.astype(np.float64) - actual.astype(np.float64)
    byte_different = fresh.view('<u4') != actual.view('<u4')
    numeric_different = fresh != actual
    ulp = np.abs(ordered_bits(fresh) - ordered_bits(actual))
    ulp[~numeric_different] = 0  # Zero signs are reported separately, never rewritten.
    return {'components': fresh.size,
            'byte_different_components': int(byte_different.sum()),
            'numeric_different_components': int(numeric_different.sum()),
            'signed_zero_only_components': int((byte_different & ~numeric_different).sum()),
            'max_absolute_difference': float(np.abs(difference).max(initial=0)),
            'max_ulp_distance': int(ulp.max(initial=0)),
            'nonzero_ulp_histogram': {str(int(k)): int(v) for k, v in
                                      zip(*np.unique(ulp[numeric_different], return_counts=True))},
            'fresh_negative_zero_components': int(((fresh == 0) & np.signbit(fresh)).sum()),
            'glb_negative_zero_components': int(((actual == 0) & np.signbit(actual)).sum())}


def compare_bucket(fattrs, ftri, gattrs, gtri):
    fg, gg = triangle_groups(fattrs, ftri), triangle_groups(gattrs, gtri)
    pairs, unresolved, refinement = [], [], 0
    for key in sorted(set(fg) | set(gg)):
        left, right = fg.get(key, []), gg.get(key, [])
        if len(left) != len(right) or not left or any(not t['rotation_unique'] for t in left + right):
            unresolved.append({'position_key_sha256': hashlib.sha256(key).hexdigest(),
                               'fresh_triangles': len(left), 'glb_triangles': len(right),
                               'reason': 'position multiplicity or cyclic rotation ambiguity'})
            continue
        if len(left) == 1:
            pairs.append((left[0], right[0], 'POSITION_unique'))
            continue
        # No UV or arbitrary storage-order pairing. Require a uniquely bijective
        # exact numeric NORMAL relation; signed zero is equal numerically here.
        matches = [[j for j, b in enumerate(right)
                    if np.array_equal(values(fattrs, a, 'NORMAL'), values(gattrs, b, 'NORMAL'))]
                   for a in left]
        if all(len(m) == 1 for m in matches) and len({m[0] for m in matches}) == len(right):
            pairs.extend((a, right[m[0]], 'POSITION_then_exact_numeric_NORMAL')
                         for a, m in zip(left, matches))
            refinement += len(left)
        else:
            unresolved.append({'position_key_sha256': hashlib.sha256(key).hexdigest(),
                               'fresh_triangles': len(left), 'glb_triangles': len(right),
                               'reason': 'exact numeric NORMAL does not uniquely resolve duplicates'})
    assert pairs
    fu = np.asarray([values(fattrs, a, 'TEXCOORD_0') for a, _, _ in pairs])
    gu = np.asarray([values(gattrs, b, 'TEXCOORD_0') for _, b, _ in pairs])
    fn = np.asarray([values(fattrs, a, 'NORMAL') for a, _, _ in pairs])
    gn = np.asarray([values(gattrs, b, 'NORMAL') for _, b, _ in pairs])
    diff = fu.astype(np.float64) - gu.astype(np.float64)
    mismatched = np.argwhere(fu != gu)
    sample_indices = [tuple(map(int, x)) for x in mismatched[:4]]
    if mismatched.size:
        worst = tuple(map(int, np.unravel_index(np.abs(diff).argmax(), diff.shape)))
        if worst not in sample_indices:
            sample_indices.append(worst)
    samples = []
    for ti, corner, axis in sample_indices:
        a, b, basis = pairs[ti]
        fcorner, gcorner = (corner + a['rotation']) % 3, (corner + b['rotation']) % 3
        samples.append({'fresh_triangle_in_bucket': a['triangle'], 'glb_triangle_in_primitive': b['triangle'],
                        'fresh_loop_index': int(a['corners'][fcorner]),
                        'glb_vertex_index': int(b['corners'][gcorner]), 'axis': 'UV'[axis],
                        'correspondence_basis': basis,
                        'position': fattrs['POSITION'][a['corners'][fcorner]].tolist(),
                        'fresh_uv': fu[ti, corner].tolist(), 'glb_uv': gu[ti, corner].tolist(),
                        'fresh_component_bits_hex': hex(int(fu.view('<u4')[ti, corner, axis])),
                        'glb_component_bits_hex': hex(int(gu.view('<u4')[ti, corner, axis])),
                        'fresh_minus_glb': diff[ti, corner].tolist()})
    # Counterfactual diagnostics only: never choose/apply a transform or feed
    # these values to the legacy gate. Both directions of difference disprove a
    # single real additive offset; explicit flip/swap are tested as exact bits.
    swaps = fu[:, :, ::-1].copy()
    vflip = fu.copy()
    vflip[:, :, 1] *= -1
    vflip[:, :, 1] += 1
    return {'fresh_triangles': len(ftri), 'glb_triangles': len(gtri),
            'position_group_sets_identical': set(fg) == set(gg),
            'position_multiplicities_identical': {k: len(v) for k, v in fg.items()} == {k: len(v) for k, v in gg.items()},
            'position_duplicate_groups': sum(len(v) > 1 for v in fg.values()),
            'position_unique_pairs': len(pairs) - refinement,
            'pairs_resolved_by_exact_numeric_normal': refinement,
            'matched_triangles': len(pairs), 'unresolved_groups': unresolved,
            'uv': field_comparison(fu, gu),
            'uv_by_axis': {axis: field_comparison(np.ascontiguousarray(fu[:, :, i]),
                                                 np.ascontiguousarray(gu[:, :, i])) for i, axis in enumerate('UV')},
            'uv_numeric_different_corners': int(np.any(fu != gu, axis=2).sum()),
            'uv_numeric_different_triangles': int(np.any(fu != gu, axis=(1, 2)).sum()),
            'uv_difference_ranges': [[float(diff[:, :, i].min()), float(diff[:, :, i].max())] for i in range(2)],
            'single_constant_real_offset': [bool(np.all(diff[:, :, i] == diff[0, 0, i])) for i in range(2)],
            'counterfactual_v_flip_exact_numeric_match': bool(np.array_equal(vflip, gu)),
            'counterfactual_uv_swap_exact_numeric_match': bool(np.array_equal(swaps, gu)),
            'paired_normal': field_comparison(fn, gn), 'examples': samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.parent == HERE and not output.exists(), 'New output inside uv-analysis-01 only'
    cfg = json.loads((BASE / 'capture.json').read_text())
    assert replay.runtime_identity() == cfg['runtime'], 'Use the fixed official bundled Python/NumPy'
    source_dir = Path(cfg['inputs']['official_nodes']['path']).parent
    extra = [BASE / 'capture.json', BASE / 'capture_native.py', BASE / 'replay_capture.py',
             BASE / 'run-01' / 'replay-report.json',
             Path(cfg['inputs']['references']['path']).with_name('native-report.json'),
             source_dir / 'mesh.py', Path(__file__)]
    raw_paths = [BASE / 'run-01' / (t['object'] + '.json') for t in cfg['targets']]
    fixed = {k: replay.file_record(v['path']) for k, v in cfg['inputs'].items()}
    assert fixed == cfg['inputs']
    additional = [replay.file_record(p) for p in extra + raw_paths]
    decoder = replay.load_decoder(cfg['inputs']['decoder']['path'])
    asset = decoder._GLB(Path(cfg['inputs']['glb']['path']).read_bytes())
    refs = json.loads(Path(cfg['inputs']['references']['path']).read_text())
    prior = json.loads((BASE / 'run-01' / 'replay-report.json').read_text())
    results = []
    for target in cfg['targets']:
        name, ref_id = target['object'], target['reference_mesh_id']
        record = json.loads((BASE / 'run-01' / (name + '.json')).read_text())
        assert record['runtime'] == cfg['runtime']
        a, attrs, fresh, _ = replay.attributes_and_legacy(record, decoder)
        expected = refs['meshes'][ref_id]
        saved = next(r for r in prior['targets'] if r['object'] == name)
        assert fresh == saved['fresh_legacy_record'] and expected == saved['run03_record']
        nodes = [(i, n) for i, n in enumerate(asset.j['nodes']) if n.get('name') == name]
        assert len(nodes) == 1 and refs['nodes'][name] == ref_id
        node_index, node = nodes[0]
        primitives = asset.j['meshes'][node['mesh']]['primitives']
        slots = record['evaluated_material_slots']
        buckets = []
        used_slots = set()
        for pi, primitive in enumerate(primitives):
            material_name = asset.j['materials'][primitive['material']]['name']
            candidates = [i for i in np.unique(a['triangle_material']) if slots[int(i)] == material_name]
            assert len(candidates) == 1, 'Ambiguous material slots must not be paired'
            slot = int(candidates[0]); assert slot not in used_slots; used_slots.add(slot)
            gat = {k: asset.accessor(v)[0] for k, v in primitive['attributes'].items()}
            assert set(gat) == set(attrs) == {'POSITION', 'NORMAL', 'TEXCOORD_0'}
            gtri = asset.accessor(primitive['indices'])[0].reshape(-1, 3)
            ftri = a['triangle_loop'][a['triangle_material'] == slot]
            actual_signature = decoder.oriented_signature(gat, gtri)
            oldpart = next(p for p in expected['parts'] if p['source_material_slot'] == slot)
            bucket = compare_bucket(attrs, ftri, gat, gtri)
            bucket.update({'material_name': material_name, 'source_material_slot': slot,
                           'glb_primitive': pi,
                           'run03_signatures': oldpart['signature']['signatures'],
                           'glb_signatures': actual_signature['signatures'],
                           'fresh_signatures': next(p for p in fresh['parts'] if p['source_material_slot'] == slot)['signature']['signatures'],
                           'glb_vs_run03_signature_equal': {k: v == oldpart['signature']['signatures'][k]
                                                          for k, v in actual_signature['signatures'].items()}})
            buckets.append(bucket)
        assert used_slots == set(map(int, np.unique(a['triangle_material'])))
        results.append({'object': name, 'reference_mesh_id': ref_id, 'glb_node_index': node_index,
                        'glb_mesh_index': node['mesh'], 'legacy_correspondence': saved['correspondence'],
                        'buckets': buckets})
    guards = (fixed == {k: replay.file_record(v['path']) for k, v in cfg['inputs'].items()}
              and additional == [replay.file_record(p) for p in extra + raw_paths])
    assert guards
    report = {'schema': 'maz-saved-ten-uv-diagnosis-v1', 'status': 'DIAGNOSIS_ONLY_NOT_ACCEPTANCE',
              'runtime': replay.runtime_identity(), 'cpu_affinity': sorted(os.sched_getaffinity(0)),
              'fixed_inputs': fixed, 'additional_inputs': additional,
              'inputs_unchanged': guards, 'targets': results,
              'formal_signed_zero_gate': 'NOT_RUN_OLD_REFERENCE_MISMATCH',
              'unchanged_qualification': cfg['unchanged_qualification'],
              'conclusion': 'Fresh evaluated UV values differ numerically from run03. No capture/replay UV conversion defect or native-UV exporter write-back was demonstrated. The cause of evaluation drift remains unproven.',
              'limits': ['No Blender, source evaluation, new export, data correction or epsilon change occurred.',
                         'Only ten saved targets and the pinned GLB are covered.',
                         'Per-semantic signatures alone do not prove joint binding. Explicit oriented POSITION pairing and exact numeric NORMAL refinement are diagnostic only.',
                         'NORMAL numeric equality intentionally treats signed zeros as numerically equal during ambiguous POSITION refinement; no attribute buffer is changed and no formal +0 validation is run.',
                         'The missing historical raw normals/UV arrays remain missing. Fresh raw is not historical raw.',
                         'BEVEL interpolation, validation-triggered recomputation, and evaluation/cache/order effects remain hypotheses. No unique model or UV repair is justified.']}
    replay.write_json(output, report)
    print(json.dumps({'output': str(output), 'inputs_unchanged': guards,
                      'matched_triangles': sum(b['matched_triangles'] for r in results for b in r['buckets']),
                      'unresolved_groups': sum(len(b['unresolved_groups']) for r in results for b in r['buckets']),
                      'uv_numeric_different_components': sum(b['uv']['numeric_different_components'] for r in results for b in r['buckets']),
                      'uv_max_absolute_difference': max(b['uv']['max_absolute_difference'] for r in results for b in r['buckets'])}))


if __name__ == '__main__':
    main()
