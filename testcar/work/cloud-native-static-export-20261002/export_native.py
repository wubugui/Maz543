"""One official saved-frame GLB export. Run only through reviewed run_export.py.

References read actual native mesh fields in supported exporter hooks. No mesh
construction, source save, render, frame advance, conversion or modifier edits.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
import bpy
from validate_glb import oriented_signature


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def array(collection, name, width, dtype=np.float32):
    result = np.empty(len(collection) * width, dtype=dtype)
    collection.foreach_get(name, result)
    return result.reshape(-1, width)


def yup(values):
    values = values.copy()
    values[:, [1, 2]] = values[:, [2, 1]]
    values[:, 2] *= -1
    return values


def value(v):
    if v is None or isinstance(v, (str, int, bool, float)):
        return v
    if isinstance(v, bpy.types.ID):
        return {'type': v.bl_rna.identifier, 'name': v.name,
                'library': v.library.filepath if v.library else None}
    if isinstance(v, set):
        return sorted(v)
    if hasattr(v, 'to_dict'):
        return {k: value(x) for k, x in v.to_dict().items()}
    return [value(x) for x in v]


def authored_rna(block):
    out = {}
    for p in block.bl_rna.properties:
        if p.is_readonly or p.identifier == 'rna_type' or p.type == 'COLLECTION':
            continue
        v = getattr(block, p.identifier)
        if p.type == 'POINTER' and v is not None and not isinstance(v, bpy.types.ID):
            continue
        out[p.identifier] = value(v)
    return out


def custom(block):
    return {k: value(block[k]) for k in block.keys()}


def tree_record(tree):
    if tree is None:
        return None
    return {'name': tree.name, 'custom': custom(tree), 'nodes': [
        {'name': n.name, 'type': n.bl_idname, 'properties': authored_rna(n), 'custom': custom(n),
         'inputs': [[s.identifier, value(s.default_value)] for s in n.inputs if hasattr(s, 'default_value')]}
        for n in tree.nodes],
        'links': [[l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier]
                  for l in tree.links]}


def material_record(mat):
    return {'identity': value(mat), 'properties': authored_rna(mat), 'custom': custom(mat),
            'node_tree': tree_record(mat.node_tree)}


def protection(graph_module, action_record, mesh_signature):
    graph = graph_module.snapshot(action_record)
    # All original Mesh datablocks, not just selected meshes. Attribute payloads,
    # shape keys, material slots and authored topology are covered by pinned helper.
    meshes = {m.name: mesh_signature(m) for m in bpy.data.meshes}
    curves = {}
    for c in bpy.data.curves:
        curves[c.name] = {'properties': authored_rna(c), 'custom': custom(c),
                         'materials': [value(m) for m in c.materials],
                         'splines': [{'properties': authored_rna(s),
                                      'points': [authored_rna(p) for p in s.points],
                                      'bezier_points': [authored_rna(p) for p in s.bezier_points]}
                                     for s in c.splines]}
        if hasattr(c, 'body_format'):
            curves[c.name]['body_format'] = [authored_rna(x) for x in c.body_format]
    materials = {m.name: material_record(m) for m in bpy.data.materials}
    node_groups = {n.name: tree_record(n) for n in bpy.data.node_groups}
    images = {i.name: {'identity': value(i), 'source': i.source, 'filepath': i.filepath,
                       'size': list(i.size), 'colorspace': i.colorspace_settings.name,
                       'alpha_mode': i.alpha_mode,
                       'packed': [{'bytes': len(p.packed_file.data),
                                   'sha256': hashlib.sha256(p.packed_file.data).hexdigest()}
                                  for p in i.packed_files]}
              for i in bpy.data.images}
    objects = {o.name: {'basis': [list(r) for r in o.matrix_basis],
                         'parent_inverse': [list(r) for r in o.matrix_parent_inverse],
                         'material_slots': [[s.link, value(s.material)] for s in o.material_slots],
                         'custom': custom(o),
                         'modifiers': [authored_rna(m) for m in o.modifiers],
                         'constraints': [authored_rna(c) for c in o.constraints]}
               for o in bpy.data.objects}
    sections = dict(meshes=meshes, curves=curves, materials=materials,
                    node_groups=node_groups, images=images, objects=objects)
    return graph, sections


class NativeReference:
    def __init__(self, out):
        self.out = out
        self.mesh_ids = {}
        self.references = {'schema': 'maz-native-export-field-references-v1',
                           'meshes': {}, 'nodes': {}, 'materials': {}, 'known_empty_nodes': [], 'hook_errors': [],
                           'limits': ['Native fields are captured during this official export, not from GLB primitive arrays.',
                                      'Official curve/font tessellation is not independently qualified.',
                                      'Cross-evaluation UV determinism and shader/render equivalence are not asserted.']}

    def error(self, hook):
        self.references['hook_errors'].append({'hook': hook, 'traceback': traceback.format_exc()})

    def gather_mesh_hook(self, gltf_mesh, mesh, obj, vertex_groups, modifiers, materials, settings):
        try:
            assert settings['gltf_current_frame'] and not settings['gltf_animations']
            assert not settings['gltf_draco_mesh_compression']
            assert mesh.shape_keys is None, 'Shape keys need a separately qualified static path'
            assert len(mesh.color_attributes) == 0, 'Unexpected native color attributes'
            mesh.calc_loop_triangles()
            coords = yup(array(mesh.vertices, 'co', 3))
            loops = array(mesh.loops, 'vertex_index', 1, np.int32).reshape(-1)
            triangles = array(mesh.loop_triangles, 'loops', 3, np.int32)
            material_indices = array(mesh.loop_triangles, 'material_index', 1, np.int32).reshape(-1)
            raw_normals = array(mesh.corner_normals, 'vector', 3)
            assert len(raw_normals) == len(loops)
            converted = np.round(raw_normals, 4)
            lengths = np.linalg.norm(converted, axis=1, keepdims=True)
            np.divide(converted, lengths, out=converted, where=lengths != 0)
            zero = ~converted.any(axis=1)
            converted[zero, 2] = 1
            normal_error = np.linalg.norm(converted.astype(np.float64) - raw_normals, axis=1)
            attrs = {'POSITION': coords[loops], 'NORMAL': yup(converted)}
            uv_rows = []
            if mesh.uv_layers.active:
                for i, uv in enumerate(mesh.uv_layers):
                    values = array(uv.uv, 'vector', 2)
                    values[:, 1] *= -1
                    values[:, 1] += 1
                    attrs['TEXCOORD_' + str(i)] = values
                    uv_rows.append({'index': i, 'name': uv.name,
                                    'active': uv == mesh.uv_layers.active,
                                    'active_render': uv.active_render})
            parts = []
            used_materials = []
            for slot in np.unique(material_indices):
                # Match the official native slot semantics, not an inferred GLB index.
                mat = materials[int(slot)] if int(slot) < len(materials) else materials[-1] if materials else None
                mat_name = mat.name if mat else None
                used_materials.append(mat_name)
                parts.append({'material_name': mat_name, 'source_material_slot': int(slot),
                              'signature': oriented_signature(attrs, triangles[material_indices == slot].reshape(-1))})
                if mat:
                    original = mat.original
                    self.references['materials'][original.name] = material_record(original)
            assert len(parts) == len(gltf_mesh.primitives), 'Unexpected split, loose primitive or UDIM export'
            # Check identities only; no generated glTF position/normal/UV/index array
            # is ever used to construct expected records.
            actual_materials = [p.material.name if p.material else None for p in gltf_mesh.primitives]
            assert actual_materials == used_materials, ('Material remap', actual_materials, used_materials)
            mesh_id = 'mesh-' + str(len(self.mesh_ids)).zfill(5)
            assert id(gltf_mesh) not in self.mesh_ids
            self.mesh_ids[id(gltf_mesh)] = mesh_id
            self.references['meshes'][mesh_id] = {
                'native_mesh_name': mesh.name, 'vertices': len(coords), 'loops': len(loops),
                'parts': parts, 'triangles': len(triangles), 'uv_layers': uv_rows,
                'bounds': [coords[loops[triangles.reshape(-1)]].min(axis=0).tolist(), coords[loops[triangles.reshape(-1)]].max(axis=0).tolist()] if len(triangles) else None,
                'raw_normal_zero_count': int((~raw_normals.any(axis=1)).sum()),
                'rounded_normal_zero_count': int(zero.sum()),
                'raw_to_official_normal_max_vector_error': float(normal_error.max(initial=0)),
                'raw_to_official_normal_max_nonzero_error': float(normal_error[~zero].max(initial=0)),
                'normal_rule': 'float32 round4, normalize, replace exact0 with native+Z, swizzle(x,z,-y)',
                'loose_edges_omitted': sum(e.is_loose for e in mesh.edges),
                'unused_vertices_omitted': len(set(range(len(coords))) - set(map(int, loops))),
                'tangents': 'Explicitly omitted; native/generated tangent equivalence remains unqualified'}
        except BaseException:
            self.error('gather_mesh_hook')

    def gather_node_hook(self, node, obj, settings):
        try:
            assert obj is not None and node.name == obj.name
            assert node.name not in self.references['nodes']
            self.references['nodes'][node.name] = self.mesh_ids[id(node.mesh)] if node.mesh else None
            if node.mesh is None and obj.type in {'MESH', 'CURVE', 'FONT'}:
                dg = bpy.context.evaluated_depsgraph_get()
                evaluated = obj.evaluated_get(dg)
                empty = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
                try:
                    assert empty is not None and len(empty.polygons) == 0, ('Unexplained omitted geometry', obj.name)
                    self.references['known_empty_nodes'].append(obj.name)
                finally:
                    evaluated.to_mesh_clear()
            if len(self.references['nodes']) % 100 == 0:
                print('NATIVE_EXPORT_NODES', len(self.references['nodes']), flush=True)
        except BaseException:
            self.error('gather_node_hook')


def main(args, report):
    cfg = json.loads(args.inputs.read_text())
    ip = {k: Path(v['path']) for k, v in cfg['inputs'].items()}
    sys.path.insert(0, str(ip['graph_common'].parent))
    import graph_common as gc
    import inspect_native_graph as gi
    expected_graph = json.loads(ip['native_graph'].read_text())
    expected_inventory = json.loads(ip['object_inventory'].read_text())
    expected_state = json.loads(ip['saved_expected'].read_text())
    stations = json.loads(ip['stations'].read_text())
    names = expected_graph['full_union_ancestry_closed']
    assert len(names) == 2675 and len(set(names)) == 2675
    assert expected_graph['union_additional_ancestors'] == []
    assert len(expected_graph['full_native_s543_subtree']) == 1985
    gc.required_station_names(stations, expected_inventory)
    assert bpy.app.version == (4, 5, 13) and bpy.app.build_hash.decode() == 'daeeeca98fb0'
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    bpy.ops.wm.open_mainfile(filepath=str(ip['artifact']))
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert bpy.context.mode == 'OBJECT'
    assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
    action_record, issues = gc.read_only_action_helper(ip['helper'], ip['builder'], bpy)
    namespace = dict(bpy=bpy, np=np, hashlib=hashlib, json=json, math=math)
    needed = {'require', 'as_plain', 'scalar_rna', 'array', 'mesh_signature', 'animation_state', 'driver_description'}
    defs = [n for n in ast.parse(ip['mesh_protection_helper'].read_bytes()).body
            if isinstance(n, ast.FunctionDef) and n.name in needed]
    assert {n.name for n in defs} == needed
    exec(compile(ast.Module(body=defs, type_ignores=[]), str(ip['mesh_protection_helper']), 'exec'), namespace)
    print('NATIVE_PHASE', 'original-data-protection', flush=True)
    before, authored_before = protection(gi, action_record, namespace['mesh_signature'])
    assert sorted(before['objects']) == expected_state['object_names'] and len(before['objects']) == 8522
    for key in ('world_matrices_sha256', 'parents_sha256', 'actions_sha256'):
        assert before['state'][key] == expected_state[key], key
    assert not issues, issues
    relevant_before = gi.graph_records(names, before['objects'])
    assert relevant_before == expected_graph['records']
    report['completed_checks'].append('saved_source_graph_and_enumerated_raw_data_before')
    # Only hashes are persisted for unchanged whole-scene raw state; the .blend
    # and pinned extraction code are the recoverable payload, no second mesh copy.
    write(args.output / 'protection-before.json', {'state': before['state'],
          'authored_sections': {k: digest(v) for k, v in authored_before.items()},
          'meshes': {k: {'sha256': v['sha256'], 'counts': v['counts']} for k, v in authored_before['meshes'].items()}})
    for name in names:
        obj = bpy.data.objects[name]
        assert obj.type in {'MESH', 'EMPTY', 'CURVE', 'FONT'}
        assert obj.visible_get() and not obj.hide_render and not obj.hide_select, name
        assert not obj.instance_collection and obj.instance_type == 'NONE', name
        assert not any(m.type == 'ARMATURE' for m in obj.modifiers), name
        assert getattr(obj.data, 'shape_keys', None) is None, name
        assert obj.data is None or not obj.data.get('gltf2_variant_default_materials'), ('Material variants reset source data', name)
        if obj.type == 'MESH':
            assert len(obj.data.color_attributes) == 0, ('Color attributes require explicit preservation', name)
        if obj.type in {'CURVE', 'FONT'}:
            assert all(s.material for s in obj.material_slots), ('Nonmesh empty-slot remap', name)
    dg = bpy.context.evaluated_depsgraph_get()
    instances = []
    for instance in dg.object_instances:
        if instance.is_instance:
            parent = instance.parent.original.name if instance.parent else None
            owner = instance.object.original.name if instance.object else None
            if parent in names or owner in names:
                instances.append({'parent': parent, 'object': owner})
    write(args.output / 'static-preflight.json', {'derived_instances': instances,
          'shape_keys': 0, 'armature_modifiers': 0, 'frame': 0, 'all16_vehicle_gates': 'OPEN'})
    assert not instances, 'Separate instances require provenance and extra node scope'
    for image in bpy.data.images:
        assert image.source != 'TILED', 'UDIM requires an explicit tile/reference plan'
    report['completed_checks'].append('static_shape_skin_instance_color_and_udim_preflight')
    selected = [o for o in bpy.context.view_layer.objects if o.select_get()]
    active = bpy.context.view_layer.objects.active
    # Track only documented exporter bookkeeping so its cleanup cannot mask any
    # other native node-property change.
    all_trees = list(bpy.data.node_groups) + [m.node_tree for m in bpy.data.materials if m.node_tree]
    image_nodes = [(n, 'used' in n, value(n.get('used'))) for tree in all_trees for n in tree.nodes if n.type == 'TEX_IMAGE']
    from io_scene_gltf2.blender.exp import export as official
    collector = NativeReference(args.output)
    original_save = official.save
    def audited_save(context, settings):
        assert settings['gltf_user_extensions'] == [] and settings['pre_export_callbacks'] == [] and settings['post_export_callbacks'] == []
        assert settings['gltf_current_frame'] is True and settings['gltf_animations'] is False
        settings['gltf_user_extensions'].append(collector)
        return original_save(context, settings)
    official.save = audited_save
    export_result = None
    export_error = None
    try:
        for o in bpy.context.view_layer.objects:
            o.select_set(o.name in names)
        assert {o.name for o in bpy.context.selected_objects} == set(names)
        bpy.context.view_layer.objects.active = bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        print('NATIVE_PHASE', 'official-export', flush=True)
        export_result = bpy.ops.export_scene.gltf(filepath=str(args.output / 'native-static.glb'), **cfg['export_options'])
    except BaseException:
        export_error = traceback.format_exc()
    finally:
        official.save = original_save
        for o in bpy.context.view_layer.objects:
            o.select_set(o in selected)
        bpy.context.view_layer.objects.active = active
        bookkeeping = []
        for node, existed, old in image_nodes:
            new = value(node.get('used'))
            if ('used' in node) != existed or new != old:
                bookkeeping.append({'node': node.name, 'tree': node.id_data.name, 'before_exists': existed, 'before': old, 'after': new})
            if existed:
                node['used'] = old
            elif 'used' in node:
                del node['used']
        report['exporter_bookkeeping_restored'] = bookkeeping
        # Persist reference observations even if the official export/one hook failed.
        for name in collector.references['materials']:
            collector.references['materials'][name] = authored_before['materials'][name]
        write(args.output / 'native-references.json', collector.references)
        print('NATIVE_PHASE', 'source-protection-after', flush=True)
        after, authored_after = protection(gi, action_record, namespace['mesh_signature'])
        relevant_after = gi.graph_records(names, after['objects'])
        report['source_memory_preserved'] = (after == before and relevant_after == relevant_before and authored_after == authored_before)
        report['changed_authored_sections'] = [k for k in authored_before if authored_before[k] != authored_after[k]]
        write(args.output / 'protection-after.json', {'state': after['state'],
              'authored_sections': {k: digest(v) for k, v in authored_after.items()},
              'meshes': {k: {'sha256': v['sha256'], 'counts': v['counts']} for k, v in authored_after['meshes'].items()},
              'changed_authored_sections': report['changed_authored_sections'],
              'enumerated_snapshot_unchanged': after == before, 'relevant_graph_unchanged': relevant_after == relevant_before})
        # Details of any changed field are kept; never "repair" geometry to pass.
        if not report['source_memory_preserved']:
            write(args.output / 'preservation-failure.json', {
                  'before': before if before != after else None, 'after': after if before != after else None,
                  'authored_differences': {k: {'before': authored_before[k], 'after': authored_after[k]}
                                           for k in report['changed_authored_sections']}})
    report['completed_checks'].append('source_post_export_protection_attempted')
    assert export_error is None, export_error
    assert export_result == {'FINISHED'}, export_result
    report['asset_written'] = True
    assert report['source_memory_preserved'], report['changed_authored_sections']
    assert not collector.references['hook_errors'], collector.references['hook_errors']
    assert set(collector.references['nodes']) == set(names), 'Incomplete hook/source mapping'
    report['status'] = 'EXPORTED_SOURCE_PROTECTED_REFERENCES_CAPTURED'



if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert args.output.is_dir() and not (args.output / 'native-report.json').exists()
    report = {'status': 'INCOMPLETE', 'completed_checks': [], 'asset_written': False,
              'model_saved': False, 'rendered': False, 'frame_advanced': False,
              'all16_vehicle_gates': 'OPEN', 'global_timeline': 'BLOCKED_NINE_ORIGINAL_NODES',
              'source_shader_render_equivalence': 'UNQUALIFIED',
              'cross_evaluation_uv_determinism': 'NOT_CLAIMED'}
    try:
        main(args, report)
    except BaseException:
        report['error'] = traceback.format_exc()
        raise
    finally:
        write(args.output / 'native-report.json', report)
