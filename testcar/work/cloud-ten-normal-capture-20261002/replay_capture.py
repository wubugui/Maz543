"""Pure numerical replay of fresh ten-target data; never starts Blender."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def file_record(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def write_json(path, value, compact=False):
    text = json.dumps(value, ensure_ascii=False, allow_nan=False,
                      indent=None if compact else 2,
                      separators=(',', ':') if compact else None) + '\n'
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(text)


def pack_array(values, dtype):
    a = np.ascontiguousarray(values, dtype=dtype)
    assert np.isfinite(a).all()
    return {'dtype': a.dtype.str, 'shape': list(a.shape),
            'buffer_bytes': a.nbytes, 'buffer_sha256': hashlib.sha256(a.tobytes()).hexdigest(),
            'values': a.tolist()}


def unpack_array(record):
    assert record['dtype'] in ('<f4', '<i4')
    a = np.asarray(record['values'], dtype=record['dtype'])
    assert list(a.shape) == record['shape'] and a.nbytes == record['buffer_bytes']
    assert np.isfinite(a).all() and hashlib.sha256(a.tobytes()).hexdigest() == record['buffer_sha256']
    return a


def load_decoder(path):
    # This pinned module has no CLI, bpy dependency, writes, or action entry point.
    spec = importlib.util.spec_from_file_location('pinned_ten_capture_decoder', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_identity():
    return {'python_version': sys.version, 'numpy_version': np.__version__,
            'numpy_file': str(Path(np.__file__).resolve())}


def yup(values):
    values = values.copy()
    values[:, [1, 2]] = values[:, [2, 1]]
    values[:, 2] *= -1
    return values


def conversion(raw):
    # Exact export_native.py:448-455 dtype and operation order, BEFORE yup.
    rounded = np.round(raw, 4)
    converted = rounded.copy()
    lengths = np.linalg.norm(converted, axis=1, keepdims=True)
    np.divide(converted, lengths, out=converted, where=lengths != 0)
    zero = ~converted.any(axis=1)
    converted[zero, 2] = 1
    error = np.linalg.norm(converted.astype(np.float64) - raw, axis=1)
    return rounded, converted, zero, error


def attributes_and_legacy(record, decoder):
    a = {name: unpack_array(value) for name, value in record['arrays'].items()}
    raw, coords = a['raw_normals_native'], yup(a['position_native'])
    loops, triangles, material_indices = a['loop_vertex'], a['triangle_loop'], a['triangle_material']
    assert raw.shape == (len(loops), 3) and coords.shape[1] == 3
    assert loops.ndim == 1 and triangles.ndim == 2 and triangles.shape[1] == 3
    assert material_indices.shape == (len(triangles),)
    assert loops.size and 0 <= loops.min() <= loops.max() < len(coords)
    assert triangles.size and 0 <= triangles.min() <= triangles.max() < len(loops)
    assert material_indices.min() >= 0
    rounded, converted, zero, error = conversion(raw)
    attrs = {'POSITION': coords[loops], 'NORMAL': yup(converted)}
    uv_rows = []
    for i, uv in enumerate(record['uv_layers']):
        values = unpack_array(uv['native_values'])
        assert values.shape == (len(loops), 2)
        if record['uv_active_present']:
            values = values.copy()
            values[:, 1] *= -1
            values[:, 1] += 1
            attrs['TEXCOORD_' + str(i)] = values
            uv_rows.append({k: uv[k] for k in ('index', 'name', 'active', 'active_render')})
    parts = material_parts(attrs, triangles, material_indices, record['evaluated_material_slots'], decoder)
    old = {
        'native_mesh_name': record['native_mesh_name'], 'vertices': len(coords), 'loops': len(loops),
        'parts': parts, 'triangles': len(triangles), 'uv_layers': uv_rows,
        'bounds': [coords[loops[triangles.reshape(-1)]].min(axis=0).tolist(),
                   coords[loops[triangles.reshape(-1)]].max(axis=0).tolist()] if len(triangles) else None,
        'raw_normal_zero_count': int((~raw.any(axis=1)).sum()),
        'rounded_normal_zero_count': int(zero.sum()),
        'raw_to_official_normal_max_vector_error': float(error.max(initial=0)),
        'raw_to_official_normal_max_nonzero_error': float(error[~zero].max(initial=0)),
        'normal_rule': 'float32 round4, normalize, replace exact0 with native+Z, swizzle(x,z,-y)',
        'loose_edges_omitted': record['loose_edges_omitted'],
        'unused_vertices_omitted': len(set(range(len(coords))) - set(map(int, loops))),
        'tangents': 'Explicitly omitted; native/generated tangent equivalence remains unqualified'}
    return a, attrs, old, (rounded, converted, zero, error)


def material_parts(attrs, triangles, material_indices, slots, decoder):
    parts = []
    for slot in np.unique(material_indices):
        name = slots[int(slot)] if int(slot) < len(slots) else slots[-1] if slots else None
        parts.append({'material_name': name, 'source_material_slot': int(slot),
                      'signature': decoder.oriented_signature(attrs, triangles[material_indices == slot].reshape(-1))})
    return parts


def canonical_corner_attributes(attrs):
    result = {key: value.copy() for key, value in attrs.items()}
    changed = {}
    for name, a in result.items():
        if name == 'NORMAL' or (name.startswith('TEXCOORD_') and name[9:].isdigit()):
            changed[name] = int(((a == 0) & np.signbit(a)).sum())
            a[a == 0] = np.float32(0)
    assert result['POSITION'].tobytes() == attrs['POSITION'].tobytes()
    assert all(np.array_equal(result[k], attrs[k]) for k in attrs)
    return result, changed


def statistics(a, transformed):
    raw = a['raw_normals_native']
    rounded, converted, zero, error = transformed
    raw64, converted64 = raw.astype(np.float64), converted.astype(np.float64)
    lengths = np.linalg.norm(raw64, axis=1)
    converted_lengths = np.linalg.norm(converted64, axis=1)
    perturbation = np.linalg.norm(rounded.astype(np.float64) - raw64, axis=1)
    valid = (lengths > 0) & (converted_lengths > 0) & ~zero
    direction_error = np.zeros(len(raw))
    angle = np.zeros(len(raw))
    raw_direction = raw64[valid] / lengths[valid, None]
    converted_direction = converted64[valid] / converted_lengths[valid, None]
    direction_error[valid] = np.linalg.norm(raw_direction - converted_direction, axis=1)
    # atan2(cross,dot) behaves well for very small direction differences.
    angle[valid] = np.degrees(np.arctan2(np.linalg.norm(np.cross(raw_direction, converted_direction), axis=1),
                                        np.einsum('ij,ij->i', raw_direction, converted_direction)))
    used = np.zeros(len(raw), dtype=bool)
    used[a['triangle_loop'].reshape(-1)] = True

    def summary(values, mask=None):
        values = values if mask is None else values[mask]
        if not values.size:
            return {'count': 0}
        return {'count': len(values), 'min': float(values.min()), 'max': float(values.max()),
                'mean': float(values.mean()), 'p50': float(np.quantile(values, .5)),
                'p95': float(np.quantile(values, .95)), 'p99': float(np.quantile(values, .99))}

    def corner(index):
        index = int(index)
        memberships = np.argwhere(a['triangle_loop'] == index)
        return {'loop_index': index, 'vertex_index': int(a['loop_vertex'][index]),
                'position_native': a['position_native'][a['loop_vertex'][index]].tolist(),
                'raw_normal_native': raw[index].tolist(), 'rounded_normal_native': rounded[index].tolist(),
                'converted_normal_native': converted[index].tolist(), 'raw_length': float(lengths[index]),
                'converted_length': float(converted_lengths[index]),
                'round4_vector_perturbation': float(perturbation[index]),
                'raw_to_reproduced_conversion_vector_error': float(error[index]),
                'direction_vector_error': float(direction_error[index]) if valid[index] else None,
                'direction_angle_degrees': float(angle[index]) if valid[index] else None,
                'direction_is_defined_nonzero': bool(valid[index]),
                'used_by_triangle': bool(used[index]),
                'triangle_memberships': [{'triangle_index': int(t), 'corner_in_triangle': int(c),
                                          'material_slot': int(a['triangle_material'][t])} for t, c in memberships]}

    worst = {'conversion_vector_error': corner(error.argmax()),
             'round4_perturbation': corner(perturbation.argmax()),
             'raw_length_minimum': corner(lengths.argmin()), 'raw_length_maximum': corner(lengths.argmax()),
             'raw_length_distance_from_unit': corner(np.abs(lengths - 1).argmax())}
    if valid.any():
        indices = np.flatnonzero(valid)
        worst['direction_vector_error'] = corner(indices[direction_error[valid].argmax()])
        worst['direction_angle_degrees'] = corner(indices[angle[valid].argmax()])
    return {'measurement': 'Fresh read-only raw vectors, not recovered historical raw bytes',
            'conversion_metric': 'Native raw versus reproduced float32 round4/normalize/zero replacement before yup; not directly raw versus GLB',
            'raw_length': summary(lengths), 'round4_vector_perturbation': summary(perturbation),
            'conversion_vector_error': summary(error), 'conversion_vector_error_triangle_used': summary(error, used),
            'direction_vector_error': summary(direction_error, valid), 'direction_angle_degrees': summary(angle, valid),
            'direction_excluded_count': int((~valid).sum()), 'triangle_used_loops': int(used.sum()),
            'unused_loops': int((~used).sum()), 'raw_length_below_one': int((lengths < 1).sum()),
            'raw_length_above_one': int((lengths > 1).sum()),
            'unchanged_nonzero_conversion_error_limit': 2e-4,
            'nonzero_conversion_error_exceeding_limit_count': int((error[~zero] > 2e-4).sum()), 'worst_corners': worst}


def part_key(part):
    return json.dumps([part['material_name'], part['signature']], sort_keys=True, separators=(',', ':'))


def decode_target(asset, name, decoder):
    nodes = [n for n in asset.j.get('nodes', []) if n.get('name') == name]
    assert len(nodes) == 1 and 'mesh' in nodes[0]
    node = nodes[0]
    assert 'skin' not in node and not node.get('weights')
    mesh = asset.item('meshes', node['mesh'])
    assert not mesh.get('weights')
    parts, positions = [], []
    for primitive in mesh['primitives']:
        assert primitive.get('mode', 4) == 4 and 'indices' in primitive and not primitive.get('targets')
        attrs = {}
        for semantic, index in primitive['attributes'].items():
            a, meta = asset.accessor(index)
            width = 3 if semantic in ('POSITION', 'NORMAL') else 2 if semantic.startswith('TEXCOORD_') and semantic[9:].isdigit() else None
            assert width is not None and a.shape[1] == width and meta['componentType'] == 5126 and not meta.get('normalized', False)
            attrs[semantic] = a
        assert 'POSITION' in attrs and 'NORMAL' in attrs
        ix, meta = asset.accessor(primitive['indices'])
        assert meta['type'] == 'SCALAR' and meta['componentType'] in (5121, 5123, 5125) and not meta.get('normalized', False)
        material = asset.item('materials', primitive['material']) if 'material' in primitive else None
        parts.append({'material_name': material.get('name') if material else None,
                      'signature': decoder.oriented_signature(attrs, ix.reshape(-1))})
        positions.append(attrs['POSITION'])
    assert parts
    return {'node_mesh_index': node['mesh'], 'parts': parts,
            'bounds': [np.minimum.reduce([p.min(axis=0) for p in positions]).tolist(),
                       np.maximum.reduce([p.max(axis=0) for p in positions]).tolist()]}


def analyze(capture_dir, cfg, stage=lambda *args: None):
    assert runtime_identity() == cfg['runtime'], 'Replay requires the pinned official Python/NumPy runtime; a host-runtime difference is not source drift'
    for row in cfg['inputs'].values():
        assert file_record(row['path']) == row, row['path']
    decoder = load_decoder(cfg['inputs']['decoder']['path'])
    references = json.loads(Path(cfg['inputs']['references']['path']).read_text())
    rows, prepared = [], []
    for target in cfg['targets']:
        name, ref_id = target['object'], target['reference_mesh_id']
        stage('REPLAY_OLD_REFERENCE', name)
        record = json.loads((Path(capture_dir) / (name + '.json')).read_text())
        assert record['object'] == name and record['reference_mesh_id'] == ref_id
        assert record['runtime'] == cfg['runtime']
        a, attrs, fresh, transformed = attributes_and_legacy(record, decoder)
        assert references['nodes'][name] == ref_id
        expected = references['meshes'][ref_id]
        differences = [key for key in sorted(set(fresh) | set(expected)) if fresh.get(key) != expected.get(key)]
        material_differences = [key for key, val in record['materials'].items() if references['materials'].get(key) != val]
        matches = not differences and not material_differences
        rows.append({'object': name, 'reference_mesh_id': ref_id,
                     'correspondence': 'FRESH_CONVERTED_RECORD_MATCHES_RUN03' if matches else 'FRESH_NOT_CORRESPONDING_RUN03',
                     'differing_fields': differences, 'differing_material_records': material_differences,
                     'fresh_legacy_record': fresh, 'run03_record': expected, 'statistics': statistics(a, transformed)})
        prepared.append((record, a, attrs))
    matched = all(row['correspondence'] == 'FRESH_CONVERTED_RECORD_MATCHES_RUN03' for row in rows)
    report = {'schema': 'maz-fresh-ten-normal-replay-v1',
              'runtime': runtime_identity(),
              'correspondence': 'TEN_FRESH_CONVERTED_RECORDS_MATCH_RUN03' if matched else 'FRESH_NOT_CORRESPONDING_RUN03',
              'targets': rows, 'signed_zero_comparison': {'status': 'NOT_RUN_OLD_REFERENCE_MISMATCH'},
              'limits': cfg['limits'], 'unchanged_qualification': cfg['unchanged_qualification']}
    if matched:
        stage('DECODE_EXISTING_GLB_TEN_TARGETS')
        asset = decoder._GLB(Path(cfg['inputs']['glb']['path']).read_bytes())
        results = []
        for row, (record, a, attrs) in zip(rows, prepared):
            stage('COMPARE_CANONICAL_CORNER_ZERO', row['object'])
            canonical, changed = canonical_corner_attributes(attrs)
            expected_parts = material_parts(canonical, a['triangle_loop'], a['triangle_material'], record['evaluated_material_slots'], decoder)
            actual = decode_target(asset, row['object'], decoder)
            counts = Counter(part_key(p) for p in expected_parts) == Counter(part_key(p) for p in actual['parts'])
            bounds_match = actual['bounds'] == row['fresh_legacy_record']['bounds']
            results.append({'object': row['object'], 'status': 'MATCH' if counts and bounds_match else 'MISMATCH',
                            'canonicalized_negative_zero_components': changed,
                            'position_bytes_unchanged': True, 'numeric_attribute_change': 0,
                            'expected_parts': expected_parts, 'decoded': actual,
                            'material_aware_oriented_signatures_match': counts, 'bounds_match': bounds_match})
        report['signed_zero_comparison'] = {'status': 'TEN_MATCH' if all(r['status'] == 'MATCH' for r in results) else 'MISMATCH',
                                           'targets': results, 'coverage': 'These ten targets only; no conclusion for other 2364 unique meshes'}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New report path, never overwrite evidence')
    args = parser.parse_args()
    cfg = json.loads((HERE / 'capture.json').read_text())
    report = analyze(args.capture_dir, cfg)
    write_json(args.output, report)
    print(report['correspondence'], report['signed_zero_comparison']['status'])


if __name__ == '__main__':
    main()
