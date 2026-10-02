"""Pure/static preparation checks. Never imports bpy or launches Blender."""
import ast
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from run_export import verify_inputs, record_exit_observation, native_exit_passes, check_output_limit, decode_exception_status
from validate_glb import test_controls

HERE = Path(__file__).resolve().parent

def main():
    cfg = json.loads((HERE / 'inputs.json').read_text())
    pins = verify_inputs(cfg)
    compiled = []
    for p in sorted(HERE.glob('*.py')):
        compile(p.read_bytes(), str(p), 'exec')
        compiled.append(p.name)
    addon_init = next(Path(v['path']) for v in pins.values() if v['path'].endswith('io_scene_gltf2/__init__.py'))
    tree = ast.parse(addon_init.read_text())
    options = {n.target.id for n in ast.walk(tree) if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
    assert set(cfg['export_options']) <= options, set(cfg['export_options']) - options
    op = cfg['export_options']
    assert op['export_current_frame'] is True and op['export_animations'] is False
    assert op['export_draco_mesh_compression_enable'] is False
    assert op['use_selection'] and op['use_active_scene'] and not op['export_gpu_instances']
    native = ast.parse((HERE / 'export_native.py').read_text())
    calls = []
    for n in ast.walk(native):
        if isinstance(n, ast.Call):
            name = ast.unparse(n.func)
            if name.startswith('bpy.ops.'):
                calls.append(name)
            assert not name.endswith('.frame_set'), 'No global timeline advancement'
            assert not any(token in name for token in ('save_as_mainfile', 'save_mainfile', 'render.render', 'object.convert', 'from_pydata')), name
    assert sorted(calls) == ['bpy.ops.export_scene.gltf', 'bpy.ops.wm.open_mainfile']
    assert cfg['execution']['native_budget_seconds'] == 900
    deadline_controls = []
    for elapsed, expected in [(899.95, True), (900.1, False)]:
        record = {'timed_out': False}
        record_exit_observation(record, 0, elapsed, 900.0, 0.0, 'pure-control')
        assert native_exit_passes(record) is expected
        assert record['native_exit_code'] == 0
        deadline_controls.append({'observed_seconds': elapsed, 'passes': expected})
    capacity_controls = []
    for total, expected in [(768 * 1024**2, True), (768 * 1024**2 + 1, False)]:
        record = {'timed_out': False}
        assert check_output_limit(record, total, 'native-terminal') is expected
        assert record['timed_out'] is False and 'deadline_failure_reason' not in record
        capacity_controls.append({'terminal_bytes': total, 'passes': expected, 'timed_out': record['timed_out']})
    import subprocess
    decode_controls = []
    for exc, expected in [(subprocess.TimeoutExpired('decode', 300), 'TIMEOUT'),
                          (InterruptedError('stop'), 'INTERRUPTED'),
                          (KeyboardInterrupt(), 'INTERRUPTED'),
                          (ValueError('bad report'), 'FAILED')]:
        assert decode_exception_status(exc) == expected
        decode_controls.append({'exception': type(exc).__name__, 'status': expected})
    graph = json.loads(Path(pins['native_graph']['path']).read_text())
    inventory = json.loads(Path(pins['object_inventory']['path']).read_text())
    names = graph['full_union_ancestry_closed']
    from collections import Counter
    assert len(names) == 2675 and len(set(names)) == 2675
    assert len(graph['full_native_s543_subtree']) == 1985
    assert set(names) == set(graph['records'])
    assert dict(Counter(inventory[n]['type'] for n in names)) == cfg['expected']['types']
    assert all(inventory[n]['parent'] is None or inventory[n]['parent'] in names for n in names)
    stations = json.loads(Path(pins['stations']['path']).read_text())
    sys.path.insert(0, str(Path(pins['graph_common']['path']).parent))
    from graph_common import required_station_names
    assert len(required_station_names(stations, inventory)) == 48
    from torsion_neutral import TORSION_NAMES, neutral_schema_issues
    import copy
    fixture = {'name': TORSION_NAMES[0], 'type': 'MESH', 'mesh_name': TORSION_NAMES[0] + '_mesh',
               'data_object_users': [TORSION_NAMES[0]], 'modifiers': [], 'counts': [800, 1568, 3072, 768],
               'show_only_shape_key': False, 'use_relative': True, 'reference_key': 'Basis',
               'animation': {'drivers': [], 'nla': []},
               'keys': [{'name': n, 'value': 0.0, 'relative_key': 'Basis', 'mute': False,
                         'vertex_group': '', 'points': 800} for n in ['Basis', 'Twist_-1', 'Twist_1']]}
    torsion_controls = []
    for name in TORSION_NAMES:
        row = copy.deepcopy(fixture)
        row.update(name=name, mesh_name=name + '_mesh', data_object_users=[name])
        assert not neutral_schema_issues(row), name
    torsion_controls.append('all16 exact neutral identities accepted')
    cases = [('unknown object', lambda r: r.update(name='unknown')),
             ('shared mesh', lambda r: r['data_object_users'].append('other')),
             ('dummy modifier', lambda r: r['modifiers'].append('dummy')),
             ('wrong topology', lambda r: r['counts'].__setitem__(0, 799)),
             ('show only', lambda r: r.update(show_only_shape_key=True)),
             ('absolute keys', lambda r: r.update(use_relative=False)),
             ('missing key', lambda r: r['keys'].pop()),
             ('nonzero twist', lambda r: r['keys'][1].update(value=0.1)),
             ('relative key', lambda r: r['keys'][2].update(relative_key='Twist_-1')),
             ('muted key', lambda r: r['keys'][2].update(mute=True)),
             ('vertex group', lambda r: r['keys'][2].update(vertex_group='group')),
             ('driver', lambda r: r['animation']['drivers'].append('driver')),
             ('NLA', lambda r: r['animation']['nla'].append('track'))]
    for label, mutate in cases:
        row = copy.deepcopy(fixture); mutate(row)
        assert neutral_schema_issues(row), label
        torsion_controls.append(label + ' rejected')
    assert tuple(cfg['expected']['neutral_torsion_names']) == TORSION_NAMES
    assert len(TORSION_NAMES) == len(set(TORSION_NAMES)) == 16
    assert all(name in names for name in TORSION_NAMES)
    from self_component import source_issues, component_issues, count_issues, INT_MAX
    expected_components = {n: inventory[n]['type'] for n in names if inventory[n]['type'] in {'CURVE', 'FONT'}}
    assert cfg['expected']['self_components'] == expected_components
    assert dict(Counter(expected_components.values())) == {'CURVE': 13, 'FONT': 7}
    identity = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    source = {'pointer': 1, 'type': 'CURVE', 'original': {'pointer': 1}, 'matrix_world': identity,
              'instance_type': 'NONE', 'instance_collection': None, 'particle_system_count': 0,
              'modifier_types': ['WELD'], 'is_instancer': False, 'data': {'pointer': 10, 'rna_type': 'Curve'}}
    evaluated = dict(source, pointer=2, data={'pointer': 20, 'rna_type': 'Curve'})
    temporary = dict(source, pointer=3, type='MESH', data={'pointer': 30, 'rna_type': 'Mesh'})
    native_fields = {'position': 'native-coordinate-hash', 'corner_normals': 'native-normal-hash',
                     'uvs': 'native-UV-hash', 'materials': ['actual-material']}
    proof = {'source': source, 'evaluated_object': evaluated, 'saved_matrix': identity,
             'evaluated_mesh_fields': native_fields}
    entry = {'is_instance': True, 'object': temporary, 'instance_object': evaluated, 'parent': evaluated,
             'matrix_world': identity, 'persistent_id': [0] + [INT_MAX] * 7,
             'particle_system': None, 'mesh_fields': native_fields}
    assert not source_issues(source, 'CURVE', identity)
    assert not component_issues(proof, entry)
    for ordinary in (0, 1):
        assert not count_issues(ordinary, [entry])
    component_controls = ['root self Mesh accepted; ordinary count 0 or 1 does not infer multiplicity']
    for label, mutate in [
        ('foreign original', lambda r: r['object'].update(original={'pointer': 99})),
        ('different evaluated parent', lambda r: r['parent'].update(pointer=99)),
        ('displaced matrix', lambda r: r['matrix_world'][0].__setitem__(3, 0.1)),
        ('nested persistent ID', lambda r: r['persistent_id'].__setitem__(1, 0)),
        ('Curve instead of Mesh', lambda r: r['object'].update(type='CURVE')),
        ('particle instance', lambda r: r.update(particle_system={'pointer': 99})),
        ('different native UV', lambda r: r['mesh_fields'].update(uvs='different')),
        ('different material group', lambda r: r['mesh_fields'].update(materials=['other']))]:
        row = copy.deepcopy(entry); mutate(row)
        assert component_issues(proof, row), label
        component_controls.append(label + ' rejected')
    for label, mutate in [('Geometry Nodes source', lambda r: r['modifier_types'].append('NODES')),
                           ('legacy instancer', lambda r: r.update(is_instancer=True))]:
        row = copy.deepcopy(source); mutate(row)
        assert source_issues(row, 'CURVE', identity), label
        component_controls.append(label + ' rejected')
    assert count_issues(1, []) and count_issues(1, [entry, entry])
    component_controls.append('missing or duplicate component rejected')
    result = {'status': 'PURE_STATIC_PREPARATION_PASS', 'compiled': compiled,
              'verified_input_count': len(pins), 'official_option_names': len(op),
              'scope_names': len(names), 'station_names': 48,
              'scope_types': cfg['expected']['types'], 'deadline_controls': deadline_controls,
              'neutral_torsion_schema_controls': torsion_controls,
              'self_component_controls': component_controls,
              'capacity_controls': capacity_controls, 'decode_failure_controls': decode_controls,
              'decoder_controls': test_controls(), 'native_execution': False,
              'asset_created': False, 'all16_vehicle_gates': 'OPEN'}
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
