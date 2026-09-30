from pathlib import Path
p=Path('scripts/cooling-upper-detail.py');s=p.read_text();s=s.replace(',CAST,',',uppercast,');p.write_text(s)
p=Path('scripts/cooling-lower-surfaces.py');s=p.read_text();s=s.replace('def bake_lower_surfaces():',"def bake_cooling_surfaces(material_name, flag, prefix):").replace("bpy.data.materials['COOL_lower_black_storage_enamel']","bpy.data.materials[material_name]").replace("o.get('lowerDrive')","o.get(flag)").replace("'COOL_lower_cast_normal'","prefix+'_normal'").replace("'COOL_lower_cast_roughness'","prefix+'_roughness'")
s=s.replace("ramp.color_ramp.elements[0].color=(.28,.28,.28,1);ramp.color_ramp.elements[1].color=(.48,.48,.48,1)","lo,hi=(.28,.48) if flag=='lowerDrive' else (.40,.60);ramp.color_ramp.elements[0].color=(lo,lo,lo,1);ramp.color_ramp.elements[1].color=(hi,hi,hi,1)")
s=s.replace("o['surfaceEvidence']='Storage enamel appearance from inspected 543-1308509 photo; procedurally reconstructed microtexture, not photo-extracted measurement'","o['surfaceEvidence']='Procedural cast finish; lower storage enamel photo-guided, upper alloy finish unverified; not measured surface topography'")
s=s.replace("print('COOLING_LOWER_BAKED_SURFACES',len(objects)","print('COOLING_BAKED_SURFACES',material_name,len(objects)")
s=s.replace('bake_lower_surfaces()',"bake_cooling_surfaces('COOL_lower_black_storage_enamel','lowerDrive','COOL_lower_cast')\nbake_cooling_surfaces('COOL_upper_cast_alloy','upperGearbox','COOL_upper_cast')")
p.write_text(s)
