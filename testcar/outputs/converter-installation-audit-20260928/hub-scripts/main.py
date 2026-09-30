"""Read-only converter installation audit (Hub Blender 4.5.13).

Temporarily installs the saved four-wheel converter assembly into the vehicle
master, coaxial with the gearbox turbine/input shaft 15 (source topology:
turbine 11 -> hub 2 -> turbine shaft 15 -> gearbox input), then measures shaft
agreement, envelopes, triangle-surface interference with every nearby vehicle
mesh, and the relation to the D12 flywheel/crankshaft. Nothing is saved.
Interference = triangle/triangle surface crossings (BVH overlap); a solid wholly
inside another without crossing surfaces is not detected.
"""
import bpy, json, math, os
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = Path(os.environ['HUB_OUTPUT_DIR']); OUT.mkdir(parents=True, exist_ok=True)
ROOT = Path.cwd()
def log(*a): print('[audit]', *a, flush=True)

bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'MAZ543A_Master.blend'))
tx = bpy.data.objects['S543_TRANSMISSION']
tx_shaft = bpy.data.objects['TX_15_input_shaft']
vehicle_meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
log('vehicle meshes', len(vehicle_meshes))

with bpy.data.libraries.load(str(ROOT / 'MAZ543A_Converter_FourWheelAssembly.blend'), link=False) as (src, dst):
    dst.objects = list(src.objects)
for ob in dst.objects:
    if ob.name not in bpy.context.scene.objects: bpy.context.collection.objects.link(ob)
    ob.animation_data_clear()
conv = next(o for o in dst.objects if o.name.startswith('S543_CONVERTER_ASSEMBLY'))
conv_meshes = [o for o in dst.objects if o.type == 'MESH']
ca_shaft = next(o for o in dst.objects if o.name.startswith('CA_15_turbine_shaft'))
bpy.context.view_layer.update()

def local_stats(ob, frame):
    """Axial (x) extent, radial extent and axis centroid of ob's vertices in frame's space."""
    m = frame.matrix_world.inverted() @ ob.matrix_world
    xs, rs, ys, zs = [], [], [], []
    for v in ob.data.vertices:
        p = m @ v.co; xs.append(p.x); rs.append(math.hypot(p.y, p.z)); ys.append(p.y); zs.append(p.z)
    return {'xMin': min(xs), 'xMax': max(xs), 'rMin': min(rs), 'rMax': max(rs),
            'axisCentroidYZ': [sum(ys) / len(ys), sum(zs) / len(zs)], 'lengthM': max(xs) - min(xs)}

conv_frame_before = conv.matrix_world.copy()
tx_shaft_tx = local_stats(tx_shaft, tx)
ca_shaft_conv = local_stats(ca_shaft, conv)
# Same shaft 15: put the converter's turbine-hub end of shaft 15 at the gearbox shaft's front end.
x0 = tx_shaft_tx['xMin'] - ca_shaft_conv['xMin']
conv.parent = tx; conv.matrix_parent_inverse = Matrix.Identity(4)
conv.location = (x0, 0.0, 0.0); conv.rotation_mode = 'XYZ'; conv.rotation_euler = (0, 0, 0); conv.scale = (1, 1, 1)
bpy.context.view_layer.update()
ca_shaft_tx = local_stats(ca_shaft, tx)
log('placement x0 (transmission frame, m)', x0)

# Converter envelope in the transmission frame.
env = {'xMin': 1e9, 'xMax': -1e9, 'rMax': 0.0}
for ob in conv_meshes:
    s = local_stats(ob, tx); env['xMin'] = min(env['xMin'], s['xMin']); env['xMax'] = max(env['xMax'], s['xMax']); env['rMax'] = max(env['rMax'], s['rMax'])
def under(o, name):
    while o:
        if o.name == name: return True
        o = o.parent
    return False
housing_parts = [o for o in tx.children_recursive if o.type == 'MESH' and under(o, 'TX_housing')]
housing = {'xMin': 1e9, 'xMax': -1e9, 'rMax': 0.0, 'meshes': len(housing_parts)}
for ob in housing_parts:
    s = local_stats(ob, tx); housing['xMin'] = min(housing['xMin'], s['xMin']); housing['xMax'] = max(housing['xMax'], s['xMax']); housing['rMax'] = max(housing['rMax'], s['rMax'])
tx_all = [o for o in tx.children_recursive if o.type == 'MESH' and o not in conv_meshes]
txenv = {'xMin': 1e9, 'xMax': -1e9, 'rMax': 0.0}
for ob in tx_all:
    s = local_stats(ob, tx); txenv['xMin'] = min(txenv['xMin'], s['xMin']); txenv['xMax'] = max(txenv['xMax'], s['xMax']); txenv['rMax'] = max(txenv['rMax'], s['rMax'])

# World triangle BVH of the converter, with a triangle -> object map.
def world_tris(objs):
    pts, faces, owner = [], [], []
    for ob in objs:
        me = ob.data; me.calc_loop_triangles(); mw = ob.matrix_world; base = len(pts)
        pts.extend(mw @ v.co for v in me.vertices)
        for t in me.loop_triangles: faces.append(tuple(base + i for i in t.vertices)); owner.append(ob.name)
    return pts, faces, owner
cp, cf, cowner = world_tris(conv_meshes)
cbvh = BVHTree.FromPolygons(cp, cf, all_triangles=True)
cmin = Vector((min(p.x for p in cp), min(p.y for p in cp), min(p.z for p in cp))) - Vector((.002, .002, .002))
cmax = Vector((max(p.x for p in cp), max(p.y for p in cp), max(p.z for p in cp))) + Vector((.002, .002, .002))
log('converter triangles', len(cf))

def aabb(ob):
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))), Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
candidates = []
for ob in vehicle_meshes:
    lo, hi = aabb(ob)
    if all(lo[i] <= cmax[i] and hi[i] >= cmin[i] for i in range(3)): candidates.append(ob)
log('AABB candidates', len(candidates))
conflicts = []
for ob in candidates:
    p, f, _ = world_tris([ob])
    if not f: continue
    pairs = cbvh.overlap(BVHTree.FromPolygons(p, f, all_triangles=True))
    if pairs:
        by = {}
        for a, _b in pairs: by[cowner[a]] = by.get(cowner[a], 0) + 1
        top = sorted(by.items(), key=lambda kv: -kv[1])[:6]
        conflicts.append({'vehicleMesh': ob.name, 'hiddenInRender': ob.hide_render, 'trianglePairs': len(pairs), 'converterMeshes': len(by), 'topConverterMeshes': top})
conflicts.sort(key=lambda c: -c['trianglePairs'])

# Engine relation, expressed along/around the gearbox axis.
ax_o = tx.matrix_world.translation.copy(); ax_d = (tx.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
def along(p): return (p - ax_o).dot(ax_d)
def off_axis(p): v = p - ax_o; return (v - ax_d * v.dot(ax_d)).length
engine = {}
for name in ['D12_flywheel', 'D12_flywheel_bellhousing', 'D12_crankshaft']:
    ob = bpy.data.objects.get(name)
    if not ob or ob.type != 'MESH': engine[name] = None; continue
    ws = [ob.matrix_world @ v.co for v in ob.data.vertices]; c = sum(ws, Vector()) / len(ws)
    engine[name] = {'alongGearboxAxisM': [min(along(p) for p in ws), max(along(p) for p in ws)], 'centroidOffAxisM': off_axis(c),
                    'localXAxisAngleToGearboxDeg': math.degrees((ob.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized().angle(ax_d))}
crank = bpy.data.objects.get('D12_crankshaft')
conv_along = [min(along(p) for p in cp), max(along(p) for p in cp)]

report = {
    'status': 'AUDIT ONLY - nothing saved; installation OPEN',
    'blender': bpy.app.version_string,
    'method': 'Converter shaft 15 front end placed on gearbox shaft 15 front end; both are source part 15 (turbine shaft / gearbox input). Axes: both modules revolve about their local X.',
    'placementXInTransmissionFrameM': x0,
    'converterRootMatrixBeforeInstall': [list(r) for r in conv_frame_before],
    'shaft15': {'gearbox_TX_15_input_shaft': tx_shaft_tx, 'converter_CA_15_turbine_shaft_installed': ca_shaft_tx,
                'outerRadiusDifferenceMM': (tx_shaft_tx['rMax'] - ca_shaft_tx['rMax']) * 1000,
                'boreRadiusDifferenceMM': (tx_shaft_tx['rMin'] - ca_shaft_tx['rMin']) * 1000,
                'lengthDifferenceMM': (tx_shaft_tx['lengthM'] - ca_shaft_tx['lengthM']) * 1000,
                'rearEndDifferenceMM': (tx_shaft_tx['xMax'] - ca_shaft_tx['xMax']) * 1000},
    'converterEnvelopeTransmissionFrameM': env,
    'gearboxHousingEnvelopeTransmissionFrameM': housing,
    'gearboxModuleEnvelopeTransmissionFrameM': txenv,
    'axialOverlapConverterVsGearboxHousingMM': max(0.0, min(env['xMax'], housing['xMax']) - max(env['xMin'], housing['xMin'])) * 1000,
    'gearboxAxisWorld': {'origin': list(ax_o), 'direction': list(ax_d)},
    'converterAlongGearboxAxisM': conv_along,
    'engine': engine,
    'interference': {'aabbCandidates': len(candidates), 'meshesWithSurfaceCrossings': len(conflicts), 'conflicts': conflicts[:60]},
    'limits': ['Only one converter pose (as saved) and the master neutral pose are checked.',
               'Surface-crossing test only; enclosed-volume overlaps without crossings are not detected.',
               'Duplicate shaft 15 (gearbox and converter models) is expected to overlap itself; it is reported, not excused.',
               'All converter dimensions except 12.5x22 mm rollers are fitted reconstruction parameters.'],
}
(OUT / 'converter-installation-audit.json').write_text(json.dumps(report, indent=2))
log('conflicts', len(conflicts), 'written')
