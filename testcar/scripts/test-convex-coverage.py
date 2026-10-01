#!/usr/bin/env python3
"""Deterministic analytic/adversarial tests; no geometry packages or Blender."""
import json
import math
from pathlib import Path
import random
import sys
import unittest

from convex_coverage import InvalidGeometry, assess_coverage

ROOT = Path(__file__).resolve().parents[1]/"work/cloud-side-rivet-attachment-20261001/coverage-controls"
ROOT.mkdir(parents=True,exist_ok=True)
OCT = [(1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1)]


def rectangle(x0, y0, x1, y1):
    return [[(x0, y0), (x1, y0), (x1, y1)],
            [(x0, y0), (x1, y1), (x0, y1)]]


def frame(hole=(0.4, 0.4, 0.6, 0.6), top=True):
    x0, y0, x1, y1 = hole
    tris = rectangle(-3, -3, x0, 3) + rectangle(x1, -3, 3, 3)
    tris += rectangle(x0, -3, x1, y0)
    if top:
        tris += rectangle(x0, y1, x1, 3)
    return tris


def fan(poly=OCT):
    return [[(0, 0), p, poly[(i + 1) % len(poly)]] for i, p in enumerate(poly)]


def contains(point, tri):
    # Deliberately separate, simple point-sample oracle: this is NOT coverage.
    sides = []
    for a, b in zip(tri, tri[1:] + tri[:1]):
        sides.append((b[0] - a[0]) * (point[1] - a[1]) -
                     (b[1] - a[1]) * (point[0] - a[0]))
    return all(v >= 0 for v in sides) or all(v <= 0 for v in sides)


class CoverageTests(unittest.TestCase):
    reports = {}

    def result(self, name, triangles, footprint=OCT, **kw):
        result = assess_coverage(footprint, triangles, **kw)
        self.reports[name] = result
        self.assertGreaterEqual(result['uncovered_area'], 0)
        return result

    def test_full_support_across_diagonal_seam(self):
        r = self.result('full_diagonal', rectangle(-3, -3, 3, 3))
        self.assertTrue(r['numerical_coverage_pass'])
        self.assertEqual(r['footprint_area'], 14)
        self.assertEqual(r['covered_union_area'], 14)
        self.assertEqual(r['uncovered_area'], 0)
        self.assertEqual(r['pairwise_overlap_area_sum'], 0)

    def test_full_support_across_eight_fan_seams(self):
        r = self.result('full_fan', fan())
        self.assertTrue(r['numerical_coverage_pass'])
        self.assertEqual(r['covered_union_area'], 14)

    def test_interior_hole_evades_all_nine_points(self):
        triangles = frame()
        self.assertTrue(all(any(contains(p, t) for t in triangles) for p in OCT + [(0, 0)]))
        r = self.result('nine_point_false_positive_hole', triangles)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertAlmostEqual(r['uncovered_area'], .04, places=13)
        self.assertTrue(r['uncovered_polygons_local'])
        self.assertLessEqual(r['pairwise_overlap_area_sum'], r['area_tolerance'])

    def test_notch_evades_all_nine_points(self):
        triangles = frame(top=False)
        self.assertTrue(all(any(contains(p, t) for t in triangles) for p in OCT + [(0, 0)]))
        r = self.result('nine_point_false_positive_notch', triangles)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertAlmostEqual(r['uncovered_area'], .32, places=13)

    def test_duplicate_support_cannot_mask_missing_fan(self):
        triangles = fan()[1:] + [fan()[2]]
        self.assertTrue(all(any(contains(p, t) for t in triangles) for p in OCT + [(0, 0)]))
        r = self.result('duplicate_masks_missing_fan', triangles)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertEqual(r['summed_clipped_support_area'], 14)
        self.assertEqual(r['uncovered_area'], 2)
        self.assertEqual(r['covered_union_area'], 12)
        self.assertEqual(r['pairwise_overlap_area_sum'], 2)
        self.assertEqual(r['overlap_excess_multiplicity_area'], 2)
        self.assertTrue(r['duplicate_clipped_region_pairs'])

    def test_partial_overlap_rejected_with_no_hole(self):
        triangles = rectangle(-3, -3, .5, 3) + rectangle(-.5, -3, 3, 3)
        r = self.result('partial_overlap_without_hole', triangles)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertEqual(r['uncovered_area'], 0)
        self.assertAlmostEqual(r['pairwise_overlap_area_sum'], 4, places=13)
        self.assertIn('pairwise_support_overlap_exceeds_tolerance', r['rejection_reasons'])

    def test_triplicate_overlap_is_not_union_overlap(self):
        triangles = fan() + [fan()[0], fan()[0]]
        r = self.result('triple_support_multiplicity', triangles)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertEqual(r['uncovered_area'], 0)
        self.assertEqual(r['overlap_excess_multiplicity_area'], 4)
        self.assertEqual(r['pairwise_overlap_area_sum'], 6)

    def test_reversed_and_mixed_winding(self):
        tris = rectangle(-3, -3, 3, 3)
        for i, tri in enumerate(tris):
            if i % 2:
                tris[i] = list(reversed(tri))
        r = self.result('mixed_winding', tris, list(reversed(OCT)))
        self.assertTrue(r['numerical_coverage_pass'])
        r = self.result('reverse_hole', [list(reversed(t)) for t in frame()], list(reversed(OCT)))
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertAlmostEqual(r['uncovered_area'], .04, places=13)

    def test_disjoint_edge_only_empty(self):
        cases = {'empty': [], 'disjoint': rectangle(5, 5, 6, 6),
                 'edge_only': [[(-1, 2), (1, 2), (0, 3)]],
                 'point_only': [[(2, 1), (3, 1), (3, 2)]]}
        for name, triangles in cases.items():
            r = self.result(name, triangles)
            self.assertFalse(r['numerical_coverage_pass'])
            self.assertEqual(r['uncovered_area'], 14)
            self.assertEqual(r['positive_area_support_count'], 0)

    def test_large_coordinate_offset_preserves_represented_geometry(self):
        # Integer and dyadic coordinates are exactly representable at 2**40.
        offset = (2**40, -(2**40))
        def shift(poly):
            return [(x + offset[0], z + offset[1]) for x, z in poly]
        triangles = frame(hole=(.25, .25, .5, .5))
        r = self.result('large_offset_hole', [shift(t) for t in triangles], shift(OCT))
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertAlmostEqual(r['uncovered_area'], .0625, places=13)
        self.assertEqual(r['footprint_area'], 14)
        r = self.result('large_offset_full', [shift(t) for t in rectangle(-3, -3, 3, 3)], shift(OCT))
        self.assertTrue(r['numerical_coverage_pass'])

    def test_rivet_scale_and_declared_tolerance(self):
        s = .003
        fp = [(x * s, z * s) for x, z in OCT]
        tris = [[(x * s, z * s) for x, z in t] for t in frame()]
        r = self.result('millimetric_head_hole', tris, fp, area_tolerance=1e-14)
        self.assertEqual(r['area_tolerance'], 1e-14)
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertAlmostEqual(r['uncovered_area'], .04*s*s, delta=1e-19)
        r = self.result('millimetric_head_full', [[(x*s, z*s) for x,z in t] for t in fan()], fp,
                        area_tolerance=1e-14)
        self.assertTrue(r['numerical_coverage_pass'])

    def test_tiny_area_is_preserved_and_explicitly_tolerated(self):
        h = (0.5, 0.5, .5000001, .5000001)
        r = self.result('subtolerance_hole', frame(hole=h), area_tolerance=1e-12)
        self.assertGreater(r['uncovered_area'], 0)
        self.assertTrue(r['numerical_coverage_pass'])
        # Sequential binary64 clipping may retain seam-roundoff fragments.
        # Assert within a tiny declared budget, not impossible exact area precision.
        self.assertAlmostEqual(r['uncovered_area'], 1e-14, delta=1e-15)
        self.assertTrue(r['uncovered_polygons_local'])
        self.assertEqual(r['assessment'], 'numerical coverage only; not formal interval math or factory acceptance')

    def test_invalid_triangles(self):
        cases = [[], [(0,0),(1,1)], [(0,0),(1,1),(2,2)], [(0,0),(0,0),(1,1)],
                 [(0,0),(1,0),(math.nan,1)], [(0,0),(1,0),(1,math.inf)],
                 [(0,0),(1,0),(True,1)], [(0,0),(1,0),('1',1)],
                 [(0,0),(1,0),(1e308,1e308)]]
        for tri in cases:
            with self.subTest(tri=tri), self.assertRaises(InvalidGeometry):
                assess_coverage(OCT, [tri])
        # A degenerate disjoint triangle must also reject the entire input.
        with self.assertRaises(InvalidGeometry):
            assess_coverage(OCT, rectangle(-3,-3,3,3) + [[(100,100),(101,101),(102,102)]])

    def test_invalid_footprints(self):
        concave = list(OCT)
        concave[0] = (0, 0)
        crossed = [OCT[i] for i in (0,2,4,6,1,3,5,7)]
        repeated = list(OCT)
        repeated[0] = repeated[1]
        collinear = list(OCT)
        collinear[0] = (0, 2)
        collinear[7] = (1, 2)
        for fp in [OCT[:-1], OCT + [(0,0)], concave, crossed, repeated, collinear,
                   [(0,0)] * 8, [(float('inf'), z) for _,z in OCT]]:
            with self.subTest(fp=fp), self.assertRaises(InvalidGeometry):
                assess_coverage(fp, [])

    def test_invalid_tolerance_and_limits(self):
        for tol in [-1, 14, 15, float('nan'), float('inf'), True, '1e-12']:
            with self.subTest(tol=tol), self.assertRaises(InvalidGeometry):
                assess_coverage(OCT, [], area_tolerance=tol)
        with self.assertRaises(InvalidGeometry):
            assess_coverage(OCT, fan(), max_triangles=2)
        with self.assertRaises(InvalidGeometry):
            assess_coverage(OCT, frame(), max_fragments=1)

    def test_order_and_winding_invariance_for_hole_and_duplicates(self):
        rng = random.Random(20261001)
        triangles = frame() + [frame()[0]]
        baseline = assess_coverage(OCT, triangles)
        for _ in range(100):
            rng.shuffle(triangles)
            triangles = [list(reversed(t)) if rng.getrandbits(1) else t for t in triangles]
            r = assess_coverage(OCT, triangles)
            self.assertFalse(r['numerical_coverage_pass'])
            self.assertAlmostEqual(r['uncovered_area'], baseline['uncovered_area'], places=12)
            self.assertAlmostEqual(r['pairwise_overlap_area_sum'], baseline['pairwise_overlap_area_sum'], places=12)

    def test_subnormal_ring_rejected_instead_of_losing_hole(self):
        outer = [(x * 2.0**-530, z * 2.0**-530) for x,z in OCT]
        inner = [(x * 2.0**-538, z * 2.0**-538) for x,z in OCT]
        triangles = []
        for i in range(8):
            j = (i + 1) % 8
            triangles += [[outer[i], outer[j], inner[j]], [outer[i], inner[j], inner[i]]]
        with self.assertRaises(InvalidGeometry):
            assess_coverage(outer, triangles)
        with self.assertRaises(InvalidGeometry):
            assess_coverage(outer, triangles, area_tolerance=0)

    def test_cyclic_duplicate_below_area_tolerance_rejected(self):
        t = [(x*1e-4,z*1e-4) for x,z in [
            (0.020328704784760232, -0.10004670596157075),
            (-0.04283550775942638, 0.18780998261852017),
            (0.15596014934020475, -0.038083471108995764)]]
        r = self.result('cyclic_duplicate_subtolerance', fan() + [t, t[1:] + t[:1]])
        self.assertEqual(r['uncovered_area'], 0)
        self.assertLess(r['pairwise_overlap_area_sum'], r['area_tolerance'])
        self.assertFalse(r['numerical_coverage_pass'])
        self.assertIn([8,9], r['duplicate_source_triangle_pairs'])
        self.assertIn('duplicate_positive_area_support_regions', r['rejection_reasons'])

    def test_aggregate_overflow_rejects_as_invalid_geometry(self):
        s = 3e152
        fp = [(x*s,z*s) for x,z in OCT]
        tri = [(x*s,z*s) for x,z in [(-5,-3),(5,-3),(0,7)]]
        with self.assertRaises(InvalidGeometry):
            assess_coverage(fp, [tri] * 200)

    def test_random_rectangular_holes_analytic_area(self):
        rng = random.Random(912354)
        for _ in range(200):
            # Every hole lies inside [-1,1]^2, completely inside the octagon.
            x0, x1 = sorted([rng.uniform(-.9,.9), rng.uniform(-.9,.9)])
            y0, y1 = sorted([rng.uniform(-.9,.9), rng.uniform(-.9,.9)])
            r = assess_coverage(OCT, frame((x0,y0,x1,y1)))
            self.assertFalse(r['numerical_coverage_pass'])
            self.assertAlmostEqual(r['uncovered_area'], (x1-x0)*(y1-y0), places=12)
            self.assertLessEqual(r['pairwise_overlap_area_sum'], r['area_tolerance'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CoverageTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    (ROOT / 'test-results.json').write_text(json.dumps({
        'test_cases_run': result.testsRun,
        'passed': result.wasSuccessful(),
        'failures': [(str(t), e) for t,e in result.failures],
        'errors': [(str(t), e) for t,e in result.errors],
        'reports': CoverageTests.reports,
    }, indent=2, allow_nan=False) + '\n')
    sys.exit(0 if result.wasSuccessful() else 1)
