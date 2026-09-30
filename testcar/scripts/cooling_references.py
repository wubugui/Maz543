"""Part-level provenance and native reference images; no geometry modification."""
import bpy, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/'
MANUAL = 'https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm'
PHOTO = 'https://detal-potok.ru/product/reduktor-privoda-ventilyatora-543-1308509-nizhnij-na-maz-543/'
LOWER = BASE + 'reduktor_nizhnij__privod_543_1308509-86'
UPPER = BASE + 'reduktor_ventilyatora_543_1308210_a1__543_1308211_a1-83'
PUMP = BASE + 'nasos_543_1308714-87'
INSTALL = BASE + 'ustanovka_ventilyatora__privoda-78'
CARDAN = BASE + 'val_kardannyj_543_1308586_a-82'


def evidence(o):
    n = o.name
    part = str(o.get('coolingPart', 'Unresolved'))
    photos = []
    limits = str(o.get('dimensionStatus', 'Dimensions unverified'))
    if n.startswith('COOL_lower_'):
        sources, sheets = [MANUAL, LOWER], ['MAZ1973-0575.jpg', '543-lower-exploded.png']
        support = 'Lower-drive section and catalog identify arrangement; not measured part drawings.'
        # The photograph depicts the assembled unit. It cannot establish the
        # geometry of its hidden gears, bearings, hollow shafts or oil galleries.
        if any(x in n for x in ['cast_case', 'output_cup_', 'input_bearing_cup',
                                  'input_cup_land_', 'pump_front_boss', 'pump_top_cross',
                                  'oil_pump_cover', 'oil_cover_', 'fill', 'drain']):
            photos = ['543-1308509-lower-photo.png']
            sources.append(PHOTO)
            support += ' Assembled seller photo supports the visible external contour/finish only.'
        if any(x in n for x in ['oil_pump_', 'oil_gear_', 'oil_drive_coupling', 'pump_front_', 'pump_top_', 'oil_cover_']):
            sources.append(PUMP); sheets.append('543-oil-pump-exploded.png')
            support += ' Pump exploded topology; relief valve and complete passages remain incomplete.'
    elif n.startswith('COOL_upper_'):
        sources, sheets = [MANUAL, UPPER], ['MAZ1973-0582.jpg', '543-upper-exploded.png']
        support = 'Upper-drive section/catalog arrangement; no exact individual housing photograph accepted.'
    elif 'cardan' in n or o.get('coolingRole') == 'drive-pending':
        sources, sheets = [MANUAL, INSTALL, CARDAN], ['MAZ1973-0575.jpg', '543-fan-install.png', '543-cardan-exploded.png']
        support = 'Installation/assembly topology only; installed shaft closure unresolved.'
    elif o.get('coolingRole') in ['radiator', 'radiator-internal', 'shutter', 'pipe'] or any(x in n for x in ['expansion_', 'core_', 'water_tube_', 'tank_partition_']):
        sources, sheets = [MANUAL], ['MAZ1973-0534.jpg']
        support = 'Manual cooling-circuit architecture; local tube counts, fin pitch, joints and routing fitted.'
    else:
        sources, sheets = [MANUAL, UPPER], ['MAZ1973-0582.jpg', '543-upper-exploded.png']
        support = 'Fan/clutch section and assembly topology; does not establish every local feature or dimension.'
    if any(x in n for x in ['bearing_', 'ball_', 'cage_']):
        support += ' Nominal bearing envelopes only where documented; rolling-element count, race form, cage and fits fitted.'
    return dict(name=n, part=part, role=o.get('coolingRole'), sources=sources,
                drawings=sheets, photographs=photos, sourceSupports=support,
                dimensions=limits,
                individualPhoto='NOT ACCEPTED for isolated exact part',
                assemblyPhoto='Visible external feature only' if photos else 'No matching visible feature assigned')


def attach(root):
    report = []
    for o in sorted(root.children_recursive, key=lambda x: x.name):
        if o.type not in ['MESH', 'CURVE']: continue
        row = evidence(o); report.append(row)
        o['referencePartNumber'] = row['part']
        o['referenceURLs'] = ' | '.join(row['sources'])
        o['referenceDrawings'] = ' | '.join(row['drawings'])
        o['referencePhotographs'] = ' | '.join(row['photographs']) or 'NONE ACCEPTED'
        o['sourceSupports'] = row['sourceSupports']
        o['individualPhotoStatus'] = row['individualPhoto']
        o['assemblyPhotoStatus'] = row['assemblyPhoto']
    text = bpy.data.texts.get('COOLING_PART_EVIDENCE.json') or bpy.data.texts.new('COOLING_PART_EVIDENCE.json')
    text.clear(); text.write(json.dumps(report, indent=2))
    (ROOT / 'outputs/cooling-reference-register.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    col = bpy.data.collections.get('COOLING_REFERENCE_SHEETS')
    if col is None:
        col = bpy.data.collections.new('COOLING_REFERENCE_SHEETS'); bpy.context.scene.collection.children.link(col)
    col.hide_render = True; col.hide_viewport = True
    refs = [('543-1308509-lower-photo.png', PHOTO, 'Seller assembled lower gearbox; no isolated-part scale or original factory finish established.'),
            ('MAZ1973-0534.jpg', MANUAL, 'Original cooling-system description text; not a diagram or measured installation view.'),
            ('MAZ1973-0575.jpg', MANUAL, 'Fig.30 lower transmission section.'),
            ('MAZ1973-0582.jpg', MANUAL, 'Fig.31 upper drive and electromagnetic clutch section.'),
            ('543-lower-exploded.png', LOWER, 'Later catalog, lower drive; production revision unverified.'),
            ('543-upper-exploded.png', UPPER, 'Later catalog, upper drive; production revision unverified.'),
            ('543-oil-pump-exploded.png', PUMP, 'Oil pump topology; relief valve and complete passages not modeled.'),
            ('543-fan-install.png', INSTALL, 'Exploded installation; no calibrated shaft centres.'),
            ('543-cardan-exploded.png', CARDAN, 'Sliding Cardan topology; no measured fork/shaft dimensions.')]
    packed = []
    for i, (file, url, scope) in enumerate(refs):
        path = ROOT / 'work/reference-docs' / file
        im = bpy.data.images.load(str(path), check_existing=True); im.pack(); im.use_fake_user = True
        name = 'COOLING_REFERENCE_' + path.stem
        ob = bpy.data.objects.get(name)
        if ob is None: ob = bpy.data.objects.new(name, None); col.objects.link(ob)
        ob.empty_display_type = 'IMAGE'; ob.data = im; ob.empty_display_size = .7
        ob.location = (i % 3 * .85, 1 + i // 3 * .75, 0); ob.hide_render = True
        ob['sourceURL'] = url; ob['referenceScope'] = scope; ob['calibratedScale'] = False
        packed.append(dict(file=file, image=im.name, source=url, scope=scope,
                           sha256=hashlib.sha256(path.read_bytes()).hexdigest(), pixels=list(im.size), packed=bool(im.packed_file)))
    (ROOT / 'outputs/cooling-reference-sheets.json').write_text(json.dumps(packed, indent=2), encoding='utf-8')
    guide = bpy.data.texts.get('READ_ME_COOLING_REFERENCES.txt') or bpy.data.texts.new('READ_ME_COOLING_REFERENCES.txt')
    guide.clear(); guide.write('Select a modeled component and inspect its reference URLs, image names, evidence scope and photo status in Custom Properties.\n'
        'COOLING_PART_EVIDENCE.json indexes every authored mesh/curve. Open the named packed image in an Image Editor.\n'
        'COOLING_REFERENCE_SHEETS is an optional hidden comparison collection, outside the animated assembly; its images are NOT calibrated construction planes.\n'
        'One assembled gearbox photograph does not count as individual photographs of its hidden components. No isolated exact-part photo acceptance is claimed.\n')
    return report, packed


if __name__ == '__main__':
    path = ROOT / 'outputs/MAZ543A_Cooling_Master.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    def digest():
        root = bpy.data.objects['S543_COOLING']; rows = []
        for o in sorted(root.children_recursive, key=lambda x: x.name):
            geometry = [list(v.co) for v in o.data.vertices] if o.type == 'MESH' else (
                [[list(p.co) for p in spline.points] for spline in o.data.splines] if o.type == 'CURVE' else [])
            tracks = [[f.data_path, f.array_index, [list(k.co) for k in f.keyframe_points]] for f in o.animation_data.action.fcurves] if o.animation_data and o.animation_data.action else []
            rows.append([o.name, o.parent.name if o.parent else None, [list(r) for r in o.matrix_basis], geometry, tracks])
        return hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    before = digest(); report, packed = attach(bpy.data.objects['S543_COOLING'])
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path))
    assert digest() == before, 'Reference attachment changed mechanism data'
    assert len(report) > 1000
    assert all(bpy.data.images[p['image']].packed_file for p in packed)
    assert all(bpy.data.objects[r['name']].get('sourceSupports') for r in report)
    result = dict(authoredParts=len(report), packedImages=len(packed), unchangedMechanismDigest=before,
                  isolatedExactPartPhotosAccepted=0,
                  assemblyPhotoFeatureAssignments=sum(bool(r['photographs']) for r in report))
    (ROOT / 'outputs/cooling-reference-verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('COOLING_REFERENCES_VERIFIED', json.dumps(result), flush=True)
