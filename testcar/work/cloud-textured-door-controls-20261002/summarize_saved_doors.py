"""Summarize fixed saved native records; never open Blender or change a source."""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'testcar/work'
GRAPH = BASE / 'cloud-wheel-export-graph-20261002/run-02/native'
SOURCE_SHA = '48dbc4987780b8f3781aa6c815452d140c1f2bccfd10df0c3dbc7974d04fdeea'
GLB_SHA = 'e99d275080737a520293c548d947401c6910cda3bc86d101dc57396bee9c587d'


def record(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    output = HERE / 'static-findings.json'
    assert not output.exists(), 'Preserve previous evidence'
    source = ROOT.parent / 'maz-canonical-remote-9816a330-20261002/restored/MAZ543A_Textured_Front_Wheel_Parent_Study.blend'
    glb = ROOT.parent / 'maz-static-glb-remote-cfe242a8-20261002/restored/native-static.glb'
    paths = [source, glb, GRAPH / 'object-inventory.json', GRAPH / 'native-graph.json',
             GRAPH / 'native-report.json', GRAPH / 'stations.json',
             GRAPH.parents[1] / 'inspect_native_graph.py',
             BASE / 'cloud-native-static-export-20261002/run-03/native/native-references.json',
             BASE / 'cloud-cab-door-dependencies-20261001/inventory.json',
             ROOT / 'testcar/scripts/blender-export.py',
             ROOT / 'testcar/scripts/native-door-axis-controls.py', Path(__file__)]
    before = [record(p) for p in paths]
    assert before[0]['sha256'] == SOURCE_SHA and before[0]['bytes'] == 100052636
    assert before[1]['sha256'] == GLB_SHA and before[1]['bytes'] == 134267928
    inventory = json.loads(paths[2].read_text())
    graph = json.loads(paths[3].read_text())
    report = json.loads(paths[4].read_text())
    assert report['status'] == 'READ_ONLY_SAVED_FRAME_GRAPH_PASS'
    assert report['input_hashes_before']['artifact'] == before[0]
    assert report['input_hashes_after']['artifact'] == before[0]
    refs = json.loads(paths[7].read_text())
    old = json.loads(paths[8].read_text())
    old_by_name = {d['hinge']: d for d in old['doors']}
    with glb.open('rb') as f:
        magic, version, total = struct.unpack('<4sII', f.read(12))
        length, kind = struct.unpack('<II', f.read(8))
        assert (magic, version, total, kind) == (b'glTF', 2, before[1]['bytes'], 0x4e4f534a)
        gltf = json.loads(f.read(length))
    nodes = {n['name']: n for n in gltf['nodes'] if 'name' in n}
    rows = []
    for hinge, side, index in [('cab_pivot_002', -1, 0), ('cab_pivot_003', -1, 1),
                               ('cab_pivot_006', 1, 0), ('cab_pivot_007', 1, 1)]:
        item, g, prior = inventory[hinge], graph['records'][hinge], old_by_name[hinge]
        prefix = f'BL_Door_{side}_{index}_'
        children = [prefix + v for v in ('handle', 'lock', 'window')]
        green = f'BL_Merged_{hinge}_OD_green_aged_enamel'
        rubber = f'BL_Merged_{hinge}_Rubber_window_seals'
        children += [green, rubber]
        assert sorted(children) == g['children']
        assert item['type'] == 'EMPTY' and item['parent'] == 'cab'
        assert item['rotation_mode'] == 'QUATERNION' and item['modifiers'] == []
        fields = ('action', 'action_slot_handle', 'action_blend_type', 'action_influence')
        assert all(k in item and item[k] is None for k in fields)
        assert g['ancestors'] == ['cab', 'MAZ543_REFERENCE_CHASSIS']
        assert g['matrix_basis_rows'] == prior['matrix_basis']
        for name in children:
            assert inventory[name]['type'] == 'MESH' and inventory[name]['parent'] == hinge
            assert inventory[name]['modifiers'] == [] and graph['records'][name]['children'] == []
        prior_parts = {p['name']: p for p in prior['parts']}
        groups = []
        for name, suffixes in [(green, ['fasteners', 'hinge_1.47', 'hinge_1.94', 'hinge_2.38', 'pressed_shell']),
                               (rubber, ['gap', 'handle_recess', 'rubber_seal'])]:
            names = [prefix + s for s in suffixes]
            current = refs['meshes'][refs['nodes'][name]]
            sums = {key: sum(prior_parts[n][key] for n in names) for key in ('vertices', 'triangles')}
            assert all(current[k] == sums[k] for k in sums)
            assert nodes[name]['extras']['detail_meshes'] == len(names)
            groups.append({'current_object': name, 'old_components_supported_by_counts_and_join_code': names,
                           'counts': sums, 'detail_meshes': len(names),
                           'geometric_component_correspondence': 'NOT_YET_MEASURED'})
        rows.append({'hinge': hinge, 'source_side': side, 'door_index': index,
                     'saved_inventory': {k: item[k] for k in ('type', 'parent', 'rotation_mode', *fields)},
                     'saved_graph': {k: g[k] for k in ('ancestors', 'children', 'matrix_basis_rows',
                         'matrix_local_rows', 'matrix_world_rows', 'matrix_parent_inverse_rows')},
                     'current_children': children, 'old44_names_still_present': sorted(set(prior_parts) & set(inventory)),
                     'merged_group_evidence': groups})
    after = [record(p) for p in paths]
    assert before == after
    assert sum(len(r['current_children']) for r in rows) == 20
    assert sum(len(r['old44_names_still_present']) for r in rows) == 12
    assert len(inventory) == 8522 and report['protection_before']['actions_count'] == 552
    result = {'status': 'SAVED_DATA_SCOPE_ESTABLISHED_NOT_FRESH_NATIVE_INTAKE',
              'source_sha256': SOURCE_SHA, 'input_records_before': before, 'input_records_after': after,
              'inputs_unchanged': True, 'objects_current_door_geometry': 20, 'old_names_present': 12,
              'native_animdata_inference': {'code': str(paths[6]), 'lines': '81,96-100',
                  'rule': 'action_slot_handle/action_blend_type/action_influence are None only when ad=obj.animation_data is absent',
                  'finding': 'The four pivots had no AnimData in this source-bound native snapshot; the previous 16-driver control is not installed',
                  'limit': 'No fresh native execution here; custom/UI, constraints and component geometry must still be read before mutation'},
              'doors': rows,
              'next_scope': ['Read current four pivots and cab/root control/ancestor state without advancing frame',
                  'Read current20 mesh identities, raw attributes/materials and closed geometry; retain merged representation',
                  'Uniquely identify three barrel components in each green mesh from its actual topology/geometry; do not assume old axis or raw48 topology',
                  'Preserve all8522 object names/parents/matrices, all552 original actions and current front-wheel bindings',
                  'If identities/axes/dependencies conflict or are ambiguous, stop before adding controls'],
              'limits': ['Counts, names and join provenance do not prove individual merged component correspondence',
                  'No source edit, Blender, export, render, movement, geometry reconstruction or OEM axis claim',
                  'Old six closed contacts remain OPEN; all16 vehicle gates remain OPEN',
                  'Use current measured axes for any later native controls; never only replace the old script source SHA']}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(output), 'door_meshes': 20, 'pivots': 4, 'inputs_unchanged': True}))


if __name__ == '__main__':
    main()
