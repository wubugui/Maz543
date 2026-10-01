"""Numerical 2D footprint coverage by coplanar triangular support.

Dependency-free Python binary64 geometry. Coordinates are translated near the
footprint centroid before predicates/area arithmetic. No sampling is used.

This does NOT verify coplanarity, source identity, face normals, surface thickness,
attachment strength, collision clearance, or factory acceptance. The caller must
supply triangles from ONE verified coplanar outer-skin face, in a consistent XZ
coordinate frame and unit system. Numerical coverage at a declared tolerance is
not interval arithmetic, an exact geometric proof, or a manufacturing criterion.

API: result = assess_coverage(octagon_xz, triangles_xz,
                              area_tolerance=1e-14)
CLI: python convex_coverage.py input.json > report.json
JSON input keys: footprint, triangles, and optional area_tolerance.
Local result polygon coordinates use result['origin']; add it to recover XZ.
"""
from __future__ import annotations

import argparse
import json
import math
import numbers
import sys
from typing import Iterable, Sequence

Point = tuple[float, float]
Polygon = list[Point]
DEFAULT_RELATIVE_AREA_TOLERANCE = 1e-10


class InvalidGeometry(ValueError):
    """Input is nonfinite, degenerate, invalid, or beyond arithmetic range."""


def _finite(value: float, what: str) -> float:
    if not math.isfinite(value):
        raise InvalidGeometry(f"Nonfinite arithmetic or coordinate: {what}")
    if value != 0.0 and abs(value) < sys.float_info.min:
        raise InvalidGeometry(f"Subnormal coordinate/arithmetic is unsupported: {what}")
    return value


def _product(a: float, b: float, what: str) -> float:
    value = _finite(a * b, what)
    if a != 0.0 and b != 0.0 and value == 0.0:
        raise InvalidGeometry(f"Multiplication underflow is unsupported: {what}")
    return value


def _divide(a: float, b: float, what: str) -> float:
    value = _finite(a / b, what)
    if a != 0.0 and value == 0.0:
        raise InvalidGeometry(f"Division underflow is unsupported: {what}")
    return value


def _sum(values: Iterable[float], what: str) -> float:
    try:
        return _finite(math.fsum(values), what)
    except OverflowError as exc:
        raise InvalidGeometry(f"Summation exceeds binary64 range: {what}") from exc


def _float(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise InvalidGeometry(f"{what} must be a finite real number, not {value!r}")
    try:
        return _finite(float(value), what)
    except (ValueError, OverflowError) as exc:
        raise InvalidGeometry(f"{what} is outside finite binary64 range") from exc


def _points(vertices: Iterable[Sequence[float]], count: int, what: str) -> Polygon:
    try:
        raw = list(vertices)
    except TypeError as exc:
        raise InvalidGeometry(f"{what} must be a sequence of points") from exc
    if len(raw) != count:
        raise InvalidGeometry(f"{what} must have exactly {count} vertices")
    points = []
    for i, p in enumerate(raw):
        try:
            if len(p) != 2:
                raise InvalidGeometry(f"{what}[{i}] must contain exactly two coordinates")
            points.append((_float(p[0], f"{what}[{i}].x"),
                           _float(p[1], f"{what}[{i}].z")))
        except TypeError as exc:
            raise InvalidGeometry(f"{what}[{i}] must be a coordinate pair") from exc
    if len(set(points)) != count:
        raise InvalidGeometry(f"{what} contains repeated vertices")
    return points


def _cross(a: Point, b: Point) -> float:
    products = (_product(a[0], b[1], "cross product"),
                _product(-a[1], b[0], "cross product"))
    try:
        return _finite(math.fsum(products), "cross product sum")
    except OverflowError as exc:
        raise InvalidGeometry("Cross product exceeds binary64 range") from exc


def _sub(a: Point, b: Point) -> Point:
    return (_finite(a[0] - b[0], "coordinate difference"),
            _finite(a[1] - b[1], "coordinate difference"))


def _side(p: Point, a: Point, b: Point) -> float:
    return _cross(_sub(b, a), _sub(p, a))


def _signed_area(poly: Sequence[Point]) -> float:
    # Fan anchored at an actual vertex avoids cancellation from global offsets.
    if len(poly) < 3:
        return 0.0
    a = poly[0]
    try:
        return _finite(0.5 * math.fsum(
            _cross(_sub(poly[i], a), _sub(poly[i + 1], a))
            for i in range(1, len(poly) - 1)), "polygon area")
    except OverflowError as exc:
        raise InvalidGeometry("Area exceeds binary64 range") from exc


def _clean(poly: Sequence[Point]) -> Polygon:
    result: Polygon = []
    for p in poly:
        if not result or p != result[-1]:
            result.append(p)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    # Keep all nonzero slivers; no distance or area epsilon changes the geometry.
    if len(result) < 3 or _signed_area(result) == 0.0:
        return []
    if _signed_area(result) < 0.0:
        result.reverse()
    return result


def _validate_convex(poly: Polygon, what: str) -> Polygon:
    area = _signed_area(poly)
    if area == 0.0:
        raise InvalidGeometry(f"{what} is degenerate (zero numerical area)")
    if area < 0.0:
        poly = list(reversed(poly))
    # All other vertices must lie strictly to the left of every boundary edge.
    # This rejects concavity, crossed order, collinearity, and repeated vertices.
    for i, a in enumerate(poly):
        j = (i + 1) % len(poly)
        for k, p in enumerate(poly):
            if k != i and k != j and _side(p, a, poly[j]) <= 0.0:
                raise InvalidGeometry(f"{what} is not strictly convex in boundary order")
    return poly


def _crossing(p: Point, q: Point, dp: float, dq: float) -> Point:
    # dp and dq have opposite signs, or one is zero. Avoid dp-dq overflow.
    if dp == 0.0:
        return p
    if dq == 0.0:
        return q
    ap, aq = abs(dp), abs(dq)
    if ap <= aq:
        ratio = _divide(ap, aq, "intersection ratio")
        t = _divide(ratio, 1.0 + ratio, "intersection fraction")
    else:
        t = 1.0 / (1.0 + _divide(aq, ap, "intersection ratio"))
    delta = _sub(q, p)
    return (_finite(p[0] + _product(t, delta[0], "intersection step"), "intersection x"),
            _finite(p[1] + _product(t, delta[1], "intersection step"), "intersection z"))


def _split(poly: Polygon, a: Point, b: Point) -> tuple[Polygon, Polygon]:
    """Split convex poly into closed left/right halfplanes of directed a->b.

    Both pieces share the same computed intersection coordinates. Boundary lines
    have zero area. No epsilon-expanded clipping region is used.
    """
    if not poly:
        return [], []
    left: Polygon = []
    right: Polygon = []
    p, dp = poly[-1], _side(poly[-1], a, b)
    for q in poly:
        dq = _side(q, a, b)
        if (dp < 0.0 < dq) or (dq < 0.0 < dp):
            r = _crossing(p, q, dp, dq)
            left.append(r)
            right.append(r)
        if dq >= 0.0:
            left.append(q)
        if dq <= 0.0:
            right.append(q)
        p, dp = q, dq
    return _clean(left), _clean(right)


def _intersection(subject: Polygon, clip: Polygon) -> Polygon:
    result = subject
    for i, a in enumerate(clip):
        result, _ = _split(result, a, clip[(i + 1) % len(clip)])
        if not result:
            break
    return result


def _difference(subject: Polygon, clip: Polygon) -> list[Polygon]:
    """Partition convex subject minus convex clip into convex, disjoint pieces."""
    inside = subject
    outside: list[Polygon] = []
    for i, a in enumerate(clip):
        inside, fragment = _split(inside, a, clip[(i + 1) % len(clip)])
        if fragment:
            outside.append(fragment)
        if not inside:
            break
    return outside


def _bbox(poly: Polygon) -> tuple[float, float, float, float]:
    return (min(p[0] for p in poly), min(p[1] for p in poly),
            max(p[0] for p in poly), max(p[1] for p in poly))


def _bbox_positive_overlap(a: tuple, b: tuple) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def assess_coverage(footprint: Iterable[Sequence[float]],
                    triangles: Iterable[Iterable[Sequence[float]]], *,
                    area_tolerance: float | None = None,
                    max_triangles: int = 10000,
                    max_fragments: int = 100000) -> dict:
    """Return an auditable numerical coverage report; invalid inputs raise.

    Pass requires uncovered area AND summed pairwise overlap area <= the declared
    area tolerance, plus no exact duplicate positive-area source triangles or clipped regions and no
    excessive area-accounting discrepancy. Tolerance is in coordinate-units².
    Default tolerance is footprint_area * 1e-10 (reported, never silently raised).
    Pairwise overlap counts triple intersections more than once; it is a strict
    diagnostic, not the area of the union of all overlap regions.

    Input footprint must be a strictly convex, boundary-ordered octagon. Each
    support triangle must be finite and nondegenerate, even if outside footprint.
    Winding may differ. Subnormal/underflow arithmetic rejects rather than accepting.
    Empty support is valid input and returns uncovered.
    Resource-limit failures raise rather than producing a partial acceptance.
    """
    if sys.float_info.mant_dig != 53:
        raise RuntimeError("This helper requires IEEE-style binary64 Python floats")
    if isinstance(max_triangles, bool) or not isinstance(max_triangles, int) or max_triangles < 0:
        raise InvalidGeometry("max_triangles must be a nonnegative integer")
    if isinstance(max_fragments, bool) or not isinstance(max_fragments, int) or max_fragments < 1:
        raise InvalidGeometry("max_fragments must be a positive integer")
    raw_fp = _points(footprint, 8, "footprint")
    anchor = raw_fp[0]
    origin = tuple(_finite(anchor[d] + math.fsum(
        _finite(p[d] - anchor[d], "centering difference") / len(raw_fp)
        for p in raw_fp), "origin") for d in range(2))
    fp = _validate_convex([_sub(p, origin) for p in raw_fp], "footprint")
    fp_area = _signed_area(fp)
    tol = (_product(fp_area, DEFAULT_RELATIVE_AREA_TOLERANCE, "default tolerance") if area_tolerance is None
           else _float(area_tolerance, "area_tolerance"))
    if not math.isfinite(tol) or tol < 0.0 or tol >= fp_area:
        raise InvalidGeometry("area_tolerance must be finite, nonnegative, and smaller than footprint area")
    try:
        iterator = iter(triangles)
    except TypeError as exc:
        raise InvalidGeometry("triangles must be an iterable") from exc
    clipped: list[tuple[int, Polygon]] = []
    zero_area_indices = []
    source_duplicate_pairs = []
    positive_source_keys: dict[tuple, list[int]] = {}
    source_keys: dict[int, tuple] = {}
    count = 0
    for index, triangle in enumerate(iterator):
        count += 1
        if count > max_triangles:
            raise InvalidGeometry("Triangle resource limit exceeded; no result accepted")
        tri = _validate_convex([_sub(p, origin) for p in _points(triangle, 3, f"triangle[{index}]")],
                               f"triangle[{index}]")
        source_key = tuple(sorted(tri))
        source_keys[index] = source_key
        region = _intersection(fp, tri)
        if region:
            source_duplicate_pairs.extend([previous, index]
                                          for previous in positive_source_keys.get(source_key, []))
            positive_source_keys.setdefault(source_key, []).append(index)
            clipped.append((index, region))
        else:
            zero_area_indices.append(index)
    uncovered: list[Polygon] = [fp]
    for _, region in clipped:
        region_bbox = _bbox(region)
        next_uncovered = []
        for fragment in uncovered:
            if _bbox_positive_overlap(_bbox(fragment), region_bbox):
                next_uncovered.extend(_difference(fragment, region))
            else:
                next_uncovered.append(fragment)
            if len(next_uncovered) > max_fragments:
                raise InvalidGeometry("Fragment resource limit exceeded; no result accepted")
        uncovered = next_uncovered
    uncovered_area = _sum((_signed_area(p) for p in uncovered), "uncovered area")
    union_area = fp_area - uncovered_area
    summed_support_area = _sum((_signed_area(p) for _, p in clipped), "summed support area")
    overlaps = []
    bboxes = [_bbox(p) for _, p in clipped]
    for i, (source_i, p) in enumerate(clipped):
        for j in range(i + 1, len(clipped)):
            source_j, q = clipped[j]
            if not _bbox_positive_overlap(bboxes[i], bboxes[j]):
                continue
            region = _intersection(p, q)
            if region:
                area = _signed_area(region)
                overlaps.append({"triangle_indices": [source_i, source_j],
                                 "area": area,
                                 "exact_duplicate_clipped_region": set(p) == set(q),
                                 "exact_duplicate_source_triangle": source_keys[source_i] == source_keys[source_j],
                                 "polygon_local": region})
    pairwise_overlap_area = _sum((item["area"] for item in overlaps), "pairwise overlap sum")
    duplicate_pairs = [item["triangle_indices"] for item in overlaps
                       if item["exact_duplicate_clipped_region"]]
    # Excess multiplicity is <= pairwise overlap; equality only if no triples.
    excess = summed_support_area - union_area
    account_violation = max(0.0, -union_area, union_area - fp_area,
                            -excess, excess - pairwise_overlap_area)
    reasons = []
    if uncovered_area > tol:
        reasons.append("uncovered_area_exceeds_tolerance")
    if pairwise_overlap_area > tol:
        reasons.append("pairwise_support_overlap_exceeds_tolerance")
    if duplicate_pairs or source_duplicate_pairs:
        reasons.append("duplicate_positive_area_support_regions")
    if account_violation > tol:
        reasons.append("numerical_area_accounting_inconsistent")
    return {
        "method": "binary64 convex half-plane clipping and convex-difference union coverage",
        "assessment": "numerical coverage only; not formal interval math or factory acceptance",
        "numerical_coverage_pass": not reasons,
        "rejection_reasons": reasons,
        "origin": origin,
        "area_units": "input coordinate units squared",
        "area_tolerance": tol,
        "relative_area_tolerance": tol / fp_area,
        "footprint_area": fp_area,
        "covered_union_area": union_area,
        "uncovered_area": uncovered_area,
        "uncovered_fraction": uncovered_area / fp_area,
        "uncovered_polygons_local": uncovered,
        "summed_clipped_support_area": summed_support_area,
        "overlap_excess_multiplicity_area": excess,
        "pairwise_overlap_area_sum": pairwise_overlap_area,
        "overlap_findings": overlaps,
        "duplicate_clipped_region_pairs": duplicate_pairs,
        "duplicate_source_triangle_pairs": source_duplicate_pairs,
        "area_accounting_violation": account_violation,
        "input_triangle_count": count,
        "positive_area_support_count": len(clipped),
        "zero_area_intersection_triangle_indices": zero_area_indices,
        "clipped_support_regions": [{"triangle_index": i, "area": _signed_area(p),
                                     "polygon_local": p} for i, p in clipped],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="JSON with footprint, triangles, optional area_tolerance")
    args = parser.parse_args()
    try:
        with open(args.input_json, encoding="utf-8") as stream:
            data = json.load(stream)
        result = assess_coverage(data["footprint"], data["triangles"],
                                 area_tolerance=data.get("area_tolerance"))
        json.dump(result, sys.stdout, indent=2, allow_nan=False)
        sys.stdout.write("\n")
        return 0 if result["numerical_coverage_pass"] else 1
    except (InvalidGeometry, KeyError, TypeError, json.JSONDecodeError) as exc:
        json.dump({"numerical_coverage_pass": False, "invalid_input": str(exc)}, sys.stdout,
                  indent=2, allow_nan=False)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
