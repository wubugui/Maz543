"""Read one pinned Textured file; never construct, change poses, save, or render.

Reports are compact hashes and structural records. This is an intake decision,
not a repaired candidate, motion test, export test, or acceptance certificate.
"""
import argparse
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
input_path = Path(a.inputs)
I = json.loads(input_path.read_text())
out = Path(a.output)
assert out.is_dir() and not (out / 'native-report.json').exists()
sha = lambda b: hashlib.sha256(b).hexdigest()
source = Path(I['source_path'])
issues = []
report = {'status': 'READ_IN_PROGRESS_NOT_VALIDATED', 'source_sha256': I['source_sha256'],
          'inputs_sha256': sha(input_path.read_bytes()), 'saved_blend': False,
          'constructed_objects': False, 'rendered': False, 'pose_mutations': False,
          'issues': issues, 'limitations': [
              'Frame zero VIEWPORT intake only; no candidate or motion verification.',
              'Old build signatures combine geometry, UV and material indices; their differences do not isolate geometry changes.',
              'Hash equality is same-process evidence. No cross-process evaluated UV equality is presumed.',
              'Node references are conservatively inspected; unknown relevant node dependencies stop qualification.',
              'All-object reverse index covers recorded Object/Collection RNA pointers, nested modifier/constraint collections, recursive ID properties, driver targets, instancing, and node references.',
              'Particle systems and pose/armature systems anywhere in the source stop qualification; their non-ID RNA dependency chains are not proved.',
              'No arbitrary non-ID RNA pointer traversal or proof of Blender internals, caches, add-on handlers, custom driver namespaces, or material displacement is claimed.',
              'No renderer/material-displacement evaluation, arbitrary timeline, collision, factory dimensions, or browser acceptance.',
              'The 72 editable tyre source FONT objects remain in the separate Master; none are created in Textured.',
              'No claim about original-source drum vertex count is imported from Master or decoded GLB seams.'
          ]}


def write(name, data):
    path = out / name
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def problem(owner, reason, detail=None):
    row = {'owner': owner, 'reason': reason}
    if detail is not None:
        row['detail'] = detail
    issues.append(row)


def idref(value):
    return {'id_type': value.bl_rna.identifier, 'name': value.name,
            'library': value.library.filepath if value.library else None}


def value_record(value):
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {'nonfinite': str(value)}
    if isinstance(value, bpy.types.ID):
        return idref(value)
    if isinstance(value, set):
        return sorted(value)
    if hasattr(value, 'to_list'):
        return value.to_list()
    if hasattr(value, 'to_tuple'):
        return [value_record(v) for v in value.to_tuple()]
    if type(value).__module__ == 'mathutils':
        return [value_record(v) for v in value]
    if isinstance(value, (tuple, list)) or type(value).__name__ == 'bpy_prop_array':
        return [value_record(v) for v in value]
    return {'unserialized_type': type(value).__name__}


def rna_values(block):
    if block is None:
        return None
    result = {}
    for prop in block.bl_rna.properties:
        name = prop.identifier
        if name in {'rna_type', 'id_data', 'original', 'execution_time'} or prop.type == 'COLLECTION':
            continue
        try:
            value = getattr(block, name)
            if prop.type == 'POINTER' and value is not None and not isinstance(value, bpy.types.ID):
                result[name] = {'rna_type': value.bl_rna.identifier}
            else:
                result[name] = value_record(value)
        except Exception as exc:
            problem(getattr(block, 'name', type(block).__name__), 'unreadable RNA field', [name, str(exc)])
    return result


def curves_of(action):
    curves = []
    if hasattr(action, 'fcurves'):
        curves.extend(action.fcurves)
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            if not hasattr(strip, 'channelbags'):
                problem(action.name, 'unknown action strip channel storage', strip.type)
                continue
            for bag in strip.channelbags:
                curves.extend(bag.fcurves)
    return list({f.as_pointer(): f for f in curves}.values())


def animation_record(block, owner, reject_action=False):
    ad = getattr(block, 'animation_data', None)
    if not ad:
        return None
    drivers = []
    for f in ad.drivers:
        d = f.driver
        drivers.append({'path': f.data_path, 'array_index': f.array_index, 'mute': f.mute,
                        'type': d.type, 'expression': d.expression,
                        'variables': [{'name': v.name, 'type': v.type,
                                       'targets': [rna_values(t) for t in v.targets]} for v in d.variables],
                        'fcurve_modifiers': [rna_values(m) for m in f.modifiers]})
    act = ad.action
    action = None if act is None else {
        'name': act.name, 'frame_range': list(act.frame_range),
        'curves': [{'path': f.data_path, 'array_index': f.array_index, 'mute': f.mute,
                    'keyframes': len(f.keyframe_points), 'sampled_points': len(f.sampled_points),
                    'modifiers': [rna_values(m) for m in f.modifiers]} for f in curves_of(act)]}
    nla = [{'name': t.name, 'mute': t.mute, 'strips': [
        {'name': s.name, 'type': s.type, 'action': s.action.name if s.action else None,
         'frame_start': s.frame_start, 'frame_end': s.frame_end} for s in t.strips]} for t in ad.nla_tracks]
    if drivers or nla or (reject_action and action):
        problem(owner, 'unqualified animation dependency', {'drivers': len(drivers), 'nla_tracks': len(nla), 'action': action and action['name']})
    if action and any(f['path'] not in {'location', 'rotation_euler', 'rotation_quaternion', 'scale'} for f in action['curves']):
        problem(owner, 'action affects fields beyond held object transform', action)
    return {'action': action, 'drivers': drivers, 'nla_tracks': nla,
            'action_blend_type': ad.action_blend_type, 'action_influence': ad.action_influence,
            'action_scope': 'Observed frame zero only; any later reparent/detach must explicitly handle retained actions'}


def array_hash(sequence, prop, width, dtype):
    v = np.empty(len(sequence) * width, dtype=dtype)
    sequence.foreach_get(prop, v)
    return sha(v.tobytes()), v


def mesh_summary(m, matrix):
    combined = hashlib.sha256()
    fields = {}
    raw_vertices = None
    for label, seq, prop, size, dtype in [
            ('positions', m.vertices, 'co', 3, np.float32),
            ('loop_vertex_indices', m.loops, 'vertex_index', 1, np.int32),
            ('polygon_loop_start', m.polygons, 'loop_start', 1, np.int32),
            ('polygon_loop_total', m.polygons, 'loop_total', 1, np.int32),
            ('polygon_material_index', m.polygons, 'material_index', 1, np.int32)]:
        digest, values = array_hash(seq, prop, size, dtype)
        fields[label] = digest
        combined.update(values.tobytes())
        if label == 'positions':
            raw_vertices = values.reshape(-1, 3).astype(np.float64)
    uv = []
    for layer in m.uv_layers:
        digest, values = array_hash(layer.uv, 'vector', 2, np.float32)
        combined.update(values.tobytes())
        uv.append({'name': layer.name, 'loop_count': len(layer.uv), 'sha256': digest,
                   'active_render': layer.active_render, 'active_clone': layer.active_clone})
    m.calc_loop_triangles()
    tri_hash, tri = array_hash(m.loop_triangles, 'vertices', 3, np.int32)
    w = np.asarray(matrix, dtype=np.float64)
    world = raw_vertices @ w[:3, :3].T + w[:3, 3]
    return {'vertices': len(m.vertices), 'edges': len(m.edges), 'loops': len(m.loops),
            'polygons': len(m.polygons), 'triangles': len(m.loop_triangles),
            'component_sha256': fields, 'triangle_indices_sha256': tri_hash,
            'authored_geometry_uv': combined.hexdigest(), 'uv_layers': uv,
            'active_uv': m.uv_layers.active.name if m.uv_layers.active else None,
            'materials': [x.name if x else None for x in m.materials],
            'world_positions_float64_sha256': sha(world.tobytes()),
            'world_bounds': None if not len(world) else [world.min(axis=0).tolist(), world.max(axis=0).tolist()],
            'finite': bool(np.isfinite(world).all())}, world


def evaluated_summary(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    try:
        return mesh_summary(m, e.matrix_world)
    finally:
        e.to_mesh_clear()


def appearance(o):
    return {'slots': [{'link': s.link, 'material': s.material.name if s.material else None} for s in o.material_slots],
            'active_material_index': o.active_material_index}


def node_tree_record(tree):
    if tree is None:
        return None
    return {'name': tree.name, 'nodes': [
        {'name': n.name, 'type': n.bl_idname, 'properties': rna_values(n),
         'input_defaults': {str(i) + ':' + s.name: value_record(s.default_value)
                            for i, s in enumerate(n.inputs) if hasattr(s, 'default_value')}} for n in tree.nodes],
        'links': [[l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier] for l in tree.links]}


def main():
    snapshots_from_chunks = {}
    for item in I['expected_snapshot_chunks']:
        chunk_path = input_path.parent / item['path']
        assert chunk_path.parent == input_path.parent
        content = chunk_path.read_bytes()
        assert len(content) == item['bytes'] and sha(content) == item['sha256']
        chunk = json.loads(content)
        assert len(chunk) == item['objects'] and not (snapshots_from_chunks.keys() & chunk.keys())
        snapshots_from_chunks.update(chunk)
    assert set(snapshots_from_chunks) == set(I['whitelist'])
    I['expected_snapshots'] = snapshots_from_chunks
    assert list(bpy.app.version) == I['blender_version'] and bpy.app.build_hash.decode() == I['blender_build_hash']
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert source.stat().st_size == I['source_bytes'] and sha(source.read_bytes()) == I['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
    assert bpy.context.evaluated_depsgraph_get().mode == 'VIEWPORT'
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    print('OPENED_PINNED_TEXTURED_SOURCE', len(bpy.data.objects), flush=True)
    names = set(bpy.data.objects.keys())
    object_identity_before = {o.name: o.as_pointer() for o in bpy.data.objects}
    report['object_count'] = len(names)
    if len(names) != I['expected_native_object_count']:
        problem('scene', 'native object count differs from pinned readback', len(names))
    missing = sorted(set(I['whitelist']) - names)
    report['missing_whitelist_objects'] = missing
    if missing:
        problem('scene', 'missing fixed whitelist', missing)
        report['status'] = 'READ_ONLY_INTAKE_BLOCKED'
        return
    scope = set(I['scope_names'])
    whitelist = set(I['whitelist'])
    observed_scope = set()
    for row in I['stations']:
        for key in ('carrier', 'brake'):
            root = bpy.data.objects[row[key]]
            observed_scope.add(root.name)
            observed_scope.update(x.name for x in root.children_recursive)
    report['scope_identity'] = {'expected_count': len(scope), 'actual_count': len(observed_scope),
                                'added': sorted(observed_scope - scope), 'missing': sorted(scope - observed_scope)}
    if observed_scope != scope:
        problem('scene', 'moving descendants differ from recorded 160-object scope', report['scope_identity'])
    fonts = sorted(n for n in names if n.startswith('SOURCE_BL_Tyre_'))
    report['source_font_objects'] = fonts
    report['source_font_count'] = len(fonts)
    if fonts:
        problem('scene', 'unexpected tyre source FONT identities; inspect rather than apply Master assumptions', fonts)
    profiles = sorted(set(I['missing_original_tyre_profiles_expected']) & names)
    report['original_tyre_profiles_present'] = profiles
    if profiles:
        problem('scene', 'unexpected original tyre profiles', profiles)
    new_frames = [f'S543_{i}_native_steering_joint_frame' for i in range(4)]
    if set(new_frames) & names:
        problem('scene', 'repair frames already exist in pinned source', sorted(set(new_frames) & names))
    by_data = {}
    for o in bpy.data.objects:
        if o.data:
            by_data.setdefault(o.data.as_pointer(), []).append(o.name)
    glyphs = {n for row in I['stations'] for n in row['glyphs']}
    glyph_station = {n: row['station'] for row in I['stations'] for n in row['glyphs']}
    records = []
    snapshots = {}
    world_before = {o.name: [list(r) for r in o.matrix_world] for o in bpy.data.objects}
    for name in sorted(whitelist):
        o = bpy.data.objects[name]
        old = I['expected_snapshots'][name]
        current = {'type': o.type, 'parent': o.parent.name if o.parent else None,
                   'world': [list(r) for r in o.matrix_world], 'local': [list(r) for r in o.matrix_local],
                   'hide_render': o.hide_render, 'hide_viewport': o.hide_viewport,
                   'materials': [x.name if x else None for x in o.data.materials] if hasattr(o.data, 'materials') else [],
                   'collections': sorted(c.name for c in o.users_collection)}
        if o.type == 'MESH':
            raw, _ = mesh_summary(o.data, o.matrix_world)
            current['authored_geometry_uv'] = raw['authored_geometry_uv']
        else:
            raw = None
            current['authored_geometry_uv'] = sha(b'')
        mismatch = []
        for key, expected in old.items():
            if key in {'world', 'local'}:
                delta = float(np.max(np.abs(np.asarray(current[key]) - np.asarray(expected))))
                if delta > 1e-6:
                    mismatch.append([key, delta])
            elif current[key] != expected:
                mismatch.append([key, current[key], expected])
        if mismatch:
            problem(name, 'pinned saved identity mismatch', mismatch)
        row = {'name': name, **current, 'core_object': name in I['core_names'],
               'parent_type': o.parent_type, 'parent_bone': o.parent_bone,
               'matrix_basis': [list(r) for r in o.matrix_basis],
               'matrix_parent_inverse': [list(r) for r in o.matrix_parent_inverse],
               'rotation_mode': o.rotation_mode, 'hide_get': o.hide_get(),
               'instance_type': o.instance_type, 'instance_collection': o.instance_collection.name if o.instance_collection else None,
               'object_animation': animation_record(o, name),
               'data_animation': animation_record(o.data, name + ':data', True),
               'constraints': [rna_values(c) for c in o.constraints],
               'modifiers': [rna_values(m) for m in o.modifiers],
               'shape_keys': None if not getattr(o.data, 'shape_keys', None) else o.data.shape_keys.name,
               'mesh_data': None if not o.data else {'name': o.data.name, 'users': o.data.users,
                   'object_users': sorted(by_data[o.data.as_pointer()]), 'library': o.data.library.filepath if o.data.library else None},
               'custom_identity': {k: value_record(o.get(k)) for k in ('tyreIndex', 'originalEmbossName', 'detail_meshes') if k in o},
               'material_slots': appearance(o), 'raw_geometry': raw}
        if o.parent_type != 'OBJECT' or o.rigid_body or o.rigid_body_constraint or o.pose or o.type == 'ARMATURE' or o.library or (o.data and o.data.library):
            problem(name, 'unsupported parenting, linked library, physical simulation or pose input')
        if o.constraints or o.instance_type != 'NONE' or getattr(o.data, 'shape_keys', None):
            problem(name, 'unqualified constraints, instancing or keyed data')
        if name in glyphs and (o.type != 'MESH' or len(o.modifiers) != 0):
            problem(name, 'BAKED_GLYPH_ASSUMPTION_REJECTED', {'type': o.type, 'modifiers': row['modifiers']})
        if name in glyphs and (o.get('tyreIndex') != glyph_station[name] or o.get('originalEmbossName') != name):
            problem(name, 'glyph semantic identity mismatch', row['custom_identity'])
        for m in o.modifiers:
            if m.show_viewport and m.type not in {'BEVEL', 'SOLIDIFY', 'WEIGHTED_NORMAL'}:
                problem(name, 'unknown active modifier; NODES/SUBSURF are not implicitly qualified', m.type)
        if o.type == 'MESH':
            ev, _ = evaluated_summary(o)
            row['evaluated_geometry'] = ev
            snapshots[name] = ev
            if not ev['finite'] or not ev['vertices']:
                problem(name, 'empty or nonfinite evaluated geometry')
        records.append(row)
    report['object_records'] = records
    write('objects.json', records)
    print('FIXED_SCOPE_READ', len(records), 'GEOMETRY', len(snapshots), flush=True)

    # Compact whole-scene reverse-reference scan: no outside evaluated meshes.
    reverse = []
    dependencies = []
    unreadable = []
    collection_cache = {}
    owner_contexts = {}
    no_idproperty_storage_types = set()
    def affected(value):
        if isinstance(value, bpy.types.Object):
            return value.name in scope
        if isinstance(value, bpy.types.Collection):
            if value.as_pointer() not in collection_cache:
                collection_cache[value.as_pointer()] = sorted(o.name for o in value.all_objects if o.name in scope)
            return bool(collection_cache[value.as_pointer()])
        return False
    def pointer(owner, label, field, value):
        if not isinstance(value, (bpy.types.Object, bpy.types.Collection)):
            return
        row = {'owner': owner, 'location': label, 'field': field, 'target': idref(value)}
        contexts = owner_contexts.get(owner, [owner])
        if owner in owner_contexts:
            row['using_objects'] = contexts
        if affected(value) and not all(n in scope for n in contexts):
            reverse.append(row)
        if any(n in whitelist for n in contexts):
            dependencies.append(row)
            if label not in {'object_parent'}:
                problem(owner, 'relevant Object/Collection dependency requires explicit qualification', row)
    def scan_idprop_value(value, owner, label, depth=0):
        if depth > 8:
            unreadable.append({'owner': owner, 'location': label, 'error': 'ID-property nesting exceeds explicit bound'})
            return
        if isinstance(value, bpy.types.ID):
            pointer(owner, label, 'id_property', value)
        elif hasattr(value, 'items'):
            for key, child in value.items():
                scan_idprop_value(child, owner, label + ':' + str(key), depth + 1)
        elif isinstance(value, (list, tuple)) or type(value).__name__ in {'IDPropertyArray', 'bpy_prop_array'}:
            if len(value) > 10000:
                unreadable.append({'owner': owner, 'location': label, 'error': 'ID-property array exceeds explicit bound'})
            else:
                for index, child in enumerate(value):
                    scan_idprop_value(child, owner, label + ':' + str(index), depth + 1)
        elif value is not None and not isinstance(value, (str, int, bool, float)):
            unreadable.append({'owner': owner, 'location': label, 'error': 'Unknown ID-property value type ' + type(value).__name__})
    def scan_block(block, owner, label, include_collections=False, trail=()):
        if block is None:
            return
        address = block.as_pointer()
        if address in trail:
            return
        if len(trail) > 4:
            unreadable.append({'owner': owner, 'location': label, 'error': 'RNA collection nesting exceeds explicit bound'})
            return
        trail = trail + (address,)
        try:
            if hasattr(block, 'keys'):
                for key in block.keys():
                    scan_idprop_value(block[key], owner, label + ':IDPROPERTY:' + key)
        except TypeError as exc:
            if 'doesn\'t support IDProperties' in str(exc):
                no_idproperty_storage_types.add(block.bl_rna.identifier)
            else:
                unreadable.append({'owner': owner, 'location': label, 'error': 'Unreadable ID properties: ' + str(exc)})
        except Exception as exc:
            unreadable.append({'owner': owner, 'location': label, 'error': 'Unreadable ID properties: ' + str(exc)})
        for prop in block.bl_rna.properties:
            if prop.identifier in {'rna_type', 'id_data', 'original'}:
                continue
            try:
                if prop.type == 'POINTER':
                    pointer(owner, label, prop.identifier, getattr(block, prop.identifier))
                elif prop.type == 'COLLECTION' and include_collections:
                    children = getattr(block, prop.identifier)
                    if len(children) > 10000:
                        raise ValueError('RNA collection exceeds explicit bound')
                    for index, child in enumerate(children):
                        child_label = label + ':' + prop.identifier + ':' + str(index)
                        if isinstance(child, bpy.types.ID):
                            pointer(owner, child_label, 'collection_item', child)
                        elif hasattr(child, 'bl_rna'):
                            scan_block(child, owner, child_label, True, trail)
                        else:
                            unreadable.append({'owner': owner, 'location': child_label, 'error': 'Unknown RNA collection item type'})
            except Exception as exc:
                unreadable.append({'owner': owner, 'location': label, 'field': prop.identifier, 'error': str(exc)})
    def scan_drivers(block, owner, label):
        ad = getattr(block, 'animation_data', None)
        if ad:
            for f in ad.drivers:
                if f.driver.type == 'SCRIPTED' and not f.driver.is_simple_expression:
                    problem(owner, 'non-simple scripted driver has unknown implicit dependencies',
                            {'location': label, 'path': f.data_path, 'expression': f.driver.expression})
                for v in f.driver.variables:
                    for t in v.targets:
                        pointer(owner, label + ':' + f.data_path, v.name, t.id)
    def scan_tree(tree, owner, label, seen):
        if tree is None or tree.as_pointer() in seen:
            return
        seen.add(tree.as_pointer())
        scan_block(tree, owner, label + ':tree')
        scan_drivers(tree, owner, label + ':tree_drivers')
        for n in tree.nodes:
            scan_block(n, owner, label + ':' + n.name)
            for s in n.inputs:
                if hasattr(s, 'default_value'):
                    pointer(owner, label + ':' + n.name, s.name, s.default_value)
                elif getattr(s, 'type', None) in {'OBJECT', 'COLLECTION'}:
                    problem(owner, 'node reference socket lacks a readable static default; dependency remains unknown',
                            {'tree': tree.name, 'node': n.name, 'socket': s.name, 'linked': s.is_linked})
            if hasattr(n, 'node_tree'):
                scan_tree(n.node_tree, owner, label + ':' + n.name, seen)
    scanned = 0
    material_owners = {}
    for o in bpy.data.objects:
        scanned += 1
        if len(o.particle_systems):
            problem(o.name, 'UNKNOWN_PARTICLE_SYSTEM_DEPENDENCIES: non-ID ParticleSystem/settings chains are not qualified',
                    [s.name for s in o.particle_systems])
        if o.pose or o.type == 'ARMATURE':
            problem(o.name, 'UNKNOWN_POSE_ARMATURE_DEPENDENCIES: bone/pose constraint chains are not qualified')
        pointer(o.name, 'object_parent', 'parent', o.parent)
        pointer(o.name, 'instance_collection', 'instance_collection', o.instance_collection)
        # Object RNA itself contains parent/instance pointers already handled;
        # only its ID properties are added here to avoid duplicate pointer rows.
        try:
            for key in o.keys():
                scan_idprop_value(o[key], o.name, 'object:IDPROPERTY:' + key)
        except Exception as exc:
            unreadable.append({'owner': o.name, 'location': 'object_id_properties', 'error': str(exc)})
        scan_block(o.data, o.name, 'data')
        scan_block(o.rigid_body_constraint, o.name, 'rigid_body_constraint')
        scan_drivers(o, o.name, 'object_driver')
        scan_drivers(o.data, o.name, 'data_driver')
        scan_drivers(getattr(o.data, 'shape_keys', None), o.name, 'shape_key_driver')
        for item in list(o.constraints) + list(o.modifiers):
            scan_block(item, o.name, item.type + ':' + item.name, True)
            if item.type == 'NODES':
                scan_tree(item.node_group, o.name, 'modifier_nodes:' + item.name, set())
        for slot in o.material_slots:
            if slot.material:
                material_owners.setdefault(slot.material.name, {'material': slot.material, 'owners': set()})['owners'].add(o.name)
    for name, item in sorted(material_owners.items()):
        material = item['material']
        owner = '<material:' + name + '>'
        owner_contexts[owner] = sorted(item['owners'])
        scan_block(material, owner, 'material:' + name)
        scan_drivers(material, owner, 'material_driver:' + name)
        scan_tree(material.node_tree, owner, 'material:' + name, set())
    if bpy.context.scene.world:
        scan_block(bpy.context.scene.world, '<world>', 'world')
        scan_drivers(bpy.context.scene.world, '<world>', 'world_driver')
        scan_tree(bpy.context.scene.world.node_tree, '<world>', 'world', set())
    for row in reverse:
        problem(row['owner'], 'external reference to moving scope', row)
    if unreadable:
        problem('reverse_index', 'unreadable references prevent qualification', unreadable)
    report['reverse_index'] = {'objects_scanned': scanned, 'outside_evaluated_meshes': 0,
                               'external_references': reverse, 'scoped_object_collection_dependencies': dependencies,
                               'unreadable': unreadable, 'collection_reference_cache_count': len(collection_cache),
                               'unique_materials_scanned': len(material_owners),
                               'api_confirmed_no_idproperty_storage_types': sorted(no_idproperty_storage_types)}
    write('dependency-index.json', report['reverse_index'])
    print('REVERSE_INDEX_COMPLETE', scanned, len(reverse), flush=True)

    materials = {slot.material.name: slot.material for n in I['geometry_names']
                 for slot in bpy.data.objects[n].material_slots if slot.material}
    material_records = {name: {'use_nodes': m.use_nodes, 'node_tree': node_tree_record(m.node_tree),
                               'diffuse_color': list(m.diffuse_color), 'roughness': m.roughness,
                               'metallic': m.metallic} for name, m in sorted(materials.items())}
    report['material_records'] = material_records
    write('materials.json', material_records)
    fits = []
    for s in I['stations']:
        spin = bpy.data.objects[s['spin']]
        drum = bpy.data.objects[s['drum']]
        king = bpy.data.objects[s['kingpin']]
        _, xyz = evaluated_summary(drum)
        inv = np.asarray(spin.matrix_world.inverted(), dtype=np.float64)
        local = xyz @ inv[:3, :3].T + inv[:3, 3]
        radius = np.linalg.norm(local[:, [0, 2]], axis=1)
        ring = local[radius > radius.max() * .99][:, [0, 2]]
        A = np.c_[2 * ring, np.ones(len(ring))]
        q, _, rank, _ = np.linalg.lstsq(A, (ring * ring).sum(axis=1), rcond=None)
        rad = math.sqrt(float(q[2] + q[0] ** 2 + q[1] ** 2))
        residual = float(np.max(np.abs(np.linalg.norm(ring - q[:2], axis=1) - rad)))
        _, king_xyz = evaluated_summary(king)
        covariance = np.cov(king_xyz - king_xyz.mean(axis=0), rowvar=False)
        values, vectors = np.linalg.eigh(covariance)
        axis = vectors[:, int(np.argmax(np.abs(vectors[2, :])))]
        if axis[2] < 0:
            axis *= -1
        row = {'station': s['station'], 'drum': drum.name, 'native_drum_vertices': len(drum.data.vertices),
               'ring_vertices': len(ring), 'fit_rank': int(rank), 'fitted_radius_m': rad,
               'circle_centre_spin_xz_m': q[:2].tolist(), 'radial_max_residual_m': residual,
               'axis_span_m': [float(local[:, 1].min()), float(local[:, 1].max())],
               'kingpin_centre_m': king_xyz.mean(axis=0).tolist(), 'kingpin_axis': axis.tolist(),
               'kingpin_covariance_eigenvalues': values.tolist()}
        row['source_cylinder_dimensions_match'] = bool(rank == 3 and np.linalg.norm(q[:2]) < 2e-6 and abs(rad - .335) < 2e-6
            and abs(np.ptp(local[:, 1]) - .13) < 2e-6 and residual < 2e-6)
        row['kingpin_vertical_axis_qualified'] = bool(axis[2] > .999999 and values[2] > 20 * values[1])
        if not row['source_cylinder_dimensions_match'] or not row['kingpin_vertical_axis_qualified']:
            problem(drum.name, 'drum or kingpin retained authoring fit is not qualified', row)
        fits.append(row)
    report['station_fits'] = fits
    # Re-read summaries without changing any object, frame, material or visibility.
    repeat = []
    for name, before in snapshots.items():
        after, _ = evaluated_summary(bpy.data.objects[name])
        if before != after:
            repeat.append({'object': name, 'changed_fields': [k for k in before if before[k] != after[k]]})
    material_after = {name: {'use_nodes': m.use_nodes, 'node_tree': node_tree_record(m.node_tree),
                             'diffuse_color': list(m.diffuse_color), 'roughness': m.roughness,
                             'metallic': m.metallic} for name, m in sorted(materials.items())}
    matrix_changes = [o.name for o in bpy.data.objects if world_before.get(o.name) != [list(r) for r in o.matrix_world]]
    object_identity_after = {o.name: o.as_pointer() for o in bpy.data.objects}
    object_identity_changes = {'added': sorted(object_identity_after.keys() - object_identity_before.keys()),
                               'removed': sorted(object_identity_before.keys() - object_identity_after.keys()),
                               'replaced': sorted(n for n in object_identity_before.keys() & object_identity_after.keys()
                                                  if object_identity_before[n] != object_identity_after[n])}
    report['same_process_readback'] = {'evaluated_geometry_rechecked': len(snapshots), 'geometry_changes': repeat,
                                     'all_original_matrices_rechecked': len(world_before), 'matrix_changes': matrix_changes,
                                     'object_identity_changes': object_identity_changes,
                                     'material_records_identical': material_after == material_records}
    if repeat or matrix_changes or any(object_identity_changes.values()) or material_after != material_records:
        problem('same_process_readback', 'read-only observations changed; no portability qualification', report['same_process_readback'])
    # Exact prior export membership only; no blanket S543 ancestor exclusion is changed.
    excluded = {'D12A_525A', 'S543_COOLING', 'S543_SUSPENSION', 'S543_STARTING', 'C5_STARTER',
                'C5_FLYWHEEL_RING', 'MZN_PREOIL', 'STARTING_ENGINE_MOUNT', 'S543_CARDAN', 'S543_TRANSMISSION'}
    def allowed(o):
        if o.hide_render or o.name.startswith(('SOURCE_', 'ARCHIVE_', 'CUTTER_')):
            return False
        while o:
            if o.name in excluded:
                return False
            o = o.parent
        return True
    root = bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
    selected = {root.name} | {o.name for o in root.children_recursive if allowed(o)}
    expected = set(I['previous_export_names'])
    report['old_export_membership'] = {'actual_count': len(selected), 'matches_saved_850_names': selected == expected,
                                      'added': sorted(selected - expected), 'missing': sorted(expected - selected)}
    if selected != expected:
        problem('export_selection', 'prior export membership changed', report['old_export_membership'])
    report['baked_glyph_count'] = len(glyphs)
    report['status'] = 'READ_ONLY_INTAKE_BLOCKED' if issues else 'READ_ONLY_INTAKE_ELIGIBLE_FOR_PARENT_CHAIN_PROPOSAL_ONLY'


started = time.monotonic()
try:
    main()
except Exception as exc:
    report['status'] = 'READ_ONLY_INTAKE_ERROR'
    report['exception'] = type(exc).__name__ + ': ' + str(exc)
    report['traceback'] = traceback.format_exc()
finally:
    report['elapsed_seconds'] = time.monotonic() - started
    try:
        report['source_sha256_after'] = sha(source.read_bytes())
    except Exception as exc:
        report['source_sha256_after'] = None
        report['source_final_read_error'] = type(exc).__name__ + ': ' + str(exc)
    report['source_unchanged'] = report['source_sha256_after'] == I['source_sha256']
    if not report['source_unchanged']:
        report['status'] = 'READ_ONLY_INTAKE_SOURCE_CHANGED'
    # Detailed parts already have their own files; avoid duplicating them.
    for key, filename in [('object_records', 'objects.json'), ('material_records', 'materials.json')]:
        if key in report:
            del report[key]
            report[key + '_file'] = filename
    write('native-report.json', report)
    print('NATIVE_READ_TERMINAL', report['status'], 'ISSUES', len(issues), flush=True)
if report['status'] != 'READ_ONLY_INTAKE_ELIGIBLE_FOR_PARENT_CHAIN_PROPOSAL_ONLY':
    raise SystemExit(1)
