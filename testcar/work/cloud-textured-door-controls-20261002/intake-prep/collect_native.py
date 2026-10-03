"""Read saved Textured doors once. No modeling entry point is imported or run."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def functions_only(path, names, namespace):
    nodes = [n for n in ast.parse(Path(path).read_bytes()).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names) and {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)  # --help exits without importing bpy or opening a file.
    import bpy
    import numpy as np
    sys.path.insert(0, str(HERE))
    from components import summarize_components

    output = args.output.resolve(strict=True)
    assert output.parent == HERE
    cfg = json.loads((HERE / 'inputs/intake.json').read_text())
    ip = {k: v['path'] for k, v in cfg['inputs'].items()}
    common = functions_only(ip['array_helper'], {'file_record', 'write_json', 'pack_array',
                              'unpack_array', 'runtime_identity'},
                            dict(Path=Path, np=np, hashlib=hashlib, json=json, sys=sys))
    write = common['write_json']
    export = functions_only(ip['legacy_export_helper'],
                            {'value', 'authored_rna', 'custom', 'tree_record', 'material_record'},
                            dict(bpy=bpy))
    mesh = functions_only(ip['mesh_protection_helper'],
                          {'require', 'as_plain', 'scalar_rna', 'array', 'mesh_signature',
                           'authored', 'animation_state', 'driver_description'},
                          dict(np=np, bpy=bpy, hashlib=hashlib, json=json))
    original = functions_only(ip['graph_common'], {'digest', 'read_only_action_helper'},
                              dict(Path=Path, ast=ast, math=math, hashlib=hashlib, json=json))
    digest = original['digest']
    action_record, legacy_issues = original['read_only_action_helper'](ip['helper'], ip['builder'], bpy)
    issues = []
    H = dict(bpy=bpy, math=math, issues=issues)
    H['problem'] = lambda owner, reason, detail=None: issues.append(
        {'owner': owner, 'reason': reason, 'detail': detail})
    functions_only(ip['helper'], {'idref', 'value_record', 'rna_values', 'curves_of'}, H)
    rna, plain = H['rna_values'], export['value']
    graph = functions_only(ip['graph_inspector'],
                           {'ident', 'rows', 'collections_and_layers', 'snapshot'},
                           dict(bpy=bpy, digest=digest))
    started = time.monotonic()
    report = {'status': 'STARTING', 'phase': cfg['phase'],
              'qualification': cfg['qualification'], 'limits': cfg['limits'],
              'raw_files': [], 'component_files': [], 'dependency_blockers': [],
              'guard_scope': 'Explicit stored fields only; no guarantee for unenumerated RNA or runtime caches'}
    before = None

    def stage(name, target=None):
        row = {'stage': name, 'target': target, 'elapsed_seconds': time.monotonic() - started,
               'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        temp = output / 'stage.json.tmp'
        temp.write_text(json.dumps(row) + '\n')
        temp.replace(output / 'stage.json')
        with (output / 'stages.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print('INTAKE_STAGE ' + json.dumps(row), flush=True)

    def custom_ui(block):
        result = {}
        for key in block.keys():
            try:
                result[key] = plain(block.id_properties_ui(key).as_dict())
            except TypeError:
                # ID/group/unsupported IDProperty types have no UI data manager.
                result[key] = {'ui_metadata': 'NOT_SUPPORTED_FOR_PROPERTY_TYPE'}
        return result

    def modifier_record(mod):
        result = {'rna': rna(mod), 'collections': {}}
        for prop in mod.bl_rna.properties:
            if prop.type != 'COLLECTION':
                continue
            values = getattr(mod, prop.identifier)
            result['collections'][prop.identifier] = [rna(v) for v in values]
            for value in values:
                nested = [p.identifier for p in value.bl_rna.properties
                          if p.type == 'COLLECTION' and len(getattr(value, p.identifier))]
                if nested:
                    issues.append({'owner': mod.name, 'reason': 'unserialized nested modifier/constraint collection',
                                   'fields': nested})
        return result

    def fcurve_record(fc, driver=False):
        result = {'rna': rna(fc), 'group': rna(fc.group) if fc.group else None,
                  'keyframes': [rna(k) for k in fc.keyframe_points],
                  'sampled_points': [rna(k) for k in fc.sampled_points],
                  'modifiers': [modifier_record(m) for m in fc.modifiers]}
        if driver:
            result['driver'] = {'rna': rna(fc.driver), 'variables': [
                {'rna': rna(v), 'targets': [rna(t) for t in v.targets]} for v in fc.driver.variables]}
        return result

    def strip_record(strip):
        return {'rna': rna(strip), 'fcurves': [fcurve_record(f) for f in strip.fcurves],
                'modifiers': [modifier_record(m) for m in strip.modifiers],
                'strips': [strip_record(s) for s in strip.strips]}

    def animation(block):
        ad = getattr(block, 'animation_data', None)
        if ad is None:
            return None
        return {'rna': rna(ad), 'action': plain(ad.action),
                'action_slot_handle': ad.action_slot_handle,
                'drivers': [fcurve_record(f, True) for f in ad.drivers],
                'nla_tracks': [{'rna': rna(t), 'strips': [strip_record(s) for s in t.strips]}
                               for t in ad.nla_tracks]}

    def action_detail(action):
        return {'rna': rna(action), 'custom': export['custom'](action), 'custom_ui': custom_ui(action),
                'fake_user': action.use_fake_user, 'legacy_key_record': action_record(action),
                'fcurves': [fcurve_record(f) for f in H['curves_of'](action)],
                'storage': 'LAYERED' if action.is_action_layered else 'LEGACY',
                'groups': [] if action.is_action_layered else [rna(g) for g in action.groups],
                'pose_markers': [rna(m) for m in getattr(action, 'pose_markers', [])],
                'slots': [rna(s) for s in action.slots],
                'layers': [{'rna': rna(layer), 'strips': [
                    {'rna': rna(s), 'channelbags': [
                        {'rna': rna(b), 'groups': [rna(g) for g in b.groups],
                         'fcurve_references': [[f.data_path, f.array_index] for f in b.fcurves]}
                        for b in getattr(s, 'channelbags', [])]}
                    for s in layer.strips]} for layer in action.layers]}

    def id_state(block):
        ov = block.override_library
        return {'id': plain(block), 'pointer_session_only': block.as_pointer(),
                'library': plain(block.library), 'is_library_indirect': block.is_library_indirect,
                'is_editable': block.is_editable, 'use_fake_user': block.use_fake_user,
                'override': None if ov is None else {'rna': rna(ov), 'properties': [
                    {'rna': rna(p), 'operations': [rna(op) for op in p.operations]}
                    for p in ov.properties]}}

    def object_detail(obj):
        return {'identity': id_state(obj), 'properties': rna(obj),
                'authored_transforms': mesh['authored'](obj), 'matrix_local': plain(obj.matrix_local),
                'custom': export['custom'](obj), 'custom_ui': custom_ui(obj),
                'animation': animation(obj), 'constraints': [modifier_record(c) for c in obj.constraints],
                'modifiers': [modifier_record(m) for m in obj.modifiers],
                'data_identity': id_state(obj.data) if obj.data else None,
                'data_animation': animation(obj.data) if obj.data else None,
                'materials': [[s.link, plain(s.material)] for s in obj.material_slots],
                'vertex_groups': [rna(g) for g in obj.vertex_groups],
                'collections': sorted(c.name for c in obj.users_collection),
                'hide_get': obj.hide_get(), 'select_get': obj.select_get(),
                'children': sorted(c.name for c in obj.children)}

    def signature(block):
        try:
            return mesh['mesh_signature'](block)
        except Exception as exc:
            row = {'mesh': block.name, 'reason': 'unsupported mesh signature field',
                   'error': type(exc).__name__ + ': ' + str(exc)}
            issues.append(row)
            return {'status': 'INCOMPLETE_NO_PRESERVATION_PASS', **row}

    def action_summary(action, field_inventories):
        # Read every enumerated key value, hash it, and retain coverage/counts.
        # The pinned, recoverable source remains the full numeric action archive.
        detail = action_detail(action)
        paths = set()
        def visit(value, prefix):
            if isinstance(value, dict):
                for key, child in value.items():
                    visit(child, prefix + '.' + key)
            elif isinstance(value, list):
                if not value:
                    paths.add(prefix + '[]')
                for child in value:
                    visit(child, prefix + '[]')
            else:
                paths.add(prefix)
        visit(detail, 'action')
        fields = sorted(paths)
        fields_key = digest(fields)
        field_inventories[fields_key] = fields
        return {'sha256': digest(detail), 'legacy_key_sha256': digest(detail['legacy_key_record']),
                'fake_user': action.use_fake_user, 'identity': plain(action),
                'read_field_inventory': fields_key,
                'counts': {'fcurves': len(detail['fcurves']),
                           'keyframes': sum(len(f['keyframes']) for f in detail['fcurves']),
                           'samples': sum(len(f['sampled_points']) for f in detail['fcurves']),
                           'slots': len(detail['slots']), 'layers': len(detail['layers'])}}

    def snapshot():
        # Reuse the prior comparison algorithm for8522 names/world/parents/actions.
        prior = graph['snapshot'](action_record)
        field_inventories = {}
        actions = {a.name: action_summary(a, field_inventories) for a in bpy.data.actions}
        return {'legacy_graph_state': prior['state'],
                'all_objects': {o.name: {'parent': o.parent.name if o.parent else None,
                                'matrices': {k: plain(getattr(o, k)) for k in
                                ('matrix_world', 'matrix_local', 'matrix_basis', 'matrix_parent_inverse')}}
                                for o in bpy.data.objects},
                'all_binding_signatures': {o.name: {'sha256': digest(animation(o)),
                    'action': plain(o.animation_data.action) if o.animation_data else None,
                    'slot_handle': o.animation_data.action_slot_handle}
                    for o in bpy.data.objects if o.animation_data is not None},
                'binding_scope': 'All objects with AnimData; all other names in all_objects have no AnimData',
                'actions': actions, 'action_read_field_inventories': field_inventories,
                'named_inventory': {n: prior['objects'][n] for n in detail_names},
                'details': {name: object_detail(bpy.data.objects[name]) for name in detail_names},
                'door_meshes': {o.name: {'identity': id_state(o.data),
                                        'signature': signature(o.data)} for o in targets},
                'door_materials': {m.name: export['material_record'](m) for m in materials}}

    def raw_geometry(obj):
        m = obj.data
        arrays = {}
        for key, seq, field, width, dtype in [
            ('position', m.vertices, 'co', 3, '<f4'), ('edges', m.edges, 'vertices', 2, '<i4'),
            ('loop_vertex', m.loops, 'vertex_index', 1, '<i4'),
            ('loop_edge', m.loops, 'edge_index', 1, '<i4'),
            ('polygon_start', m.polygons, 'loop_start', 1, '<i4'),
            ('polygon_size', m.polygons, 'loop_total', 1, '<i4'),
            ('polygon_material', m.polygons, 'material_index', 1, '<i4')]:
            arrays[key] = common['pack_array'](mesh['array'](seq, field, width, np.dtype(dtype)), dtype)
        return {'schema': 'maz-raw-door-topology-v1', 'object': obj.name, 'mesh': m.name,
                'arrays': arrays, 'matrix_world': plain(obj.matrix_world),
                'geometry_scope': 'Original saved mesh; no evaluation or triangulation mutation',
                'signature': signature(m)}

    try:
        stage('VERIFY_PINNED_INPUTS')
        assert bpy.app.version == tuple(cfg['expected']['blender_version'])
        assert bpy.app.build_hash.decode() == cfg['expected']['build_hash']
        assert common['runtime_identity']() == cfg['runtime']
        report['observed_runtime'] = {'blender_version': list(bpy.app.version),
                                      'build_hash': bpy.app.build_hash.decode(),
                                      **common['runtime_identity']()}
        for name, row in cfg['inputs'].items():
            assert common['file_record'](row['path']) == row, name
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        stage('OPEN_SAVED_SOURCE')
        assert bpy.ops.wm.open_mainfile(filepath=ip['source'], load_ui=False) == {'FINISHED'}
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        assert bpy.context.mode == 'OBJECT'
        assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
        report['observed_counts'] = {'objects': len(bpy.data.objects), 'actions': len(bpy.data.actions)}
        expected = json.loads(Path(ip['saved_expected']).read_text())
        old_inventory = json.loads(Path(ip['inventory']).read_text())
        old_graph = json.loads(Path(ip['graph']).read_text())
        stations = json.loads(Path(ip['stations']).read_text())[:4]
        assert [s['station'] for s in stations] == [0, 1, 2, 3]
        fresh = json.loads(Path(ip['wheel_fresh_report']).read_text())
        assert fresh['artifact_sha256'] == cfg['inputs']['source']['sha256']
        assert (fresh['raw_meshes_exact'], fresh['moving_evaluated_meshes_exact'], fresh['selected_materials_exact']) == (132, 128, 7)
        report['prior_wheel_evidence'] = fresh
        report['prior_wheel_evidence_scope'] = 'Historical4.5.13 only;132raw/128evaluated/7materials are not requalified in4.5.14'
        targets = [bpy.data.objects[n] for d in cfg['doors'] for n in d['children']]
        assert len(targets) == 20 and len({o.name for o in targets}) == 20
        for d in cfg['doors']:
            h = bpy.data.objects[d['hinge']]
            assert h.type == 'EMPTY', ('UNREADABLE_CORE_CONTROL_SCOPE', h.name, h.type)
            for n in d['children']:
                assert bpy.data.objects[n].type == 'MESH', ('UNREADABLE_CORE_MESH_SCOPE', n)
        detail_names = set(cfg['controls']) | {o.name for o in targets}
        wheel_names = {s[r] for s in stations for r in
                       ('joint_frame', 'carrier', 'spin', 'brake', 'drum', 'upright', 'kingpin')}
        detail_names |= wheel_names
        for name in list(detail_names):
            obj = bpy.data.objects[name]
            seen = set()
            while obj:
                assert obj.name not in seen, 'Parent cycle'
                seen.add(obj.name)
                detail_names.add(obj.name)
                obj = obj.parent
        detail_names = sorted(detail_names)
        materials = {s.material for o in targets for s in o.material_slots if s.material}
        stage('GUARD_BEFORE')
        before = snapshot()
        write(output / 'source-before.json', before, compact=True)
        # Comparison with the4.5.13 baseline is deliberately after raw capture.
        # A version mismatch cannot prevent saving readable current door arrays.
        for name in cfg['controls'] + [o.name for o in targets]:
            row = before['details'][name]
            blockers = []
            if row['animation'] is not None:
                blockers.append('EXISTING_ANIMDATA_REQUIRES_REVIEW')
            if row['constraints'] or row['modifiers']:
                blockers.append('CONSTRAINT_OR_MODIFIER_REQUIRES_REVIEW')
            if row['identity']['library'] or row['identity']['override']:
                blockers.append('LINKED_OR_OVERRIDE_REQUIRES_REVIEW')
            if any(k in row['custom'] for k in ('open_angle_deg', 'maz_native_axis_control_v1')):
                blockers.append('EXISTING_CONTROL_OR_PROPERTY_CONFLICT')
            if row['data_animation'] or (row['data_identity'] and (row['data_identity']['library'] or row['data_identity']['override'])):
                blockers.append('DATA_DEPENDENCY_REQUIRES_REVIEW')
            if blockers:
                report['dependency_blockers'].append({'object': name, 'reasons': blockers})
        # Record inbound ID users without traversing unrelated geometry or evaluating.
        selected_ids = {bpy.data.objects[n] for n in cfg['controls']} | set(targets) | {o.data for o in targets}
        try:
            users = bpy.data.user_map(subset=selected_ids)
            report['inbound_id_users'] = sorted([
                {'target': plain(x), 'users': sorted((plain(v) for v in u),
                                                   key=lambda v: (v['type'], v['name']))}
                for x, u in users.items()], key=lambda row: (row['target']['type'], row['target']['name']))
        except Exception:
            issues.append({'reason': 'inbound ID user coverage incomplete', 'traceback': traceback.format_exc()})
        greens = {d['green'] for d in cfg['doors']}
        for obj in targets:
            stage('SAVE_RAW_DOOR', obj.name)
            raw = raw_geometry(obj)
            path = output / (obj.name + '.raw.json')
            write(path, raw, compact=True)
            saved = json.loads(path.read_text())
            arrays = {k: common['unpack_array'](v) for k, v in saved['arrays'].items()}
            report['raw_files'].append(common['file_record'](path))
            if obj.name in greens:
                stage('SUMMARIZE_INDEX_COMPONENTS', obj.name)
                try:
                    summary = summarize_components(**{k: arrays[k] for k in
                        ('position', 'edges', 'loop_vertex', 'loop_edge', 'polygon_start', 'polygon_size')},
                        world=np.asarray(saved['matrix_world'], dtype=np.float64))
                    cpath = output / (obj.name + '.components.json')
                    write(cpath, summary, compact=True)
                    report['component_files'].append(common['file_record'](cpath))
                except Exception:
                    report.setdefault('component_errors', []).append({'object': obj.name, 'traceback': traceback.format_exc()})
        stage('COMPARE_HISTORICAL_4513_BASELINE')
        differences = []
        def compare(field, old, current):
            if old != current:
                differences.append({'field': field, 'expected_4513': old, 'observed_4514': current})
        def stable_id(value):
            return None if value is None else {k: v for k, v in value.items() if k != 'pointer_session_only'}
        compare('object_names', expected['object_names'], sorted(before['all_objects']))
        for key in ('objects', 'actions'):
            compare('counts/' + key, cfg['expected'][key], report['observed_counts'][key])
        for key in ('world_matrices_sha256', 'parents_sha256', 'actions_sha256'):
            compare('legacy_graph/' + key, expected[key], before['legacy_graph_state'][key])
        for name in detail_names:
            current = before['named_inventory'][name]
            old = old_inventory.get(name)
            if old is None:
                differences.append({'field': 'inventory/' + name, 'expected_4513': 'MISSING',
                                    'observed_4514': current})
                continue
            for key in ('type', 'parent', 'parent_type', 'parent_bone', 'rotation_mode',
                        'action_slot_handle', 'action_blend_type', 'action_influence'):
                compare('inventory/' + name + '/' + key, old[key], current[key])
            for key in ('data', 'action'):
                compare('inventory/' + name + '/' + key, stable_id(old[key]), stable_id(current[key]))
            old_record = old_graph['records'].get(name)
            if old_record is not None:
                for key in ('matrix_world', 'matrix_local', 'matrix_basis', 'matrix_parent_inverse'):
                    compare('matrices/' + name + '/' + key, old_record[key + '_rows'],
                            before['all_objects'][name]['matrices'][key])
                compare('children/' + name, old_record['children'], before['details'][name]['children'])
        for station in stations:
            compare('required_xyz_spin/' + station['spin'], 'XYZ',
                    before['named_inventory'][station['spin']]['rotation_mode'])
        report['legacy_baseline_comparison'] = {
            'status': 'RECORDED_FIELDS_EXACT' if not differences else 'MISMATCH_BLOCKS_AXES_AND_INSTALLATION',
            'differences': differences,
            'scope': 'Whole names/parents/world/original action key digests; exact named control/door/wheel identity, mode, binding and available original graph matrices. No missing historical values reconstructed from hashes.',
            'compatibility_claim': 'Limited saved-frame field comparison only; not Blender version, whole vehicle, timeline, geometry evaluation or wheel acceptance'}
        report['status'] = 'CAPTURE_COMPLETE_PENDING_GUARDS'
    except BaseException:
        report['status'] = 'CAPTURE_FAILED_OR_INCOMPLETE'
        report['traceback'] = traceback.format_exc()
    finally:
        try:
            if before is not None:
                stage('GUARD_AFTER')
                after = snapshot()
                write(output / 'source-after.json', after, compact=True)
                report['source_guards_pass'] = after == before
            stage('VERIFY_INPUTS_AFTER')
            report['inputs_after'] = {name: common['file_record'](row['path']) for name, row in cfg['inputs'].items()}
            report['file_guards_pass'] = report['inputs_after'] == cfg['inputs']
            report['unsupported_read_fields'] = issues + legacy_issues
        except BaseException:
            report['guard_traceback'] = traceback.format_exc()
        if (report['status'] == 'CAPTURE_COMPLETE_PENDING_GUARDS' and report.get('source_guards_pass')
                and report.get('file_guards_pass') and not issues and not legacy_issues):
            report['status'] = 'CAPTURE_COMPLETE_GUARDS_PASS'
        elif report['status'] == 'CAPTURE_COMPLETE_PENDING_GUARDS':
            report['status'] = 'CAPTURE_FAILED_GUARDS_OR_COVERAGE'
        report['elapsed_seconds'] = time.monotonic() - started
        baseline_ok = report.get('legacy_baseline_comparison', {}).get('status') == 'RECORDED_FIELDS_EXACT'
        blocked = (report['status'] != 'CAPTURE_COMPLETE_GUARDS_PASS' or not baseline_ok
                   or bool(report['dependency_blockers']) or bool(issues) or bool(legacy_issues))
        report['axis_identification'] = 'BLOCKED_BASELINE_OR_DEPENDENCY' if blocked else 'NOT_IDENTIFIED_REVIEW_SAVED_RAW'
        report['installation_eligibility'] = 'BLOCKED_BASELINE_OR_DEPENDENCY' if blocked else 'BLOCKED_AXES_UNIDENTIFIED'
        report['component_summary_complete'] = len(report['component_files']) == 4
        report['installation'] = 'NOT_RUN'
        write(output / 'capture-report.json', report)
        stage(report['status'])
    print(json.dumps({k: report[k] for k in ('status', 'axis_identification', 'installation')}), flush=True)
    if report['status'] != 'CAPTURE_COMPLETE_GUARDS_PASS':
        raise RuntimeError(report['status'])


if __name__ == '__main__':
    main()
