"""Inspect the saved frame, without selection, evaluation requests, or model writes.

Run only through run_graph_inspection.py after review/publication. This script
opens the exact explicit artifact and emits fresh JSON files. It does not call
frame_set, view_layer.update, evaluated_get, to_mesh, export, save, or render.
"""
import argparse
import json
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_common import (digest, file_record, legacy_stations, load_inputs,
                          original_selector, read_glb_graph, read_only_action_helper,
                          verify_inputs, write_new)
import bpy


def ident(block):
    if block is None:
        return None
    return {'name': block.name, 'type': block.bl_rna.identifier,
            'library': block.library.filepath if block.library else None,
            'pointer_session_only': block.as_pointer()}


def rows(matrix):
    return [[float(value) for value in row] for row in matrix]


def ancestors(obj):
    seen, result = set(), []
    current = obj.parent
    while current:
        assert current.name not in seen, ('native parent cycle', obj.name)
        seen.add(current.name)
        result.append(current.name)
        current = current.parent
    return result


def collections_and_layers():
    collections = {c.name: {'identity': ident(c), 'hide_viewport': c.hide_viewport,
                           'hide_render': c.hide_render, 'hide_select': c.hide_select,
                           'children': sorted(x.name for x in c.children)}
                   for c in bpy.data.collections}
    layers = []
    def visit(lc, scene, layer, path):
        path = path + [lc.name]
        layers.append({'scene': scene.name, 'view_layer': layer.name, 'path': path,
                       'collection': lc.collection.name, 'exclude': lc.exclude,
                       'hide_viewport': lc.hide_viewport, 'holdout': lc.holdout,
                       'indirect_only': lc.indirect_only, 'is_visible': lc.is_visible,
                       'collection_hide_viewport': lc.collection.hide_viewport,
                       'collection_hide_render': lc.collection.hide_render,
                       'collection_hide_select': lc.collection.hide_select})
        for child in lc.children:
            visit(child, scene, layer, path)
    for scene in bpy.data.scenes:
        # Master scene Collections may not appear in bpy.data.collections.
        c = scene.collection
        collections['SCENE_ROOT:' + scene.name] = {
            'identity': ident(c), 'hide_viewport': c.hide_viewport,
            'hide_render': c.hide_render, 'hide_select': c.hide_select,
            'children': sorted(x.name for x in c.children)}
        for layer in scene.view_layers:
            visit(layer.layer_collection, scene, layer, [])
    return {'collections': collections, 'layer_collections': layers}


def snapshot(action_record):
    """Whole saved inventory/state, no mesh payload access."""
    objects, worlds, parents = {}, {}, {}
    scene = bpy.context.scene
    layer = bpy.context.view_layer
    members = set(layer.objects.keys())
    for obj in bpy.data.objects:
        ad = obj.animation_data
        objects[obj.name] = {
            'identity': ident(obj), 'type': obj.type, 'parent': obj.parent.name if obj.parent else None,
            'parent_type': obj.parent_type, 'parent_bone': obj.parent_bone,
            'data': ident(obj.data), 'collections': sorted(c.name for c in obj.users_collection),
            'hide_viewport': obj.hide_viewport, 'hide_render': obj.hide_render,
            'hide_select': obj.hide_select, 'rotation_mode': obj.rotation_mode,
            'hide_get_active_layer': obj.hide_get(view_layer=layer) if obj.name in members else None,
            'select_get_active_layer': obj.select_get(view_layer=layer) if obj.name in members else None,
            'visible_camera': obj.visible_camera, 'visible_shadow': obj.visible_shadow,
            'visible_diffuse': obj.visible_diffuse, 'visible_glossy': obj.visible_glossy,
            'visible_transmission': obj.visible_transmission, 'visible_volume_scatter': obj.visible_volume_scatter,
            'show_instancer_for_viewport': obj.show_instancer_for_viewport,
            'show_instancer_for_render': obj.show_instancer_for_render,
            'instance_type': obj.instance_type, 'instance_collection': ident(obj.instance_collection),
            'action': ident(ad.action) if ad else None,
            'action_slot_handle': ad.action_slot_handle if ad else None,
            'action_blend_type': ad.action_blend_type if ad else None,
            'action_influence': ad.action_influence if ad else None,
            'modifiers': [{'name': m.name, 'type': m.type, 'show_viewport': m.show_viewport,
                           'show_render': m.show_render,
                           'node_group': ident(m.node_group) if m.type == 'NODES' else None}
                          for m in obj.modifiers]}
        worlds[obj.name] = rows(obj.matrix_world)
        parents[obj.name] = objects[obj.name]['parent']
    actions = {a.name: digest(action_record(a)) for a in bpy.data.actions}
    scene_state = [{'name': s.name, 'frame': s.frame_current, 'subframe': s.frame_subframe,
                    'view_layers': [{'name': v.name, 'use': v.use,
                                     'active_object': v.objects.active.name if v.objects.active else None}
                                    for v in s.view_layers]} for s in bpy.data.scenes]
    visibility = collections_and_layers()
    return {'objects': objects, 'visibility': visibility,
            'state': {'objects_sha256': digest(objects), 'object_names_sha256': digest(sorted(objects)),
                      'world_matrices_sha256': digest(worlds), 'parents_sha256': digest(parents),
                      'actions_sha256': digest(actions), 'actions_count': len(actions),
                      'actions_fake_users_sha256': digest({a.name: a.use_fake_user for a in bpy.data.actions}),
                      'collection_layer_visibility_sha256': digest(visibility),
                      'scene_state': scene_state, 'active_scene': scene.name,
                      'active_view_layer': layer.name, 'mode': bpy.context.mode}}


def graph_records(names, inventory):
    result = {}
    scene = bpy.context.scene
    layers = [(layer, set(layer.objects.keys())) for layer in scene.view_layers]
    for name in sorted(names):
        obj = bpy.data.objects[name]
        record = {'inventory_ref': name, 'ancestors': ancestors(obj),
                  'children': sorted(child.name for child in obj.children),
                  'matrix_local_rows': rows(obj.matrix_local),
                  'matrix_world_rows': rows(obj.matrix_world),
                  'matrix_basis_rows': rows(obj.matrix_basis),
                  'matrix_parent_inverse_rows': rows(obj.matrix_parent_inverse),
                  'viewport_visibility': {}}
        for layer, members in layers:
            present = name in members
            record['viewport_visibility'][layer.name] = {
                'included_in_view_layer': present,
                'visible_get_no_viewport': obj.visible_get(view_layer=layer) if present else False,
                'hide_get': obj.hide_get(view_layer=layer) if present else None,
                'select_get': obj.select_get(view_layer=layer) if present else None}
        record['ancestor_raw_flags'] = [
            {'name': ancestor, 'hide_viewport': inventory[ancestor]['hide_viewport'],
             'hide_render': inventory[ancestor]['hide_render'],
             'hide_get_active_layer': inventory[ancestor]['hide_get_active_layer'],
             'collections': inventory[ancestor]['collections']}
            for ancestor in record['ancestors']]
        result[name] = record
    return result


def run(args, report):
    cfg = load_inputs(args.inputs)
    report['input_hashes_before'] = verify_inputs(cfg)
    ip = {key: Path(value['path']) for key, value in cfg['inputs'].items()}
    expected = json.loads(ip['saved_expected'].read_text())
    original = json.loads(ip['original_inputs'].read_text())
    old_report = json.loads(ip['original_report'].read_text())
    assert old_report['saved_sha256'] == cfg['inputs']['artifact']['sha256']
    assert old_report['saved_bytes'] == cfg['inputs']['artifact']['bytes'] and old_report['saved_blend']
    review = read_glb_graph(ip['review_glb'])
    external = read_glb_graph(ip['suspension_glb'])
    previous = set(review['nodes'])
    assert previous == set(original['previous_export_names']) and len(previous) == cfg['expected']['review_nodes']
    assert external['node_count'] == cfg['expected']['suspension_nodes']
    stations = legacy_stations(ip['bindings'], review, original)
    allowed, excluded = original_selector(ip['exporter'])
    action_record, issues = read_only_action_helper(ip['helper'], ip['builder'], bpy)
    assert list(bpy.app.version) == cfg['expected']['blender_version']
    assert bpy.app.build_hash.decode() == cfg['expected']['blender_build_hash']
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    bpy.ops.wm.open_mainfile(filepath=str(ip['artifact']))
    # Loading is the sole bpy operator. Do not change a frame or force an update.
    assert Path(bpy.data.filepath).resolve() == ip['artifact'].resolve()
    assert bpy.context.scene.frame_current == 0 and bpy.context.scene.frame_subframe == 0
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    before = snapshot(action_record)
    report['protection_before'] = before['state']
    assert sorted(before['objects']) == expected['object_names']
    assert len(before['objects']) == cfg['expected']['objects']
    for key in ('world_matrices_sha256', 'parents_sha256', 'actions_sha256'):
        assert before['state'][key] == expected[key], ('saved-state mismatch', key)
    assert not issues, issues
    write_new(args.output / 'object-inventory.json', before['objects'])
    write_new(args.output / 'collection-visibility.json', before['visibility'])
    write_new(args.output / 'protection-before.json', before['state'])
    vehicle = bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
    source_objects = set(before['objects'])
    assert previous <= source_objects
    # Read the original predicate. Never select the objects it returns.
    selected = {vehicle.name} | {o.name for o in vehicle.children_recursive if allowed(o)}
    minimal = set(previous)
    for name in previous:
        minimal.update(ancestors(bpy.data.objects[name]))
    additions = minimal - previous
    assert additions == set(cfg['expected']['minimum_added_names'])
    assert all(bpy.data.objects[name].type == 'EMPTY' for name in additions)
    s543 = bpy.data.objects['S543_SUSPENSION']
    subtree = {s543.name} | {o.name for o in s543.children_recursive}
    full_union = previous | subtree
    full_union_ancestry = set(full_union)
    for name in full_union:
        full_union_ancestry.update(ancestors(bpy.data.objects[name]))
    moved = set(original['scope_names'])
    assert len(moved) == cfg['expected']['moved_scope'] and moved <= previous
    rejected = {}
    for name in sorted(previous - selected):
        obj = bpy.data.objects[name]
        rejected[name] = {'hide_render': obj.hide_render,
                          'name_prefix_excluded': obj.name.startswith(('SOURCE_', 'ARCHIVE_', 'CUTTER_')),
                          'excluded_ancestry': [n for n in [name] + ancestors(obj) if n in excluded]}
    station_names = {row[key] for row in stations for key in
                     ('carrier', 'spin', 'brake', 'drum', 'upright', 'kingpin')}
    for row in stations:
        if 'joint_frame' in row:
            station_names.add(row['joint_frame'])
    assert station_names <= source_objects
    relevant = full_union_ancestry | minimal | selected | station_names
    records = graph_records(relevant, before['objects'])
    active_layer = bpy.context.view_layer.name
    for row in stations:
        row['native_records'] = {key: records[row[key]] for key in
                                 ('carrier', 'spin', 'brake', 'drum', 'upright', 'kingpin')}
        row['legacy_target_chain_matches'] = (
            bpy.data.objects[row['carrier']].parent.name == 'wheels' and
            bpy.data.objects[row['spin']].parent.name == row['carrier'] and
            bpy.data.objects[row['brake']].parent.name == 'brakes')
    for row in old_report['detached_retained_actions']:
        obj = bpy.data.objects[row['object']]
        assert obj.animation_data and obj.animation_data.action is None
        assert bpy.data.actions[row['action']].use_fake_user
    graph = {'previous_export_names': sorted(previous), 'old_predicate_on_actual_candidate': {
        'selected_names': sorted(selected), 'lost_previous_names': sorted(previous - selected),
        'new_names': sorted(selected - previous), 'rejected_previous_reasons': rejected,
        'moved_scope_lost': sorted(moved - selected), 'excluded_ancestor_roots': excluded},
        'minimal_ancestry_closure': sorted(minimal), 'minimal_added_ancestors': sorted(additions),
        'full_native_s543_subtree': sorted(subtree), 'old_export_union_full_s543': sorted(full_union),
        'union_additional_ancestors': sorted(full_union_ancestry - full_union),
        'full_union_ancestry_closed': sorted(full_union_ancestry),
        'subtree_beyond_minimal_closure': sorted(subtree - minimal),
        'coordinate_scope': 'Native Blender matrices, row-major. GLB node transforms remain glTF Y-up; no cross-space numeric equality claim.',
        'records': records}
    conflicts = {'minimum_vs_external': sorted(minimal & set(external['nodes'])),
                 'full_union_vs_external': sorted(full_union & set(external['nodes'])),
                 'external_only_vs_full_union': sorted(set(external['nodes']) - full_union),
                 'shared_name_records': {n: {'native_inventory': before['objects'][n],
                                            'native_graph': records[n], 'external_glb': external['nodes'][n]}
                                        for n in sorted(full_union & set(external['nodes']))},
                 'interpretation': 'Name overlap is a conflict inventory, not proof of identical data or transforms. No dropping, reparenting, merging or alias resolution.'}
    assert conflicts['minimum_vs_external'] == sorted(['S543_SUSPENSION'] + [f'S543_{s}_upright' for s in range(4)])
    nodes = [{'object': n, **m} for n, row in before['objects'].items()
             for m in row['modifiers'] if m['type'] == 'NODES']
    assert len(nodes) == 9
    visibility = {}
    for label, names in [('old850', previous), ('minimum', minimal), ('s543_subtree', subtree),
                         ('full_union', full_union), ('moved160', moved)]:
        visible = sorted(n for n in names if records[n]['viewport_visibility'][active_layer]['visible_get_no_viewport'])
        visibility[label] = {'count': len(names), 'active_view_layer_visible_count': len(visible),
                             'active_view_layer_visible_names': visible,
                             'active_view_layer_not_visible_names': sorted(names - set(visible)),
                             'raw_hide_render_names': sorted(n for n in names if before['objects'][n]['hide_render']),
                             'types': dict(Counter(before['objects'][n]['type'] for n in names))}
    data_users = defaultdict(list)
    for name, row in before['objects'].items():
        if row['data']:
            data_users[str(row['data']['pointer_session_only'])].append(name)
    graph['relevant_data_users'] = {key: sorted(names) for key, names in data_users.items()
                                    if set(names) & relevant}
    write_new(args.output / 'native-graph.json', graph)
    write_new(args.output / 'stations.json', stations)
    write_new(args.output / 'external-conflicts.json', conflicts)
    write_new(args.output / 'visibility-summary.json', visibility)
    write_new(args.output / 'glb-graphs.json', {'review': review, 'external_suspension': external})
    # Re-read exactly the enumerated snapshot and relevant graph fields.
    after = snapshot(action_record)
    records_after = graph_records(relevant, after['objects'])
    report['protection_after'] = after['state']
    report['relevant_records_comparison'] = {
        'count': len(relevant), 'before_sha256': digest(records),
        'after_sha256': digest(records_after), 'exactly_equal': records_after == records}
    write_new(args.output / 'protection-after.json', after['state'])
    assert after == before, 'An enumerated native snapshot field changed'
    assert records_after == records, 'An enumerated relevant matrix/graph/view-layer field changed'
    assert not issues, issues
    report['input_hashes_after'] = verify_inputs(cfg)
    assert report['input_hashes_after'] == report['input_hashes_before']
    report.update(status='READ_ONLY_SAVED_FRAME_GRAPH_PASS', actual_opened_filepath=bpy.data.filepath,
                  saved_object_names_world_parent_action_digests_exact=True,
                  enumerated_snapshot_fields_unchanged=True,
                  relevant_graph_matrix_view_layer_fields_unchanged=True,
                  original_action_record_data_exact=True,
                  object_count=len(before['objects']), minimum_count=len(minimal),
                  full_subtree_count=len(subtree), full_union_count=len(full_union),
                  old_predicate_selected_count=len(selected), old_names_lost_count=len(previous - selected),
                  moved_scope_lost_count=len(moved - selected), shared_full_union_names=len(conflicts['full_union_vs_external']),
                  unqualified_original_nodes=nodes, active_view_layer=active_layer,
                  legacy_target_chain_matches_by_station={str(s['station']): s['legacy_target_chain_matches'] for s in stations})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', type=Path, required=True, help='Explicit file paths and exact expected hashes')
    parser.add_argument('--output', type=Path, required=True, help='Fresh native evidence directory')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert args.inputs.is_file() and not args.output.exists()
    args.output.mkdir(parents=False)
    report = {'status': 'READ_ONLY_SAVED_FRAME_GRAPH_STARTED', 'frame_advanced': False,
              'selection_pose_visibility_modified': False, 'model_saved': False, 'exported': False,
              'rendered': False, 'geometry_payload_reread': False, 'runtime_route_enabled': False,
              'timeline_status': 'BLOCKED_NOT_EXECUTED', 'all16_vehicle_gates': 'OPEN',
              'protection_scope': 'Only snapshot() and graph_records() fields are compared. All8522 names/world/parents and original action_record digests match saved evidence. Relevant local/world/basis/parent-inverse matrices and active-scene per-view-layer hide/select/visible fields are read twice. No claim for unenumerated Blender RNA, caches, geometry or dependency-graph state.',
              'visibility_limit': 'Saved native flags and visible_get in each active-scene view layer without a viewport. No local-view, camera, occlusion, material or renderer acceptance.'}
    try:
        run(args, report)
    except BaseException as exc:
        report.update(status='READ_ONLY_SAVED_FRAME_GRAPH_FAILED', error=type(exc).__name__ + ': ' + str(exc),
                      traceback=traceback.format_exc())
        write_new(args.output / 'native-report.json', report)
        raise
    write_new(args.output / 'native-report.json', report)
    print(report['status'], flush=True)


if __name__ == '__main__':
    main()
