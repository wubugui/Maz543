"""Save and reopen the 38 discrete surface-contact equilibria, without dynamics."""
import bpy,bmesh,json,sys,math,runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from converter_strip_mesh import geometry
study=json.loads((ROOT/'work/freewheel-contact/strip-surface-verified-domain.json').read_text())
audit=json.loads((ROOT/'outputs/converter-strip-surface-verified-domain-native.json').read_text())
assert len(study['rows'])==38
assert len(audit['rows'])==38 and all(r['geometryValid'] for r in audit['rows'])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/MAZ543A_Converter_CurvedStripStudy.blend'))
old=bpy.data.objects['CS_curved_strip'];material=old.data.materials[0];root=old.parent
bpy.data.objects.remove(old,do_unlink=True)
root.animation_data_clear();roller=bpy.data.objects['CS_roller_12_5x22'];roller.animation_data_clear()
root['status']='38 independent fitted static surface-contact equilibria; no motion interpolation. Continuous solver remains incomplete.'
root['limits']='Interpreted curved strip. Unknown factory shape, material and clamp. Maximum incremental stress about 9.364 GPa invalidates any claim of demonstrated elastic operating range.'
anchor=study['rows'][0]['solution']['points'][0]
def transformed(vertices):return [(x,-(z-anchor[1]),y-anchor[0]) for x,y,z in vertices]
fit=study['fit'];rows=study['rows'];vertices,faces=geometry(rows[0]['solution']['points'],fit['widthM'],fit['thicknessM'])
mesh=bpy.data.meshes.new('CS_surface_strip');mesh.from_pydata(transformed(vertices),[],faces);mesh.materials.append(material)
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);assert bm.calc_volume()>0;bm.to_mesh(mesh);bm.free()
strip=bpy.data.objects.new('CS_curved_strip',mesh);bpy.context.scene.collection.objects.link(strip);strip.parent=root
strip.location=(0,-anchor[1],anchor[0])
strip.shape_key_add(name='Basis');strip.data.shape_keys.use_relative=False
for i,row in enumerate(rows):
    solution=row['solution'];vertices,_=geometry(solution['points'],fit['widthM'],fit['thicknessM'])
    block=strip.data.shape_keys.key_blocks[0] if i==0 else strip.shape_key_add(name=f'Surface_equilibrium_{i:02d}')
    for v,p in zip(block.data,transformed(vertices)):v.co=p
    block.interpolation='KEY_LINEAR';strip.data.shape_keys.eval_time=block.frame;strip.data.shape_keys.keyframe_insert('eval_time',frame=i)
    y,z=row['centreM'];roller.location=(0,-z,y);roller.keyframe_insert('location',frame=i)
    for name,value in [('beta_rad',row['betaRad']),('spring_force_N',solution['forceN']),('spring_energy_J',solution['energyJ']),('incremental_stress_Pa',solution['maximumIncrementalBendingStressPa']),('radial_clearance_fraction',row['radialClearanceFraction']),('roller_contact_count',len(solution['rollerContacts']))]:
        root[name]=value;root.keyframe_insert(data_path='["'+name+'"]',frame=i)
for animated in [root,roller,strip.data.shape_keys]:
    for curve in animated.animation_data.action.fcurves:
        for key in curve.keyframe_points:key.interpolation='CONSTANT'
text=bpy.data.texts.new('SURFACE_CONTACT_STATES_AND_LIMITS');text.write(json.dumps(study,ensure_ascii=False))
scene=bpy.context.scene;scene.frame_start=0;scene.frame_end=len(rows)-1;scene.render.fps=1;scene.frame_set(0)
target=ROOT/'outputs/MAZ543A_Converter_StripSurfaceStudy.blend'
assert not target.exists(),'Preserve any existing saved study'
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
runpy.run_path(str(ROOT/'scripts/verify-converter-strip-surface-saved.py'),run_name='__main__')
