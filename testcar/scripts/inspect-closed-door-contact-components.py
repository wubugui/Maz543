"""Read-only provenance localization of the six retained closed-door contacts.

Raw indexed connectivity and exact-coordinate seam grouping are both reported.
Neither is a physical-part count. No native welding, separation, hiding or save.
"""
import bpy, hashlib, json, struct
from collections import Counter
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
SEED = ROOT / 'work/mechanical-seed.glb'
TRIAL = ROOT / 'work/cloud-door-barrel-motion-trial-20261001/trial-report.json'
OUT = ROOT / 'work/cloud-closed-door-contact-components-20261001'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
SEED_SHA = '5c5849b68a5fa62e903b46b5554b8eb942495eabb3a12cb26caf24742cd9681c'
assert sha(SOURCE) == EXPECTED and sha(SEED) == SEED_SHA
assert bpy.app.version[:3] == (4, 5, 13)
trial = json.loads(TRIAL.read_text())
assert trial['source_sha256'] == trial['source_sha256_after'] == EXPECTED
expected_contacts = [c for d in trial['doors'] for p in d['poses'] if p['degrees'] == 0 for c in p['trial_surface_overlap_candidates']]
assert len(expected_contacts) == 6

def groups(xyz, tri, seam=False):
    parents = list(range(len(xyz)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def join(a, b):
        a, b = root(int(a)), root(int(b))
        if a != b:
            parents[max(a,b)] = min(a,b)
    for t in tri:
        join(t[0], t[1]); join(t[1], t[2])
    if seam:
        first = {}
        for i, p in enumerate(xyz):
            key = tuple(p)
            if key in first:
                join(i, first[key])
            else:
                first[key] = i
    by_root = {}
    for i in range(len(xyz)):
        by_root.setdefault(root(i), []).append(i)
    result = []
    for ids in sorted(by_root.values(), key=min):
        component = len(result)
        result.append({'component': component, 'vertices': ids, 'triangles': [],
                       'bounds_world': [xyz[ids].min(0).tolist(), xyz[ids].max(0).tolist()]})
    index = {v:r['component'] for r in result for v in r['vertices']}
    for i,t in enumerate(tri):
        assert len({index[int(v)] for v in t}) == 1
        result[index[int(t[0])]]['triangles'].append(i)
    return result, index

def canon(t):
    corners = [tuple(float(v) for v in p) for p in t]
    return min(tuple(corners[i:]+corners[:i]) for i in range(3))

# Decode the existing uncompressed seed exactly; never regenerate it from newer
# authoring code. Reject any unexpected transforms, compression or accessor type.
seed_bytes = SEED.read_bytes()
magic, version, length = struct.unpack_from('<4sII', seed_bytes)
assert magic == b'glTF' and version == 2 and length == len(seed_bytes)
jslen, tag = struct.unpack_from('<II', seed_bytes, 12)
assert tag == 0x4e4f534a
gltf = json.loads(seed_bytes[20:20+jslen])
bin_offset = 20+jslen
binlen, tag = struct.unpack_from('<II', seed_bytes, bin_offset)
assert tag == 0x004e4942 and bin_offset+8+binlen == len(seed_bytes)
binary = memoryview(seed_bytes)[bin_offset+8:]
def accessor(index, kind):
    a = gltf['accessors'][index]; view = gltf['bufferViews'][a['bufferView']]
    assert not a.get('sparse') and not a.get('normalized') and view.get('buffer',0) == 0
    assert a['type'] == kind
    dtype = {5126:'<f4', 5123:'<u2', 5125:'<u4'}[a['componentType']]
    width = 3 if kind == 'VEC3' else 1
    itemsize = np.dtype(dtype).itemsize
    assert view.get('byteStride', itemsize*width) == itemsize*width
    begin = view.get('byteOffset',0)+a.get('byteOffset',0)
    return np.frombuffer(binary, dtype=dtype, count=a['count']*width, offset=begin).reshape(-1,width).copy()
node_index = next(i for i,n in enumerate(gltf['nodes']) if n.get('name') == 'cab_0063')
node = gltf['nodes'][node_index]
ancestry = [node_index]
while True:
    ps = [i for i,n in enumerate(gltf['nodes']) if ancestry[-1] in n.get('children',[])]
    assert len(ps) <= 1
    if not ps: break
    ancestry.append(ps[0])
for i in ancestry:
    assert not any(k in gltf['nodes'][i] for k in ['matrix','translation','rotation','scale'])
primitives = gltf['meshes'][node['mesh']]['primitives']; assert len(primitives) == 1
primitive = primitives[0]; assert primitive.get('mode',4) == 4 and not primitive.get('extensions')
seed_xyz_gltf = accessor(primitive['attributes']['POSITION'],'VEC3').astype(np.float64)
seed_xyz = seed_xyz_gltf[:,[0,2,1]] * np.array([1.,-1.,1.])
seed_tri = accessor(primitive['indices'],'SCALAR').reshape(-1,3)
seed_groups, seed_index = groups(seed_xyz, seed_tri, True)
seed_faces = Counter(canon(seed_xyz[t]) for t in seed_tri)
assert len(seed_groups) == node['extras']['fixedDetailCount'] == 17

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def mesh(o, evaluated=True):
    e = o.evaluated_get(dg) if evaluated else o
    m = e.to_mesh() if evaluated else o.data
    try:
        xyz = np.asarray([tuple(v.co) for v in m.vertices], dtype=np.float64)
        w = np.asarray(e.matrix_world, dtype=np.float64)
        xyz = xyz @ w[:3,:3].T + w[:3,3]
        m.calc_loop_triangles()
        tri = np.asarray([tuple(t.vertices) for t in m.loop_triangles],dtype=np.int32)
        return xyz, tri
    finally:
        if evaluated: e.to_mesh_clear()

report = {'status':'CLOSED_SURFACE_CANDIDATE_COMPONENT_PROVENANCE_ONLY',
          'source_sha256':EXPECTED, 'seed_sha256':SEED_SHA, 'trial_sha256':sha(TRIAL),
          'frame':0, 'blender_version':bpy.app.version_string,
          'source_saved':False, 'geometry_modified':False,
          'fixed_objects':{}, 'contacts':[], 'whole_vehicle_acceptance':'16 OPEN',
          'limits':[
              'Indexed and exact-coordinate connectivity are not semantic or physical-part counts',
              'BVH overlaps are surface-contact candidates, not depth or intended/unintended contact classification',
              'Matching historical seed triangles verifies imported geometry provenance, not factory dimensions or permission to remove it',
              'Virtual seam grouping changes no Blender data; coordinates are not rounded or tolerance-welded',
              'No full-angle clearance, hidden-object inclusion, renderer or web validation',
          ]}
snapshots = {}; component_indices = {}
for name in sorted({c['fixed'] for c in expected_contacts}):
    o = bpy.data.objects[name]
    assert o.type == 'MESH' and not o.modifiers
    xyz,tri = mesh(o); raw = mesh(o,False)
    assert np.array_equal(xyz,raw[0]) and np.array_equal(tri,raw[1])
    raw_groups,_ = groups(xyz,tri); joined,idx = groups(xyz,tri,True)
    snapshots[name] = (xyz,tri); component_indices[name] = idx
    report['fixed_objects'][name] = {'vertices':len(xyz),'triangles':len(tri),
        'materials':[m.name for m in o.data.materials], 'raw_evaluated_exact':True,
        'raw_indexed_components':raw_groups, 'exact_coordinate_components':joined}

xyz,tri = snapshots['cab_0063']
current_faces = Counter(canon(xyz[t]) for t in tri)
unmatched = current_faces - seed_faces
report['seed_identity'] = {'seed_node':node['name'], 'seed_node_extras':node.get('extras'),
    'seed_vertices':len(seed_xyz),'seed_triangles':len(seed_tri),
    'seed_exact_coordinate_components':len(seed_groups), 'current_exact_coordinate_components':len(report['fixed_objects']['cab_0063']['exact_coordinate_components']),
    'current_oriented_triangles':len(tri), 'current_triangles_absent_from_seed':sum(unmatched.values()),
    'seed_triangles_not_in_current':sum((seed_faces-current_faces).values()),
    'exact_corner_match':not unmatched}
assert not unmatched, 'Original source identity is not exact; do not infer a match'
probe = next(xyz[t].copy() for t in tri if np.linalg.norm(np.cross(xyz[t[1]]-xyz[t[0]],xyz[t[2]]-xyz[t[0]]))>1e-10)
corrupt = probe.copy(); corrupt[0,0] += 1e-4
assert canon(corrupt) not in seed_faces and canon(probe[[0,2,1]]) not in seed_faces
report['seed_identity']['rejected_controls'] = ['one_corner_shifted_100um','reversed_non_degenerate_triangle_winding']
source_components = {i:Counter(canon(seed_xyz[seed_tri[j]]) for j in c['triangles']) for i,c in enumerate(seed_groups)}
matched_source_components = []
for c in report['fixed_objects']['cab_0063']['exact_coordinate_components']:
    faces = Counter(canon(xyz[tri[j]]) for j in c['triangles'])
    matches = [i for i, f in source_components.items() if faces == f]
    assert len(matches)==1
    c['exact_seed_component'] = matches[0]
    matched_source_components.extend(matches)
    # Bounds alone are not sufficient to label a cylinder. Check actual rings
    # and cap centres on the exact-coordinate group, without changing geometry.
    delta = np.asarray(c['bounds_world'][1])-c['bounds_world'][0]
    c['shape_diagnostic'] = 'other_retained_seed_geometry'
    if np.max(np.abs(delta-[.05,.05,.22]))<1e-6:
        unique = np.unique(xyz[c['vertices']],axis=0)
        center = (np.asarray(c['bounds_world'][0])+np.asarray(c['bounds_world'][1]))/2
        radial = np.linalg.norm(unique[:,:2]-center[:2],axis=1)
        ends = sorted(set(unique[:,2])); cap_centres = radial<1e-6
        rim = ~cap_centres
        ring_counts = [int(np.count_nonzero((unique[:,2]==z)&rim)) for z in ends]
        valid = len(ends)==2 and ring_counts==[24,24] and int(cap_centres.sum())==2 and bool(np.all(np.abs(radial[rim]-.025)<1e-6))
        c['ring_validation'] = {'two_axial_planes_z_m':ends, 'rim_vertex_counts':ring_counts,
            'cap_centres':int(cap_centres.sum()),'ring_radius_min_max_m':[float(radial[rim].min()),float(radial[rim].max())],
            'valid_vertical_24_sided_cylinder':valid}
        if valid: c['shape_diagnostic'] = 'vertical_24_sided_cylinder_50mm_diameter_220mm_length'
report['seed_identity']['seed_components_not_in_current_object'] = [
    {'component':i,'vertices':len(c['vertices']),'triangles':len(c['triangles']),'bounds_world':c['bounds_world']}
    for i,c in enumerate(seed_groups) if i not in matched_source_components]
report['seed_identity']['missing_component_limit'] = 'Not present in this one object; not a claim of missing vehicle geometry or a new edit'

for prior in expected_contacts:
    moving = mesh(bpy.data.objects[prior['moving']]); fixed = snapshots[prior['fixed']]
    moving_bvh = BVHTree.FromPolygons(moving[0].tolist(),moving[1].tolist(),all_triangles=True,epsilon=0.)
    fixed_bvh = BVHTree.FromPolygons(fixed[0].tolist(),fixed[1].tolist(),all_triangles=True,epsilon=0.)
    hits = sorted(moving_bvh.overlap(fixed_bvh))
    assert len(hits) == prior['triangle_pair_count']
    components = {}
    for mi,fi in hits:
        component = component_indices[prior['fixed']][int(fixed[1][fi][0])]
        components.setdefault(component,[]).append([mi,fi])
    details = []
    for ci, pairs in sorted(components.items()):
        target = report['fixed_objects'][prior['fixed']]['exact_coordinate_components'][ci]
        details.append({'fixed_component':ci,'triangle_pairs':pairs,'component_bounds_world':target['bounds_world'],
                        'exact_seed_component':target.get('exact_seed_component'),
                        'shape_diagnostic':target.get('shape_diagnostic')})
    report['contacts'].append({'moving':prior['moving'],'fixed':prior['fixed'],
        'triangle_pair_count':len(hits),'matched_published_closed_contact_count':True,'hit_components':details})
report['source_sha256_after'] = sha(SOURCE); report['seed_sha256_after'] = sha(SEED)
assert report['source_sha256_after']==EXPECTED and report['seed_sha256_after']==SEED_SHA
(OUT/'component-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('CONTACT_COMPONENTS_FINISHED',report['seed_identity'],flush=True)
for c in report['contacts']:
    print('CLOSED_COMPONENT_CONTACT',c['moving'],c['fixed'],c['triangle_pair_count'],
          [(r['fixed_component'],r['component_bounds_world'],r['shape_diagnostic']) for r in c['hit_components']],flush=True)
