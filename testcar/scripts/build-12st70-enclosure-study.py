"""Add source-supported, dimensionally fitted cover forms to an isolated study.

No mounting holes/fasteners or factory mechanism are invented. The generic
1983 fig4 does not identify the exact 12ST70/70M production variant.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/cloud-12st70-structure-20261001/12ST70_Family_Structure_Study.blend'
OUT=ROOT/'outputs/cloud-12st70-enclosure-20261001';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original_sha=sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
scene.name='12ST70_FAMILY_ENCLOSURE_FORMS_NOT_FACTORY_ASSEMBLY'
root=bpy.data.objects['BATTERY_STRUCTURE_NOT_VEHICLE_INSTALLATION']
dg=bpy.context.evaluated_depsgraph_get()
def vertices(o):
    e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@x.co for x in m.vertices];e.to_mesh_clear();return v
register=json.loads((SOURCE.parent/'parts-register.json').read_text())
old=[bpy.data.objects[r['name']] for r in register]
old_points={o.name:[[float(x) for x in p] for p in vertices(o)] for o in old}
def bounds(objects):
    points=[p for o in objects for p in vertices(o)]
    return [min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]
wood_min,wood_max=bounds([o for o in old if o['role']=='wood_case'])
term_min,term_max=bounds([o for o in old if o['role'] in {'front_lead','front_terminal'}])
all_min,all_max=bounds(old)
def cube(name,minimum,maximum,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=[(a+b)/2 for a,b in zip(minimum,maximum)])
    o=bpy.context.object;o.name=name;o.dimensions=[b-a for a,b in zip(minimum,maximum)]
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    o.parent=root;return o
def bevel(o,width):
    m=o.modifiers.new('Native fitted edge rounding','BEVEL');m.width=width;m.segments=3
lidmin=[wood_min[0]-.002,wood_min[1]-.002,all_max[2]+.001]
lidmax=[wood_max[0]+.002,wood_max[1]+.002,lidmin[2]+.004]
lid=cube('FITTED_pressed_wood_overall_lid',lidmin,lidmax,bpy.data.materials['Acid-resistant dark lacquer on wood | finish fitted'])
bevel(lid,.0007)
hoodmat=bpy.data.materials.new('Hood appearance neutral | source material unresolved');hoodmat.diffuse_color=(.075,.075,.075,1);hoodmat.use_nodes=True
hoodmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.075,.075,.075,1)
hoodmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.45
# Front panel plus two side returns; native exact Boolean leaves a real open U.
# 1.5mm wall,3mm internal clearance,5mm vertical coverage are explicit fitted
# study parameters, NOT values measured from fig4 or a factory drawing.
wall=.0015;clearance=.003
hoodmin=[term_min[0]-clearance-wall,term_min[1]-clearance-wall,term_min[2]-.005]
hoodmax=[wood_min[0]-.001,term_max[1]+clearance+wall,term_max[2]+.005]
hood=cube('FITTED_terminal_protective_hood',hoodmin,hoodmax,hoodmat)
cutter=cube('TOOL_open_hood_back_top_bottom',[hoodmin[0]+wall,hoodmin[1]+wall,hoodmin[2]-.01],[hoodmax[0]+.01,hoodmax[1]-wall,hoodmax[2]+.01],None)
cutter.hide_render=True;cutter.hide_set(True);cutter.display_type='WIRE';cutter['construction_only']=True
mod=hood.modifiers.new('Native exact open U enclosure','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bevel(hood,.00035)
# The first fitted lid used only the original73 parts as its height bound and
# intersected the newly added hood. Include that real component in the fit.
lid.location.z+=max(0,hoodmax[2]+.001-lidmin[2])
added=[lid,hood]
for o,role in [(lid,'overall_lid_form'),(hood,'terminal_hood_form')]:
    o['role']=role;o['dimension_status']='FITTED_NOT_FACTORY_DIMENSIONS';o['source']='1983 guide p11 explicit family description; fig4 generic form only'
    o['attachment_status']='UNMODELED: no guessed mounting holes, bolt axis or cover catches'
    register.append({'name':o.name,'role':role,'source':o['source'],'dimensions':'FITTED','detail':o['attachment_status']})
root['status']='UNACCEPTED_ENCLOSURE_FORM_STUDY; NO_FACTORY_ATTACHMENT_OR_VEHICLE_INSTALLATION'
root['unmodeled']='Exact plate packs/separators and count; electrolyte; copper inserts; terminal-hood fastening; overall-lid catches; precise carrying hardware; vehicle box/four-unit installation.'
root['enclosure_source_boundary']='1983 fig4 is generic tank-battery construction. It cannot establish70vs70M variant, fastener location, dimensions, terminal-hood material or a factory removal trajectory.'
for name in ['PROTECTIVE_TERMINAL_HOOD_UNMODELED','PRESSED_WOOD_TOP_COVER_UNMODELED']:
    o=bpy.data.objects[name];o['status']='FORM_NOW_FITTED; FACTORY_ATTACHMENT_STILL_UNMODELED'
bpy.context.view_layer.update()
for o in old:
    assert old_points[o.name]==[[float(x) for x in p] for p in vertices(o)],o.name
manifest={'status':'SOURCE_SUPPORTED_FORMS_WITH_FITTED_DIMENSIONS_NOT_ASSEMBLY_ACCEPTANCE','source_blend':str(SOURCE.relative_to(ROOT)),'source_sha256':original_sha,'preserved_old_parts':len(old),'new_parts':[o.name for o in added],
 'fitted_parameters_m':{'hood_wall':wall,'hood_internal_clearance':clearance,'hood_vertical_margin':.005,'hood_rear_gap_to_wood':.001,'lid_overhang':.002,'lid_gap_above_all_existing_parts_including_new_hood':.001,'lid_thickness':.004},
 'attachment_unmodeled':True,'generic_figure_cannot_identify_variant':True,'all16VehicleGates':'OPEN'}
(OUT/'parts-register.json').write_text(json.dumps(register,indent=2))
(OUT/'build-manifest.json').write_text(json.dumps(manifest,indent=2))
bpy.data.texts['READ_ME_BATTERY_STUDY'].write('\n\nENCLOSURE_STAGE\n'+json.dumps(manifest,indent=2))
scene.cycles.samples=48;scene.render.threads=4;scene.camera.data.ortho_scale=1.02
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'12ST70_Enclosure_Form_Study.blend'),compress=True)
records=[]
for name in ['enclosure-fitted-forms','enclosure-separated-inspection']:
    if name.endswith('inspection'):
        lid.location.z+=.105;hood.location.x-=.075;cutter.location.x-=.075
    bpy.context.view_layer.update()
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    records.append({'file':name+'.png','part_world_matrices':{o.name:[list(r) for r in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world] for o in added},'display_offsets_only_not_factory_service_motion':name.endswith('inspection')})
(OUT/'render-provenance.json').write_text(json.dumps({'engine':'Actual Cycles CPU,48samples,4threads','records':records,'not_installed_on_vehicle':True},indent=2))
assert sha(SOURCE)==original_sha
print('ENCLOSURE_FORMS_SAVED',len(old),'preserved parts;2 fitted forms;attachments OPEN',flush=True)
