"""Run only inside the pinned official Blender, importing only the pinned GLB."""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_observation import file_record, utc, write_json


def scalar_properties(item):
    """Finite editable RNA value properties; excludes transient readonly caches."""
    result = {}
    for prop in item.bl_rna.properties:
        if prop.is_readonly or prop.type not in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            continue
        value = getattr(item, prop.identifier)
        if getattr(prop, 'is_array', False):
            value = list(value)
        elif isinstance(value, set):
            value = sorted(value)
        result[prop.identifier] = value
    return result


def sequence_hash(collection, field, width, code='f'):
    values = array(code, [0]) * (len(collection) * width)
    collection.foreach_get(field, values)
    return hashlib.sha256(values.tobytes()).hexdigest()


def mesh_record(mesh):
    return {
        'name': mesh.name, 'identity': mesh.as_pointer(),
        'counts': [len(mesh.vertices), len(mesh.edges), len(mesh.loops), len(mesh.polygons)],
        'positions': sequence_hash(mesh.vertices, 'co', 3),
        'edges': sequence_hash(mesh.edges, 'vertices', 2, 'i'),
        'loop_vertices': sequence_hash(mesh.loops, 'vertex_index', 1, 'i'),
        'loop_edges': sequence_hash(mesh.loops, 'edge_index', 1, 'i'),
        'polygon_start': sequence_hash(mesh.polygons, 'loop_start', 1, 'i'),
        'polygon_size': sequence_hash(mesh.polygons, 'loop_total', 1, 'i'),
        'material_indices': sequence_hash(mesh.polygons, 'material_index', 1, 'i'),
        'smooth': sequence_hash(mesh.polygons, 'use_smooth', 1, 'b'),
        'corner_normals': sequence_hash(mesh.corner_normals, 'vector', 3),
        'uv': {layer.name: sequence_hash(layer.data, 'uv', 2) for layer in mesh.uv_layers},
        'color_attributes': {layer.name: {'domain': layer.domain, 'data_type': layer.data_type,
                                          'color': sequence_hash(layer.data, 'color', 4)}
                             for layer in mesh.color_attributes},
        'materials': [mat.name if mat else None for mat in mesh.materials],
    }


def material_record(mat):
    record = {'name': mat.name, 'identity': mat.as_pointer(), 'values': scalar_properties(mat)}
    tree = mat.node_tree
    if tree is not None:
        record['nodes'] = []
        for node in sorted(tree.nodes, key=lambda node: node.name):
            record['nodes'].append({'name': node.name, 'type': node.bl_idname,
                                    'values': scalar_properties(node),
                                    'image': getattr(getattr(node, 'image', None), 'name', None),
                                    'inputs': [scalar_properties(socket) for socket in node.inputs],
                                    'outputs': [scalar_properties(socket) for socket in node.outputs]})
        record['links'] = sorted([link.from_node.name, link.from_socket.identifier,
                                  link.to_node.name, link.to_socket.identifier] for link in tree.links)
    return record


def snapshot(objects, meshes, materials, images):
    def matrix(value):
        return [list(row) for row in value]
    return {
        'objects': [{'name': obj.name, 'identity': obj.as_pointer(), 'type': obj.type,
                     'data': obj.data.as_pointer() if obj.data else None,
                     'parent': obj.parent.as_pointer() if obj.parent else None,
                     'matrix_world': matrix(obj.matrix_world), 'matrix_local': matrix(obj.matrix_local),
                     'matrix_basis': matrix(obj.matrix_basis), 'matrix_parent_inverse': matrix(obj.matrix_parent_inverse),
                     'hide_render': obj.hide_render, 'hide_viewport': obj.hide_viewport,
                     'hide_get': obj.hide_get(), 'visible_get': obj.visible_get(),
                     'material_slots': [(slot.link, getattr(slot.material, 'name', None)) for slot in obj.material_slots],
                     'collections': [(col.name, col.hide_render, col.hide_viewport) for col in obj.users_collection]}
                    for obj in objects],
        'meshes': [mesh_record(mesh) for mesh in meshes],
        'materials': [material_record(mat) for mat in materials],
        'images': [{'name': img.name, 'identity': img.as_pointer(), 'size': list(img.size),
                    'filepath': img.filepath, 'source': img.source, 'alpha_mode': img.alpha_mode,
                    'colorspace': img.colorspace_settings.name,
                    'packed_sha256': hashlib.sha256(bytes(img.packed_file.data)).hexdigest() if img.packed_file else None}
                   for img in images],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--view', choices=('overview', 'side'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    folder = Path(__file__).resolve().parent
    cfg = json.loads((folder / 'observation.json').read_text())
    output = args.output.resolve(strict=True)
    assert output.parent == folder
    started = time.monotonic()
    report = {'title': cfg['title'], 'view': args.view, 'status': 'STARTING', 'started_utc': utc(),
              'qualification': cfg['qualification'], 'render_settings': cfg['render'],
              'guard_scope': 'Imported objects: identity, parent/data, transforms, visibility, slots and collection visibility. Meshes: identity, positions, topology, corner normals, UV, vertex colors and material assignments. Materials: editable scalar/array RNA, node values/sockets/links and image binding. Images: identity, packed bytes and color settings. This is a finite non-mutation guard, not native-source equivalence.'}
    before = None
    model = meshes = materials = images = None

    def stage(name):
        row = {'stage': name, 'utc': utc(), 'elapsed_seconds': time.monotonic() - started}
        write_json(output / 'stage.json', row)
        with (output / 'stages.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print('OBSERVATION_STAGE ' + json.dumps(row), flush=True)

    try:
        stage('VERIFY_INPUT_AND_EMPTY_SCENE')
        assert bpy.app.version == tuple(map(int, cfg['blender']['version'].split('.')))
        assert bpy.app.build_hash.decode() == cfg['blender']['build_hash']
        report['blender'] = {'version': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode()}
        report['input_before'] = file_record(cfg['input']['path'])
        assert report['input_before'] == cfg['input']
        # Remove only factory-startup data, before importing any model.
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
            for block in list(datablocks):
                datablocks.remove(block)
        scene = bpy.data.scenes.new('Offline GLB observation')
        bpy.context.window.scene = scene
        for old_scene in list(bpy.data.scenes):
            if old_scene != scene:
                bpy.data.scenes.remove(old_scene)
        scene.unit_settings.scale_length = 1.0
        stage('IMPORT_GLTF')
        import_started = time.monotonic()
        result = bpy.ops.import_scene.gltf(filepath=cfg['input']['path'], merge_vertices=False,
                                         import_shading='NORMALS', import_pack_images=True,
                                         import_unused_materials=True, import_merge_material_slots=False,
                                         import_select_created_objects=False)
        assert result == {'FINISHED'}, result
        bpy.context.view_layer.update()
        report['import_seconds'] = time.monotonic() - import_started
        model = sorted(list(scene.objects), key=lambda obj: obj.name)
        meshes = sorted(list(bpy.data.meshes), key=lambda mesh: mesh.name)
        materials = sorted(list(bpy.data.materials), key=lambda mat: mat.name)
        images = sorted(list(bpy.data.images), key=lambda img: img.name)
        assert model and meshes
        report['imported_counts'] = {'objects': len(model), 'mesh_objects': sum(obj.type == 'MESH' for obj in model),
                                     'unique_meshes': len(meshes), 'materials': len(materials), 'images': len(images),
                                     'vertices': sum(len(mesh.vertices) for mesh in meshes),
                                     'polygons': sum(len(mesh.polygons) for mesh in meshes)}
        stage('GUARD_BEFORE')
        before = snapshot(model, meshes, materials, images)
        write_json(output / 'model-before.json', before)
        # World-space bounds only determine observer positions. The model never moves.
        corners = [obj.matrix_world @ Vector(corner) for obj in model if obj.type == 'MESH' for corner in obj.bound_box]
        lower = Vector([min(point[axis] for point in corners) for axis in range(3)])
        upper = Vector([max(point[axis] for point in corners) for axis in range(3)])
        center = (lower + upper) * 0.5
        radius = (upper - lower).length * 0.5
        assert math.isfinite(radius) and radius > 0
        report['bounds_blender'] = {'min': list(lower), 'max': list(upper), 'center': list(center), 'radius': radius}
        stage('SET_OBSERVERS')
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = cfg['render']['samples']
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.max_bounces = 8
        scene.cycles.transmission_bounces = 8
        scene.cycles.transparent_max_bounces = 8
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 2
        scene.render.resolution_x, scene.render.resolution_y = cfg['render']['resolution']
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.image_settings.color_depth = '8'
        scene.render.film_transparent = False
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.exposure = 0
        scene.view_settings.gamma = 1
        world = bpy.data.worlds.new('Observation background')
        scene.world = world
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.6, 0.65, 0.63, 1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
        for name, direction, energy in [('Key', (-6, -8, 10), 2.5), ('Fill', (6, 4, 5), 0.8)]:
            light_data = bpy.data.lights.new('Observation ' + name, 'SUN')
            light_data.energy = energy
            light_data.angle = 0.12
            light = bpy.data.objects.new(light_data.name, light_data)
            scene.collection.objects.link(light)
            light.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
        camera_data = bpy.data.cameras.new('Observation camera')
        camera_data.sensor_fit = 'VERTICAL'
        camera = bpy.data.objects.new(camera_data.name, camera_data)
        scene.collection.objects.link(camera)
        scene.camera = camera
        x, y, z = cfg['views_gltf'][args.view]
        direction = Vector((x, -z, y)).normalized()  # Official importer: X,Y,Z -> X,-Z,Y.
        rotation = (-direction).to_track_quat('-Z', 'Y')
        camera.rotation_euler = rotation.to_euler()
        right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
        aspect = scene.render.resolution_x / scene.render.resolution_y
        if args.view == 'side':
            camera_data.type = 'ORTHO'
            camera_data.ortho_scale = 2 * max(max(abs((point - center).dot(up)) for point in corners),
                                              max(abs((point - center).dot(right)) for point in corners) / aspect) * 1.12
            distance = radius * 3
        else:
            camera_data.type = 'PERSP'
            tangent = math.tan(math.radians(35) / 2)
            camera_data.lens = camera_data.sensor_height / (2 * tangent)
            distance = max((point - center).dot(direction) + max(abs((point - center).dot(up)) / tangent,
                           abs((point - center).dot(right)) / (tangent * aspect)) for point in corners) * 1.12
        camera.location = center + direction * distance
        camera_data.clip_start = max(0.001, radius / 10000)
        camera_data.clip_end = max(100, radius * 100)
        bpy.context.view_layer.update()
        report['camera'] = {'gltf_direction': cfg['views_gltf'][args.view], 'blender_direction': list(direction),
                            'location': list(camera.location), 'target': list(center), 'projection': camera_data.type,
                            'lens_mm': camera_data.lens, 'ortho_scale': camera_data.ortho_scale,
                            'matrix_world': [list(row) for row in camera.matrix_world]}
        image_path = output / (args.view + '-offline-glb-pending-normal-joint-fail-16-open.png')
        assert not image_path.exists()
        scene.render.filepath = str(image_path)
        (output / 'README.txt').write_text(
            cfg['title'] + '\n\n' + image_path.name + '\n'
            'Official Blender 4.5.13 imports the exact published GLB; Cycles CPU2, 1024x640, 16 samples, no denoising.\n'
            'Raw render pixels have no baked status caption; this file and the qualified filename must accompany the image.\n'
            'normal+joint: FAIL_STATIC_NATIVE_TRANSPORT, 2299 issues; all 16 whole-vehicle gates OPEN.\n'
            'This is offline GLB observation. Browser QA is NOT_RUN; native shader equivalence is NOT_ESTABLISHED.\n'
            'No source .blend is opened or saved. No GLB is exported. Consult process.json for terminal success/failure.\n',
            encoding='utf-8')
        stage('RENDER_' + args.view.upper())
        render_started = time.monotonic()
        try:
            result = bpy.ops.render.render(write_still=True)
        finally:
            report['render_seconds'] = time.monotonic() - render_started
        assert result == {'FINISHED'} and image_path.is_file(), result
        report['image'] = {'title': cfg['title'], **file_record(image_path), 'resolution': cfg['render']['resolution']}
    except BaseException as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        report['traceback'] = traceback.format_exc()
        print(report['traceback'], flush=True)
    finally:
        try:
            stage('FINAL_GUARDS')
            report['input_after'] = file_record(cfg['input']['path'])
            report['input_unchanged'] = report['input_after'] == cfg['input']
            if before is not None:
                after = snapshot(model, meshes, materials, images)
                write_json(output / 'model-after.json', after)
                report['model_unchanged_in_guard_scope'] = before == after
        except BaseException as exc:
            report['guard_error'] = type(exc).__name__ + ': ' + str(exc)
        passed = (not report.get('error') and not report.get('guard_error') and report.get('image')
                  and report.get('input_unchanged') is True and report.get('model_unchanged_in_guard_scope') is True)
        report['status'] = 'OFFLINE_OBSERVATION_RENDERED_GUARDS_PASS' if passed else 'FAILED_OR_INCOMPLETE'
        report['elapsed_seconds'] = time.monotonic() - started
        report['finished_utc'] = utc()
        write_json(output / 'observation-report.json', report)
        stage(report['status'])
    if not passed:
        raise RuntimeError('Offline GLB observation failed; preserve all outputs and consult observation-report.json')


if __name__ == '__main__':
    main()
