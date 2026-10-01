"""Prove the tyre operation preserved the rest of the current hood candidate."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'outputs/cloud-cover-contour-20261001';OUT=ROOT/'outputs/cloud-hood-tyre-composite-20261001'
repair=json.loads((OUT/'lettering-verification.json').read_text());rows=[]
def uv_hashes(mesh):
    result={}
    for layer in mesh.uv_layers:
        a=np.full(len(layer.uv)*2,np.nan,dtype=np.float32);layer.uv.foreach_get('vector',a)
        assert np.isfinite(a).all(),('Invalid UV data',layer.name)
        result[layer.name]=hashlib.sha256(a.tobytes()).hexdigest()
    return result
def modifier_inputs(o):
    def value(v):
        if v is None or isinstance(v,(str,bool,int,float)):return v
        if isinstance(v,bpy.types.ID):return {'id_type':v.bl_rna.identifier,'name':v.name}
        try:return [value(x) for x in v]
        except TypeError:return str(v)
    rows=[]
    for m in o.modifiers:
        props={p.identifier:value(getattr(m,p.identifier)) for p in m.bl_rna.properties if not p.is_readonly}
        # Geometry Nodes modifiers own socket IDProperties; ordinary modifier
        # RNA types need not support IDProperties at all.
        custom={k:value(v) for k,v in m.items() if not k.startswith('_')} if m.type=='NODES' else None
        rows.append({'type':m.type,'name':m.name,'editable_properties':props,'custom_inputs':custom})
    return rows
def snapshot_all():
    dg=bpy.context.evaluated_depsgraph_get();result={}
    for o in bpy.context.scene.objects:
        if o.type not in {'MESH','CURVE','SURFACE','FONT'}:continue
        e=o.evaluated_get(dg);m=e.to_mesh(preserve_all_data_layers=True,depsgraph=dg);m.calc_loop_triangles();h=hashlib.sha256()
        v=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',v);h.update(v.tobytes())
        t=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',t);h.update(t.tobytes())
        result[o.name]={'object_type':o.type,'modifier_inputs':modifier_inputs(o),'authored_mesh_uv_layer_sha256':uv_hashes(o.data) if o.type=='MESH' else None,'evaluated_local_position_triangle_sha256':h.hexdigest(),'matrix_world':[list(r) for r in e.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'material_slots':[mat.name if mat else None for mat in o.data.materials],'evaluated_uv_layer_sha256':uv_hashes(m),'vertices':len(m.vertices),'triangles':len(m.loop_triangles)}
        e.to_mesh_clear()
    return result
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    source=SOURCE/filename;candidate=OUT/filename;source_sha=hashlib.sha256(source.read_bytes()).hexdigest();candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
    assert source_sha==repair['input_native_sha256'][filename]
    bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();original=snapshot_all()
    bpy.ops.wm.open_mainfile(filepath=str(candidate));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();current=snapshot_all()
    if filename=='MAZ543A_Master.blend':allowed={n for n in original if n.startswith('BL_Tyre_') and '_emboss_' in n};assert len(allowed)==144
    else:allowed={r['mesh'] for r in repair['oldGlyphTrianglesRemoved']};assert len(allowed)==8
    mismatches=[];derived_uv_differences=[]
    for name,old in original.items():
        if name in allowed:continue
        actual=current.get(name,{})
        if any(actual.get(k)!=v for k,v in old.items() if k!='evaluated_uv_layer_sha256'):mismatches.append(name)
        if actual.get('evaluated_uv_layer_sha256')!=old['evaluated_uv_layer_sha256']:derived_uv_differences.append(name)
    if mismatches:
        (OUT/(filename+'.preservation-field-differences.json')).write_text(json.dumps({n:{k:{'source':v,'candidate':current.get(n,{}).get(k)} for k,v in original[n].items() if current.get(n,{}).get(k)!=v} for n in mismatches},indent=2))
    glyphs=[]
    for name,o in sorted(bpy.data.objects.items()):
        if not (name.startswith('BL_Tyre_') and '_emboss_' in name):continue
        index=int(o['tyreIndex']);expected=f'wheels_pivot_{2+7*index:03d}'
        assert index==int(name.split('_')[2])
        assert o.parent and o.parent.name==expected,(name,o.parent.name if o.parent else None)
        glyphs.append({'name':name,'wheel':index,'actual_spin_parent':o.parent.name})
    for name in ['BL_Front_cover_front_panel','BL_Photo_front_cover_top_grip_-1','BL_Photo_front_cover_top_grip_1']:
        assert name not in allowed and name not in mismatches,name
    row={'file':filename,'source_sha256':source_sha,'candidate_sha256':candidate_sha,'status':'FAIL_DERIVED_UV_BITWISE_PRESERVATION' if derived_uv_differences else 'PASS_SCOPED_PRESERVATION','explicitly_changed_original_objects':sorted(allowed),'unchanged_original_geometry_objects':len(original)-len(allowed),'unrelated_geometry_authored_uv_modifier_input_material_slot_or_parent_changes':mismatches,'derived_uv_bitwise_differences':derived_uv_differences,'new_glyph_hierarchy':glyphs,'source_and_candidate_bytes_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_sha and hashlib.sha256(candidate.read_bytes()).hexdigest()==candidate_sha,'scope':'Evaluated positions/triangles, object transforms/parents/render visibility, authored UVs, editable modifier inputs and material slot names outside typography scope. Derived UV bitwise differences remain a separate FAIL; no relaxed numeric threshold. Not every shader property, runtime behavior or factory calibration.','all16VehicleGates':'OPEN'}
    rows.append(row);(OUT/'integration-preservation.json').write_text(json.dumps(rows,indent=2))
    assert not mismatches,mismatches
    assert len(glyphs)==144 and row['source_and_candidate_bytes_unchanged']
    assert all(sum(g['wheel']==index for g in glyphs)==18 for index in range(8))
    print('HOOD_TYRE_GEOMETRY_INPUTS_PRESERVED',filename,row['unchanged_original_geometry_objects'],'objects;derivedUVbitwiseDifferences',len(derived_uv_differences),flush=True)
# Preserve the original strict failure condition, after recording both files.
assert not any(r['derived_uv_bitwise_differences'] for r in rows),'Derived UV exact bitwise preservation remains unresolved; see same-source repeat controls'
