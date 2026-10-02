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
    result = {'status': 'PURE_STATIC_PREPARATION_PASS', 'compiled': compiled,
              'verified_input_count': len(pins), 'official_option_names': len(op),
              'scope_names': len(names), 'station_names': 48,
              'scope_types': cfg['expected']['types'], 'deadline_controls': deadline_controls,
              'capacity_controls': capacity_controls, 'decode_failure_controls': decode_controls,
              'decoder_controls': test_controls(), 'native_execution': False,
              'asset_created': False, 'all16_vehicle_gates': 'OPEN'}
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
