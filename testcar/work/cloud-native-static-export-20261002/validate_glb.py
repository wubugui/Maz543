"""Read-only validation of one official, static, uncompressed MAZ glTF export.

Reference bounds/attributes use glTF axes. Signatures prove oriented triangle
corner transport, not vertex connectivity/storage, shader or render equivalence.
No bpy dependency, CLI, source mutation, or output writes. Caller saves the report.
"""
import hashlib
import io
import json
import struct
from collections import Counter
from pathlib import Path

import numpy as np


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def oriented_signature(attributes, indices):
    """Hash full float32 corner records; ignore only cyclic rotation/storage order.

    Each result is SHA256(concatenated sorted 32-byte triangle SHA256 digests).
    Each triangle digest hashes the lexicographically least cyclic rotation of
    its three little-endian float32 corner byte records. Multiplicity is retained.
    """
    names = sorted(attributes)
    _need('POSITION' in names, 'Missing POSITION')
    arrays = {k: np.asarray(attributes[k], dtype='<f4') for k in names}
    count = len(arrays['POSITION'])
    for k, a in arrays.items():
        _need(a.ndim == 2 and len(a) == count and a.shape[1] > 0, 'Attribute shape: ' + k)
        _need(np.isfinite(a).all(), 'Nonfinite attribute: ' + k)
    ix = np.asarray(indices)
    _need(ix.dtype.kind in 'iu' and ix.ndim in (1, 2) and ix.size % 3 == 0, 'Invalid triangle indices')
    _need(ix.ndim == 1 or ix.shape[1] == 3, 'Invalid triangle index width')
    ix = ix.reshape(-1, 3)
    _need(not ix.size or (int(ix.min()) >= 0 and int(ix.max()) < count), 'Index outside attribute')
    signatures = {}
    for label, selected in [('all', names)] + [(k, [k]) for k in names]:
        vertices = np.ascontiguousarray(np.concatenate([arrays[k] for k in selected], axis=1), dtype='<f4')
        width = vertices.shape[1] * 4
        digests = np.empty(len(ix), dtype='S32')
        for start in range(0, len(ix), 4096):
            rows = vertices[ix[start:start + 4096]].reshape(-1, 3 * vertices.shape[1])
            for j, row in enumerate(rows):
                b = row.tobytes()
                b = min(b, b[width:] + b[:width], b[2 * width:] + b[:2 * width])
                digests[start + j] = hashlib.sha256(b).digest()
        digests.sort()
        signatures[label] = _sha(digests.tobytes())
    return {'triangles': len(ix), 'attributes': names, 'signatures': signatures}


class _GLB:
    def __init__(self, data):
        self.data = data
        _need(len(data) >= 28, 'Truncated GLB')
        magic, version, size = struct.unpack_from('<III', data)
        _need(magic == 0x46546C67 and version == 2 and size == len(data), 'Invalid GLB header')
        chunks, offset = [], 12
        while offset < size:
            _need(offset + 8 <= size, 'Truncated chunk header')
            length, kind = struct.unpack_from('<II', data, offset)
            offset += 8
            _need(length % 4 == 0 and offset + length <= size, 'Invalid chunk extent/alignment')
            chunks.append((kind, memoryview(data)[offset:offset + length]))
            offset += length
        _need([k for k, _ in chunks] == [0x4E4F534A, 0x004E4942], 'Expected exactly JSON then BIN chunks')
        self.j = json.loads(bytes(chunks[0][1]).decode('utf8'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON constant: ' + x)))
        self.bin = chunks[1][1]
        _need(self.j.get('asset', {}).get('version') == '2.0', 'Not glTF 2.0')
        buffers = self.j.get('buffers', [])
        _need(len(buffers) == 1 and 'uri' not in buffers[0], 'Expected one embedded buffer')
        self.length = buffers[0]['byteLength']
        _need(type(self.length) is int and 0 <= self.length <= len(self.bin) <= self.length + 3, 'Invalid buffer length')
        _need(not any(self.bin[self.length:]), 'Nonzero BIN padding')
        for i in range(len(self.j.get('bufferViews', []))):
            self.view(i)

    def item(self, kind, index):
        entries = self.j.get(kind, [])
        _need(type(index) is int and 0 <= index < len(entries), 'Invalid ' + kind + ' index')
        return entries[index]

    def view(self, index):
        v = self.item('bufferViews', index)
        start, length = v.get('byteOffset', 0), v['byteLength']
        _need(v.get('buffer') == 0 and type(start) is int and type(length) is int and start >= 0 and length > 0 and start + length <= self.length, 'Invalid bufferView extent')
        return v, start, length

    def accessor(self, index):
        a = self.item('accessors', index)
        _need('sparse' not in a and 'bufferView' in a, 'Sparse/bufferless accessor outside static export contract')
        types = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
        widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
        _need(a.get('componentType') in types and a.get('type') in widths, 'Unsupported accessor type')
        dtype, width, count = np.dtype(types[a['componentType']]), widths[a['type']], a['count']
        v, base, length = self.view(a['bufferView'])
        offset, packed = a.get('byteOffset', 0), dtype.itemsize * width
        stride = v.get('byteStride', packed)
        _need(type(count) is int and count > 0 and type(offset) is int and offset >= 0, 'Invalid accessor count/offset')
        _need(type(stride) is int and stride >= packed and stride % dtype.itemsize == 0, 'Invalid accessor stride')
        _need('byteStride' not in v or (4 <= stride <= 252 and stride % 4 == 0), 'Invalid interleaved stride')
        _need((base + offset) % dtype.itemsize == 0 and offset + (count - 1) * stride + packed <= length, 'Accessor outside bufferView/misaligned')
        result = np.ndarray((count, width), dtype=dtype, buffer=self.bin, offset=base + offset, strides=(stride, dtype.itemsize))
        _need(np.isfinite(result).all(), 'Nonfinite accessor values')
        return result, a


def _local(node):
    if 'matrix' in node:
        _need(not any(k in node for k in ('translation', 'rotation', 'scale')), 'Matrix mixed with TRS')
        m = np.asarray(node['matrix'], dtype=np.float64)
        _need(m.shape == (16,), 'Invalid node matrix')
        m = m.reshape(4, 4).T
    else:
        t, q, s = (np.asarray(node.get(k, d), dtype=np.float64) for k, d in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])])
        _need(t.shape == (3,) and q.shape == (4,) and s.shape == (3,), 'Invalid node TRS')
        _need(abs(float(q @ q) - 1) <= 1e-5, 'Nonunit node quaternion')
        x, y, z, w = q
        r = np.array([[1 - 2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        m = np.eye(4); m[:3, :3] = r @ np.diag(s); m[:3, 3] = t
    _need(np.isfinite(m).all() and np.array_equal(m[3], [0, 0, 0, 1]), 'Invalid affine matrix')
    return m


def _scene(asset):
    j, nodes = asset.j, asset.j.get('nodes', [])
    _need(len(j.get('scenes', [])) == 1 and j.get('scene', 0) == 0, 'Expected one scene')
    roots = j['scenes'][0].get('nodes', [])
    parents, worlds, locals_, order = {}, {}, {}, []
    def visit(i, parent, world):
        node = asset.item('nodes', i)
        _need(i not in parents, 'Cycle, repeated root, or multiple node parents')
        parents[i] = parent; locals_[i] = _local(node); worlds[i] = world @ locals_[i]; order.append(i)
        _need(np.isfinite(worlds[i]).all(), 'Nonfinite accumulated world matrix')
        for child in node.get('children', []):
            visit(child, i, worlds[i])
    for i in roots:
        visit(i, None, np.eye(4))
    _need(len(order) == len(nodes), 'Unreachable nodes in GLB')
    return parents, worlds, locals_, order


def validate(path, references, graph, inventory, limits):
    """Return fidelity failures as issues; malformed/unsupported structure raises.

    limits optionally supplies expected_nodes (default2675), matrix_tolerance
    (default1e-5), world_position_tolerance_m (default2e-5), decode_png (defaultTrue).
    MESH/CURVE/FONT without geometry must appear in references.known_empty_nodes.
    """
    asset = _GLB(Path(path).read_bytes()); j = asset.j
    parents, worlds, locals_, order = _scene(asset)
    issues, rows, mesh_cache, used_meshes = [], [], {}, set()
    def check(ok, text):
        if not ok: issues.append(text)
    limits = limits if isinstance(limits, dict) else {'scope_limits': limits}
    mt, pt = limits.get('matrix_tolerance', 1e-5), limits.get('world_position_tolerance_m', 2e-5)
    expected = set(graph['full_union_ancestry_closed']); nodes = j.get('nodes', [])
    names = [n.get('name') for n in nodes]
    check(len(nodes) == limits.get('expected_nodes', 2675), 'Node count differs from required scope')
    _need(all(isinstance(n, str) for n in names) and len(names) == len(set(names)), 'Missing/duplicate node names')
    check(set(names) == expected, 'Node identity mismatch: ' + json.dumps({'missing': sorted(expected-set(names)), 'extra': sorted(set(names)-expected)}))
    check(set(references['nodes']) == expected, 'Reference node inventory differs')
    check(not j.get('animations') and not j.get('skins'), 'Animation/skin data present')
    forbidden = {'KHR_draco_mesh_compression', 'KHR_mesh_quantization', 'EXT_mesh_gpu_instancing', 'EXT_meshopt_compression'}
    def scan(value):
        if isinstance(value, dict):
            check(not ('uri' in value), 'External/data URI present')
            check(not forbidden.intersection(value.get('extensions', {})), 'Forbidden encoding/instance extension present')
            for v in value.values(): scan(v)
        elif isinstance(value, list):
            for v in value: scan(v)
    scan(j)
    check(not forbidden.intersection(j.get('extensionsUsed', []) + j.get('extensionsRequired', [])), 'Forbidden extension declaration')
    C = np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]], dtype=np.float64)
    counts = {'unique_mesh_triangles': 0, 'node_instanced_triangles': 0, 'decoded_primitives': 0}
    unknown = set(); max_world = max_local = max_disp = 0.0
    def part_key(part):
        return json.dumps([part['material_name'], part['signature']], sort_keys=True, separators=(',', ':'))
    def decode_mesh(index):
        if index in mesh_cache: return mesh_cache[index]
        mesh = asset.item('meshes', index); parts, positions = [], []
        check(not mesh.get('weights'), 'Mesh morph weights present: ' + str(index))
        for primitive in mesh.get('primitives', []):
            check(not primitive.get('targets'), 'Morph targets present: ' + str(index))
            _need(primitive.get('mode', 4) == 4 and 'indices' in primitive, 'Expected indexed triangles')
            attrs = {}
            for semantic, ai in primitive.get('attributes', {}).items():
                a, meta = asset.accessor(ai)
                expected_width = 3 if semantic in ('POSITION', 'NORMAL') else 2 if semantic.startswith('TEXCOORD_') and semantic[9:].isdigit() else None
                if expected_width is None: unknown.add(semantic)
                else:
                    _need(meta['componentType'] == 5126 and not meta.get('normalized', False), 'Non-float32 vertex accessor')
                    _need(a.shape[1] == expected_width, 'Invalid semantic width: ' + semantic)
                attrs[semantic] = a
                for bound, actual in [('min', a.min(axis=0)), ('max', a.max(axis=0))]:
                    if bound in meta:
                        value = np.asarray(meta[bound], dtype=np.float64)
                        check(value.shape == actual.shape and np.array_equal(value, actual.astype(np.float64)), 'Accessor ' + str(ai) + ' ' + bound + ' differs from payload')
                if semantic == 'POSITION': check('min' in meta and 'max' in meta, 'POSITION missing bounds')
            _need('POSITION' in attrs, 'Primitive missing POSITION')
            check('NORMAL' in attrs, 'Primitive missing NORMAL')
            ix, meta = asset.accessor(primitive['indices'])
            _need(meta['type'] == 'SCALAR' and meta['componentType'] in (5121,5123,5125) and not meta.get('normalized', False), 'Invalid index accessor')
            signature = oriented_signature(attrs, ix.reshape(-1))
            material = asset.item('materials', primitive['material']) if 'material' in primitive else None
            if material:
                check(material.get('name') in references.get('materials', {}), 'Unknown source material: ' + str(material.get('name')))
                def texture_refs(value):
                    if not isinstance(value, dict): return
                    for key, item in value.items():
                        if key.endswith('Texture') and isinstance(item, dict) and 'index' in item:
                            asset.item('textures', item['index'])
                            uv = item.get('extensions', {}).get('KHR_texture_transform', {}).get('texCoord', item.get('texCoord', 0))
                            _need(type(uv) is int and uv >= 0, 'Invalid material texCoord')
                            check('TEXCOORD_' + str(uv) in attrs, 'Material refers to absent UV set')
                        texture_refs(item)
                texture_refs(material)
            parts.append({'material_name': material.get('name') if material else None, 'signature': signature})
            positions.append(attrs['POSITION']); counts['unique_mesh_triangles'] += signature['triangles']; counts['decoded_primitives'] += 1
        _need(parts, 'Mesh has no triangle primitives')
        bounds = [np.minimum.reduce([p.min(axis=0) for p in positions]).tolist(), np.maximum.reduce([p.max(axis=0) for p in positions]).tolist()]
        mesh_cache[index] = (parts, positions, bounds)
        return mesh_cache[index]
    for i in order:
        node, name = nodes[i], names[i]
        check('skin' not in node and not node.get('weights'), 'Node skin/morph weights: ' + name)
        if name not in expected: continue
        expected_parent = inventory[name]['parent']; expected_parent = expected_parent.get('name') if isinstance(expected_parent, dict) else expected_parent
        parent_name = names[parents[i]] if parents[i] is not None else None
        check(parent_name == expected_parent, 'Parent differs: ' + name)
        rec = graph['records'][name]
        native_world = C @ np.asarray(rec['matrix_world_rows'], dtype=np.float64) @ C.T
        native_local = C @ np.asarray(rec['matrix_local_rows'], dtype=np.float64) @ C.T
        _need(native_world.shape == (4,4) and native_local.shape == (4,4) and np.isfinite(native_world).all() and np.isfinite(native_local).all(), 'Invalid native matrices')
        le, we = float(np.max(np.abs(locals_[i]-native_local))), float(np.max(np.abs(worlds[i]-native_world)))
        max_local, max_world = max(max_local, le), max(max_world, we)
        check(le <= mt and we <= mt, 'Matrix tolerance exceeded: ' + name)
        ref_id = references['nodes'].get(name); displacement = 0.0
        check(('mesh' in node) == (ref_id is not None), 'Mesh presence differs: ' + name)
        if ref_id is None:
            check(inventory[name]['type'] == 'EMPTY' or name in references.get('known_empty_nodes', []), 'Unqualified empty geometry: ' + name)
        if 'mesh' in node:
            used_meshes.add(node['mesh']); parts, positions, bounds = decode_mesh(node['mesh'])
            counts['node_instanced_triangles'] += sum(p['signature']['triangles'] for p in parts)
            if ref_id is not None:
                ref = references['meshes'].get(ref_id)
                check(ref is not None, 'Missing reference mesh: ' + str(ref_id))
                if ref is not None:
                    check(Counter(map(part_key, parts)) == Counter(map(part_key, ref['parts'])), 'Triangle attributes/material buckets differ: ' + name)
                    check(np.array_equal(np.asarray(bounds), np.asarray(ref['bounds'])), 'Native local bounds differ: ' + name)
            for p in positions:
                for start in range(0, len(p), 65536):
                    v = p[start:start+65536].astype(np.float64)
                    actual_points = v @ worlds[i][:3,:3].T + worlds[i][:3,3]
                    native_points = v @ native_world[:3,:3].T + native_world[:3,3]
                    _need(np.isfinite(actual_points).all() and np.isfinite(native_points).all(), 'Nonfinite world positions')
                    delta = actual_points - native_points
                    displacement = max(displacement, float(np.max(np.linalg.norm(delta, axis=1))))
            check(displacement <= pt, 'World position tolerance exceeded: ' + name)
        max_disp = max(max_disp, displacement)
        rows.append({'name': name, 'reference_mesh': ref_id, 'glb_mesh': node.get('mesh'), 'local_matrix_max_error': le, 'world_matrix_max_error': we, 'max_world_displacement_m': displacement})
    check(not unknown, 'Unexpected attributes: ' + ', '.join(sorted(unknown)))
    check(used_meshes == set(range(len(j.get('meshes', [])))), 'Unreferenced or missing GLB meshes')
    check(set(references['meshes']) == {v for v in references['nodes'].values() if v is not None}, 'Unreferenced native mesh records')
    images = []
    for i, im in enumerate(j.get('images', [])):
        _need('bufferView' in im and im.get('mimeType') in ('image/png','image/jpeg','image/webp'), 'Invalid embedded image')
        _, start, length = asset.view(im['bufferView']); b = bytes(asset.bin[start:start+length])
        valid_magic = b.startswith(b'\x89PNG\r\n\x1a\n') if im['mimeType'] == 'image/png' else b.startswith(b'\xff\xd8\xff') if im['mimeType'] == 'image/jpeg' else b.startswith(b'RIFF') and b[8:12] == b'WEBP'
        _need(valid_magic, 'Image bytes disagree with MIME type')
        row = {'index': i, 'name': im.get('name'), 'mime_type': im['mimeType'], 'bytes': len(b), 'sha256': _sha(b)}
        if im['mimeType'] == 'image/png' and limits.get('decode_png', True):
            try:
                from PIL import Image
                with Image.open(io.BytesIO(b)) as picture:
                    picture.load(); rgba = picture.convert('RGBA')
                    row.update(pixel_mode='RGBA8', dimensions=list(rgba.size), decoded_pixels_sha256=_sha(rgba.tobytes()))
            except ImportError: row['pixel_decode'] = 'Pillow unavailable'
        images.append(row)
    for tex in j.get('textures', []):
        if 'source' in tex: asset.item('images', tex['source'])
        if 'sampler' in tex: asset.item('samplers', tex['sampler'])
    return {'status': 'PASS_STATIC_NATIVE_TRANSPORT' if not issues else 'FAIL_STATIC_NATIVE_TRANSPORT', 'issues': issues, 'glb_sha256': _sha(asset.data), 'glb_bytes': len(asset.data), 'nodes': len(nodes), 'unique_meshes': len(used_meshes), **counts, 'max_local_matrix_error': max_local, 'max_world_matrix_error': max_world, 'max_world_displacement_m': max_disp, 'matrix_tolerance': mt, 'world_position_tolerance_m': pt, 'unknown_attributes': sorted(unknown), 'node_results': rows, 'mesh_results': {str(k): {'parts': v[0], 'bounds': v[2]} for k,v in mesh_cache.items()}, 'actual_materials': j.get('materials', []), 'actual_textures': j.get('textures', []), 'actual_samplers': j.get('samplers', []), 'embedded_images': images, 'decoding': 'Actual uncompressed raw GLB accessors decoded; Draco intentionally absent', 'limits': ['Oriented float32 triangle-corner transport with material assignment; no vertex storage/connectivity identity claim', 'World displacement uses actual float32 local positions and native versus GLB matrices; local geometry equality is checked separately', 'No shader, pixel-render, camera, animation, physical assembly, or whole-vehicle acceptance claim'], 'requested_limits': limits}


def test_controls():
    """Pure in-memory controls only; never constructs Blender/vehicle meshes."""
    a = {'POSITION': np.array([[0,0,0],[1,0,0],[0,1,0]], dtype='<f4'), 'NORMAL': np.tile([0,0,1], (3,1)), 'TEXCOORD_0': np.array([[0,0],[1,0],[0,1]], dtype='<f4')}
    baseline = oriented_signature(a, np.array([0,1,2], dtype=np.uint32)); checks = []
    assert baseline == oriented_signature(a, np.array([1,2,0], dtype=np.uint16)); checks.append('cyclic rotation accepted')
    assert baseline != oriented_signature(a, np.array([0,2,1], dtype=np.uint32)); checks.append('reversed winding rejected')
    assert baseline != oriented_signature(a, np.array([0,1,2,0,1,2], dtype=np.uint32)); checks.append('triangle multiplicity retained')
    assert oriented_signature(a, np.array([0,1,2,0,2,1], dtype=np.uint32)) == oriented_signature(a, np.array([0,2,1,0,1,2], dtype=np.uint32)); checks.append('triangle storage order ignored')
    reordered = {k: np.asarray(v)[[2,0,1]] for k,v in a.items()}
    assert baseline == oriented_signature(reordered, np.array([1,2,0], dtype=np.uint32)); checks.append('vertex storage order ignored')
    rebound = dict(a); rebound['TEXCOORD_0'] = a['TEXCOORD_0'][[1,2,0]]
    changed = oriented_signature(rebound, np.array([0,1,2], dtype=np.uint32))
    assert changed['signatures']['TEXCOORD_0'] == baseline['signatures']['TEXCOORD_0'] and changed['signatures']['all'] != baseline['signatures']['all']; checks.append('joint position/UV binding retained')
    for name in a:
        b = {k: np.array(v, dtype='<f4', copy=True) for k,v in a.items()}; b[name][0,0] += .125
        assert oriented_signature(b, np.array([0,1,2], dtype=np.uint32))['signatures']['all'] != baseline['signatures']['all']; checks.append(name + ' corruption rejected')
    b = {k: np.array(v, dtype='<f4', copy=True) for k,v in a.items()}; b['POSITION'][0,0] = -0.0
    assert oriented_signature(b, np.array([0,1,2], dtype=np.uint32)) != baseline; checks.append('negative zero retained')
    payload = a['POSITION'].tobytes(); doc = {'asset': {'version':'2.0'}, 'buffers':[{'byteLength':len(payload)}], 'bufferViews':[{'buffer':0,'byteLength':len(payload)}], 'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'}], 'scenes':[{'nodes':[0]}], 'nodes':[{'name':'fixture'}]}
    def packed(d):
        jb = json.dumps(d).encode(); jb += b' ' * (-len(jb)%4)
        return struct.pack('<III',0x46546C67,2,28+len(jb)+len(payload)) + struct.pack('<II',len(jb),0x4E4F534A) + jb + struct.pack('<II',len(payload),0x004E4942) + payload
    g = _GLB(packed(doc)); assert np.array_equal(g.accessor(0)[0], a['POSITION']); _scene(g); checks.append('actual embedded raw accessor decoded')
    bad = json.loads(json.dumps(doc)); bad['accessors'][0]['count'] = 4
    cases = [('accessor overrun', lambda: _GLB(packed(bad)).accessor(0)), ('bad GLB magic', lambda: _GLB(b'BAD!' + packed(doc)[4:])), ('out-of-range triangle index', lambda: oriented_signature(a, np.array([0,1,3], dtype=np.uint32)))]
    cyclic = json.loads(json.dumps(doc)); cyclic['nodes'][0]['children'] = [0]
    cases.append(('node cycle', lambda: _scene(_GLB(packed(cyclic)))))
    nonfinite = {k: np.array(v, dtype='<f4', copy=True) for k,v in a.items()}; nonfinite['NORMAL'][0,0] = np.nan
    cases.append(('nonfinite normal', lambda: oriented_signature(nonfinite, np.array([0,1,2], dtype=np.uint32))))
    for name, fn in cases:
        try: fn()
        except ValueError: checks.append(name + ' rejected')
        else: raise AssertionError(name + ' accepted')
    return {'passed': True, 'checks': checks}
