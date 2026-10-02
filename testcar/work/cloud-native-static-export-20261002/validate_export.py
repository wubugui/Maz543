"""Actual decoded candidate check, in a fresh Python process after Blender exits."""
import argparse
import json
from pathlib import Path
import sys
import traceback
sys.dont_write_bytecode = True
from validate_glb import validate
from run_export import file_record, verify_inputs, write_new


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    cfg = json.loads(a.inputs.read_text())
    verify_inputs(cfg)
    out = a.output.resolve()
    report_path = out / 'decoded-validation.json'
    assert not report_path.exists()
    native = json.loads((out / 'native-report.json').read_text())
    assert native['status'] == 'EXPORTED_SOURCE_PROTECTED_REFERENCES_CAPTURED'
    assert native['source_memory_preserved']
    references = json.loads((out / 'native-references.json').read_text())
    assert not references['hook_errors']
    graph = json.loads(Path(cfg['inputs']['native_graph']['path']).read_text())
    inventory = json.loads(Path(cfg['inputs']['object_inventory']['path']).read_text())
    before = file_record(out / 'native-static.glb')
    try:
        report = validate(out / 'native-static.glb', references, graph, inventory, cfg['validation_limits'])
        errors = {k: v['raw_to_official_normal_max_nonzero_error'] for k, v in references['meshes'].items()}
        maximum = max(errors.values(), default=0)
        report['raw_to_official_normal_max_nonzero_error'] = maximum
        report['zero_normals_replaced_by_official_exporter'] = sum(v['rounded_normal_zero_count'] for v in references['meshes'].values())
        # Zero-vector replacements are disclosed source defects, never raw-normal equivalence.
        report['raw_normal_equivalence'] = 'NOT_CLAIMED_OFFICIAL_ROUND4_NORMALIZATION_AND_ZERO_REPLACEMENT'
        if maximum > cfg['validation_limits']['normal_nonzero_vector_error']:
            report['status'] = 'FAIL_STATIC_NATIVE_TRANSPORT'
            report['issues'].append('Raw-to-official nonzero-normal conversion bound exceeded')
        report['asset_unchanged_during_decode'] = file_record(out / 'native-static.glb') == before
        assert report['asset_unchanged_during_decode']
    except BaseException:
        report = {'status': 'FAIL_STATIC_NATIVE_TRANSPORT', 'error': traceback.format_exc(), 'asset': before}
    write_new(report_path, report)
    print(json.dumps({k: report.get(k) for k in ('status', 'nodes', 'glb_bytes', 'max_world_displacement_m', 'issues')}, indent=2))
    return 0 if report['status'] == 'PASS_STATIC_NATIVE_TRANSPORT' else 1


if __name__ == '__main__':
    raise SystemExit(main())
