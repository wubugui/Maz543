"""Actual plate opening rays plus disabled-Boolean negative control; no save."""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/cloud-va180-panel-fit-20261001'
SOURCE=OUT/'MAZ543A_Master.blend'
build=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==build['candidate_sha256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
plate=bpy.data.objects['LEFT PANEL — real openings / fitted silhouette']
hole=bpy.data.objects['L-HOLE-B4']
modifier=next(m for m in plate.modifiers if m.type=='BOOLEAN' and
              ((m.operand_type=='OBJECT' and m.object==hole) or
               (m.operand_type=='COLLECTION' and hole.name in m.collection.objects)))
root=bpy.data.objects['VA180 PARTIAL — B4 PHOTO-FORM REVIEW']
normal=(root.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
def tree():
    ev=plate.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
    v=[ev.matrix_world@p.co for p in m.vertices];t=[tuple(p.vertices) for p in m.loop_triangles];ev.to_mesh_clear()
    return BVHTree.FromPolygons(v,t,all_triangles=True)
# Rays at the actual fitted casing's outer radius, through the whole plate.
points=[root.matrix_world@Vector((.042*math.cos(i*2*math.pi/192),.042*math.sin(i*2*math.pi/192),0)) for i in range(192)]
def hits():
    bvh=tree()
    return sum(bvh.ray_cast(p-normal*.01,normal,.02)[0] is not None for p in points)
enabled=(modifier.show_viewport,modifier.show_render)
actual=hits()
try:
    modifier.show_viewport=False;bpy.context.view_layer.update();disabled=hits()
finally:
    modifier.show_viewport,modifier.show_render=enabled;bpy.context.view_layer.update()
restored=hits()
report={'candidate_sha256':build['candidate_sha256'],'rays':192,'actual_plate_hits':actual,
        'disabled_panel_opening_boolean_hits':disabled,'restored_plate_hits':restored,
        'negative_control_operand_type':modifier.operand_type,
        'negative_control_pass':disabled==192,'opening_samples_pass':actual==restored==0,
        'scope':'192 circumferential axial rays at the casing outer radius through the actual plate. Static samples, not continuous clearance or factory dimensions.',
        'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==build['candidate_sha256'],'saved_blend':False}
(OUT/'aperture-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print('VA180_APERTURE',json.dumps(report))
assert report['negative_control_pass'] and report['opening_samples_pass'] and report['source_unchanged']
