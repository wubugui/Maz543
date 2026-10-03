"""Four pure-array tests and one action-storage branch test; no Blender."""

import ast
import json
from pathlib import Path
import unittest

import numpy as np

from components import summarize_components


def fixture(points, edges=(), faces=()):
    e = np.asarray(edges, dtype=np.int32).reshape(-1, 2)
    edge_ids = {tuple(sorted(pair)): i for i, pair in enumerate(edges)}
    vertices, loop_edges, starts, sizes = [], [], [], []
    for face in faces:
        starts.append(len(vertices))
        sizes.append(len(face))
        vertices.extend(face)
        loop_edges.extend(edge_ids[tuple(sorted((a, b)))]
                          for a, b in zip(face, face[1:] + face[:1]))
    return [np.asarray(points, dtype=np.float32).reshape(-1, 3), e,
            *(np.asarray(x, dtype=np.int32) for x in (vertices, loop_edges, starts, sizes)),
            np.eye(4, dtype=np.float64)]


class ComponentsTests(unittest.TestCase):
    def test_disconnected_coincident_vertices_stay_distinct(self):
        args = fixture([(0, 0, 0), (1, 0, 0)] * 2, [(0, 1), (2, 3)])
        before = [a.copy() for a in args]
        report = summarize_components(*args)
        self.assertEqual(report["component_count"], 2)
        self.assertEqual([c["indices"]["vertices"] for c in report["components"]], [[0, 1], [2, 3]])
        self.assertEqual(report["components"][0]["local"], report["components"][1]["local"])
        for a, old in zip(args, before):
            np.testing.assert_array_equal(a, old)
        json.dumps(report, allow_nan=False)

    def test_symmetric_components_have_no_unique_selection(self):
        square = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        args = fixture(square * 2, edges + [(a + 4, b + 4) for a, b in edges],
                       [[0, 1, 2, 3], [4, 5, 6, 7]])
        report = summarize_components(*args)
        self.assertIsNone(report["selection"]["component"])
        self.assertIsNone(report["selection"]["axis"])
        for component in report["components"]:
            pca = component["local"]["pca"]
            self.assertEqual(pca["exact_affine_rank_of_sample_values"], 2)
            self.assertIn([0, 1], pca["exact_equal_eigenvalue_groups"])
            self.assertEqual(len(pca["axis_measures"]), 3)
            self.assertIsNone(pca["axis_selection"])

    def test_noncontiguous_input_indices_round_trip(self):
        args = fixture([(0, 0, 0), (10, 0, 0), (0, 1, 0), (10, 1, 0),
                        (1, 0, 0), (11, 0, 0)],
                       [(1, 3), (0, 2), (3, 5), (2, 4), (5, 1), (4, 0)],
                       [[1, 3, 5], [0, 2, 4]])
        args[-1][:3, 3] = [2, 3, 4]
        report = summarize_components(*args)
        self.assertEqual(report["components"][0]["indices"],
                         {"vertices": [0, 2, 4], "edges": [1, 3, 5],
                          "loops": [3, 4, 5], "polygons": [1]})
        for name, owners in report["original_to_component"].items():
            for original, component in enumerate(owners):
                local = report["original_to_component_local"][name][original]
                self.assertEqual(report["components"][component]["indices"][name][local], original)
        np.testing.assert_array_equal(report["components"][0]["world"]["bounds_min"], [2, 3, 4])

    def test_invalid_indices_and_topology_rejected(self):
        valid = fixture([(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                        [(0, 1), (1, 2), (2, 0)], [[0, 1, 2]])
        mutations = [(1, (0, 1), 3), (2, 0, -1), (3, 0, 3),
                     (3, 0, 1), (4, 0, 1), (5, 0, 2), (0, (0, 0), np.nan)]
        for array, index, value in mutations:
            with self.subTest(array=array, value=value):
                args = [a.copy() for a in valid]
                args[array][index] = value
                with self.assertRaises(ValueError):
                    summarize_components(*args)

    def test_layered_action_does_not_read_legacy_groups(self):
        tree = ast.parse(Path(__file__).with_name('collect_native.py').read_bytes())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        node = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'action_detail')
        namespace = dict(rna=lambda value: {'recorded': str(value)},
                         export={'custom': lambda _: {}}, custom_ui=lambda _: {},
                         action_record=lambda _: {}, H={'curves_of': lambda _: []})
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'isolated_action_detail', 'exec'), namespace)
        class Action:
            use_fake_user = False
            is_action_layered = True
            slots, layers, pose_markers = [], [], []
            @property
            def groups(self):
                if self.is_action_layered:
                    raise AssertionError('Layered action accessed legacy collection')
                return ['legacy_group']
        action = Action()
        self.assertEqual(namespace['action_detail'](action)['groups'], [])
        action.is_action_layered = False
        self.assertEqual(namespace['action_detail'](action)['groups'], [{'recorded': 'legacy_group'}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
