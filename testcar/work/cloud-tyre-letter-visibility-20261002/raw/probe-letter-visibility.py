"""Read-only station0 glyph diagnosis. No Apply, transforms, render, or save.

The caller supplies a new evidence directory. Geometry queries use a VIEWPORT
depsgraph; finite rays are observations, not a rendered-visibility certificate.
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SOURCE = Path('/workspace/scratch/a29d03198654/Maz543/testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend')
SOURCE_SHA = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
CAMERA_RECORD = Path('/workspace/scratch/a29d03198654/maz-native-wheel-views-20261002/attempt-station0-neutral-01/ready-to-render.json')
CAMERA_SHA = '054d8e227e1947ae27e49ace5dbe9601cbcd648960e3d8223cf069ff523defe0'
START = time.monotonic()
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
OUT = Path(args.output).resolve()
assert OUT.is_dir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()


def phase(name, **extra):
    record = {'phase': name, 'elapsed_seconds': time.monotonic() - START, **extra}
    with (OUT / 'phase.jsonl').open('a') as stream:
        stream.write(json.dumps(record, allow_nan=False) + '\n')
        stream.flush()
    print('PHASE ' + json.dumps(record), flush=True)


def flags(obj):
    return {key: bool(getattr(obj, key)) for key in
            ['hide_render', 'hide_viewport', 'visible_camera', 'visible_shadow',
             'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter']}


def collection_paths(root, wanted, layer=False):
    records = []
    def walk(item, chain):
        collection = item.collection if layer else item
        node = {'name': item.name, 'collection': collection.name,
                'hide_viewport': bool(item.hide_viewport)}
        if layer:
            node.update(exclude=bool(item.exclude), holdout=bool(item.holdout),
                        indirect_only=bool(item.indirect_only))
        else:
            node['hide_render'] = bool(item.hide_render)
        path = chain + [node]
        if collection in wanted:
            records.append(path)
        for child in item.children:
            walk(child, path)
    walk(root, [])
    return records


def visibility(obj):
    collections = set(obj.users_collection)
    row = {'name': obj.name, 'type': obj.type, **flags(obj),
           'hide_get': bool(obj.hide_get(view_layer=bpy.context.view_layer)),
           'visible_get': bool(obj.visible_get(view_layer=bpy.context.view_layer)),
           'users_collection': sorted(c.name for c in collections),
           'scene_collection_paths': collection_paths(bpy.context.scene.collection, collections),
           'active_view_layer_paths': collection_paths(bpy.context.view_layer.layer_collection, collections, True),
           'modifiers': []}
    for mod in obj.modifiers:
        item = {'name': mod.name, 'type': mod.type, 'show_viewport': mod.show_viewport,
                'show_render': mod.show_render}
        if mod.type == 'SOLIDIFY':
            item.update(thickness=mod.thickness, offset=mod.offset, use_even_offset=mod.use_even_offset)
        if mod.type == 'SHRINKWRAP':
            item.update(target=mod.target.name if mod.target else None, wrap_method=mod.wrap_method,
                        wrap_mode=mod.wrap_mode, offset=mod.offset)
        row['modifiers'].append(item)
    row['material_slots'] = [{'slot_link': s.link, 'material': s.material.name if s.material else None}
                             for s in obj.material_slots]
    if obj.type == 'FONT':
        row['font'] = {k: getattr(obj.data, k) for k in
                       ['body', 'size', 'extrude', 'bevel_depth', 'align_x', 'align_y', 'space_character', 'offset']}
        row['font']['font_name'] = obj.data.font.name
    return row


def mesh_arrays(obj, evaluated):
    queried = obj.evaluated_get(DG) if evaluated else obj
    mesh = queried.to_mesh(preserve_all_data_layers=False, depsgraph=DG)
    try:
        if mesh is None:
            return np.empty((0, 3)), np.empty((0, 3), dtype=np.int32), None
        mesh.calc_loop_triangles()
        local = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', local)
        local = local.reshape(-1, 3)
        triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int32)
        mesh.loop_triangles.foreach_get('vertices', triangles)
        triangles = triangles.reshape(-1, 3)
        world = np.asarray(queried.matrix_world.copy(), dtype=np.float64)
        return local @ world[:3, :3].T + world[:3, 3], triangles, world
    finally:
        queried.to_mesh_clear()


def projected(points):
    local = points @ CAM_INV[:3, :3].T + CAM_INV[:3, 3]
    pixel = np.column_stack((WIDTH / 2 + local[:, 0] * WIDTH / ORTHO,
                             HEIGHT / 2 - local[:, 1] * HEIGHT / VERTICAL_SPAN))
    return np.column_stack((pixel, -local[:, 2]))


def bounds(points):
    if not len(points):
        return None
    return [points.min(axis=0).tolist(), points.max(axis=0).tolist()]


def signed_samples(points, label):
    """Keep original winding signs and an explicitly separate +Y-oriented view."""
    values = []
    witnesses = []
    missing = 0
    normal_positive = normal_negative = normal_tangent = 0
    for index, point in enumerate(points):
        hit, normal, face, distance = TYRE_BVH.find_nearest(Vector(point))
        if hit is None:
            missing += 1
            continue
        h = np.asarray(hit, dtype=float)
        n = np.asarray(normal, dtype=float)
        expected_dot = float(n @ OUTWARD)
        raw_signed = float((point - h) @ n)
        if expected_dot > 1e-8:
            oriented_signed = raw_signed
            normal_positive += 1
        elif expected_dot < -1e-8:
            oriented_signed = -raw_signed
            normal_negative += 1
        else:
            oriented_signed = None
            normal_tangent += 1
        values.append([index, float(distance), raw_signed,
                       oriented_signed if oriented_signed is not None else float('nan'), expected_dot, float(h[1] - TYRE_CENTER[1])])
        witnesses.append({'sample_index': index, 'sample_world_m': point.tolist(), 'hit_world_m': h.tolist(),
                          'tyre_triangle_index': int(face), 'normal_original_winding': n.tolist(),
                          'normal_dot_expected_plus_y': expected_dot, 'nearest_distance_m': float(distance),
                          'signed_original_normal_m': raw_signed, 'signed_plus_y_oriented_normal_m': oriented_signed})
    if not values:
        return {'sample_kind': label, 'count': len(points), 'missing_nearest': missing}
    array = np.asarray(values)
    finite_outward = np.isfinite(array[:, 3])
    extrema = set()
    for column in [1, 2, 3, 4, 5]:
        valid = np.flatnonzero(np.isfinite(array[:, column]))
        if len(valid):
            extrema.add(int(valid[np.argmin(array[valid, column])]))
            extrema.add(int(valid[np.argmax(array[valid, column])]))
    return {'sample_kind': label, 'count': len(points), 'missing_nearest': missing,
            'nearest_distance_m': [float(array[:, 1].min()), float(array[:, 1].max())],
            'signed_original_normal_m': [float(array[:, 2].min()), float(array[:, 2].max())],
            'signed_plus_y_oriented_normal_m': [float(array[finite_outward, 3].min()), float(array[finite_outward, 3].max())] if finite_outward.any() else None,
            'original_normal_dot_plus_y_range': [float(array[:, 4].min()), float(array[:, 4].max())],
            'nearest_hit_y_minus_wheel_center_m': [float(array[:, 5].min()), float(array[:, 5].max())],
            'original_normals_plus_y_minus_y_tangent_counts': [normal_positive, normal_negative, normal_tangent],
            'original_signed_negative_zero_positive_counts': [int((array[:, 2] < 0).sum()), int((array[:, 2] == 0).sum()), int((array[:, 2] > 0).sum())],
            'plus_y_signed_negative_zero_positive_counts': [int((array[finite_outward, 3] < 0).sum()), int((array[finite_outward, 3] == 0).sum()), int((array[finite_outward, 3] > 0).sum())],
            'extreme_witnesses': [witnesses[i] for i in sorted(extrema)],
            'limits': 'Nearest target triangle and finite vertex/triangle-centroid samples; not closed-surface containment or all-face exposure. +Y orientation is a separately labelled expected outside-face convention; raw winding is retained.'}


def geometry(obj, evaluated):
    xyz, triangles, matrix = mesh_arrays(obj, evaluated)
    row = {'name': obj.name, 'query': 'VIEWPORT_evaluated' if evaluated else 'original_object_native_to_mesh_no_modifier_evaluation',
           'vertex_count': len(xyz), 'triangle_count': len(triangles),
           'world_matrix': matrix.tolist() if matrix is not None else None,
           'world_bbox_m': bounds(xyz), 'pixel_xy_camera_depth_bbox': bounds(projected(xyz)),
           'bounds_scope': 'Bounds of actual queried vertex set, not source FONT origin or 40mm em estimate'}
    if len(xyz):
        row['vertices_to_tyre'] = signed_samples(xyz, 'all_queried_vertices')
    if len(triangles):
        corners = xyz[triangles]
        centers = corners.mean(axis=1)
        area_vectors = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        lengths = np.linalg.norm(area_vectors, axis=1)
        valid = lengths > 1e-20
        normals = np.zeros_like(area_vectors)
        normals[valid] = area_vectors[valid] / lengths[valid, None]
        row['triangle_centroids_to_tyre'] = signed_samples(centers, 'all_queried_triangle_centroids')
        row['triangle_winding'] = {'degenerate_count': int((~valid).sum()),
            'normal_dot_plus_y_range': [float((normals[valid] @ OUTWARD).min()), float((normals[valid] @ OUTWARD).max())] if valid.any() else None,
            'normal_dot_camera_outward_range': [float((normals[valid] @ CAMERA_OUTWARD).min()), float((normals[valid] @ CAMERA_OUTWARD).max())] if valid.any() else None}
        if evaluated and obj.name in REPRESENTATIVES:
            candidates = np.flatnonzero(valid & ((normals @ OUTWARD) > .5) & ((normals @ CAMERA_OUTWARD) > .1))
            ordered = sorted(candidates, key=lambda i: (-float(lengths[i]), int(i)))[:3]
            RAY_POINTS[obj.name] = [{'triangle_index': int(i), 'barycentric': [1/3, 1/3, 1/3],
                                     'point_world_m': centers[i].tolist(), 'triangle_world_m': corners[i].tolist(),
                                     'normal_original_winding': normals[i].tolist(),
                                     'twice_triangle_area_m2': float(lengths[i])} for i in ordered]
            row['finite_ray_candidates'] = RAY_POINTS[obj.name]
    return row


report = {'status': 'STARTED', 'source_sha256': SOURCE_SHA, 'camera_record_sha256': CAMERA_SHA,
          'scope': 'Station0 original18 MESH glyphs and18 preserved SOURCE FONT objects, original frame0. No repair replay.',
          'saved_blend': False, 'saved_glb': False, 'all_16_gates': 'OPEN',
          'limits': ['VIEWPORT depsgraph geometry can differ from render depsgraph.',
                     'scene.ray_cast is a geometric viewport query, not Cycles camera visibility; hide_render, visible_camera, collection render flags, transparent shaders, alpha and shader displacement are not certified by hits.',
                     'Nine or fewer interior-face rays do not certify whole-glyph visibility. A first hit alone is not a rendered readability claim.',
                     'Source FONT solids retain their original extrusion/bevel and are hidden authoring sources, not the rendered glyph geometry.',
                     'Signed nearest triangle distances preserve raw winding; the separately labelled +Y convention is not a volume containment test.']}
originals = []
snapshots = []
VISIBILITY_BEFORE = {}
DG = None
failed = False
try:
    assert sha(SOURCE) == SOURCE_SHA and sha(CAMERA_RECORD) == CAMERA_SHA
    camera_record = json.loads(CAMERA_RECORD.read_text())
    assert bpy.app.version == (4, 5, 13), bpy.app.version
    assert bpy.app.build_hash.decode() == 'daeeeca98fb0', bpy.app.build_hash
    report.update(blender_version=bpy.app.version_string, build_hash=bpy.app.build_hash.decode())
    autoexec_enabled = bool(bpy.context.preferences.filepaths.use_scripts_auto_execute)
    report['autoexec_before_open'] = {'use_scripts_auto_execute': autoexec_enabled,
                                     'assertion': 'Must be false before opening the pinned blend'}
    write('native-preflight.json', {'blender_version': report['blender_version'],
                                   'build_hash': report['build_hash'],
                                   'autoexec_before_open': report['autoexec_before_open']})
    assert not autoexec_enabled, 'Refusing to open source with script auto-execution enabled'
    phase('OPEN_SOURCE_BEGIN')
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(0)
    bpy.context.view_layer.update()
    originals = list(bpy.data.objects)
    snapshots = [(obj, obj.name, obj.as_pointer(), np.asarray(obj.matrix_world.copy(), dtype=np.float64)) for obj in originals]
    glyphs = sorted([o for o in originals if o.name.startswith('BL_Tyre_0_emboss_')], key=lambda o: int(o.name.rsplit('_', 1)[1]))
    assert len(glyphs) == 18 and all(o.type == 'MESH' for o in glyphs)
    fonts = [bpy.data.objects['SOURCE_' + o.name] for o in glyphs]
    assert all(o.type == 'FONT' for o in fonts)
    tyre = bpy.data.objects['BL_Tyre_0_VI203_profile']
    selected = glyphs + fonts + [tyre]
    VISIBILITY_BEFORE = {obj.name: visibility(obj) for obj in selected}
    write('visibility-prefix.json', {'status': 'COMPLETE_VISIBILITY_PREFIX', 'frame': scene.frame_current,
                                   'view_layer': bpy.context.view_layer.name, 'original_object_count': len(originals),
                                   'objects': VISIBILITY_BEFORE})
    phase('VISIBILITY_PREFIX_DURABLE', objects=len(selected))
    CAM = np.asarray(camera_record['camera_world_matrix'], dtype=np.float64)
    CAM_INV = np.linalg.inv(CAM)
    WIDTH, HEIGHT = camera_record['resolution']
    ORTHO = camera_record['camera_orthographic_scale_m']
    assert WIDTH == 1100 and HEIGHT == 1000 and ORTHO == 2.6
    pixel_aspect = [scene.render.pixel_aspect_x, scene.render.pixel_aspect_y]
    assert pixel_aspect == [1.0, 1.0], ('Saved render inherited pixel aspect; square-pixel formula requires verified source values', pixel_aspect)
    VERTICAL_SPAN = ORTHO * HEIGHT / WIDTH
    CAMERA_OUTWARD = CAM[:3, 2] / np.linalg.norm(CAM[:3, 2])
    DIRECTION = -CAMERA_OUTWARD
    OUTWARD = np.array([0.0, 1.0, 0.0])
    TYRE_CENTER = np.asarray(bpy.data.objects['wheels_pivot_002'].matrix_world.translation, dtype=float)
    REPRESENTATIVES = {'BL_Tyre_0_emboss_1', 'BL_Tyre_0_emboss_10', 'BL_Tyre_0_emboss_19'}
    RAY_POINTS = {}
    report['camera'] = {'world_matrix': CAM.tolist(), 'resolution': [WIDTH, HEIGHT], 'ortho_scale_m': ORTHO,
                        'source_scene_pixel_aspect': pixel_aspect, 'camera_ray_direction_world': DIRECTION.tolist(),
                        'projection': 'Saved orthographic camera; pixels measured from top left. Independent parallel origin for every sampled point at camera-local z=-0.01m; no new camera object.'}
    DG = bpy.context.evaluated_depsgraph_get()
    report['depsgraph_mode'] = DG.mode
    assert DG.mode == 'VIEWPORT'
    tyre_xyz, tyre_triangles, tyre_matrix = mesh_arrays(tyre, True)
    assert len(tyre_xyz) and len(tyre_triangles)
    actual_tyre_pixel_bbox = np.asarray(bounds(projected(tyre_xyz)[:, :2]), dtype=float)
    recorded_ndc_bbox = np.asarray(camera_record['neutral_tyre_projected_bounds'], dtype=float)
    recorded_pixel_bbox = np.array([[recorded_ndc_bbox[0, 0] * WIDTH,
                                     (1.0 - recorded_ndc_bbox[1, 1]) * HEIGHT],
                                    [recorded_ndc_bbox[1, 0] * WIDTH,
                                     (1.0 - recorded_ndc_bbox[0, 1]) * HEIGHT]])
    projection_error = float(np.max(np.abs(actual_tyre_pixel_bbox - recorded_pixel_bbox)))
    projection_check = {'actual_current_tyre_vertex_pixel_xy_bbox': actual_tyre_pixel_bbox.tolist(),
                        'recorded_world_to_camera_view_ndc_bbox': recorded_ndc_bbox.tolist(),
                        'recorded_ndc_converted_pixel_xy_bbox': recorded_pixel_bbox.tolist(),
                        'conversion': 'xmin=u_min*width; xmax=u_max*width; ymin=(1-v_max)*height; ymax=(1-v_min)*height',
                        'max_absolute_pixel_coordinate_difference': projection_error,
                        'limit_pixels': 1e-3,
                        'status': 'PASS' if projection_error <= 1e-3 else 'FAIL',
                        'scope': 'Formula consistency with the saved camera and unchanged neutral tyre bounds only; not glyph or rendered visibility'}
    report['tyre_projection_formula_check'] = projection_check
    write('tyre-projection-check.json', projection_check)
    assert projection_error <= 1e-3, ('Current projection formula disagrees with recorded native tyre bounds', projection_error)
    TYRE_BVH = BVHTree.FromPolygons([Vector(p) for p in tyre_xyz], [tuple(t) for t in tyre_triangles], all_triangles=True, epsilon=0.0)
    write('tyre-reference.json', {'name': tyre.name, 'query': 'VIEWPORT_evaluated', 'vertices': len(tyre_xyz),
                                 'triangles': len(tyre_triangles), 'world_bbox_m': bounds(tyre_xyz),
                                 'world_matrix': tyre_matrix.tolist(), 'wheel_center_m': TYRE_CENTER.tolist(),
                                 'position_sha256_float64': hashlib.sha256(tyre_xyz.tobytes()).hexdigest(),
                                 'triangle_sha256_int32': hashlib.sha256(tyre_triangles.tobytes()).hexdigest(),
                                 'bvh_normals': 'Original evaluated triangle winding; never edited'})
    report['geometry_files'] = []
    for obj in selected[:-1]:
        rows = []
        for evaluated in [False, True]:
            try:
                rows.append(geometry(obj, evaluated))
            except Exception as exc:
                rows.append({'name': obj.name, 'evaluated': evaluated, 'error': type(exc).__name__ + ': ' + str(exc)})
                failed = True
        filename = 'geometry-' + obj.name + '.json'
        write(filename, rows)
        report['geometry_files'].append(filename)
        phase('OBJECT_GEOMETRY_DURABLE', object=obj.name)
    write('geometry-prefix.json', {'status': 'COMPLETE_WITH_ERRORS' if failed else 'COMPLETE',
                                  'camera': report['camera'], 'files': report['geometry_files'],
                                  'ray_candidates': RAY_POINTS})
    phase('GEOMETRY_PREFIX_DURABLE_RAYS_BEGIN')
    report['rays'] = []
    for name in sorted(REPRESENTATIVES):
        for sample in RAY_POINTS.get(name, []):
            point = np.asarray(sample['point_world_m'])
            local = CAM_INV[:3, :3] @ point + CAM_INV[:3, 3]
            origin = CAM[:3, :3] @ np.array([local[0], local[1], -.01]) + CAM[:3, 3]
            along = float((point - origin) @ DIRECTION)
            perpendicular = float(np.linalg.norm((point - origin) - along * DIRECTION))
            assert along > 0 and perpendicular < 1e-10
            hit, location, normal, face_index, hit_obj, hit_matrix = scene.ray_cast(DG, Vector(origin), Vector(DIRECTION), distance=99.99)
            row = {'target': name, **sample, 'origin_world_m': origin.tolist(), 'direction_world': DIRECTION.tolist(),
                   'target_pixel_xy_depth': projected(point.reshape(1, 3))[0].tolist(),
                   'target_distance_m': along, 'ray_perpendicular_target_error_m': perpendicular,
                   'hit': bool(hit), 'query_scope': 'VIEWPORT_scene.ray_cast_geometric_first_hit'}
            if hit:
                hit_original = getattr(hit_obj, 'original', hit_obj)
                distance = float((np.asarray(location) - origin) @ DIRECTION)
                row.update(first_hit_object=hit_obj.name, first_hit_original_object=hit_original.name,
                           first_hit_face_index=int(face_index), first_hit_world_m=list(location),
                           first_hit_normal=list(normal), first_hit_distance_m=distance,
                           first_hit_minus_target_distance_m=distance - along,
                           first_hit_matches_target_name=hit_original.name == name,
                           first_hit_object_flags=flags(hit_original))
            report['rays'].append(row)
            write('ray-' + name + '-' + str(sample['triangle_index']) + '.json', row)
            phase('RAY_DURABLE', target=name, hit=bool(hit))
    report['status'] = 'READ_ONLY_DIAGNOSTIC_COMPLETE_WITH_ERRORS' if failed else 'READ_ONLY_DIAGNOSTIC_COMPLETE_NOT_VISIBILITY_CERTIFICATE'
except BaseException as exc:
    failed = True
    report.update(status='READ_ONLY_DIAGNOSTIC_FAILED_PREFIX_PRESERVED', error=type(exc).__name__ + ': ' + str(exc))
    phase('PROBE_EXCEPTION', error=report['error'])
finally:
    protection = {'original_snapshot_count': len(snapshots), 'matrix_changes': [], 'identity_changes': []}
    try:
        now_pointers = {o.as_pointer() for o in bpy.data.objects}
        before_pointers = {row[2] for row in snapshots}
        protection['object_identity_set_unchanged'] = now_pointers == before_pointers
        maximum = 0.0
        for obj, name, pointer, before in snapshots:
            if obj.as_pointer() != pointer or obj.name != name:
                protection['identity_changes'].append(name)
            after = np.asarray(obj.matrix_world.copy(), dtype=np.float64)
            error = float(np.max(np.abs(after - before)))
            maximum = max(maximum, error)
            if error != 0.0:
                protection['matrix_changes'].append({'name': name, 'max_matrix_element_error': error})
        protection['max_matrix_element_error'] = maximum
        protection['actual_matrix_reads'] = len(snapshots)
        protection['selected_visibility_or_modifier_changes'] = [name for name, before in VISIBILITY_BEFORE.items()
                                                                  if visibility(bpy.data.objects[name]) != before]
        protection['frame_after'] = bpy.context.scene.frame_current if snapshots else None
        protection['source_sha256_after'] = sha(SOURCE)
        protection['source_unchanged'] = protection['source_sha256_after'] == SOURCE_SHA
        protection['camera_record_unchanged'] = sha(CAMERA_RECORD) == CAMERA_SHA
        protection['status'] = 'PASS' if (bool(snapshots) and protection['object_identity_set_unchanged'] and
                              not protection['matrix_changes'] and not protection['identity_changes'] and
                              not protection['selected_visibility_or_modifier_changes'] and protection['frame_after'] == 0 and
                              protection['source_unchanged'] and protection['camera_record_unchanged']) else 'FAIL'
    except BaseException as exc:
        protection.update(status='PROTECTION_CHECK_FAILED', error=type(exc).__name__ + ': ' + str(exc))
    write('final-protection.json', protection)
    report['protection'] = protection
    report['elapsed_seconds'] = time.monotonic() - START
    write('report.json', report)
    phase('PROBE_TERMINAL', status=report['status'], protection=protection['status'])
if failed or protection['status'] != 'PASS':
    raise SystemExit(1)
