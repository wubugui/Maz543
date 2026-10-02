"""Pinned source read-only capture. Only run through the reviewed runner."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import bpy
import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from replay_capture import analyze, file_record, pack_array, runtime_identity, unpack_array, write_json


def functions_only(path, names, namespace):
    # Never import either source's entry point, imports, assignments, or classes.
    nodes = [node for node in ast.parse(Path(path).read_bytes()).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def snapshot(objects, targets, helper, authored):
    value, rna, custom = authored['value'], authored['authored_rna'], authored['custom']
    rows = []
    for obj in objects:
        rows.append({'name': obj.name, 'pointer_session_only': obj.as_pointer(),
                     'data_pointer_session_only': obj.data.as_pointer() if obj.data else None,
                     'parent_pointer_session_only': obj.parent.as_pointer() if obj.parent else None,
                     'properties': rna(obj), 'custom': custom(obj),
                     'matrices': {k: [list(r) for r in getattr(obj, k)] for k in
                                  ('matrix_world', 'matrix_local', 'matrix_basis', 'matrix_parent_inverse')},
                     'hide_get': obj.hide_get(), 'collections': sorted(c.name for c in obj.users_collection),
                     'modifiers': [rna(m) for m in obj.modifiers],
                     'constraints': [rna(c) for c in obj.constraints],
                     'material_slots': [[s.link, value(s.material)] for s in obj.material_slots],
                     'animation': helper['animation_state'](obj)})
    meshes = {obj.data.name: {'pointer_session_only': obj.data.as_pointer(),
                              'signature': helper['mesh_signature'](obj.data)} for obj in targets}
    mats = {slot.material.name: authored['material_record'](slot.material)
            for obj in targets for slot in obj.material_slots if slot.material}
    return {'frame': bpy.context.scene.frame_current, 'subframe': bpy.context.scene.frame_subframe,
            'scene': bpy.context.scene.name, 'view_layer': bpy.context.view_layer.name,
            'objects_and_ancestors': rows, 'target_authored_meshes': meshes, 'target_materials': mats}


def capture(obj, mesh, target, authored):
    array = authored['array']
    assert mesh is not None and mesh.shape_keys is None and len(mesh.color_attributes) == 0
    mesh.calc_loop_triangles()
    materials = tuple(mesh.materials)
    fallback = len(materials) == 1 and materials[0] is None
    if fallback:
        materials = tuple(slot.material for slot in obj.material_slots)
    fields = {}
    for key, collection, field, width, dtype in [
        ('position_native', mesh.vertices, 'co', 3, '<f4'),
        ('raw_normals_native', mesh.corner_normals, 'vector', 3, '<f4'),
        ('loop_vertex', mesh.loops, 'vertex_index', 1, '<i4'),
        ('triangle_loop', mesh.loop_triangles, 'loops', 3, '<i4'),
        ('triangle_material', mesh.loop_triangles, 'material_index', 1, '<i4')]:
        a = array(collection, field, width, np.dtype(dtype))
        fields[key] = pack_array(a.reshape(-1) if width == 1 else a, dtype)
    uvs = [{'index': i, 'name': uv.name, 'active': uv == mesh.uv_layers.active,
            'active_render': uv.active_render, 'active_clone': uv.active_clone,
            'native_values': pack_array(array(uv.uv, 'vector', 2), '<f4')}
           for i, uv in enumerate(mesh.uv_layers)]
    return {'schema': 'maz-fresh-ten-normal-arrays-v1', 'object': obj.name,
            'reference_mesh_id': target['reference_mesh_id'], 'native_mesh_name': mesh.name,
            'measurement': 'Fresh evaluated source fields; historical raw vectors were not stored',
            'arrays': fields, 'uv_layers': uvs, 'uv_active_present': bool(mesh.uv_layers.active),
            'evaluated_material_slots': [mat.name if mat else None for mat in materials],
            'material_slot_source': 'object_single_null_fallback' if fallback else 'evaluated_mesh',
            'source_object_material_slots': [[s.link, s.material.name if s.material else None] for s in obj.material_slots],
            'materials': {mat.original.name: authored['material_record'](mat.original) for mat in materials if mat},
            'loose_edges_omitted': sum(edge.is_loose for edge in mesh.edges),
            'source_object_pointer_session_only': obj.as_pointer(),
            'source_mesh_pointer_session_only': obj.data.as_pointer()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    output = args.output.resolve(strict=True)
    assert output.parent == HERE
    cfg = json.loads((HERE / 'capture.json').read_text())
    started = time.monotonic()
    report = {'status': 'STARTING', 'unchanged_qualification': cfg['unchanged_qualification'],
              'limits': cfg['limits'], 'captured_files': [],
              'guard_scope': 'Only target source mesh authored payloads, target materials, and target/ancestor object identities, transforms, properties, modifiers, constraints and animation descriptions. File hashes pin all inputs. This is finite non-mutation coverage, not a new whole-project audit.'}
    before = None

    def stage(name, target=None):
        row = {'stage': name, 'target': target, 'elapsed_seconds': time.monotonic() - started,
               'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        temp = output / 'stage.json.tmp'
        temp.write_text(json.dumps(row) + '\n')
        temp.replace(output / 'stage.json')
        with (output / 'stages.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print('CAPTURE_STAGE ' + json.dumps(row), flush=True)

    try:
        stage('VERIFY_PINNED_INPUTS')
        assert bpy.app.version == (4, 5, 13) and bpy.app.build_hash.decode() == 'daeeeca98fb0'
        assert runtime_identity() == cfg['runtime']
        report['runtime'] = runtime_identity()
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        for row in cfg['inputs'].values():
            assert file_record(row['path']) == row, row['path']
        authored = functions_only(cfg['inputs']['legacy_export_helper']['path'],
                                  {'array', 'value', 'authored_rna', 'custom', 'tree_record', 'material_record'},
                                  dict(np=np, bpy=bpy))
        helper = functions_only(cfg['inputs']['mesh_protection_helper']['path'],
                                {'require', 'as_plain', 'scalar_rna', 'array', 'mesh_signature',
                                 'animation_state', 'driver_description'},
                                dict(np=np, bpy=bpy, hashlib=hashlib, json=json))
        stage('OPEN_PINNED_SAVED_SOURCE')
        result = bpy.ops.wm.open_mainfile(filepath=cfg['inputs']['source']['path'])
        assert result == {'FINISHED'}
        assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
        assert bpy.context.mode == 'OBJECT'
        assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
        targets = [bpy.data.objects[target['object']] for target in cfg['targets']]
        objects = {}
        for obj in targets:
            assert obj.type == 'MESH' and obj.data.shape_keys is None
            assert [m.type for m in obj.modifiers] == ['BEVEL', 'WEIGHTED_NORMAL'], obj.name
            assert not obj.is_instancer and len(obj.particle_systems) == 0
            current, chain = obj, set()
            while current is not None:
                assert current.name not in chain, 'Parent cycle'
                chain.add(current.name)
                objects[current.name] = current
                current = current.parent
        objects = [objects[name] for name in sorted(objects)]
        stage('GUARD_BEFORE')
        before = snapshot(objects, targets, helper, authored)
        write_json(output / 'source-before.json', before)
        stage('GET_DEPSGRAPH')
        dg = bpy.context.evaluated_depsgraph_get()
        for obj, target in zip(targets, cfg['targets']):
            stage('EVALUATE_TARGET', obj.name)
            evaluated = obj.evaluated_get(dg)
            try:
                mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
                stage('CAPTURE_TARGET_ARRAYS', obj.name)
                record = capture(obj, mesh, target, authored)
                record['runtime'] = runtime_identity()
                path = output / (obj.name + '.json')
                write_json(path, record, compact=True)
                # JSON float values must recover every float32 bit, including -0.
                saved = json.loads(path.read_text())
                for value in saved['arrays'].values():
                    unpack_array(value)
                for uv in saved['uv_layers']:
                    unpack_array(uv['native_values'])
                report['captured_files'].append(file_record(path))
            finally:
                evaluated.to_mesh_clear()
        stage('REPLAY_SAVED_ARRAYS')
        replay = analyze(output, cfg, stage)
        write_json(output / 'replay-report.json', replay)
        report['correspondence'] = replay['correspondence']
        report['signed_zero_comparison'] = replay['signed_zero_comparison']['status']
        report['status'] = 'CAPTURE_COMPLETE_PENDING_GUARDS'
    except BaseException:
        report['status'] = 'CAPTURE_FAILED_OR_INCOMPLETE'
        report['traceback'] = traceback.format_exc()
    finally:
        try:
            if before is not None:
                stage('GUARD_AFTER')
                after = snapshot(objects, targets, helper, authored)
                write_json(output / 'source-after.json', after)
                report['source_guards_pass'] = after == before
            stage('VERIFY_INPUTS_AFTER')
            report['inputs_after'] = {name: file_record(row['path']) for name, row in cfg['inputs'].items()}
            report['file_guards_pass'] = report['inputs_after'] == cfg['inputs']
        except BaseException:
            report['guard_traceback'] = traceback.format_exc()
        if report['status'] == 'CAPTURE_COMPLETE_PENDING_GUARDS' and report.get('source_guards_pass') and report.get('file_guards_pass'):
            report['status'] = 'CAPTURE_COMPLETE_GUARDS_PASS'
        elif report['status'] == 'CAPTURE_COMPLETE_PENDING_GUARDS':
            report['status'] = 'CAPTURE_FAILED_GUARDS'
        report['elapsed_seconds'] = time.monotonic() - started
        write_json(output / 'capture-report.json', report)
        stage(report['status'])
    print(json.dumps({key: report.get(key) for key in ('status', 'correspondence', 'signed_zero_comparison')}), flush=True)
    if report['status'] != 'CAPTURE_COMPLETE_GUARDS_PASS':
        raise RuntimeError(report['status'])


if __name__ == '__main__':
    main()
