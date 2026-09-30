import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for filename in ['MAZ543A_Cooling_Master.blend','MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    path=ROOT/'outputs'/filename;bpy.ops.wm.open_mainfile(filepath=str(path))
    text=bpy.data.texts.get('COOLING_REFERENCE_NOTES.md') or bpy.data.texts.new('COOLING_REFERENCE_NOTES.md')
    text.clear();text.write((ROOT/'docs/COOLING_REFERENCE_NOTES.md').read_text(encoding='utf-8'))
    text=bpy.data.texts.get('PART_PHOTO_WORKFLOW.md') or bpy.data.texts.new('PART_PHOTO_WORKFLOW.md')
    text.clear();text.write((ROOT/'docs/PART_PHOTO_WORKFLOW.md').read_text(encoding='utf-8'))
    if filename!='MAZ543A_Cooling_Master.blend':
        text=bpy.data.texts.get('CAB_PHOTO_FIT_NOTES.md') or bpy.data.texts.new('CAB_PHOTO_FIT_NOTES.md')
        text.clear();text.write((ROOT/'docs/CAB_PHOTO_FIT_NOTES.md').read_text(encoding='utf-8'))
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
path=ROOT/'outputs/MAZ543A_Cardan_Master.blend'
if path.exists():
    from mathutils import Vector
    bpy.ops.wm.open_mainfile(filepath=str(path))
    text=bpy.data.texts.get('CARDAN_REFERENCE_NOTES.md') or bpy.data.texts.new('CARDAN_REFERENCE_NOTES.md')
    text.clear();text.write((ROOT/'docs/CARDAN_REFERENCE_NOTES.md').read_text(encoding='utf-8'))
    text=bpy.data.texts.get('PART_PHOTO_WORKFLOW.md') or bpy.data.texts.new('PART_PHOTO_WORKFLOW.md')
    text.clear();text.write((ROOT/'docs/PART_PHOTO_WORKFLOW.md').read_text(encoding='utf-8'))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.clip_start=.0001;space.region_3d.view_distance=.70
                space.region_3d.view_location=(.12,-.04,0);space.region_3d.view_rotation=Vector((.28,.57,-.28)).to_track_quat('-Z','Y');space.region_3d.view_perspective='PERSP'
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
