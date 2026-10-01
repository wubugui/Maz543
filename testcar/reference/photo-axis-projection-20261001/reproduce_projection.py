#!/usr/bin/env python3
"""Reproduce the small, model-independent collinear axle projection diagnostic.

Requires numpy and scipy. Reads only landmarks.json; never opens a model or
downloads anything. Prints JSON to stdout; redirect to a NEW output if wanted.
This is not a full camera, lens, chassis-height or cab-dimension calibration.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def cross_ratio(x):
    return float((x[0] - x[2]) * (x[1] - x[3]) /
                 ((x[0] - x[3]) * (x[1] - x[2])))


def inspect_photo(photo, stations):
    observed = np.array(photo["points_front_to_rear_px"], dtype=float)
    centred = observed - observed.mean(axis=0)
    _, _, vh = np.linalg.svd(centred)
    line_coordinate = centred @ vh[0]

    # This is the image of one nominal straight world line. Five parameters
    # represent a restricted 3x2 projective map, not a complete camera matrix.
    def project(q):
        a, b, c, d, e = q
        den = e * stations + 1
        return np.column_stack(((a * stations + b) / den,
                                (c * stations + d) / den))

    result = least_squares(
        lambda q: (project(q) - observed).ravel(),
        [-70, observed[0, 0], 0, observed[0, 1], 0.02],
    )
    if not result.success:
        raise RuntimeError(result.message)
    q = result.x
    fitted = project(q)
    errors = np.linalg.norm(fitted - observed, axis=1)
    width, height = photo["size_px"]
    cx, cy = width / 2, height / 2
    alternatives = []
    for focal_px in (1000, 1500, 2250, 3000):
        # Assumed square pixels, zero skew and centred principal point.
        # Recover a unit world-line direction and metric translation for
        # EACH arbitrary focal length. Rotation about that line remains free.
        k = np.array([[focal_px, 0, cx], [0, focal_px, cy], [0, 0, 1.]])
        direction_raw = np.linalg.solve(k, [q[0], q[2], q[4]])
        translation_raw = np.linalg.solve(k, [q[1], q[3], 1.])
        scale = np.linalg.norm(direction_raw)
        direction = direction_raw / scale
        translation = translation_raw / scale
        camera_points = stations[:, None] * direction + translation
        projected_h = camera_points @ k.T
        reconstructed = projected_h[:, :2] / projected_h[:, 2:]
        alternatives.append({
            "ASSUMED_focal_length_px": focal_px,
            "ASSUMED_principal_point_px": [cx, cy],
            "same_projection_max_difference_px": float(np.max(np.abs(reconstructed - fitted))),
            "conditional_distance_camera_to_front_hub_m": float(np.linalg.norm(translation)),
            "conditional_axle_line_direction_camera_coordinates": direction.tolist(),
        })
    return {
        "file": photo["file"],
        "nominal_axle_cross_ratio": cross_ratio(stations),
        "observed_cross_ratio_after_line_projection": cross_ratio(line_coordinate),
        "rms_2d_point_residual_px": float(np.sqrt(np.mean(errors ** 2))),
        "individual_2d_point_residuals_px": errors.tolist(),
        "fitted_image_points_px": fitted.tolist(),
        "projective_coefficients_a_b_c_d_e": q.tolist(),
        "longitudinal_vanishing_point_px_not_full_horizon": (q[[0, 2]] / q[4]).tolist(),
        "nonuniqueness_demonstration_NOT_camera_estimates": alternatives,
    }


def main():
    data = json.loads(Path(__file__).with_name("landmarks.json").read_text())
    stations = np.array(data["axle_stations_m"], dtype=float)
    report = {
        "status": "LIMITED_1D_DIAGNOSTIC_ONLY_ALL_VEHICLE_GATES_STILL_OPEN",
        "model_geometry_used": False,
        "track_used": False,
        "distortion_estimated": False,
        "point_picking_allowance_px": data["picking_uncertainty_px"],
        "method": "Fit u=(a*s+b)/(e*s+1), v=(c*s+d)/(e*s+1) to four nominal axle stations; demonstrate focal-distance ambiguity without assuming cab geometry.",
        "results": [inspect_photo(photo, stations) for photo in data["images"]],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
