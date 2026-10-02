"""One magnified neutral tyre-letter observation. No model or material edits.

This is a visualization replay of the scoped repair verified at 66085d7.
Only18qualified station0 glyphs and its support/drum parenting are replayed.
All original four-station structural/reverse eligibility checks remain intact.
Run only through the reviewed bounded runner after parent coordination.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import struct
import sys
import time
import traceback
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

REPO = Path('/workspace/scratch/a29d03198654/Maz543')
BASE = REPO / 'testcar/outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
BASE_SHA = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
EVIDENCE = REPO / 'testcar/work/cloud-wheel-native-repair-pass-20261002'
REPAIR = EVIDENCE / 'executed-script.py'
REPAIR_SHA = '5940176455cbb19373f96d0b2150dd636006e67eb73d404e44bf77b9313d49e8'
SUMMARY_SHA = 'cc4a64c3da191351a289100abc6f9a87f0f20204d872e71e9995a6f1331854ac'
PROCESS_SHA = '2ba906d3cf8f6000a002a4c96dc5f739d51779b28be3bb1123b8d1a1b7b42244'
COMMIT = '66085d7f353b6a5ee6d441243f3e0618e2ac0b64'
START = time.monotonic()
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--view', choices=['neutral', 'spin'], required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
assert args.view == 'neutral', 'This controlled close-up changes framing only at the original neutral pose'
OUT = args.output.resolve()
assert OUT.is_dir() and not any(OUT.glob('*.png'))

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

def file_sha(path):
    return sha_bytes(Path(path).read_bytes())

def emit(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def phase(label):
    row = {'phase': label, 'elapsed_seconds': time.monotonic() - START}
    with (OUT / 'phase.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    print('PHASE ' + json.dumps(row), flush=True)

def canonical_ast(value):
    # Empty type_params is a Python3.12 AST serialization addition; exclude
    # that empty metadata field for identical3.11/3.12 source-tree fingerprints.
    # The executable AST itself is never altered by this serializer.
    if isinstance(value, ast.AST):
        return {'node': type(value).__name__, 'fields': {name: canonical_ast(item) for name, item in ast.iter_fields(value)
                if not (name == 'type_params' and item == [])}}
    if isinstance(value, list):
        return [canonical_ast(item) for item in value]
    if isinstance(value, bytes):
        return {'bytes_hex': value.hex()}
    return value

def ast_sha(node):
    return sha_bytes(json.dumps(canonical_ast(node), sort_keys=True, separators=(',', ':')).encode())

def station0_prefix(source):
    assert sha_bytes(source) == REPAIR_SHA
    tree = ast.parse(source)
    expected = {
        67: '71f758f2cefa802881198ae6a3a783507acc327f8412217e0a5e127340ae0f64',
        68: 'd4d8fca6af44cf50bec52cc341933a110893dfca5b7b91fb311d882e9cd2a780',
        90: 'db66c957620c8cfd9d398b5db420cc825f9a75b6b8c9237a4096786dcb012686',
        91: 'f54e6063a2080b88704640c8196c488c59e7c9e6ba2d1298970da7b807597fe5',
    }
    before = [ast_sha(node) for node in tree.body]
    changes = []
    for index, digest in expected.items():
        assert before[index] == digest, ('Unexpected original AST node', index)
        changes.append({'top_level_index': index, 'original_line': tree.body[index].lineno,
                        'before_ast_sha256': digest, 'before_ast': canonical_ast(tree.body[index])})
    node = tree.body[67]
    assert isinstance(node, ast.Assign) and len(node.value.generators) == 1 and not node.value.generators[0].ifs
    node.value.generators[0].ifs.append(ast.parse("row['object'].startswith('BL_Tyre_0_emboss_')", mode='eval').body)
    assert tree.body[68].test.comparators[0].value == 72
    tree.body[68].test.comparators[0].value = 18
    assert tree.body[90].test.values[0].comparators[0].value == 72
    tree.body[90].test.values[0].comparators[0].value = 18
    assert isinstance(tree.body[91], ast.For) and isinstance(tree.body[91].iter, ast.Name) and tree.body[91].iter.id == 'station'
    tree.body[91].iter = ast.parse('station[:1]', mode='eval').body
    ast.fix_missing_locations(tree)
    after = [ast_sha(node) for node in tree.body]
    assert len(before) == len(after) and [i for i, (a, b) in enumerate(zip(before, after)) if a != b] == [67, 68, 90, 91]
    for row in changes:
        node = tree.body[row['top_level_index']]
        row.update(after_ast_sha256=ast_sha(node), after_ast=canonical_ast(node))
    return tree, {'source_sha256': REPAIR_SHA, 'changed_top_level_nodes': [67, 68, 90, 91],
                  'all_other_top_level_nodes_unchanged': True, 'changes': changes,
                  'scope': 'Only station0 native demonstration; full4station eligibility and all original geometry remain; not full4station candidate replay'}

def matrix(value):
    return [list(row) for row in value]

def plain(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bpy.types.ID):
        return [value.bl_rna.identifier, value.name, value.as_pointer()]
    try:
        return [plain(item) for item in value]
    except TypeError:
        return str(value)

def shader_tree(tree, seen=None):
    if tree is None:
        return None
    seen = set() if seen is None else seen
    if tree.as_pointer() in seen:
        return ['already_observed', tree.name]
    seen.add(tree.as_pointer())
    nodes = []
    for node in tree.nodes:
        properties = {}
        for prop in node.bl_rna.properties:
            if prop.identifier in {'rna_type', 'id_data', 'internal_links', 'inputs', 'outputs', 'dimensions', 'select', 'location', 'width', 'height'}:
                continue
            if prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM', 'POINTER'}:
                properties[prop.identifier] = plain(getattr(node, prop.identifier))
        nodes.append({'name': node.name, 'type': node.bl_idname, 'properties': properties,
                      'inputs': [[socket.identifier, plain(socket.default_value)] for socket in node.inputs if hasattr(socket, 'default_value')],
                      'group': shader_tree(getattr(node, 'node_tree', None), seen)})
    return {'name': tree.name, 'nodes': nodes,
            'links': sorted([link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier] for link in tree.links)}

def material_signature():
    records = []
    for material in sorted(bpy.data.materials, key=lambda item: item.name):
        properties = {}
        for prop in material.bl_rna.properties:
            if prop.identifier in {'rna_type', 'id_data', 'original', 'users', 'tag', 'is_updated', 'is_updated_data', 'preview', 'node_tree'}:
                continue
            if prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
                properties[prop.identifier] = plain(getattr(material, prop.identifier))
        records.append({'name': material.name, 'properties': properties, 'tree': shader_tree(material.node_tree)})
    return sha_bytes(json.dumps(records, sort_keys=True).encode())

def object_visibility(objects):
    return {obj.name: [obj.hide_render, obj.hide_viewport, obj.hide_get(), obj.visible_camera,
                       [collection.name for collection in obj.users_collection]] for obj in objects}

def object_bindings(objects):
    return {obj.name: [[slot.link, slot.material.name if slot.material else None] for slot in obj.material_slots]
            for obj in objects}

def collection_visibility():
    result = {'collections': {item.name: [item.hide_render, item.hide_viewport] for item in bpy.data.collections}, 'layers': {}}
    def walk(layer, path):
        key = path + '/' + layer.name
        result['layers'][key] = [layer.exclude, layer.hide_viewport, layer.holdout, layer.indirect_only]
        for child in layer.children:
            walk(child, key)
    for view_layer in bpy.context.scene.view_layers:
        walk(view_layer.layer_collection, view_layer.name)
    return result

report = {'status': 'STARTED_NOT_RENDERED', 'source_sha256': file_sha(BASE), 'verified_commit': COMMIT,
          'demonstration_scope': 'Station0-only local native demonstration of the66085repair method; no full4station replay claim',
          'selected_view': args.view,
          'material_fingerprint_scope': 'Pointer-bearing fingerprint is compared only inside this process; cross-process identity is supported by pinned source plus internal protection, not equal fingerprint strings',
          'repair_script_sha256': file_sha(REPAIR), 'views': [], 'saved_blend': False, 'saved_glb': False,
          'all_16_whole_vehicle_gates': 'OPEN', 'retained_neutral_camber_degrees': 0,
          'drum_geometry': 'Original simplified capped-cylinder proxy; not factory internal construction',
          'full_prior_verification_repeated': False,
          'skipped_prior_checks': ['776-object post-repair neutral regression', '8 spin trials across all4stations',
                                   '4 station restorations and Euler no-motion negative controls',
                                   'Complete prior final-protection and report routines'],
          'inherited_verified_scope': 'See pinned SUMMARY.json and process.json from66085d7; images add no new mechanical acceptance',
          'cross_process_uv_material_hash_note': 'Prior301combined signature differences remain unresolved. The newer4representative component readout narrows those representatives to evaluated SurfaceUV summaries; cause and numeric magnitude remain unknown. This is not localization of all301objects or a cross-process pixel/appearance identity claim'}
spin = None
original_action = original_basis = original_euler = None
original_quaternion = None
original_camera = None
added_objects = []
try:
    assert report['source_sha256'] == BASE_SHA
    assert report['repair_script_sha256'] == REPAIR_SHA
    assert file_sha(EVIDENCE / 'SUMMARY.json') == SUMMARY_SHA
    assert file_sha(EVIDENCE / 'process.json') == PROCESS_SHA
    prior_process = json.loads((EVIDENCE / 'process.json').read_text())
    assert prior_process['exit_code'] == 0 and prior_process['script_sha256'] == REPAIR_SHA
    repair_source = REPAIR.read_bytes()
    tree, transformation = station0_prefix(repair_source)
    emit('ast-transformation.json', transformation)
    opening_end = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.FunctionDef) and node.name == 'update')
    repair_end = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'neutral' for target in node.targets))
    assert opening_end == 27 and repair_end == 92 and tree.body[repair_end - 1].end_lineno == 206
    namespace = {'__name__': '__native_repair_prefix__', '__file__': str(REPAIR)}
    saved_argv = sys.argv[:]
    sys.argv = [str(REPAIR), '--', '--base', str(BASE), '--sha', BASE_SHA,
                '--output', str(OUT / 'repair-prefix'), '--repository', str(REPO)]
    try:
        # Exact AST statements0:27 open the pinned source and run original guards.
        phase('SOURCE_OPEN_BEGIN')
        exec(compile(ast.Module(body=tree.body[:opening_end], type_ignores=[]), str(REPAIR), 'exec'), namespace)
        phase('SOURCE_OPEN_COMPLETE')
        original_objects = list(bpy.data.objects)
        visibility_before = object_visibility(original_objects)
        bindings_before = object_bindings(original_objects)
        collections_before = collection_visibility()
        materials_before = material_signature()
        world_before = bpy.context.scene.world
        world_signature_before = shader_tree(world_before.node_tree) if world_before else None
        # All qualification guards and the776object baseline remain unchanged.
        # Only the four recorded nodes restrict actual mutation to station0.
        for begin, end, label in [(opening_end, 60, 'FULL_ELIGIBILITY_AND_REVERSE_CHECKS'),
                                  (60, 82, 'FULL_BASELINE_AND_STATION0_PROTECTIONS'),
                                  (82, 83, 'NATIVE_18_APPLY'),
                                  (83, 91, 'POST_APPLY_FONT_AND_PEER_PROTECTIONS'),
                                  (91, repair_end, 'STATION0_NEUTRAL_PARENTING')]:
            phase(label + '_BEGIN')
            exec(compile(ast.Module(body=tree.body[begin:end], type_ignores=[]), str(REPAIR), 'exec'), namespace)
            phase(label + '_COMPLETE')
    finally:
        sys.argv = saved_argv
    assert len(namespace['apply_records']) == 18 and len(namespace['rows']) == 1
    assert len(namespace['shrink']) == 72 and len(namespace['station']) == 4
    assert namespace['rows'][0]['station'] == 0
    assert all(item['object'].startswith('BL_Tyre_0_emboss_') for item in namespace['apply_records'])
    assert object_visibility(original_objects) == visibility_before
    assert object_bindings(original_objects) == bindings_before
    assert collection_visibility() == collections_before
    assert material_signature() == materials_before
    used_images = {}
    def find_material_images(tree, owner, seen):
        if tree is None or tree.as_pointer() in seen:
            return
        seen.add(tree.as_pointer())
        for node in tree.nodes:
            image = getattr(node, 'image', None)
            if image is not None:
                used_images.setdefault(image.name, {'image': image, 'owners': []})['owners'].append(owner)
            find_material_images(getattr(node, 'node_tree', None), owner, seen)
    for obj in original_objects:
        if obj.hide_render:
            continue
        for slot in obj.material_slots:
            if slot.material:
                find_material_images(slot.material.node_tree, slot.material.name, set())
    find_material_images(world_before.node_tree if world_before else None, 'original_world', set())
    resource_rows = []
    for name, item in used_images.items():
        image = item['image']
        packed = bool(image.packed_file or len(image.packed_files))
        external = image.source in {'FILE', 'MOVIE', 'SEQUENCE', 'TILED'} and not packed
        resolved = bpy.path.abspath(image.filepath, library=image.library)
        available = not external or os.path.isfile(resolved)
        resource_rows.append({'image': name, 'source': image.source, 'packed': packed,
                              'resolved_external_path': resolved if external else None, 'available': available,
                              'material_owners': sorted(set(item['owners']))})
        assert available, ('Original used image resource unavailable; do not substitute', name, resolved)
    report['original_used_image_resource_audit'] = resource_rows
    report.update(prefix_seconds=time.monotonic() - START, prefix_statement_count=repair_end,
                  prefix_source_lines=[1, 206], exact_unmodified_ast_prefix=False,
                  precisely_transformed_ast_nodes=[67, 68, 90, 91],
                  full_four_station_qualification_preserved=True,
                  native_shrinkwrap_applies=18, native_neutral_joint_frames=1,
                  source_objects_retained=len(original_objects), original_material_fingerprint=materials_before)
    print('STATION0_REPAIR_PREFIX_FINISHED', report['prefix_seconds'], flush=True)
    phase('STATION0_PREFIX_AND_PRESENTATION_PROTECTIONS_COMPLETE')
    scene = bpy.context.scene
    original_camera = scene.camera
    update = namespace['update']
    points = namespace['points']
    spin = bpy.data.objects['wheels_pivot_002']
    tyre = bpy.data.objects['BL_Tyre_0_VI203_profile']
    drum = bpy.data.objects['brakes_0003']
    glyphs = sorted([obj for obj in namespace['qualified_glyphs'] if obj.get('tyreIndex') == 0], key=lambda obj: obj.name)
    assert len(glyphs) == 18 and spin.rotation_mode == 'QUATERNION'
    assert spin.animation_data and spin.animation_data.action
    original_action = spin.animation_data.action
    original_basis = spin.matrix_basis.copy()
    original_euler = spin.rotation_euler.copy()
    original_quaternion = spin.rotation_quaternion.copy()
    world_neutral = spin.matrix_world.copy()
    witnesses = [tyre, drum, *glyphs]
    snapshot = {obj.name: points(obj) for obj in witnesses}
    neutral_matrices = {obj.name: obj.matrix_world.copy() for obj in original_objects}
    moving_names = {obj.name for obj in spin.children_recursive} | {spin.name}
    spin.animation_data.action = None
    update()
    assert max(abs(spin.matrix_world[r][c] - world_neutral[r][c]) for r in range(4) for c in range(4)) == 0

    # Preserve all original worlds, lights, geometry and visibility. The only
    # presentation objects added are one camera and two area lights.
    center = world_neutral.translation.copy()
    assert abs(center.x + 3.08) < 2e-6 and abs(center.y - 1.1875) < 2e-6 and abs(center.z - .75) < 2e-6
    # Offset the crop forward/up to retain the original interfering lower step
    # and the near door/body above the installed first wheel.
    target = center + Vector((-.38, 0, .22))
    camera_data = bpy.data.cameras.new('WHEEL_VIEW_ONLY_SAME_CAMERA')
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    added_objects.append(camera)
    camera.location = target + Vector((-.70, 5.2, .55))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 2.60
    camera_data.clip_start = .01
    camera_data.clip_end = 100
    scene.camera = camera
    light_records = []
    for name, offset, energy, size in [('WHEEL_VIEW_ONLY_KEY', (-1.5, 2.6, 2.5), 650, 1.7),
                                       ('WHEEL_VIEW_ONLY_FILL', (2.0, 2.5, .8), 220, 2.0)]:
        light_data = bpy.data.lights.new(name, 'AREA')
        light_data.energy = energy
        light_data.shape = 'DISK'
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        added_objects.append(light)
        light.location = center + Vector(offset)
        light.rotation_euler = (center - light.location).to_track_quat('-Z', 'Y').to_euler()
        light_records.append({'name': name, 'world_position_m': list(light.location), 'watts': energy, 'disk_size_m': size})
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    if hasattr(scene.cycles, 'denoising_use_gpu'):
        scene.cycles.denoising_use_gpu = False
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.seed = 20261002
    scene.cycles.use_animated_seed = False
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 4
    scene.cycles.transparent_max_bounces = 8
    scene.render.use_persistent_data = False
    scene.render.use_simplify = False
    scene.render.use_motion_blur = False
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.render.use_stamp = False
    scene.render.use_border = False
    scene.render.use_crop_to_border = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.view_settings.use_curve_mapping = False
    update()
    camera_matrix = camera.matrix_world.copy()
    report.update(camera_world_matrix=matrix(camera_matrix), camera_target_m=list(target),
                  camera_orthographic_scale_m=2.60, camera_view='Station0 installed wheel from+Y, slight front/elevated side view; original lower step and near door/body retained',
                  resolution=[1100, 1000], cycles={'device': 'CPU', 'threads': 2, 'samples': 12, 'denoise': True},
                  additional_lights=light_records, inherited_world_unchanged=True, all_original_lights_retained=True,
                  persistent_render_data=False, persistent_data_note='Single-view process; avoid retaining cross-render cache. This does not diagnose the priorSIGKILL.',
                  labels_baked_into_pixels=False, original_geometry_visibility_unchanged=True)
    # Whole tyre projection must fit without reframing between the two images.
    tyre_xyz = snapshot[tyre.name][0]
    projected = np.asarray([world_to_camera_view(scene, camera, Vector(row)) for row in tyre_xyz])
    assert projected[:, 0].min() > .02 and projected[:, 0].max() < .98
    assert projected[:, 1].min() > .02 and projected[:, 1].max() < .98
    report['neutral_tyre_projected_bounds'] = [projected.min(axis=0).tolist(), projected.max(axis=0).tolist()]
    context_records = []
    for name in ['BL_Cab_-1_step', *['BL_Step_-1_' + str(index) for index in range(20)]]:
        obj = bpy.data.objects[name]
        assert not obj.hide_render
        xyz, triangles = points(obj)
        screen = np.asarray([world_to_camera_view(scene, camera, Vector(row)) for row in xyz])
        context_records.append({'object': name, 'projected_bounds': [screen.min(axis=0).tolist(), screen.max(axis=0).tolist()],
                                'original_visibility_retained': True,
                                'limits': 'Projection only, not occlusion proof; known step/tyre interference remains'})
    assert all(row['projected_bounds'][1][0] > 0 and row['projected_bounds'][0][0] < 1 and
               row['projected_bounds'][1][1] > 0 and row['projected_bounds'][0][1] < 1 for row in context_records)
    report['full_view_step_context_before_crop'] = context_records
    report['full_view_tyre_projected_bounds_before_crop'] = report.pop('neutral_tyre_projected_bounds')
    # The original camera world matrix, lamps, materials, samples and pose stay
    # unchanged. Only orthographic scale and sensor shifts select a tighter crop.
    reference_path = Path('/workspace/scratch/a29d03198654/maz-native-wheel-views-20261002/attempt-station0-neutral-01/ready-to-render.json')
    assert file_sha(reference_path) == '054d8e227e1947ae27e49ace5dbe9601cbcd648960e3d8223cf069ff523defe0'
    reference = json.loads(reference_path.read_bytes())
    camera_reference_error = max(abs(camera_matrix[r][c] - reference['camera_world_matrix'][r][c]) for r in range(4) for c in range(4))
    assert camera_reference_error <= 1e-6
    glyph_world = np.concatenate([snapshot[obj.name][0] for obj in glyphs])
    inverse_camera = np.asarray(camera_matrix.inverted(), dtype=np.float64)
    glyph_local = glyph_world @ inverse_camera[:3,:3].T + inverse_camera[:3,3]
    lo, hi = glyph_local[:,:2].min(axis=0), glyph_local[:,:2].max(axis=0)
    centre = (lo + hi) / 2
    aspect = scene.render.resolution_x / scene.render.resolution_y
    fitted_scale = float(max(hi[0] - lo[0], (hi[1] - lo[1]) * aspect) * 1.4)
    assert .3 < fitted_scale < .9
    camera_data.ortho_scale = fitted_scale
    def native_frame_centre():
        return np.asarray([list(v) for v in camera_data.view_frame(scene=scene)], dtype=float)[:,:2].mean(axis=0)
    camera_data.shift_x = camera_data.shift_y = 0
    frame_zero = native_frame_centre()
    camera_data.shift_x = 1
    basis_x = native_frame_centre() - frame_zero
    camera_data.shift_x = 0
    camera_data.shift_y = 1
    basis_y = native_frame_centre() - frame_zero
    camera_data.shift_y = 0
    shifts = np.linalg.solve(np.column_stack((basis_x, basis_y)), centre - frame_zero)
    assert np.all(np.isfinite(shifts)) and np.max(np.abs(shifts)) < 5
    camera_data.shift_x, camera_data.shift_y = map(float, shifts)
    update()
    assert camera.matrix_world == camera_matrix, 'Framing may not change the actual camera transform'
    cropped = np.asarray([world_to_camera_view(scene, camera, Vector(row)) for row in glyph_world])
    assert np.all(np.isfinite(cropped)) and cropped[:,0].min() > .08 and cropped[:,0].max() < .92
    assert cropped[:,1].min() > .08 and cropped[:,1].max() < .92
    assert cropped[:,2].min() > camera_data.clip_start
    report['detail_crop'] = {'scope': 'Neutral magnification/crop only; whole original vehicle geometry, visibility, lights and materials retained; original body can still occlude part of the lettering',
        'source_camera_record_sha256': file_sha(reference_path), 'camera_world_matrix_max_difference_from_full_view': camera_reference_error,
        'world_matrix_unchanged_during_crop': True, 'glyphs_used_for_native_evaluated_bounds': len(glyphs),
        'fitted_margin_factor': 1.4, 'actual_ortho_scale_m': camera_data.ortho_scale,
        'actual_shift_x': camera_data.shift_x, 'actual_shift_y': camera_data.shift_y,
        'native_frame_calibration_columns': [basis_x.tolist(), basis_y.tolist()],
        'actual_all_glyph_ndc_bounds': [cropped.min(axis=0).tolist(), cropped.max(axis=0).tolist()],
        'no_lighting_material_geometry_or_pose_change': True}
    report['camera_orthographic_scale_m'] = camera_data.ortho_scale
    report['camera_shift_xy'] = [camera_data.shift_x, camera_data.shift_y]
    report['camera_view'] = 'Magnified neutral station0 lettering, same camera world matrix and original full-view illumination; no whole-vehicle readability claim'
    phase('DETAIL_CROP_READY')
    emit('ready-to-render.json', report)
    selected_views = [('neutral', 0.0)] if args.view == 'neutral' else [('spin-0p731', .731)]
    for label, angle in selected_views:
        spin.matrix_basis = original_basis @ Matrix.Rotation(angle, 4, 'Y')
        update()
        delta = spin.matrix_world @ world_neutral.inverted()
        observed_angle = delta.to_quaternion().angle
        assert abs(observed_angle - angle) < 2e-6
        delta_array = np.asarray(delta, dtype=np.float64)
        measured = []
        for obj in witnesses:
            xyz, triangles = points(obj)
            old, old_triangles = snapshot[obj.name]
            assert xyz.shape == old.shape and np.array_equal(triangles, old_triangles)
            error = float(np.max(np.linalg.norm(xyz - (old @ delta_array[:3, :3].T + delta_array[:3, 3]), axis=1)))
            displacement = float(np.max(np.linalg.norm(xyz - old, axis=1)))
            assert error < 2e-5
            if angle:
                assert displacement > .001
            measured.append({'object': obj.name, 'max_rigid_error_m': error, 'max_actual_vertex_displacement_m': displacement})
        # This is a pose-level original matrix/visibility check, not a duplicate
        # of the complete776/8trial prior geometry regression.
        fixed_errors = {}
        fixed_matrix_reads = 0
        for obj in original_objects:
            if obj.name in moving_names:
                continue
            # Read the actual current matrix exactly once per object per pose.
            # Compare all16coefficients, preserving the zero-error gate.
            current_matrix = obj.matrix_world.copy()
            fixed_matrix_reads += 1
            original_matrix = neutral_matrices[obj.name]
            fixed_errors[obj.name] = max(abs(current_matrix[r][c] - original_matrix[r][c]) for r in range(4) for c in range(4))
        assert fixed_matrix_reads == len(fixed_errors)
        assert max(fixed_errors.values(), default=0) == 0
        assert object_visibility(original_objects) == visibility_before
        assert object_bindings(original_objects) == bindings_before
        assert collection_visibility() == collections_before
        assert camera.matrix_world == camera_matrix
        png = OUT / ('wheel-' + label + '.png')
        assert not png.exists()
        scene.render.filepath = str(png)
        record = {'view': label, 'status': 'RENDER_STARTED', 'requested_spin_radians': angle,
                  'observed_world_spin_radians': observed_angle, 'measured_witnesses': measured,
                  'same_camera_world_matrix': matrix(camera_matrix), 'fixed_original_matrices_checked': len(fixed_errors),
                  'fixed_original_actual_matrix_reads_this_pose': fixed_matrix_reads,
                  'matrix_read_method': 'One fresh matrix_world.copy() per retained fixed original object at this pose; all16coefficients compared; no cross-pose reuse',
                  'fixed_original_max_matrix_error': max(fixed_errors.values(), default=0), 'started_script_seconds': time.monotonic() - START}
        emit(label + '-start.json', record)
        phase(label + '_RENDER_BEGIN')
        view_start = time.monotonic()
        try:
            result = bpy.ops.render.render(write_still=True)
            assert result == {'FINISHED'} and png.is_file()
            image_bytes = png.read_bytes()
            assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
            dimensions = list(struct.unpack('>II', image_bytes[16:24]))
            assert dimensions == [1100, 1000]
            record.update(status='RENDER_FINISHED', render_operator_return=sorted(result),
                          png=png.name, png_bytes=len(image_bytes), png_sha256=sha_bytes(image_bytes), dimensions=dimensions)
        except Exception as exc:
            record.update(status='RENDER_FAILED', error=type(exc).__name__ + ': ' + str(exc))
            raise
        finally:
            record['render_elapsed_seconds'] = time.monotonic() - view_start
            emit(label + '-terminal.json', record)
            report['views'].append(record)
            phase(label + '_RENDER_TERMINAL')
        assert scene.cycles.device == 'CPU'
        print('VIEW_TERMINAL', label, record['status'], record['render_elapsed_seconds'], flush=True)
    report['status'] = 'ONE_STATION0_NATIVE_VIEW_RENDERED_PENDING_VISUAL_REVIEW'
except Exception as exc:
    report.update(status='FAILED_OR_INCOMPLETE_NOT_ACCEPTED', error=type(exc).__name__ + ': ' + str(exc), traceback=traceback.format_exc())
    raise
finally:
    phase('FINALLY_RESTORATION_BEGIN')
    cleanup_errors = []
    if spin is not None and original_basis is not None:
        try:
            spin.rotation_euler = original_euler
            spin.matrix_basis = original_basis
            spin.animation_data.action = original_action
            bpy.context.view_layer.update()
            assert spin.matrix_basis == original_basis
            assert spin.rotation_quaternion == original_quaternion
            assert spin.rotation_euler == original_euler
            assert spin.animation_data.action == original_action
            restored = []
            for obj in witnesses:
                xyz, triangles = points(obj)
                old, old_triangles = snapshot[obj.name]
                assert np.array_equal(triangles, old_triangles)
                error = float(np.max(np.linalg.norm(xyz - old, axis=1)))
                assert error == 0
                restored.append({'object': obj.name, 'max_restored_vertex_error_m': error})
            report['restoration'] = {'original_spin_action': original_action.name, 'basis_quaternion_and_latent_euler_exact': True, 'witnesses': restored}
        except Exception as exc:
            cleanup_errors.append('spin restoration: ' + repr(exc))
    try:
        if 'original_objects' in globals():
            assert object_visibility(original_objects) == visibility_before
            assert object_bindings(original_objects) == bindings_before
            assert collection_visibility() == collections_before
            assert material_signature() == materials_before
            assert bpy.context.scene.world == world_before
            assert (shader_tree(world_before.node_tree) if world_before else None) == world_signature_before
            assert all(obj.name in bpy.data.objects and bpy.data.objects[obj.name] == obj for obj in original_objects)
            report['final_original_material_visibility_world_and_object_identity_checks'] = 'PASS'
        if 'namespace' in globals() and len(namespace.get('apply_records', [])) == 18:
            font_failures = [name for name, signature in namespace['source_fonts'].items()
                             if namespace['glyph_source_signature'](bpy.data.objects[name]) != signature]
            assert not font_failures and len(namespace['source_fonts']) == 18
            for item in namespace['apply_records']:
                obj = bpy.data.objects[item['object']]
                assert [modifier.type for modifier in obj.modifiers] == ['SOLIDIFY']
                modifier = obj.modifiers[0]
                actual = {'name': modifier.name, 'thickness': modifier.thickness, 'offset': modifier.offset,
                          'use_even_offset': modifier.use_even_offset, 'show_viewport': modifier.show_viewport, 'show_render': modifier.show_render}
                assert actual == item['preserved_solidify']
                assert (obj.hide_render, obj.hide_viewport, obj.hide_get()) == namespace['glyph_visibility'][obj.name]
            report['final_station0_FONT_Solidify_and_glyph_visibility'] = {'status': 'PASS', 'fonts': 18, 'glyphs': 18}
        report['source_sha256_after'] = file_sha(BASE)
        assert report['source_sha256_after'] == BASE_SHA
        if original_camera is not None:
            bpy.context.scene.camera = original_camera
    except Exception as exc:
        cleanup_errors.append('preservation: ' + repr(exc))
    report['cleanup_errors'] = cleanup_errors
    report['script_elapsed_seconds'] = time.monotonic() - START
    if cleanup_errors:
        report['status'] = 'FAILED_RESTORATION_OR_PRESERVATION_NOT_ACCEPTED'
    emit('render-report.json', report)
    phase('FINALLY_RESTORATION_TERMINAL')
    if cleanup_errors:
        raise RuntimeError(cleanup_errors)
