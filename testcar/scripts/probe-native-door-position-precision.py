"""Read the pinned native Textured source; encode/decode doors only in memory.

Blender 4.5.13, factory-startup, disable-autoexec, CPU1; no model/image save.
Uses the installed exporter gatherer and its real Draco encoder implementation.
It aborts before buffer/image finalization or any glTF file-writing operation.
"""
import argparse
import copy
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Vector, kdtree

SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
SOURCE_SHA = '6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266'
PIVOTS = ['cab_pivot_002', 'cab_pivot_003', 'cab_pivot_006', 'cab_pivot_007']
parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--out', required=True)
parser.add_argument('--grid-reader', required=True)
parser.add_argument('--decoder-dir', required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(args.source).resolve(), Path(args.out).resolve()
assert out.is_dir() and not (out / 'native-probe.json').exists()
assert bpy.app.version == (4, 5, 13)
assert bpy.app.build_hash.decode() == 'daeeeca98fb0'
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert SHA(source) == SOURCE_SHA
before_source = {'sha256': SHA(source), 'bytes': source.stat().st_size}
bpy.ops.wm.open_mainfile(filepath=str(source))
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

# Exact merged source, not the separate Master parts and not decoded GLB input.
selected = []
for door, pivot_name in enumerate(PIVOTS):
    pivot = bpy.data.objects[pivot_name]
    prefix = f'BL_Door_{-1 if door < 2 else 1}_{door % 2}'
    expected = {prefix + '_' + suffix for suffix in ['handle', 'lock', 'window']}
    expected |= {f'BL_Merged_{pivot_name}_{suffix}' for suffix in ['OD_green_aged_enamel', 'Rubber_window_seals']}
    assert {o.name for o in pivot.children} == expected
    selected += list(pivot.children)
assert len(selected) == 20 and all(o.type == 'MESH' for o in selected)
native_before = {o.name: {'matrix': [list(r) for r in o.matrix_world],
                         'vertices': len(o.data.vertices), 'polygons': len(o.data.polygons),
                         'data_name': o.data.name} for o in selected}

# Same native n-gon preparation as export-va180-cab-candidate.py. No save.
triangulated = []
for obj in selected:
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    count = sum(len(p.vertices) > 4 for p in mesh.polygons)
    ev.to_mesh_clear()
    if count:
        modifier = obj.modifiers.new('EXPORT ONLY native n-gon triangulation', 'TRIANGULATE')
        modifier.min_vertices = 5
        modifier.ngon_method = 'BEAUTY'
        if hasattr(modifier, 'keep_custom_normals'):
            modifier.keep_custom_normals = True
        triangulated.append({'name': obj.name, 'evaluated_ngons': count})
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for obj in selected:
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = selected[0]

from io_scene_gltf2.blender.exp import export as exporter
from io_scene_gltf2.io.exp import draco as compressor
from io_scene_gltf2.blender.exp.material import encode_image
from io_scene_gltf2.io.com.draco import dll_path
pins = {
    encode_image.__file__: '00e651d2f4eef3edfdcc48a7ada9e6175cf02a1b2623e8766db7bd235d0312a8',
    str(dll_path()): '687e03509fa38a9ff7db8a5842638002eba9ea5fa1f620839ef8c09270c4c54e',
    compressor.__file__: '783dea6179bae8ad0c1609faf4bdb2fbdff4ffad877e2900935c57ecfc887b3c',
    exporter.__file__: '273a06669ffe6c475b52460feabee22a05bb87cfbb33896e412beb8400bf8e26',
}
for filename, expected in pins.items():
    assert SHA(filename) == expected, filename
dll = C.cdll.LoadLibrary(str(dll_path()))
for name, restype, argtypes in [
    ('decoderCreate', C.c_void_p, []), ('decoderRelease', None, [C.c_void_p]),
    ('decoderDecode', C.c_bool, [C.c_void_p, C.c_void_p, C.c_size_t]),
    ('decoderReadAttribute', C.c_bool, [C.c_void_p, C.c_uint32, C.c_size_t, C.c_char_p]),
    ('decoderGetAttributeByteLength', C.c_size_t, [C.c_void_p, C.c_uint32]),
    ('decoderCopyAttribute', None, [C.c_void_p, C.c_uint32, C.c_void_p]),
    ('decoderGetVertexCount', C.c_uint32, [C.c_void_p]),
    ('decoderGetIndexCount', C.c_uint32, [C.c_void_p]),
    ('decoderReadIndices', C.c_bool, [C.c_void_p, C.c_size_t]),
    ('decoderGetIndicesByteLength', C.c_size_t, [C.c_void_p]),
    ('decoderCopyIndices', None, [C.c_void_p, C.c_void_p]),
]:
    fn = getattr(dll, name); fn.restype = restype; fn.argtypes = argtypes

def decode_positions(raw, unique_id):
    decoder = dll.decoderCreate()
    try:
        assert dll.decoderDecode(decoder, raw, len(raw))
        assert dll.decoderReadAttribute(decoder, unique_id, 5126, b'VEC3')
        size = dll.decoderGetAttributeByteLength(decoder, unique_id)
        buffer = C.create_string_buffer(size)
        dll.decoderCopyAttribute(decoder, unique_id, buffer)
        points = np.frombuffer(buffer.raw, dtype='<f4').reshape(-1, 3).astype(np.float64)
        assert len(points) == dll.decoderGetVertexCount(decoder)
        assert dll.decoderReadIndices(decoder, 5125)
        index_buffer = C.create_string_buffer(dll.decoderGetIndicesByteLength(decoder))
        dll.decoderCopyIndices(decoder, index_buffer)
        indices = np.frombuffer(index_buffer.raw, dtype='<u4').reshape(-1, 3).copy()
        assert indices.size == dll.decoderGetIndexCount(decoder)
        return points, indices
    finally:
        dll.decoderRelease(decoder)

def tree(points):
    result = kdtree.KDTree(len(points))
    for i, point in enumerate(points): result.insert(Vector(point), i)
    result.balance()
    return result

def directed_chosen_vertex_distance(points, other, other_tree):
    # KD chooses the candidate. The recorded distance is recomputed in Float64.
    # Even if KD does not choose the exact nearest, this is an upper bound to
    # some real input/output vertex; it is not a continuous surface proof.
    maximum = 0.0
    for point in points:
        _, index, _ = other_tree.find(Vector(point))
        maximum = max(maximum, float(np.linalg.norm(point - other[index])))
    return maximum

def barrel_components(points, triangles):
    parent = list(range(len(points)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(a, b):
        a, b = root(a), root(b)
        if a != b: parent[b] = a
    for a, b, c in triangles:
        join(int(a), int(b)); join(int(a), int(c))
    identical = {}
    for i, point in enumerate(points):
        key = tuple(point)
        if key in identical: join(i, identical[key])
        else: identical[key] = i
    groups, face_counts = {}, {}
    for i in range(len(points)): groups.setdefault(root(i), []).append(i)
    for triangle in triangles:
        key = root(int(triangle[0])); face_counts[key] = face_counts.get(key, 0) + 1
    result = []
    for key, ids in groups.items():
        unique = np.unique(points[ids], axis=0)
        if len(unique) == 192 and face_counts.get(key) == 380:
            result.append({'centroid': unique.mean(axis=0), 'span': np.ptp(unique, axis=0),
                           'uniquePoints': 192, 'triangles': 380})
    return result

class ProbeFinished(Exception): pass
rows, settings_record = [], {}
original_encode, original_save = compressor.encode_scene_primitives, exporter.save

def walk(node):
    yield node
    for child in node.children or []: yield from walk(child)

def probe(scenes, settings):
    settings_record.update({k: v for k, v in settings.items() if k.startswith('gltf_draco')})
    nodes = [n for scene in scenes for root in scene.nodes for n in walk(root) if n.mesh is not None]
    assert {n.name for n in nodes} == {o.name for o in selected}
    for node in sorted(nodes, key=lambda n: n.name):
        assert len(node.mesh.primitives) == 1
        native = node.mesh.primitives[0]
        assert not native.targets
        pos = native.attributes['POSITION']
        assert pos.component_type == 5126 and pos.type == 'VEC3'
        positions = np.frombuffer(pos.buffer_view.data, dtype='<f4').reshape(-1, 3).astype(np.float64)
        assert len(positions) == pos.count and np.isfinite(positions).all()
        minimum, maximum = positions.min(axis=0), positions.max(axis=0)
        native_range = float((maximum - minimum).max())
        # Native full arrays never leave memory; only the range goes to policy.
        command = ['node', args.grid_reader, '--decoder-dir', args.decoder_dir]
        required = json.loads(subprocess.run(command + ['--range', repr(native_range)], check=True,
                                           capture_output=True, timeout=10).stdout)['requiredBits']
        native_tree = tree(positions)
        index_type = {5121: '<u1', 5123: '<u2', 5125: '<u4'}[native.indices.component_type]
        native_triangles = np.frombuffer(native.indices.buffer_view.data, dtype=index_type).reshape(-1, 3)
        native_barrels = barrel_components(positions, native_triangles) if node.name.endswith('OD_green_aged_enamel') else []
        if node.name.endswith('OD_green_aged_enamel'): assert len(native_barrels) == 3
        row = {'node': node.name, 'nativeRangeM': native_range, 'nativeMin': minimum.tolist(),
               'nativeMax': maximum.tolist(), 'requiredBits': required, 'nativePoints': len(positions),
               'nativeIndices': native.indices.count, 'nativeIndicesSHA256': hashlib.sha256(native.indices.buffer_view.data).hexdigest(),
               'nativeAttributes': {name: {'count': attr.count, 'componentType': attr.component_type,
                  'type': attr.type, 'sha256': hashlib.sha256(attr.buffer_view.data).hexdigest()}
                  for name, attr in native.attributes.items()}, 'encodes': []}
        for bits in sorted({14, required, 18}):
            clone = copy.deepcopy(node)
            clone.children = []
            holder = copy.copy(scenes[0]); holder.nodes = [clone]
            local_settings = dict(settings); local_settings['gltf_draco_position_quantization'] = bits
            original_encode([holder], local_settings)
            encoded = clone.mesh.primitives[0]
            ext = encoded.extensions['KHR_draco_mesh_compression']
            raw = ext['bufferView'].data
            decoded, decoded_triangles = decode_positions(raw, ext['attributes']['POSITION'])
            index_count = decoded_triangles.size
            assert index_count == native.indices.count
            assert set(ext['attributes']) == set(native.attributes)
            assert all(encoded.attributes[n].component_type == native.attributes[n].component_type and
                       encoded.attributes[n].type == native.attributes[n].type for n in native.attributes)
            forward = directed_chosen_vertex_distance(decoded, positions, native_tree)
            reverse = directed_chosen_vertex_distance(positions, decoded, tree(decoded))
            span_error = np.abs((decoded.max(axis=0) - decoded.min(axis=0)) - (maximum - minimum))
            result = subprocess.run(command + ['--position-id', str(ext['attributes']['POSITION'])], input=raw,
                                    capture_output=True, check=True, timeout=10)
            grid = json.loads(result.stdout)
            assert grid['bits'] == bits
            barrel_checks = []
            if native_barrels:
                decoded_barrels = barrel_components(decoded, decoded_triangles)
                assert len(decoded_barrels) == len(native_barrels) == 3
                unused = list(decoded_barrels)
                for barrel in native_barrels:
                    index = min(range(len(unused)), key=lambda i: np.linalg.norm(unused[i]['centroid'] - barrel['centroid']))
                    match = unused.pop(index)
                    centroid_error = float(np.linalg.norm(match['centroid'] - barrel['centroid']))
                    # Association only; the adopted acceptance threshold remains 20um.
                    association_limit = 2 * grid['gridStepM']
                    assert centroid_error < association_limit
                    barrel_span_error = np.abs(match['span'] - barrel['span'])
                    barrel_checks.append({'nativeCentroid': barrel['centroid'].tolist(), 'nativeSpan': barrel['span'].tolist(),
                        'decodedSpan': match['span'].tolist(), 'spanErrorM': barrel_span_error.tolist(),
                        'centroidErrorM': centroid_error, 'centroid20umAccepted': centroid_error <= 20e-6,
                        'associationLimitM': association_limit, 'uniquePoints': 192, 'triangles': 380,
                        'span20umAccepted': float(barrel_span_error.max()) <= 20e-6})
            accepted = (max(forward, reverse) <= 20e-6 and float(span_error.max()) <= 20e-6
                        and all(b['span20umAccepted'] and b['centroid20umAccepted'] for b in barrel_checks))
            row['encodes'].append({'requestedBits': bits, 'streamBytes': len(raw), 'grid': grid,
                'decodedPoints': len(decoded), 'decodedIndices': index_count,
                'decodedToNativeChosenVertexMaxM': forward, 'nativeToDecodedChosenVertexMaxM': reverse,
                'spanErrorM': span_error.tolist(), 'finiteVertexAndSpan20umAccepted': accepted,
                'attributeBindings': ext['attributes'], 'barrels': barrel_checks})
            if grid['gridAccepted']:
                assert accepted, (node.name, bits, forward, reverse, span_error)
        rows.append(row)
        print('DOOR_PRECISION_PROBED', node.name, required, flush=True)
    raise ProbeFinished()

def no_write_save(context, settings):
    try:
        return original_save(context, settings)
    except ProbeFinished:
        return {'FINISHED'}

def reject_write(*_args, **_kwargs):
    raise AssertionError('File writing is forbidden in this native precision probe')

compressor.encode_scene_primitives = probe
exporter.save = no_write_save
exporter.__write_file = reject_write
exporter.__create_buffer = reject_write
# Material gathering may otherwise save a temporary PNG before the Draco hook.
# This path is forbidden too; a required image conversion must stop the probe.
encode_image._encode_temp_image = reject_write
bpy.ops.export_scene.gltf(filepath=str(out / 'FORBIDDEN.glb'), export_format='GLB', use_selection=True,
    export_apply=True, export_yup=True, export_tangents=True, export_extras=True, export_animations=False,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=18)
assert len(rows) == 20
assert not (out / 'FORBIDDEN.glb').exists()
assert SHA(source) == SOURCE_SHA
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
assert native_before == {o.name: {'matrix': [list(r) for r in o.matrix_world],
                         'vertices': len(o.data.vertices), 'polygons': len(o.data.polygons),
                         'data_name': o.data.name} for o in selected}
report = {'status': 'PASS_NATIVE_FINITE_DOOR_ENCODER_PROBE_ONLY', 'source': before_source,
          'sourceRole': 'Exact published Textured input of export-va180-cab-candidate.py',
          'blenderVersion': bpy.app.version_string, 'pinnedInstalledCode': pins,
          'scriptSHA256': SHA(__file__), 'gridReaderSHA256': SHA(args.grid_reader),
          'settings': settings_record, 'nativeTriangulation': triangulated, 'doors': rows,
          'sourceFileUnchanged': True, 'nativeModelOrAssetSaved': False, 'temporaryImageEncodingBlocked': True,
          'limits': ['Only selected 20 genuine native door primitives were gathered and encoded in memory',
                     'Finite bidirectional chosen-vertex, whole-mesh span and 12 connected barrel span comparisons; not indexed corner, UV, normal, full topology or continuous surface parity',
                     'Attribute names/types and index counts checked; attribute value transport and face correspondence not certified',
                     'No complete GLB, no material/image finalization, no asset promotion or new LFS, no browser test',
                     'Existing shipped fde04e48 GLB remains failed; native controls and whole-angle Float32 error unproved'],
          'wholeVehicleAcceptance': '16 OPEN'}
(out / 'native-probe.json').write_text(json.dumps(report, indent=2) + '\n')
print('NATIVE_DOOR_PRECISION_PROBE_COMPLETE', len(rows), flush=True)
