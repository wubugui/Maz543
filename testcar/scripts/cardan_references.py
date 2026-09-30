"""Attach per-part evidence and packed reference sheets to the native Cardan.

Reference sheets are an optional, non-rendering collection outside the mechanism.
They are not photographs or calibrated orthographic construction planes.
"""
import bpy,json,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT='https://rotor-plus.ru/autocat/gruzovye_avtomobili/maz/maz_543__7310__1146/val_kardannyj_543_1308586_a-82'
MCB='https://mcbbearings.com/wp-content/uploads/2024/02/MCB-Univeral-Joint-Catalog.pdf'
MANUAL='https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/007.htm'

def evidence(name):
    if name.startswith('CJ_flange_fork_'):
        return ('543-1308606',CAT,'Catalog 13.5: four-hole flange fork topology.',
                'Flange OD/PCD, bore, thickness, arm profile, fillets and finish fitted.')
    if name.startswith('CJ_sliding_fork_') or name in ['CJ_male_neck','CJ_male_spline','CJ_female_spline']:
        return ('543-1308603-B / 543-1308598-B',CAT,'Catalog 13.5 and 1973 description: male/female sliding forks.',
                'Exact suffix-to-male/female assignment, 12-tooth profile, neck, length, stroke and fits unverified.')
    if 'grease' in name:
        return ('Unresolved grease nipple part number',MANUAL,'1973 description: cross lubricated through grease nipple.',
                'Nipple type, hex, thread, bores and passage dimensions fitted; no individual photograph accepted.')
    if name.startswith('CJ_spider_'):
        return ('408-2201026-02; family envelope only',CAT+' | '+MCB,
                'Catalog identifies cross; MCB printed pp.7/24 gives 408-2201025 assembled D28/O42.5/L73 mm.',
                'Suffix equivalence unverified; bare cross, 16 mm pins, centre profile and grease galleries fitted.')
    if name.endswith('_seal'):
        return ('Unresolved bearing seal part number',MANUAL,'1973 description: sealing rings in needle-bearing joints.',
                'Seal section, material compound, lip preload and all seal dimensions fitted.')
    if name.endswith('_circlip'):
        return ('400-2201043',CAT+' | '+MCB,'Catalog identifies retaining ring; MCB type B shows open external clip.',
                'Clip gap, radial section and 0.9 mm thickness fitted; groove reference is from 408 family only.')
    if name.startswith('CJ_cap_'):
        return ('704902-K6 / catalog bearing 0000-1308364',CAT+' | '+MCB,
                '408-family assembled cup OD28 mm and cap-to-cap span73 mm; MCB printed pp.7/24.',
                'Bearing suffix equivalence, cup length, wall, inner race, seal recess and groove profile unverified.')
    if name.startswith('CJ_needle_'):
        return ('Needle inside 704902-K6 reference bearing',MANUAL,
                '1973 description establishes needle bearings; no measured individual roller source.',
                '2.5 x 14 mm rollers and 22 rollers per cup fitted; load/contact/lubrication not validated.')
    raise ValueError('Missing part-specific evidence: '+name)

def annotate(root):
    report=[]
    for o in sorted(root.children_recursive,key=lambda o:o.name):
        if o.type!='MESH':continue
        part,url,supported,missing=evidence(o.name)
        o['referencePartNumber']=part;o['sourceId']=url
        o['sourceSupports']=supported;o['dimensionStatus']=missing
        o['individualPhotoStatus']='NOT OBTAINED for this exact part; diagrams/family dimensions only.'
        report.append({'name':o.name,'part':part,'role':o.get('cardanRole'),'source':url,
                       'supported':supported,'dimensions':missing,'individualPhoto':o['individualPhotoStatus']})
    (ROOT/'outputs/cardan-parts-register.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text=bpy.data.texts.get('CARDAN_PART_EVIDENCE.json') or bpy.data.texts.new('CARDAN_PART_EVIDENCE.json')
    text.clear();text.write(json.dumps(report,indent=2))
    return report

def pack_sheets():
    notes=bpy.data.texts.get('CARDAN_REFERENCE_NOTES.md') or bpy.data.texts.new('CARDAN_REFERENCE_NOTES.md')
    notes.clear();notes.write((ROOT/'docs/CARDAN_REFERENCE_NOTES.md').read_text(encoding='utf-8'))
    collection=bpy.data.collections.get('CARDAN_REFERENCE_SHEETS')
    if collection is None:
        collection=bpy.data.collections.new('CARDAN_REFERENCE_SHEETS');bpy.context.scene.collection.children.link(collection)
    collection.hide_render=True;collection.hide_viewport=True
    sheets=[('543-cardan-exploded.png',CAT,'Catalog 13.5; lossless GIF-to-PNG copy, assembly topology only, not dimensioned.'),
            ('MAZ1973-0575.jpg',MANUAL,'1973 Fig.30; schematic, not a measured installation drawing.'),
            ('MCB-grooved-cross-definition.png',MCB,'Printed p.7; type B dimension definitions, not an exact MAZ cross drawing.'),
            ('MCB-408-dimensions.png',MCB,'Printed p.24; 400/408-2201025 family dimensions, suffix equivalence unverified.')]
    manifest=[]
    for i,(filename,url,scope) in enumerate(sheets):
        path=ROOT/'work/reference-docs'/filename
        image=bpy.data.images.load(str(path),check_existing=True);image.pack();image.use_fake_user=True
        name='REFERENCE_'+Path(filename).stem
        o=bpy.data.objects.get(name)
        if o is None:o=bpy.data.objects.new(name,None);collection.objects.link(o)
        o.empty_display_type='IMAGE';o.data=image;o.empty_display_size=.45
        o.location=(i*.40-.25,.45,0);o.hide_render=True
        o['sourceURL']=url;o['referenceScope']=scope;o['calibratedScale']=False
        manifest.append({'image':image.name,'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'source':url,'scope':scope,'pixels':list(image.size),'packed':bool(image.packed_file)})
    guide=bpy.data.texts.get('READ_ME_REFERENCES.txt') or bpy.data.texts.new('READ_ME_REFERENCES.txt')
    guide.clear();guide.write('Select a mechanism mesh and inspect Custom Properties: referencePartNumber, sourceSupports, dimensionStatus, individualPhotoStatus.\n'
        'Open CARDAN_PART_EVIDENCE.json in the Text Editor for the complete mesh index.\n'
        'Open the packed images in an Image Editor, or enable CARDAN_REFERENCE_SHEETS in the Outliner to see the comparison sheets.\n'
        'Sheets are reference documents at arbitrary display scale, not calibrated photo overlays. No exact-part photos have been accepted.\n'
        'The independent Cardan is not installed or dimensionally accepted as an original MAZ-543 part.\n')
    (ROOT/'outputs/cardan-reference-sheets.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

if __name__=='__main__':
    path=ROOT/'outputs/MAZ543A_Cardan_Master.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path));root=bpy.data.objects['S543_CARDAN']
    # Metadata-only change: preserve all native vertices, transforms and animation.
    def geometry_digest():
        rows=[]
        for o in sorted(root.children_recursive,key=lambda o:o.name):
            rows.append([o.name,list(o.location),list(o.rotation_quaternion),list(o.scale),
                         [list(v.co) for v in o.data.vertices] if o.type=='MESH' else [],
                         [[fc.data_path,fc.array_index,[list(k.co) for k in fc.keyframe_points]]
                          for fc in o.animation_data.action.fcurves] if o.animation_data and o.animation_data.action else []])
        return hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    before=geometry_digest();report=annotate(root);sheets=pack_sheets()
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path));root=bpy.data.objects['S543_CARDAN']
    assert geometry_digest()==before,'Reference attachment altered mechanism data'
    assert len(report)==213 and all(bpy.data.images[s['image']].packed_file for s in sheets)
    assert all(o.get('sourceSupports') and o.get('individualPhotoStatus') for o in root.children_recursive if o.type=='MESH')
    print('CARDAN_REFERENCES_VERIFIED',len(report),'meshes',len(sheets),'packed sheets; mechanism digest',before,flush=True)
