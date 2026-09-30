"""Conservative swept AABBs for a frozen, rigid mesh rotating around one axis.

This is a sufficient-separation check, never a collision detector. Overlapping
bounds remain unresolved, including after the work/depth budget is exhausted.
Each vertex follows C + A*cos(theta) + B*sin(theta); triangle interiors are
convex combinations of their vertices at a common angle, so the vertex bounds
also enclose every triangle for the entire closed interval.
"""
import math
import numpy as np


def swept_bounds(a, b, c, lo, hi, padding=2e-5):
    if not (math.isfinite(lo) and math.isfinite(hi) and lo <= hi):
        raise ValueError('Invalid closed angle interval')
    if padding < 1e-10:
        raise ValueError('Outward numerical padding is required')
    a, b, c = (np.asarray(x, dtype=np.float64) for x in (a, b, c))
    if a.shape != b.shape or a.shape != c.shape or a.ndim != 2 or a.shape[1] != 3 or not len(a):
        raise ValueError('Expected nonempty matching Nx3 coefficient arrays')
    if not all(np.isfinite(x).all() for x in (a, b, c)):
        raise ValueError('Nonfinite geometry')
    left = c + a * math.cos(lo) + b * math.sin(lo)
    right = c + a * math.cos(hi) + b * math.sin(hi)
    lower, upper = np.minimum(left, right), np.maximum(left, right)
    radius = np.hypot(a, b)
    phase = np.arctan2(b, a)
    # Expand the critical-angle membership comparison, never shrink it.
    angular_pad = 1e-12
    for shift, maximum in ((0.0, True), (math.pi, False)):
        critical = phase + shift
        first = critical + 2 * math.pi * np.ceil((lo - angular_pad - critical) / (2 * math.pi))
        included = first <= hi + angular_pad
        if maximum:
            upper = np.where(included, np.maximum(upper, c + radius), upper)
        else:
            lower = np.where(included, np.minimum(lower, c - radius), lower)
    return lower.min(axis=0) - padding, upper.max(axis=0) + padding


def separation(moving, fixed):
    """Positive result means disjoint closed boxes; zero/negative is unknown."""
    gap = np.maximum(fixed[0] - moving[1], moving[0] - fixed[1])
    axis = int(np.argmax(gap))
    return float(gap[axis]), axis


def certify_pair(a, b, c, fixed, lo, hi, max_depth=9, max_cells=2047, padding=2e-5):
    queue = [(lo, hi, 0)]
    proved, unresolved = [], []
    cells = 0
    while queue:
        left, right, depth = queue.pop()
        if cells >= max_cells:
            unresolved.append({'lo': left, 'hi': right, 'reason': 'CELL_BUDGET'})
            continue
        cells += 1
        gap, axis = separation(swept_bounds(a, b, c, left, right, padding), fixed)
        if gap > 0:
            proved.append({'lo': left, 'hi': right, 'axis': axis, 'padded_gap_m': gap})
        elif depth >= max_depth:
            unresolved.append({'lo': left, 'hi': right, 'reason': 'OVERLAPPING_BOUNDS'})
        else:
            mid = (left + right) / 2
            queue.extend([(mid, right, depth + 1), (left, mid, depth + 1)])
    width = sum(x['hi'] - x['lo'] for x in proved + unresolved)
    assert abs(width - (hi - lo)) < 1e-10, 'Intervals must cover the full request'
    return {'status': 'CERTIFIED_RIGID_SNAPSHOT_BOX_SEPARATION' if not unresolved else 'UNRESOLVED',
            'cells': cells, 'clear_intervals': proved, 'unresolved_intervals': unresolved}


def controls():
    # A tiny rigid cube enters a fixed solid box at 1.5deg while endpoint
    # poses 0 and 3deg are clear. This is not a sampled collision proxy.
    import itertools
    local = np.array(list(itertools.product([-.00005, .00005], repeat=3))) + [1., 0., 0.]
    a = np.column_stack((local[:, 0], local[:, 1], np.zeros(8)))
    b = np.column_stack((-local[:, 1], local[:, 0], np.zeros(8)))
    c = np.column_stack((np.zeros(8), np.zeros(8), local[:, 2]))
    target = np.array([math.cos(math.radians(1.5)), math.sin(math.radians(1.5)), 0.])
    fixed = (target - .0001, target + .0001)
    mid = c + a * math.cos(math.radians(1.5)) + b * math.sin(math.radians(1.5))
    assert (mid > fixed[0]).all() and (mid < fixed[1]).all()
    endpoints = [separation(swept_bounds(a, b, c, t, t), fixed)[0] > 0 for t in (0, math.radians(3))]
    crossing = certify_pair(a, b, c, fixed, 0, math.radians(3))
    assert all(endpoints) and crossing['status'] == 'UNRESOLVED'
    far = certify_pair(a, b, c, (np.array([3., 3, 3]), np.array([4., 4, 4])), 0, 2 * math.pi)
    assert far['status'].startswith('CERTIFIED')
    budget = certify_pair(a, b, c, fixed, 0, math.radians(3), max_cells=0)
    assert budget['status'] == 'UNRESOLVED'
    # Interior trigonometric extrema must be included even when absent at ends.
    lower, upper = swept_bounds(a, b, c, 0, math.pi)
    assert upper[1] >= 1 and lower[0] <= -1
    rng = np.random.default_rng(543)
    aa, bb, cc = (rng.normal(size=(20, 3)) for _ in range(3))
    low, high = swept_bounds(aa, bb, cc, -2.3, 1.9)
    for t in np.linspace(-2.3, 1.9, 1001):
        p = cc + aa * math.cos(t) + bb * math.sin(t)
        assert (p >= low).all() and (p <= high).all()
    return {'between_sample_collision_not_certified': True, 'disjoint_full_rotation_certified': True,
            'budget_exhaustion_unresolved': True, 'interior_extrema_retained': True,
            'random_enclosure_regression': True,
            'note': 'Synthetic regression supports implementation; the analytic enclosure argument establishes interval scope.'}


if __name__ == '__main__':
    import json
    print(json.dumps(controls(), indent=2))
