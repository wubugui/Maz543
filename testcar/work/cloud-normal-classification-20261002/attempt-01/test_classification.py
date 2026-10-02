"""Five bounded semantic regression groups for the diagnosis-only side report."""
import ast
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import classify_normals as d
import numpy as np


class ClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((d.CAPTURE / 'capture.json').read_text())
        assert d.replay.runtime_identity() == cls.cfg['runtime']
        cls.decoder = d.replay.load_decoder(cls.cfg['inputs']['decoder']['path'])
        cls.report = json.loads((d.HERE / 'classification.json').read_text())

    def test_1_fixed_corners_and_unchanged_legacy_gate(self):
        parsed = ast.parse((d.EXPORT / 'validate_export.py').read_text())
        gate = next(n for n in ast.walk(parsed) if isinstance(n, ast.If)
                    and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name)
                    and n.test.left.id == 'maximum')
        limits = json.loads((d.EXPORT / 'inputs.json').read_text())['validation_limits']
        for name in ('BL_Front_mirror_face_-1', 'S543_0_halfshaft_bellows'):
            result = next(t for t in self.report['normal_diagnosis']['targets'] if t['object'] == name)
            raw = json.loads((d.CAPTURE / 'run-01' / (name + '.json')).read_text())
            normals = d.replay.unpack_array(raw['arrays']['raw_normals_native'])
            q, c, fallback, errors = d.replay.conversion(normals)
            witness = result['official_conversion']['worst_vector_error_corner']
            index = witness['loop_index']
            self.assertEqual(normals[index].tolist(), witness['r'])
            self.assertEqual(q[index].tolist(), witness['q'])
            self.assertEqual(c[index].tolist(), witness['c'])
            self.assertEqual(float(errors[~fallback].max()), result['official_conversion']['legacy_value'])
            self.assertEqual(result['official_conversion']['legacy_field_name'], d.LEGACY_KEY)
            state = {'maximum': float(errors[~fallback].max()), 'cfg': {'validation_limits': limits},
                     'report': {'status': 'PASS_STATIC_NATIVE_TRANSPORT', 'issues': []}}
            exec(compile(ast.Module(body=[gate], type_ignores=[]), '<original legacy if>', 'exec'), state)
            self.assertEqual(state['report']['status'], 'FAIL_STATIC_NATIVE_TRANSPORT')
            self.assertIn('Raw-to-official nonzero-normal conversion bound exceeded', state['report']['issues'])
            dec = witness['same_corner_decomposition']
            self.assertAlmostEqual(dec['D_squared'], dec['amplitude_squared'] + dec['a_b_chord_squared'], places=14)
            self.assertTrue(witness['triangle_references'])
            if name.startswith('BL_'):
                self.assertEqual(witness['direction']['angle_degrees'], 0)
                self.assertEqual(witness['raw_length'], 0.259321004152298)
                self.assertEqual(witness['raw_to_reproduced_vector_error'], 0.740678995847702)
            else:
                self.assertAlmostEqual(witness['raw_length'], 0.7063049039932805, places=14)
                self.assertGreater(witness['direction']['angle_degrees'], 0)
            self.assertGreater(dec['amplitude_squared'], dec['a_b_chord_squared'])

    def test_2_direction_domain_and_magnitude_not_hidden(self):
        raw = np.asarray([[0, 0, 0], [0.00001, 0, 0], [np.nan, 0, 1], [np.inf, 0, 1]], dtype='<f4')
        with np.errstate(invalid='ignore'):
            _, converted, fallback, _ = d.replay.conversion(raw)
            metrics = d.directions(raw, converted, fallback, 'raw_zero')
        self.assertEqual(list(metrics[2]), ['raw_zero', 'rounded_zero_fallback', 'nonfinite_vector', 'nonfinite_vector'])
        for i in range(4):
            point = d.corner_direction(metrics, i)
            self.assertIsNone(point['angle_degrees'])
            self.assertIsNone(point['chord'])
            self.assertTrue(point['exclusion_reason'])
        json.dumps({'direction': d.direction_summary(metrics),
                    'corners': [d.corner_direction(metrics, i) for i in range(4)],
                    'nonfinite_metric': d.summary([np.nan, np.inf])}, allow_nan=False)
        reverse = d.directions([[1, 0, 0]], [[-1, 0, 0]])
        self.assertEqual(d.corner_direction(reverse, 0)['angle_degrees'], 180)
        self.assertEqual(d.corner_direction(reverse, 0)['chord'], 2)
        same_direction = d.transport(np.tile([2, 0, 0], (3, 1)), np.tile([1, 0, 0], (3, 1)), [False] * 3)
        self.assertEqual(same_direction['max_direction_angle_degrees'], 0)
        self.assertEqual(same_direction['max_vector_error'], 1)
        self.assertEqual(same_direction['numeric_different_components'], 3)
        self.assertEqual(same_direction['classification'], 'NUMERIC_DIFFERENCE_OBSERVED')
        zeros = d.transport(np.zeros((3, 3)), np.ones((3, 3)), [False] * 3)
        self.assertIsNone(zeros['max_direction_angle_degrees'])
        self.assertEqual(zeros['direction']['exclusion_reason_counts'], {'left_zero': 3})
        fallback_transport = d.transport(np.tile([0, 0, 1], (3, 1)), np.tile([0, 0, 1], (3, 1)), [True] * 3)
        self.assertIsNone(fallback_transport['max_direction_angle_degrees'])
        self.assertEqual(fallback_transport['direction']['exclusion_reason_counts'], {'rounded_zero_fallback': 3})
        json.dumps({'zero_transport': zeros, 'fallback_transport': fallback_transport}, allow_nan=False)

    def test_3_exact_bits_signed_zero_and_nonzero_ulp(self):
        plus = np.asarray([[0, 0, 1]] * 3, dtype='<f4')
        minus = plus.copy(); minus[0, 0] = np.float32(-0.0)
        before = (plus.tobytes(), minus.tobytes())
        out = d.transport(plus, minus, [False] * 3)
        self.assertEqual(out['byte_different_components'], 1)
        self.assertEqual(out['numeric_different_components'], 0)
        self.assertEqual(out['signed_zero_only_components'], 1)
        self.assertEqual(out['max_vector_error'], 0)
        changed = plus.copy(); changed[0, 2] = np.nextafter(np.float32(1), np.float32(2))
        out = d.transport(plus, changed, [False] * 3)
        self.assertEqual(out['numeric_different_components'], 1)
        self.assertEqual(out['max_ulp_distance'], 1)
        self.assertGreater(out['max_vector_error'], 0)
        p = np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype='<f4')
        n = p.copy(); n[0, 0] = np.float32(-0.0)
        sig = self.decoder.oriented_signature
        self.assertNotEqual(sig({'POSITION': p}, [0, 1, 2]), sig({'POSITION': n}, [0, 1, 2]))
        self.assertNotEqual(sig({'POSITION': p, 'NORMAL': plus}, [0, 1, 2]),
                            sig({'POSITION': p, 'NORMAL': minus}, [0, 1, 2]))
        self.assertEqual(before, (plus.tobytes(), minus.tobytes()))

    def test_4_oriented_material_multiplicity_and_conditioned_pairing(self):
        p = np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype='<f4')
        attrs = {'POSITION': p, 'NORMAL': np.tile(np.asarray([0, 0, 1], dtype='<f4'), (3, 1)),
                 'TEXCOORD_0': np.zeros((3, 2), dtype='<f4')}
        tri = np.asarray([[0, 1, 2]], dtype='<i4')
        pairs, unresolved = d.pair_triangles(attrs, tri, attrs, np.roll(tri, 1, axis=1), 'A', 'A')
        self.assertEqual(len(pairs), 1); self.assertFalse(unresolved)
        self.assertEqual(pairs[0][2], d.GROUPS[0])
        for other_tri, material in [(tri[:, ::-1], 'A'), (tri, 'B'), (np.tile(tri, (2, 1)), 'A')]:
            pairs, unresolved = d.pair_triangles(attrs, tri, attrs, other_tri, 'A', material)
            self.assertFalse(pairs); self.assertTrue(unresolved)
        doubled = {k: np.concatenate([v, v]) for k, v in attrs.items()}
        doubled_tri = np.asarray([[0, 1, 2], [3, 4, 5]], dtype='<i4')
        # UV alone uniquely distinguishes duplicates, but MUST NOT choose them.
        doubled['TEXCOORD_0'][3:] = 1
        pairs, unresolved = d.pair_triangles(doubled, doubled_tri, doubled, doubled_tri[::-1], 'A', 'A')
        self.assertFalse(pairs); self.assertEqual(unresolved[0]['fresh_triangles'], 2)
        doubled['NORMAL'][3:] *= -1
        pairs, unresolved = d.pair_triangles(doubled, doubled_tri, doubled, doubled_tri[::-1], 'A', 'A')
        self.assertEqual(len(pairs), 2); self.assertFalse(unresolved)
        self.assertEqual({p[2] for p in pairs}, {d.GROUPS[1]})
        # Two left triangles cannot claim the same sole NORMAL match on the right.
        broken = {k: v.copy() for k, v in doubled.items()}; broken['NORMAL'][3:] = broken['NORMAL'][:3]
        pairs, unresolved = d.pair_triangles(broken, doubled_tri, doubled, doubled_tri, 'A', 'A')
        self.assertFalse(pairs); self.assertTrue(unresolved)
        degenerate = np.asarray([[0, 0, 0]], dtype='<i4')
        pairs, unresolved = d.pair_triangles(attrs, degenerate, attrs, degenerate, 'A', 'A')
        self.assertFalse(pairs); self.assertTrue(unresolved)

    def test_5_real_scope_qualification_uv_and_input_guards(self):
        report = self.report; n = report['normal_diagnosis']; s = n['scope']
        self.assertEqual(n['status'], 'DIAGNOSIS_ONLY_NOT_ACCEPTANCE')
        self.assertEqual([s[k] for k in ('objects', 'original_loops', 'triangles', 'expanded_triangle_corners',
                                       'normal_component_occurrences', 'uv_component_occurrences')],
                         [10, 104256, 52216, 156648, 469944, 313296])
        self.assertEqual(n['preserved_qualification'], d.preserved_qualification(self.cfg))
        self.assertIsNone(n['direction_acceptance_limit'])
        c = n['correspondence']
        self.assertEqual((c['position_only_triangles'], c['normal_refined_triangles']), (50680, 1536))
        self.assertFalse(c['unresolved_groups']); self.assertFalse(c['uv_used_for_pairing'])
        self.assertEqual(c['legacy_record_status'], 'FRESH_NOT_CORRESPONDING_RUN03')
        groups = n['converted_glb_transport']
        self.assertTrue(groups[d.GROUPS[0]]['independent_normal_evidence'])
        self.assertFalse(groups[d.GROUPS[1]]['independent_normal_evidence'])
        self.assertEqual(sum(x['numeric_different_components'] for x in groups.values()), 0)
        self.assertEqual(sum(x['signed_zero_only_components'] for x in groups.values()), 23828)
        binding = n['attribute_binding']; uv = binding['uv']
        self.assertEqual(binding['formal_signed_zero_gate'], 'NOT_RUN_OLD_REFERENCE_MISMATCH')
        self.assertEqual(binding['full_attribute_fidelity'], 'NOT_ESTABLISHED')
        self.assertTrue(binding['glb_uv_exact_run03_all_ten'])
        self.assertEqual((uv['components'], uv['numeric_different_components'], uv['signed_zero_only_components']), (313296, 34490, 0))
        self.assertEqual(set(uv['nonzero_ulp_histogram']), {'1', '2', '3', '4', '5'})
        self.assertEqual(uv['max_absolute_difference'], 4.76837158203125e-7)
        self.assertTrue(report['inputs_unchanged'])
        self.assertEqual(report['input_records_before'], report['input_records_after'])
        self.assertEqual(report['input_records_after'], [d.replay.file_record(r['path']) for r in report['input_records_after']])
        guarded = {r['path'] for r in report['input_records_before']}
        for path in (d.EXPORT / 'validate_export.py', d.EXPORT / 'run-03/native/decoded-validation.json', d.HERE / 'design.md'):
            self.assertIn(str(path), guarded)
        self.assertEqual({t['object'] for t in n['targets']}, {t['object'] for t in self.cfg['targets']})


if __name__ == '__main__':
    unittest.main(verbosity=2)
