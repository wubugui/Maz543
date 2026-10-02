"""Pure-data support for a pinned, read-only saved-wheel graph inspection."""
import ast
import hashlib
import json
import math
import re
import struct
from pathlib import Path


# Explicit saved-candidate roles. Rear stations have no steering-kingpin/joint
# role; all listed roles are mandatory, never filtered by inventory existence.
STATION_ROLE_TABLE = (
    dict(carrier='wheels_pivot_001', spin='wheels_pivot_002', brake='brakes_pivot_001',
         drum='brakes_0003', upright='S543_0_upright', kingpin='S543_0_steering_kingpin', joint_frame='S543_0_native_steering_joint_frame'),
    dict(carrier='wheels_pivot_008', spin='wheels_pivot_009', brake='brakes_pivot_002',
         drum='brakes_0007', upright='S543_1_upright', kingpin='S543_1_steering_kingpin', joint_frame='S543_1_native_steering_joint_frame'),
    dict(carrier='wheels_pivot_015', spin='wheels_pivot_016', brake='brakes_pivot_003',
         drum='brakes_0011', upright='S543_2_upright', kingpin='S543_2_steering_kingpin', joint_frame='S543_2_native_steering_joint_frame'),
    dict(carrier='wheels_pivot_022', spin='wheels_pivot_023', brake='brakes_pivot_004',
         drum='brakes_0015', upright='S543_3_upright', kingpin='S543_3_steering_kingpin', joint_frame='S543_3_native_steering_joint_frame'),
    dict(carrier='wheels_pivot_029', spin='wheels_pivot_030', brake='brakes_pivot_005', drum='brakes_0019', upright='S543_4_upright'),
    dict(carrier='wheels_pivot_036', spin='wheels_pivot_037', brake='brakes_pivot_006', drum='brakes_0023', upright='S543_5_upright'),
    dict(carrier='wheels_pivot_043', spin='wheels_pivot_044', brake='brakes_pivot_007', drum='brakes_0027', upright='S543_6_upright'),
    dict(carrier='wheels_pivot_050', spin='wheels_pivot_051', brake='brakes_pivot_008', drum='brakes_0031', upright='S543_7_upright'),
)


def required_station_names(stations, inventory):
    assert [row['station'] for row in stations] == list(range(8)), 'Station order/identity mismatch'
    all_roles = set().union(*(set(row) for row in STATION_ROLE_TABLE))
    names = set()
    for row, expected in zip(stations, STATION_ROLE_TABLE):
        assert set(row) & all_roles == set(expected), ('Station role-set mismatch', row['station'])
        for role, name in expected.items():
            assert row[role] == name, ('Wrong station role identity', row['station'], role, row[role], name)
            assert name in inventory, ('Missing mandatory station role', row['station'], role, name)
            names.add(name)
    assert len(names) == 48
    return names


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def file_record(path):
    path = Path(path).resolve(strict=True)
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def load_inputs(path):
    cfg = json.loads(Path(path).read_text())
    assert cfg['schema'] == 'maz-wheel-graph-inputs-v1'
    assert set(cfg['inputs']) == {'artifact', 'blender', 'review_glb', 'suspension_glb',
                                 'exporter', 'bindings', 'viewport', 'original_inputs',
                                 'saved_expected', 'original_report', 'builder', 'helper'}
    for row in cfg['inputs'].values():
        assert Path(row['path']).is_absolute(), row['path']
    return cfg


def verify_inputs(cfg):
    actual = {key: file_record(row['path']) for key, row in cfg['inputs'].items()}
    for key, row in actual.items():
        assert row == cfg['inputs'][key], ('input mismatch', key, row)
    return actual


def read_glb_graph(path):
    """Read only the JSON chunk; seek past binary data, with no mesh decoding."""
    path = Path(path)
    with path.open('rb') as stream:
        magic, version, total = struct.unpack('<4sII', stream.read(12))
        assert (magic, version, total) == (b'glTF', 2, path.stat().st_size)
        chunks, document = [], None
        while stream.tell() < total:
            start = stream.tell()
            length, kind = struct.unpack('<II', stream.read(8))
            assert length % 4 == 0 and start + 8 + length <= total
            chunks.append({'offset': start, 'length': length, 'type': kind})
            if kind == 0x4E4F534A:
                assert document is None and len(chunks) == 1
                document = json.loads(stream.read(length).decode('utf-8'))
            else:
                stream.seek(length, 1)
        assert stream.tell() == total and document is not None
    nodes = document['nodes']
    names = [node.get('name') for node in nodes]
    assert all(isinstance(name, str) and name for name in names)
    assert len(names) == len(set(names)), 'Duplicate names cannot be silently merged'
    parents = {}
    for index, node in enumerate(nodes):
        children = node.get('children', [])
        assert len(children) == len(set(children))
        for child in children:
            assert isinstance(child, int) and 0 <= child < len(nodes)
            assert child not in parents and child != index
            parents[child] = index
        assert not ('matrix' in node and any(k in node for k in ('translation', 'rotation', 'scale')))
        for key, count in [('matrix', 16), ('translation', 3), ('rotation', 4), ('scale', 3)]:
            if key in node:
                assert len(node[key]) == count
                assert all(isinstance(v, (int, float)) and math.isfinite(v) for v in node[key])
    for index in range(len(nodes)):
        seen, current = set(), index
        while current in parents:
            assert current not in seen, 'GLB node parent cycle'
            seen.add(current)
            current = parents[current]
    scenes = document.get('scenes', [])
    for scene in scenes:
        for index in scene.get('nodes', []):
            assert 0 <= index < len(nodes) and index not in parents
    return {'nodes': {name: {'index': i, 'parent': names[parents[i]] if i in parents else None,
                            'node': nodes[i]} for i, name in enumerate(names)},
            'scenes': scenes, 'default_scene': document.get('scene'), 'chunks': chunks,
            'node_count': len(nodes), 'binary_payload_decoded': False}


def legacy_stations(path, review_graph, original):
    text = Path(path).read_text()
    tuples = re.findall(r"\[(\d+),'(wheels_pivot_\d+)','(wheels_pivot_\d+)','(brakes_pivot_\d+)'\]", text)
    assert [int(row[0]) for row in tuples] == list(range(8))
    result = []
    for number, carrier, spin, brake in tuples:
        station = int(number)
        row = {'station': station, **STATION_ROLE_TABLE[station]}
        assert (carrier, spin, brake) == (row['carrier'], row['spin'], row['brake'])
        drum = row['drum']
        for name, parent in [(carrier, 'wheels'), (spin, carrier), (brake, 'brakes'), (drum, brake)]:
            assert review_graph['nodes'][name]['parent'] == parent, (name, parent)
        assert 'mesh' in review_graph['nodes'][drum]['node']
        if station < 4:
            prior = original['stations'][station]
            assert all(row[key] == prior[key] for key in ('station', 'carrier', 'spin', 'brake', 'drum', 'upright', 'kingpin'))
        row['drum_identity_scope'] = ('Original saved front-four evidence' if station < 4 else
                                      'Retained legacy drum name and mesh/parent identity; geometry not reread')
        result.append(row)
    return result


def original_selector(path):
    """Extract only the exact old exclusion constant and read-only predicate."""
    tree = ast.parse(Path(path).read_bytes())
    assignment = [n for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'excluded' for t in n.targets)]
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'allowed']
    assert len(assignment) == len(definitions) == 1
    excluded = ast.literal_eval(assignment[0].value)
    assert excluded == {'D12A_525A', 'S543_COOLING', 'S543_SUSPENSION', 'S543_STARTING',
                        'C5_STARTER', 'C5_FLYWHEEL_RING', 'MZN_PREOIL', 'STARTING_ENGINE_MOUNT',
                        'S543_CARDAN', 'S543_TRANSMISSION'}
    namespace = {'excluded': excluded}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['allowed'], sorted(excluded)


def read_only_action_helper(helper_path, builder_path, bpy):
    """Reuse only the four exact helper defs and original nested action_record."""
    names = {'idref', 'value_record', 'rna_values', 'curves_of'}
    definitions = [n for n in ast.parse(Path(helper_path).read_bytes()).body
                   if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in definitions} == names
    h = {'bpy': bpy, 'math': math, 'issues': []}
    # Only reached for unknown original action storage/RNA; never silently pass it.
    def problem(owner, reason, detail=None):
        h['issues'].append({'owner': owner, 'reason': reason, 'detail': detail})
    h['problem'] = problem
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(helper_path), 'exec'), h)
    main = next(n for n in ast.parse(Path(builder_path).read_bytes()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'main')
    actions = [n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'action_record']
    assert len(actions) == 1
    namespace = {'H': h}
    exec(compile(ast.Module(body=actions, type_ignores=[]), str(builder_path), 'exec'), namespace)
    return namespace['action_record'], h['issues']
