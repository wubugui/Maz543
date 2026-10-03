"""Index-only mesh inventory. No welding, geometry edits, or hinge/axis selection.

Float64 PCA describes vertex samples, not surface/volume mass or a fitted barrel.
No geometric tolerance is used. Exact rank refers to represented sample values;
near-degeneracy remains unclassified. Equal eigenvalues permit arbitrary bases,
and every eigenvector has an arbitrary sign, even without a repeated eigenvalue.
"""

from fractions import Fraction
import json

import numpy as np


def _array(value, name, dtype, tail):
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(dtype):
        raise ValueError(f"{name} must be a {dtype} NumPy array")
    if value.ndim != 1 + len(tail) or value.shape[1:] != tail:
        raise ValueError(f"{name} has invalid shape")
    return value


def _indices(value, name, limit):
    if value.size and (np.any(value < 0) or np.any(value >= limit)):
        raise ValueError(f"{name} contains an out-of-range index")


def _exact_affine_rank(points):
    """Exact rational elimination on finite binary floats; no epsilon cutoff."""
    origin = [Fraction(float(x)) for x in points[0]]
    basis = {}
    for point in points[1:]:
        row = [Fraction(float(x)) - o for x, o in zip(point, origin)]
        for column in range(3):
            if not row[column]:
                continue
            if column in basis:
                factor = row[column]
                row = [x - factor * b for x, b in zip(row, basis[column])]
            else:
                factor = row[column]
                basis[column] = [x / factor for x in row]
                break
        if len(basis) == 3:
            break
    return len(basis)


def _geometry(points):
    center = points.mean(axis=0)
    centered = points - center
    covariance = centered.T @ centered / len(points)
    values, vectors = np.linalg.eigh(covariance)
    values, axes = values[::-1], vectors[:, ::-1].T
    if not all(np.isfinite(a).all() for a in (center, covariance, values, axes)):
        raise ValueError("non-finite derived geometry")
    measures = []
    for axis in axes:
        projection = centered @ axis
        perpendicular = centered - projection[:, None] * axis
        radius = np.linalg.norm(perpendicular, axis=1)
        measures.append({
            "projection_min": float(projection.min()),
            "projection_max": float(projection.max()),
            "radius_min": float(radius.min()), "radius_max": float(radius.max()),
            "exact_projection_min_multiplicity": int(np.sum(projection == projection.min())),
            "exact_projection_max_multiplicity": int(np.sum(projection == projection.max())),
        })
    exact_rank = _exact_affine_rank(points)
    return {
        "bounds_min": points.min(axis=0).tolist(),
        "bounds_max": points.max(axis=0).tolist(), "vertex_centroid": center.tolist(),
        "pca": {
            "covariance_population": covariance.tolist(),
            "eigenvalues_descending": values.tolist(), "axes_as_rows": axes.tolist(),
            "adjacent_eigenvalue_gaps": (values[:-1] - values[1:]).tolist(),
            "exact_equal_eigenvalue_groups": [
                np.flatnonzero(values == v).tolist() for v in np.unique(values)
                if np.count_nonzero(values == v) > 1
            ],
            "exact_affine_rank_of_sample_values": exact_rank,
            "rank_deficient_exactly": exact_rank < 3,
            "near_degeneracy": "UNCLASSIFIED_NO_TOLERANCE",
            "axis_selection": None, "axis_signs_arbitrary": True,
            "axis_measures": measures,
        },
    }


def summarize_components(position, edges, loop_vertex, loop_edge,
                         polygon_start, polygon_size, world):
    """Return a strict-JSON dict, or raise ValueError for malformed input.

    position: float32[N,3]; edges: int32[E,2]; four corner/polygon arrays:
    int32[...]. All loops must belong to exactly one polygon (>=3 distinct
    vertex indices), and each loop edge must join that corner to its successor.
    Loose vertices/edges and non-manifold edge use are retained. Connectivity
    uses edge vertex indices only, including loose edges. Components and each
    membership list are ordered by original index, never by geometry or score.
    world: finite float32/float64 affine 4x4, column-vector convention.
    No input array is mutated. Geometry is in the input's unspecified units.
    """
    position = _array(position, "position", "float32", (3,))
    edges = _array(edges, "edges", "int32", (2,))
    named = {"loop_vertex": loop_vertex, "loop_edge": loop_edge,
             "polygon_start": polygon_start, "polygon_size": polygon_size}
    for name, value in named.items():
        _array(value, name, "int32", ())
    if not np.isfinite(position).all():
        raise ValueError("position contains non-finite geometry")
    if (not isinstance(world, np.ndarray) or world.shape != (4, 4)
            or world.dtype not in (np.dtype("float32"), np.dtype("float64"))
            or not np.isfinite(world).all()
            or not np.array_equal(world[3], [0, 0, 0, 1])):
        raise ValueError("world must be a finite floating-point affine 4x4 matrix")
    n, e, l, p = len(position), len(edges), len(loop_vertex), len(polygon_start)
    if len(loop_edge) != l or len(polygon_size) != p:
        raise ValueError("parallel topology arrays have different lengths")
    _indices(edges, "edges", n)
    _indices(loop_vertex, "loop_vertex", n)
    _indices(loop_edge, "loop_edge", e)
    if np.any(edges[:, 0] == edges[:, 1]):
        raise ValueError("an edge has identical endpoint indices")
    loop_polygon = np.full(l, -1, dtype=np.int64)
    for polygon, (start, size) in enumerate(zip(polygon_start, polygon_size)):
        start, size = int(start), int(size)
        if start < 0 or size < 3 or start + size > l:
            raise ValueError("invalid polygon loop range or corner count")
        if np.any(loop_polygon[start:start + size] != -1):
            raise ValueError("overlapping polygon loop ranges")
        vertices = loop_vertex[start:start + size]
        if len(np.unique(vertices)) != size:
            raise ValueError("polygon repeats a vertex index")
        expected = np.sort(np.column_stack((vertices, np.roll(vertices, -1))), axis=1)
        actual = np.sort(edges[loop_edge[start:start + size]], axis=1)
        if not np.array_equal(expected, actual):
            raise ValueError("loop edge does not join consecutive polygon vertices")
        loop_polygon[start:start + size] = polygon
    if np.any(loop_polygon == -1):
        raise ValueError("loops are not covered by polygons")

    parent = list(range(n))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in edges:
        a, b = root(int(a)), root(int(b))
        parent[max(a, b)] = min(a, b)
    roots = [root(i) for i in range(n)]
    ids = {r: i for i, r in enumerate(sorted(set(roots)))}
    vertex_component = np.array([ids[r] for r in roots], dtype=np.int64)
    owners = {"vertices": vertex_component,
              "edges": vertex_component[edges[:, 0]],
              "loops": vertex_component[loop_vertex],
              "polygons": vertex_component[loop_vertex[polygon_start]]}
    inverse = {name: np.empty(len(owner), dtype=np.int64) for name, owner in owners.items()}
    components = []
    try:
        with np.errstate(over="raise", invalid="raise"):
            local = position.astype(np.float64)
            transformed = local @ world[:3, :3].astype(np.float64).T + world[:3, 3]
            if not np.isfinite(transformed).all():
                raise ValueError("non-finite world geometry")
            for component in range(len(ids)):
                maps = {name: np.flatnonzero(owner == component) for name, owner in owners.items()}
                for name, indices in maps.items():
                    inverse[name][indices] = np.arange(len(indices))
                counts = {name: len(indices) for name, indices in maps.items()}
                counts["polygon_fan_triangle_count"] = sum(
                    int(polygon_size[i]) - 2 for i in maps["polygons"])
                components.append({
                    "component_id": component,
                    "indices": {name: indices.tolist() for name, indices in maps.items()},
                    "counts": counts,
                    "local": _geometry(local[maps["vertices"]]),
                    "world": _geometry(transformed[maps["vertices"]]),
                    "historical_192v_380_fan_count_hint_only":
                        counts["vertices"] == 192 and counts["polygon_fan_triangle_count"] == 380,
                })
    except (FloatingPointError, np.linalg.LinAlgError) as exc:
        raise ValueError(f"geometry summary failed: {exc}") from exc
    result = {
        "schema": "index-components-v1", "component_count": len(components),
        "input_counts": {name: len(owner) for name, owner in owners.items()},
        "original_to_component": {name: owner.tolist() for name, owner in owners.items()},
        "original_to_component_local": {name: value.tolist() for name, value in inverse.items()},
        "components": components,
        "selection": {"component": None, "axis": None, "status": "UNRESOLVED_NUMERIC_SUMMARY_ONLY"},
        "limits": [
            "No welding; equal positions preserve separate indexed topology.",
            "Centroids/covariance are equally weighted vertex samples, not solid mass.",
            "Projection/radius use a centroid line along each PCA basis vector.",
            "Projection multiplicities use exact float64 equality, not ring detection.",
            "Exact rank is of represented local/world sample values, not near-rank classification.",
            "PCA basis/signs and near-ties are not mechanical axis evidence.",
            "192 vertices/380 polygon-fan triangles is a historical count hint, never a hinge identity.",
            "Polygon-fan count is combinatorial, not a native tessellation or geometry validity check.",
        ],
    }
    json.dumps(result, allow_nan=False)
    return result
