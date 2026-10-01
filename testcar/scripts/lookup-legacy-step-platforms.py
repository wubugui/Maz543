#!/usr/bin/env python3
"""Read-only, standard-library GLB lookup of four retained legacy step boxes.

Reads the exact supplied immutable seed and a historical Git blob. Writes only
JSON/text evidence to --out, never to the repository. Does not execute JavaScript,
Three.js, Blender, generation, Git writes or network operations.

Component identity = triangle connectivity after exact-coordinate seam equivalence;
numbering is zero-based, sorted by minimum original referenced vertex index.
Oriented triangle identity admits cyclic vertex rotation, never reversed winding.
"""
import argparse
import collections
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import struct
import subprocess

SEED_SHA256 = '5c5849b68a5fa62e903b46b5554b8eb942495eabb3a12cb26caf24742cd9681c'
SEED_BYTES = 8588120
SOURCE_BLOB = '5fc9408952de9549eb3d513071f6706d6df882aa'
SOURCE_SHA256 = 'bbdc06ed7bee43d6ac2a1f38170b9761e34a0e149a1f7486dd895ee9785aab06'
TYPE_COUNT = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
COMPONENT_FMT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
IDENTITY = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def native(point):
    """Published Blender import convention; proper rotation, determinant +1."""
    return (point[0], -point[2], point[1])


def canonical_triangle(points):
    points = tuple(tuple(p) for p in points)
    require(len(points) == 3, 'Not a triangle')
    return min(points, points[1:] + points[:1], points[2:] + points[:2])


def oriented_signature(triangles):
    """Sort cyclic-canonical triangles; pack little-endian Float64 coordinates."""
    canonical = sorted(canonical_triangle(t) for t in triangles)
    data = b''.join(struct.pack('<9d', *(x for p in t for x in p)) for t in canonical)
    return digest(data)


def load_glb(path):
    raw = path.read_bytes()
    require(len(raw) == SEED_BYTES and digest(raw) == SEED_SHA256, 'Wrong seed bytes/SHA')
    magic, version, size = struct.unpack_from('<4sII', raw)
    require((magic, version, size) == (b'glTF', 2, len(raw)), 'Invalid GLB header')
    chunks = []
    offset = 12
    while offset < len(raw):
        length, kind = struct.unpack_from('<I4s', raw, offset)
        offset += 8
        require(offset + length <= len(raw), 'Chunk outside GLB')
        chunks.append((kind, raw[offset:offset+length]))
        offset += length
    require(offset == len(raw) and [c[0] for c in chunks] == [b'JSON', b'BIN\0'], 'Unexpected GLB layout')
    document = json.loads(chunks[0][1])
    require(len(document['buffers']) == 1 and 'uri' not in document['buffers'][0], 'External or multiple buffers')
    require(document['buffers'][0]['byteLength'] <= len(chunks[1][1]), 'Short BIN chunk')
    return document, chunks[1][1], raw


def decode_accessor(document, binary, index):
    accessor = document['accessors'][index]
    require('sparse' not in accessor and not accessor.get('normalized'), 'Unsupported accessor encoding')
    view = document['bufferViews'][accessor['bufferView']]
    require(view.get('buffer', 0) == 0, 'Unexpected buffer')
    fmt = '<' + COMPONENT_FMT[accessor['componentType']] * TYPE_COUNT[accessor['type']]
    width = struct.calcsize(fmt)
    stride = view.get('byteStride', width)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = offset + max(0, accessor['count'] - 1) * stride + width
    require(stride >= width and end <= view.get('byteOffset', 0) + view['byteLength'], 'Accessor outside view')
    require(end <= len(binary), 'Accessor outside binary')
    return [struct.unpack_from(fmt, binary, offset + i * stride) for i in range(accessor['count'])]


def node_matrix(node):
    if 'matrix' in node:
        require(not any(k in node for k in ('translation', 'rotation', 'scale')), 'Matrix and TRS together')
        return tuple(node['matrix'])
    # This exact input has identity or explicit-matrix direct cab children. Fail
    # closed if a different source adds non-identity TRS instead of guessing.
    require(tuple(node.get('translation', (0, 0, 0))) == (0, 0, 0), 'Unexpected TRS translation')
    require(tuple(node.get('rotation', (0, 0, 0, 1))) == (0, 0, 0, 1), 'Unexpected TRS rotation')
    require(tuple(node.get('scale', (1, 1, 1))) == (1, 1, 1), 'Unexpected TRS scale')
    return IDENTITY


def transform(matrix, point):
    x, y, z = point
    require(tuple(matrix[k] for k in (3, 7, 11, 15)) == (0, 0, 0, 1), 'Non-affine matrix')
    return tuple(matrix[i]*x + matrix[4+i]*y + matrix[8+i]*z + matrix[12+i] for i in range(3))


def exact_components(positions, triangles):
    parent = list(range(len(positions)))
    used = sorted({i for t in triangles for i in t})
    require(all(0 <= i < len(positions) for i in used), 'Bad triangle index')
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def join(a, b):
        a, b = root(a), root(b)
        parent[max(a, b)] = min(a, b)
    first = {}
    for i in used:
        if positions[i] in first:
            join(i, first[positions[i]])
        else:
            first[positions[i]] = i
    for a, b, c in triangles:
        join(a, b)
        join(b, c)
    grouped = collections.defaultdict(list)
    for i in used:
        grouped[root(i)].append(i)
    result = []
    for index, vertices in enumerate(sorted(grouped.values(), key=min)):
        triangle_indices = [i for i, t in enumerate(triangles) if root(t[0]) == root(vertices[0])]
        require(all(root(i) == root(vertices[0]) for k in triangle_indices for i in triangles[k]), 'Split triangle')
        result.append({'component': index, 'vertex_indices': vertices, 'triangle_indices': triangle_indices})
    require(sum(len(c['triangle_indices']) for c in result) == len(triangles), 'Incomplete components')
    return result


def bounds(points):
    return {'min': [min(p[k] for p in points) for k in range(3)],
            'max': [max(p[k] for p in points) for k in range(3)]}


def spans(indices):
    out = []
    for _, group in itertools.groupby(enumerate(indices), lambda iv: iv[1] - iv[0]):
        values = [x[1] for x in group]
        out.append([values[0], values[-1]])
    return out


def source_boxes():
    # Evaluate only the scalar source formula, not geometry-generation code.
    # BoxGeometry initially stores half-extent coordinates as Float32. Its merge
    # applies the translation then writes Float32 again. Record both steps.
    result = []
    for side in (-1, 1):
        for door, start, end in ((0, -5.19, -4.08), (1, -3.99, -2.91)):
            length = end - start
            size = (length - .08, .055, .21)
            center = ((start + end) / 2, 1.23, side * 1.025 + side * .86 / 2)
            half = tuple(f32(v / 2) for v in size)
            corners = {tuple(f32(center[k] + signs[k] * half[k]) for k in range(3))
                       for signs in itertools.product((-1, 1), repeat=3)}
            result.append({'id': f'seed_side_{side:+d}_door_{door}', 'source_side': side,
                           'source_door_index': door, 'source_interval': [start, end],
                           'source_dimensions': size, 'source_center': center,
                           'float32_local_half_extents': half, 'corners': corners})
    return result


def verify_box(points, triangles):
    """Exact topological and outward-orientation checks on eight actual corners."""
    unique = sorted(set(points))
    require(len(unique) == 8 and len(triangles) == 12, 'Not an 8-corner/12-triangle box')
    bb = bounds(unique)
    require(set(unique) == set(itertools.product(*zip(bb['min'], bb['max']))), 'Not all AABB corners')
    face_counts = collections.Counter()
    edge_counts = collections.Counter()
    edge_orientations = collections.Counter()
    for tri in triangles:
        require(len(set(tri)) == 3, 'Degenerate triangle')
        flat = [k for k in range(3) if len({p[k] for p in tri}) == 1]
        require(len(flat) == 1, 'Triangle not on a single box face')
        k = flat[0]
        side = 0 if tri[0][k] == bb['min'][k] else 1
        require(tri[0][k] == bb['min'][k] or tri[0][k] == bb['max'][k], 'Non-boundary face')
        a, b, c = tri
        u, v = [b[j] - a[j] for j in range(3)], [c[j] - a[j] for j in range(3)]
        normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        require(normal[k] * (-1 if side == 0 else 1) > 0, 'Reversed or zero box face')
        face_counts[(k, side)] += 1
        for p, q in ((a, b), (b, c), (c, a)):
            edge = tuple(sorted((p, q)))
            edge_counts[edge] += 1
            edge_orientations[edge] += 1 if p < q else -1
    require(len(face_counts) == 6 and all(v == 2 for v in face_counts.values()), 'Incomplete six box faces')
    require(len(edge_counts) == 18 and all(v == 2 for v in edge_counts.values()), 'Box edges not manifold')
    require(all(v == 0 for v in edge_orientations.values()), 'Adjacent winding mismatch')
    return {'unique_corners': 8, 'triangles': 12, 'faces': 6, 'triangles_per_face': 2,
            'unique_triangulated_edges': 18, 'closed_two_incident_edges': True,
            'outward_winding_all_triangles': True}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    require(out != repo and repo not in out.parents, 'Evidence output must be outside repository')
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
    source = subprocess.check_output(['git', '-C', str(repo), 'show', SOURCE_BLOB], env=env)
    require(hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest() == SOURCE_BLOB, 'Wrong Git blob')
    require(digest(source) == SOURCE_SHA256, 'Wrong generator source SHA')
    source_text = source.decode('utf-8')
    require('box(cab, [length - .08, .055, .21], [(start + end) / 2, 1.23, outer], m.dark);' in source_text, 'Missing source formula')
    seed_path = repo / '.git/lfs/objects' / SEED_SHA256[:2] / SEED_SHA256[2:4] / SEED_SHA256
    document, binary, original = load_glb(seed_path)
    nodes = document['nodes']
    cab_ids = [i for i, n in enumerate(nodes) if n.get('name') == 'cab']
    require(len(cab_ids) == 1, 'Ambiguous cab')
    cab_id = cab_ids[0]
    parents = {}
    for i, node in enumerate(nodes):
        for child in node.get('children', []):
            require(child not in parents, 'Multiple node parents')
            parents[child] = i
    ancestor = cab_id
    ancestry = []
    while True:
        require(node_matrix(nodes[ancestor]) == IDENTITY, 'Nonidentity cab ancestor')
        ancestry.append({'node': ancestor, 'name': nodes[ancestor].get('name'), 'transform': 'identity'})
        if ancestor not in parents:
            break
        ancestor = parents[ancestor]
    expected = source_boxes()
    matches = []
    inventory = []
    payloads = []
    for node_id in nodes[cab_id]['children']:
        node = nodes[node_id]
        if 'mesh' not in node:
            continue
        matrix = node_matrix(node)
        mesh = document['meshes'][node['mesh']]
        for primitive_id, primitive in enumerate(mesh['primitives']):
            require(primitive.get('mode', 4) == 4 and not primitive.get('extensions'), 'Unsupported primitive')
            pos_accessor = primitive['attributes']['POSITION']
            local = decode_accessor(document, binary, pos_accessor)
            require(all(len(p) == 3 and all(math.isfinite(c) for c in p) for p in local), 'Invalid positions')
            positions = [transform(matrix, p) for p in local]
            if 'indices' in primitive:
                indices = [v[0] for v in decode_accessor(document, binary, primitive['indices'])]
            else:
                indices = list(range(len(local)))
            require(len(indices) % 3 == 0, 'Invalid triangle index count')
            triangles = [tuple(indices[i:i+3]) for i in range(0, len(indices), 3)]
            mat = primitive.get('material')
            common = {'node': node_id, 'node_name': node.get('name'), 'mesh': node['mesh'],
                      'primitive': primitive_id, 'material': mat,
                      'material_name': document['materials'][mat].get('name') if mat is not None else None,
                      'extras': node.get('extras', {}), 'position_accessor': pos_accessor,
                      'index_accessor': primitive.get('indices'), 'node_transform_identity': matrix == IDENTITY}
            components = exact_components(local, triangles)
            batch_record = dict(common, total_position_count=len(local), total_triangle_count=len(triangles), components=[])
            for component in components:
                vertex_ids, triangle_ids = component['vertex_indices'], component['triangle_indices']
                points = [positions[i] for i in vertex_ids]
                record = {'component': component['component'], 'vertex_count': len(vertex_ids),
                          'unique_position_count': len(set(points)), 'triangle_count': len(triangle_ids),
                          'vertex_index_spans_inclusive': spans(vertex_ids),
                          'triangle_index_spans_inclusive': spans(triangle_ids),
                          'seed_bounds': bounds(points), 'native_bounds': bounds([native(p) for p in points])}
                batch_record['components'].append(record)
                for target in expected:
                    if set(points) != target['corners']:
                        continue
                    oriented = [tuple(positions[i] for i in triangles[j]) for j in triangle_ids]
                    checks = verify_box(points, oriented)
                    native_triangles = [tuple(native(p) for p in t) for t in oriented]
                    match = dict(common, **record,
                                 target={k: v for k, v in target.items() if k != 'corners'},
                                 exact_source_float32_corner_match=True,
                                 source_match_method='Exact equality to 8 corners from recorded source box dimensions/translation with Float32 storage before and after translation',
                                 actual_geometry_checks=checks,
                                 seed_oriented_triangle_sha256=oriented_signature(oriented),
                                 native_oriented_triangle_sha256=oriented_signature(native_triangles),
                                 triangle_payload_file='box-triangles.json',
                                 triangle_payload_id=target['id'])
                    matches.append(match)
                    payloads.append({'id': target['id'], 'node': node_id, 'mesh': node['mesh'],
                                     'primitive': primitive_id, 'component': component['component'],
                                     'vertices': [{'primitive_vertex_index': i, 'seed': positions[i], 'native': native(positions[i])} for i in vertex_ids],
                                     'triangles': [{'primitive_triangle_index': j,
                                                    'primitive_vertex_indices': triangles[j],
                                                    'seed_oriented_corners': oriented[k],
                                                    'native_oriented_corners': native_triangles[k]}
                                                   for k, j in enumerate(triangle_ids)]})
            inventory.append(batch_record)
    require(len(matches) == 4 and collections.Counter(m['target']['id'] for m in matches) == collections.Counter(t['id'] for t in expected), 'Expected exactly one match for each of 4 boxes')
    # Independent fingerprint controls: cyclic rotations preserve, winding and
    # positional corruption reject. These test matching, not native retention.
    fixture = [tuple(tuple(p) for p in t['native_oriented_corners']) for t in payloads[0]['triangles']]
    baseline = oriented_signature(fixture)
    require(oriented_signature([t[1:] + t[:1] for t in fixture]) == baseline, 'Cyclic control failed')
    changed = list(fixture); changed[0] = (changed[0][0], changed[0][2], changed[0][1])
    require(oriented_signature(changed) != baseline, 'Winding control falsely accepted')
    changed = list(fixture); t = list(changed[0]); p = list(t[0]); p[0] += .0001; t[0] = tuple(p); changed[0] = tuple(t)
    require(oriented_signature(changed) != baseline, 'Position control falsely accepted')
    require(seed_path.read_bytes() == original, 'Seed changed during lookup')
    write_json(out / 'direct-cab-components.json', inventory)
    write_json(out / 'box-triangles.json', payloads)
    result = {'status': 'FOUR_EXACT_SEED_BOX_COMPONENTS_IDENTIFIED_NATIVE_RETENTION_NOT_TESTED',
              'seed': {'sha256': SEED_SHA256, 'bytes': SEED_BYTES, 'unchanged_after_read': True},
              'source': {'git_blob': SOURCE_BLOB, 'sha256': SOURCE_SHA256,
                         'path': 'testcar/work/compiled/maz543.mjs',
                         'box_creation_line': 173, 'support_link_lines': [174, 175],
                         'fixed_batch_merge_lines': [503, 530]},
              'coordinate_convention': {'seed': 'X longitudinal, Y up, Z lateral', 'native': '(seed.x, -seed.z, seed.y)',
                                        'winding_preserved': True, 'determinant': 1},
              'cab_ancestry': ancestry,
              'index_convention': 'All node/mesh/primitive/accessor/component/vertex/triangle indices are zero-based; ranges inclusive. Components sorted by minimum used primitive vertex index after exact-coordinate seam equivalence.',
              'exact_identity_boundary': 'Exact seed component geometry, source-derived Float32 corner equality and outward closed-box topology. A match in a native master must still be independently demonstrated using all 12 oriented triangles; object names or AABB alone are insufficient.',
              'semantic_boundary': 'The fixed under-door step-platform interpretation follows the source placement beside support links; it is not an explicit component name or a manufacturer hardware, dimension, batch or material certification. dark is a rendering material name.',
              'signature_encoding': 'Cyclic-canonicalize each oriented triangle lexicographically, sort triangle records lexicographically, then SHA256 concatenated struct.pack(<9d, 9 coordinates) records. Reversal is not admitted.',
              'controls': {'cyclic_rotation_accepted': True, 'single_reversed_triangle_rejected': True, 'single_100um_corner_change_rejected': True},
              'matches': matches,
              'artifacts': [{'file': name, 'sha256': digest((out / name).read_bytes()), 'bytes': (out / name).stat().st_size}
                            for name in ('direct-cab-components.json', 'box-triangles.json')],
              'script_sha256': digest(Path(__file__).read_bytes())}
    write_json(out / 'result.json', result)
    print(json.dumps({'status': result['status'], 'matches': [
        {k: m[k] for k in ('node_name', 'component', 'vertex_count', 'triangle_count', 'vertex_index_spans_inclusive', 'triangle_index_spans_inclusive', 'native_bounds')} for m in matches]}, indent=2))


if __name__ == '__main__':
    main()
