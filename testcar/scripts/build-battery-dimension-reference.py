"""Save a measured envelope reference, not a reconstructed or installed battery."""
import bpy,json,os,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=Path(os.environ.get('MAZ_BATTERY_REFERENCE_OUT',str(root/'outputs/cloud-battery-dimension-reference-20260930'))).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
bpy.ops.mesh.primitive_cube_add(size=1)
obj=bpy.context.object;obj.name='REFERENCE_ONLY_12ST70_OUTER_ENVELOPE';obj.dimensions=(.587,.238,.239)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
obj.display_type='WIRE';obj.hide_render=True;obj.color=(1,.65,.08,1)
obj['purpose']='Dimension reference only; this cuboid is not the battery casing geometry and is not installed in the vehicle.'
obj['source']='USSR Ministry of Defence, Lead-acid Starter Battery Guide, 1983, table 1, PDF page 5; 12ST-70 row.'
obj['source_url']='https://www.compancommand.com/literatura/Avtomob/Akkum_Batarei_1983.pdf'
obj['dimensions_m']=[.587,.238,.239];obj['nominal_voltage_V']=24;obj['nominal_10h_capacity_Ah']=70
obj['unresolved']='Terminals, cover edges, hold-down interfaces, box clearances, manufacturing tolerance, original 1977 dimensional continuity and vehicle mounting coordinates.'
obj['axis_convention']='Local X length, Y width, Z height; no mapping to vehicle axes established.'
scene['acceptance_status']='REFERENCE_ENVELOPE_ONLY; all whole-vehicle gates OPEN'
filename=out/'12ST70_dimension_reference.blend';bpy.ops.wm.save_as_mainfile(filepath=str(filename),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(filename));bpy.context.view_layer.update();obj=bpy.data.objects['REFERENCE_ONLY_12ST70_OUTER_ENVELOPE'];actual=list(obj.dimensions)
error=max(abs(a-b) for a,b in zip(actual,[.587,.238,.239]));assert error<1e-7;assert obj.hide_render and obj.display_type=='WIRE'
(out/'readback.json').write_text(json.dumps({'status':'PASS_DIMENSION_REFERENCE_READBACK','source':obj['source_url'],'source_year':1983,'target':'12ST-70 envelope only','nominal_dimensions_m':[.587,.238,.239],'actual_saved_dimensions_m':actual,'max_numeric_error_m':error,'blend_sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),'not_battery_geometry':True,'not_vehicle_installation':True,'whole_vehicle_gates':'16 OPEN'},indent=2)+'\n')
print('DIMENSION_REFERENCE_ONLY',actual,error)
