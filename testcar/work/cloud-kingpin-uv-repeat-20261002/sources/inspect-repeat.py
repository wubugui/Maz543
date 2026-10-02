"""Observe five existing meshes. Never alter modifiers, geometry, or materials."""
import argparse
import ast
import hashlib
import json
import math
import sys
import time
import traceback
from pathlib import Path

import bpy
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--inputs', required=True)
p.add_argument('--output', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
inputs = Path(a.inputs)
I = json.loads(inputs.read_bytes())
out = Path(a.output)
sys.path.insert(0, str(inputs.parent))
import float32_compare as fc

sha = lambda b: hashlib.sha256(b).hexdigest()
issues = []
report = {'status': 'DIAGNOSTIC_RUNNING', 'source_sha256': I['source_sha256'],
          'saved_blend': False, 'rendered': False, 'exported': False,
          'manual_object_transform_writes': False, 'frame_explicitly_evaluated': 0,
          'issues': issues, 'comparisons': [], 'objects': {},
          'all_16_whole_vehicle_gates': 'OPEN'}


def write(name, value):
    with (out / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=True, allow_nan=False)
        f.write('\n')


def fail(message):
    raise ValueError(message)


def read_array(sequence, field, width, dtype):
    values = np.full(len(sequence) * width, np.nan if dtype == '<f4' else 0, dtype=dtype)
    sequence.foreach_get(field, values)
    return values.reshape(len(sequence), width).copy()


def array_summary(values):
    result = {'shape': list(values.shape), 'dtype': values.dtype.str,
              'bytes': values.nbytes, 'sha256': sha(values.tobytes())}
    if values.dtype.kind == 'f':
        result.update(nonfinite=int((~np.isfinite(values)).sum()),
                      negative_zero=int(((values == 0) & np.signbit(values)).sum()))
    return result


def uv_read(mesh):
    layers = {}
    for layer in mesh.uv_layers:
        values = read_array(layer.uv, 'vector', 2, '<f4')
        direct = np.asarray([tuple(x.vector) for x in layer.uv], dtype='<f4').reshape(-1, 2)
        exact = values.tobytes() == direct.tobytes()
        if not exact:
            issues.append({'kind': 'RNA_UV_GETTERS_DISAGREE', 'mesh': mesh.name, 'layer': layer.name})
        if len(values) != len(mesh.loops):
            fail('UV layer loop count differs from mesh loops')
        layers[layer.name] = {'array': values, 'meta': {'active_render': layer.active_render,
            'active_clone': layer.active_clone, 'direct_RNA_same_float32_bits': exact}}
    return layers


def capture_mesh(mesh):
    # First observation happens before this function requests triangulation or
    # normal fields. Evaluated Bevel/WeightedNormal processing already happened.
    uv0 = uv_read(mesh)
    floats = {'positions': read_array(mesh.vertices, 'co', 3, '<f4')}
    integers = {}
    for key, seq, field, width in [
            ('edge_vertices', mesh.edges, 'vertices', 2),
            ('loop_vertex', mesh.loops, 'vertex_index', 1),
            ('loop_edge', mesh.loops, 'edge_index', 1),
            ('polygon_loop_start', mesh.polygons, 'loop_start', 1),
            ('polygon_loop_total', mesh.polygons, 'loop_total', 1),
            ('polygon_material_index', mesh.polygons, 'material_index', 1)]:
        integers[key] = read_array(seq, field, width, '<i4')
    flags = {
        'edge_sharp': read_array(mesh.edges, 'use_edge_sharp', 1, '?'),
        'edge_seam': read_array(mesh.edges, 'use_seam', 1, '?'),
        'polygon_smooth': read_array(mesh.polygons, 'use_smooth', 1, '?')}
    mesh.calc_loop_triangles()
    for key, field, width in [('triangle_vertices', 'vertices', 3),
                               ('triangle_loops', 'loops', 3),
                               ('triangle_polygon', 'polygon_index', 1)]:
        integers[key] = read_array(mesh.loop_triangles, field, width, '<i4')
    uv1 = uv_read(mesh)
    floats['vertex_normals'] = read_array(mesh.vertices, 'normal', 3, '<f4')
    floats['polygon_normals'] = read_array(mesh.polygons, 'normal', 3, '<f4')
    floats['corner_normals'] = read_array(mesh.corner_normals, 'vector', 3, '<f4')
    if len(floats['corner_normals']) != len(mesh.loops):
        fail('Actual corner_normals do not cover every loop; no synthetic fallback')
    uv2 = uv_read(mesh)
    loop_poly = np.full(len(mesh.loops), -1, dtype='<i4')
    for index, (start, count) in enumerate(zip(integers['polygon_loop_start'][:, 0], integers['polygon_loop_total'][:, 0])):
        if start < 0 or count < 0 or start + count > len(loop_poly) or (loop_poly[start:start + count] != -1).any():
            fail('Invalid or overlapping polygon loop ranges')
        loop_poly[start:start + count] = index
    if (loop_poly < 0).any():
        fail('Unowned loops')
    identities = [{'loop': i, 'vertex': int(integers['loop_vertex'][i, 0]),
                   'edge': int(integers['loop_edge'][i, 0]), 'polygon': int(loop_poly[i])}
                  for i in range(len(mesh.loops))]
    meta = {'vertices': len(mesh.vertices), 'edges': len(mesh.edges), 'loops': len(mesh.loops),
            'polygons': len(mesh.polygons), 'triangles': len(mesh.loop_triangles),
            'uv_names_ordered': list(uv0), 'active_uv': mesh.uv_layers.active.name if mesh.uv_layers.active else None,
            'materials': [m.name if m else None for m in mesh.materials],
            'has_custom_normals': mesh.has_custom_normals, 'normals_domain': mesh.normals_domain,
            'sharp_attribute_presence': {n: None if mesh.attributes.get(n) is None else
                {'domain': mesh.attributes[n].domain, 'type': mesh.attributes[n].data_type,
                 'elements': len(mesh.attributes[n].data)} for n in ('sharp_edge', 'sharp_face')}}
    for key, values in floats.items():
        if not np.isfinite(values).all():
            issues.append({'kind': 'NONFINITE_FLOAT_FIELD', 'mesh': mesh.name, 'field': key})
    for stage in [uv0, uv1, uv2]:
        for name, layer in stage.items():
            if not np.isfinite(layer['array']).all():
                issues.append({'kind': 'NONFINITE_UV', 'mesh': mesh.name, 'layer': name})
    return {'meta': meta, 'integers': integers, 'flags': flags, 'floats': floats,
            'uv': [uv0, uv1, uv2], 'loop_identities': identities}


def summarize(snapshot):
    return {'meta': snapshot['meta'],
            'arrays': {k: array_summary(v) for group in ('integers', 'flags', 'floats') for k, v in snapshot[group].items()},
            'uv_stages': [{name: {**layer['meta'], **array_summary(layer['array'])}
                           for name, layer in stage.items()} for stage in snapshot['uv']]}


def topology(snapshot):
    return {**{k: v.tobytes() for k, v in snapshot['integers'].items()},
            'counts': tuple(snapshot['meta'][n] for n in ('vertices', 'edges', 'loops', 'polygons', 'triangles')),
            'uv_names': tuple(snapshot['meta']['uv_names_ordered'])}


def compare_snapshots(label, before, after):
    result = {'label': label}
    try:
        fc.require_same_topology(topology(before), topology(after))
    except ValueError as exc:
        result.update(status='TOPOLOGY_MISMATCH_NO_LOOP_COMPARISON', error=str(exc))
        issues.append(result)
        return result
    result['topology_exact'] = True
    result['metadata_exact'] = before['meta'] == after['meta']
    result['flags_exact'] = {n: b.tobytes() == after['flags'][n].tobytes() for n, b in before['flags'].items()}
    fields = {}
    for name, values in before['floats'].items():
        ids = before['loop_identities'] if name == 'corner_normals' else None
        fields[name] = fc.compare(values.tobytes(), after['floats'][name].tobytes(), values.shape[1], ids)
    result['float_fields'] = fields
    result['uv_stages'] = []
    result['uv_metadata_exact'] = []
    for stage in range(3):
        result['uv_metadata_exact'].append(all(before['uv'][stage][n]['meta'] == after['uv'][stage][n]['meta'] for n in before['uv'][stage]))
        result['uv_stages'].append({n: fc.compare(before['uv'][stage][n]['array'].tobytes(),
            after['uv'][stage][n]['array'].tobytes(), 2, before['loop_identities']) for n in before['uv'][stage]})
    return result


def object_state(o):
    return {'name': o.name, 'pointer': o.as_pointer(), 'data_pointer': o.data.as_pointer(),
            'parent': o.parent.name if o.parent else None, 'world': [list(v) for v in o.matrix_world],
            'basis': [list(v) for v in o.matrix_basis], 'parent_inverse': [list(v) for v in o.matrix_parent_inverse],
            'modifiers': [rna_values(m) for m in o.modifiers], 'constraints': [rna_values(c) for c in o.constraints],
            'material_slots': appearance(o), 'hide': [o.hide_render, o.hide_viewport, o.hide_get()]}


def main():
    assert bpy.app.version == (4, 5, 13) and bpy.app.build_hash.decode() == 'daeeeca98fb0'
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    source = Path(I['source_path'])
    assert source.stat().st_size == I['source_bytes'] and sha(source.read_bytes()) == I['source_sha256']
    helper = inputs.parent / 'intake-helper-source.py'
    assert sha(helper.read_bytes()) == I['intake_helper_sha256']
    allowed = {'idref', 'value_record', 'rna_values', 'problem', 'appearance', 'node_tree_record'}
    tree = ast.parse(helper.read_bytes())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in allowed]
    assert {n.name for n in nodes} == allowed
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(helper), 'exec'), globals())
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert bpy.context.evaluated_depsgraph_get().mode == 'VIEWPORT'
    assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
    all_before = {o.name: {'pointer': o.as_pointer(), 'world': [list(v) for v in o.matrix_world]} for o in bpy.data.objects}
    assert len(all_before) == I['expected_object_count']
    selected = [bpy.data.objects[n] for n in I['objects']]
    assert all(o.type == 'MESH' for o in selected)
    states = {o.name: object_state(o) for o in selected}
    mats = {s.material.name: s.material for o in selected for s in o.material_slots if s.material}
    material_before = {n: node_tree_record(m.node_tree) for n, m in sorted(mats.items())}
    write('materials-before.json', material_before)
    report['objects_before'] = states
    report['object_count'] = len(all_before)
    print('OPENED_REPEAT_SOURCE', len(all_before), flush=True)
    raw_before = {o.name: capture_mesh(o.data) for o in selected}
    rounds = {o.name: [] for o in selected}
    for trial in range(3):
        for o in selected:
            evaluated = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
            try:
                snap = capture_mesh(mesh)
                rounds[o.name].append(snap)
            finally:
                evaluated.to_mesh_clear()
            print('REPEAT_CAPTURED', trial, o.name, flush=True)
    raw_after = {o.name: capture_mesh(o.data) for o in selected}
    comparisons = []
    for o in selected:
        n = o.name
        report['objects'][n] = {'raw_before': summarize(raw_before[n]),
            'evaluated_rounds': [summarize(s) for s in rounds[n]], 'raw_after': summarize(raw_after[n])}
        raw_comparison = compare_snapshots(n + ':raw-before-after', raw_before[n], raw_after[n])
        comparisons.append(raw_comparison)
        raw_exact = (raw_comparison.get('topology_exact', False)
            and raw_comparison.get('metadata_exact', False)
            and all(raw_comparison.get('flags_exact', {}).values())
            and all(raw_comparison.get('uv_metadata_exact', []))
            and all(c['bit_changes'] == 0 for c in raw_comparison.get('float_fields', {}).values())
            and all(c['bit_changes'] == 0 for stage in raw_comparison.get('uv_stages', []) for c in stage.values()))
        report['objects'][n]['raw_before_after_exact'] = raw_exact
        if not raw_exact:
            issues.append({'kind': 'RAW_MESH_READBACK_CHANGED', 'object': n})
        for trial in (1, 2):
            comparisons.append(compare_snapshots(n + ':round0-to-' + str(trial), rounds[n][0], rounds[n][trial]))
        for trial, snap in enumerate(rounds[n]):
            for end in (1, 2):
                comparisons.append({'label': n + ':round' + str(trial) + ':UV-initial-to-stage' + str(end),
                    'topology_scope': 'Same evaluated mesh object; no geometry writes.',
                    'UV': {layer: fc.compare(snap['uv'][0][layer]['array'].tobytes(),
                        snap['uv'][end][layer]['array'].tobytes(), 2, snap['loop_identities']) for layer in snap['uv'][0]}})
    report['comparisons'] = comparisons
    all_after = {o.name: {'pointer': o.as_pointer(), 'world': [list(v) for v in o.matrix_world]} for o in bpy.data.objects}
    material_after = {n: node_tree_record(m.node_tree) for n, m in sorted(mats.items())}
    states_after = {o.name: object_state(o) for o in selected}
    report['protection'] = {'all_object_identity_world_exact': all_before == all_after,
        'selected_object_fields_exact': states == states_after,
        'material_node_records_exact': material_before == material_after,
        'all_objects_checked': len(all_before)}
    if not all(v for k, v in report['protection'].items() if k.endswith('_exact')):
        issues.append({'kind': 'READ_ONLY_PROTECTION_MISMATCH', 'details': report['protection']})
    aggregate = {}
    for name in I['objects']:
        selected_rows = [r for r in comparisons if r['label'].startswith(name + ':round0-to-') and r.get('topology_exact')]
        uv_changes = [c for row in selected_rows for stage in row['uv_stages'] for c in stage.values()]
        normal_changes = [c for row in selected_rows for field, c in row['float_fields'].items() if field.endswith('_normals')]
        aggregate[name] = {'cross_round_comparisons': len(selected_rows),
            'uv_bit_changes_across_all_stages': sum(c['bit_changes'] for c in uv_changes),
            'uv_finite_numeric_changes_across_all_stages': sum(c['finite_numeric_changes'] for c in uv_changes),
            'uv_max_finite_absolute_delta': max((c['max_finite_absolute_delta'] for c in uv_changes), default=None),
            'uv_max_finite_ulp_distance': max((c['max_finite_ulp_distance'] for c in uv_changes), default=None),
            'normal_bit_changes_across_all_domains': sum(c['bit_changes'] for c in normal_changes),
            'normal_max_finite_absolute_delta': max((c['max_finite_absolute_delta'] for c in normal_changes), default=None),
            'counts_note': 'Counts include both round0 comparisons and every named stage/domain; not unique geometric loop counts.'}
    report['numeric_summary'] = aggregate
    reproduced = any(aggregate[n]['uv_bit_changes_across_all_stages'] for n in I['kingpins'])
    report['status'] = 'DIAGNOSTIC_INCOMPLETE' if issues else 'UV_CHANGE_REPRODUCED_NO_ACCEPTANCE' if reproduced else 'UV_CHANGE_NOT_REPRODUCED_IN_THIS_RUN'
    report['limitations'] = ['The first intake BLOCKED result is preserved regardless of reproduction here.',
        'No modifier was disabled or reconfigured; these observations do not isolate the responsible operation.',
        'Current MetricUV shader non-use is a separate recorded graph observation, not a pixel or appearance proof.',
        'No tolerance waiver, new parent-chain candidate, export, motion test, or whole-vehicle acceptance.',
        'No inference about the previous Master301 summary differences.']


started = time.monotonic()
try:
    main()
except BaseException as exc:
    report['status'] = 'DIAGNOSTIC_EXCEPTION'
    report['exception'] = type(exc).__name__ + ': ' + str(exc)
    report['traceback'] = traceback.format_exc()
finally:
    report['elapsed_seconds'] = time.monotonic() - started
    try:
        report['source_sha256_after'] = sha(Path(I['source_path']).read_bytes())
        report['source_unchanged'] = report['source_sha256_after'] == I['source_sha256']
    except Exception as exc:
        report['source_unchanged'] = False
        report['source_final_error'] = str(exc)
    if not report['source_unchanged']:
        report['status'] = 'SOURCE_UNCONFIRMED'
    write('native-report.json', report)
    print('REPEAT_TERMINAL', report['status'], flush=True)
raise SystemExit(0 if report['status'] in {'UV_CHANGE_REPRODUCED_NO_ACCEPTANCE', 'UV_CHANGE_NOT_REPRODUCED_IN_THIS_RUN'} else 1)
