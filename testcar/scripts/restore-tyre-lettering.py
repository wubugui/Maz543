"""Scoped native typography repair; does not rebuild or promote the vehicle.

Existing VI-203 legend/size is retained as an authored reconstruction, not a
claim about a particular historical vehicle's tyre fitment. Native text sources
are preserved. Shrinkwrap/Solidify fit raised lettering to the existing tyre.
"""
import bpy,bmesh,json,math,collections,hashlib,os
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('MAZ_TYRE_INPUT_DIR',str(ROOT/'outputs'))).resolve()
OUT=Path(os.environ.get('MAZ_TYRE_RESTORE_OUTPUT_DIR',str(ROOT/'outputs/cloud-tyre-lettering-20260930'))).resolve()
if OUT in {SOURCE,(ROOT/'outputs').resolve(),(ROOT/'public/models').resolve()}:raise RuntimeError('Refusing source or production output directory')
OUT.mkdir(parents=True,exist_ok=True)
input_hashes={name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']}
LEGEND='1500x600-635  VI-203';EXPECTED=144

def C(p):return Vector((p[0],-p[2],p[1]))
def archive(obj,collection_name,world=None):
 if world is None:
  bpy.context.view_layer.update();world=obj.matrix_world.copy()
 obj.parent=None;obj.matrix_world=world
 col=bpy.data.collections.get(collection_name)
 if col is None:col=bpy.data.collections.new(collection_name);bpy.context.scene.collection.children.link(col)
 for collection in list(obj.users_collection):collection.objects.unlink(obj)
 col.objects.link(obj);obj.hide_render=True;obj.hide_set(True)
def world_triangles(obj,origin_only=False):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in m.vertices];counter=collections.Counter()
 for t in m.loop_triangles:
  if origin_only and not all(max(abs(v) for v in vs[j])<.1 for j in t.vertices):continue
  counter[tuple(sorted(tuple(round(float(v),6) for v in vs[j]) for j in t.vertices))]+=1
 ev.to_mesh_clear();return counter
def geometry_check(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();bm=bmesh.new();bm.from_mesh(m)
 result={'vertices':len(m.vertices),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)}
 bm.free();ev.to_mesh_clear();return result

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'MAZ543A_Master.blend'));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
fonts=sorted([o for o in bpy.data.objects if o.name.startswith('BL_Tyre_') and '_emboss_' in o.name],key=lambda o:o.name)
assert len(fonts)==EXPECTED and all(o.type=='FONT' for o in fonts)
old_triangles={i:collections.Counter() for i in range(8)};created=[];rows=[]
# Read all source geometry before modifying the dependency graph.
for old in fonts:old_triangles[int(old.name.split('_')[2])].update(world_triangles(old))
print('SOURCE_GLYPHS_AUDITED',len(fonts),flush=True)
for old in fonts:
 name=old.name;index=int(name.split('_')[2]);ci=int(name.rsplit('_',1)[1]);assert old.data.body==LEGEND[ci]
 oldWorld=old.matrix_world.copy();spin=old.parent;assert spin and spin.name==f'wheels_pivot_{2+7*index:03d}'
 side=1 if index%2 else -1;center=spin.matrix_world.translation;cx=center.x;cy=center.z;cz=-center.y
 angle=.40+(ci if side<0 else len(LEGEND)-1-ci)*.050
 tangent=C((-math.sin(angle),math.cos(angle),0))*(-side);radial=C((math.cos(angle),math.sin(angle),0));normal=tangent.cross(radial)
 assert normal.dot(C((0,0,side)))>.999,'Text must face outwards'
 desired=Matrix.Translation(C((cx+.525*math.cos(angle),cy+.525*math.sin(angle),cz+side*.307)))@Matrix((tangent,radial,normal)).transposed().to_4x4()
 old.name='ARCHIVE_ORIGIN_'+name;archive(old,'ARCHIVE_TYRE_TEXT_ORIGIN_20260930',oldWorld)
 source=old.copy();source.data=old.data.copy();bpy.context.scene.collection.objects.link(source);source.name='SOURCE_'+name;source.matrix_world=desired;source['authoredLegend']=LEGEND;source['dimensionStatus']='Existing authored font size and angular range; not factory-calibrated lettering';archive(source,'SOURCE_TYRE_TEXT_20260930',desired)
 obj=source.copy();obj.data=source.data.copy();bpy.context.scene.collection.objects.link(obj);obj.name=name;obj.hide_render=False;obj.hide_set(False);obj.matrix_world=desired;obj.data.extrude=0;obj.data.bevel_depth=0;obj['originalEmbossName']=name;obj['tyreIndex']=index;obj['restoration']='Restore lost transforms; actual tyre-surface fit; typography dimensions remain reconstructed'
 created.append(obj);rows.append({'name':name,'wheel':index,'character':LEGEND[ci],'source':source.name,'worldMatrix':[list(r) for r in desired]})
print('TEXT_SOURCES_POSITIONED',len(created),flush=True)
# Convert actual editable font outlines using Blender, then add engineering modifiers.
bpy.ops.object.select_all(action='DESELECT')
for obj in created:obj.select_set(True)
bpy.context.view_layer.objects.active=created[0];bpy.ops.object.convert(target='MESH');created=[bpy.data.objects[r['name']] for r in rows]
for obj in created:
 index=obj['tyreIndex'];world=obj.matrix_world.copy();obj.parent=bpy.data.objects[f'wheels_pivot_{2+7*index:03d}'];obj.matrix_world=world
 target=bpy.data.objects[f'BL_Tyre_{index}_VI203_profile'];m=obj.modifiers.new('Conform legend to actual sidewall','SHRINKWRAP');m.target=target;m.wrap_method='NEAREST_SURFACEPOINT';m.wrap_mode='ON_SURFACE';m.offset=-.00005
 m=obj.modifiers.new('Raised rubber legend thickness','SOLIDIFY');m.thickness=.00085;m.offset=1;m.use_even_offset=True
bpy.context.view_layer.update();print('GLYPH_MODIFIERS_EVALUATED',len(created),flush=True)
for row,obj in zip(rows,created):
 row['geometry']=geometry_check(obj)
 assert row['geometry']['vertices']>0 and row['geometry']['nonManifoldEdges']==0 and row['geometry']['volume']>0,row
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Master.blend'),compress=True)
# Read the just-saved master before exporting its evaluated geometry.
bpy.ops.wm.open_mainfile(filepath=str(OUT/'MAZ543A_Master.blend'));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();created=[bpy.data.objects[r['name']] for r in rows]
# Snapshot Blender's evaluated modifier result without reevaluating a duplicated
# Shrinkwrap object under a numerically different transform. This uses Blender's
# native evaluated-mesh API, not manually constructed coordinates or triangles.
exports=[];depsgraph=bpy.context.evaluated_depsgraph_get()
for obj in created:
 evaluated=obj.evaluated_get(depsgraph)
 mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=depsgraph)
 duplicate=bpy.data.objects.new('EXPORT_'+obj.name,mesh);bpy.context.scene.collection.objects.link(duplicate)
 duplicate.matrix_world=obj.matrix_world.copy();duplicate['originalEmbossName']=obj.name;duplicate['tyreIndex']=obj['tyreIndex'];exports.append(duplicate)
 # Capture the original local vertex values before another evaluation request.
 reference=evaluated.to_mesh();assert len(reference.vertices)==len(mesh.vertices)
 assert max((a.co-b.co).length for a,b in zip(reference.vertices,mesh.vertices))<1e-9,'Native snapshot differs from evaluated source'
 evaluated.to_mesh_clear()
bpy.context.view_layer.update()
bpy.data.libraries.write(str(OUT/'lettering-components.blend'),set(exports),compress=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'MAZ543A_Textured.blend'));bpy.context.scene.frame_set(0);bpy.context.view_layer.update();removed=[]
for index in range(8):
 spin=bpy.data.objects[f'wheels_pivot_{2+7*index:03d}'];candidates=[o for o in spin.children if o.type=='MESH'];observed=collections.Counter()
 for obj in candidates:observed.update(world_triangles(obj,True))
 assert observed==old_triangles[index],('Refuse to remove unmatched origin geometry',index,sum(observed.values()),sum(old_triangles[index].values()))
 for obj in candidates:
  ids={v.index for v in obj.data.vertices if max(abs(x) for x in obj.matrix_world@v.co)<.1}
  if not ids:continue
  assert all(all(v in ids for v in p.vertices) or all(v not in ids for v in p.vertices) for p in obj.data.polygons),'Selection cuts through a real polygon'
  before=world_triangles(obj);keep=before-world_triangles(obj,True)
  bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
  for v in obj.data.vertices:v.select=v.index in ids
  for e in obj.data.edges:e.select=all(v in ids for v in e.vertices)
  for p in obj.data.polygons:p.select=all(v in ids for v in p.vertices)
  prior=set(bpy.data.objects);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
  extracted=set(bpy.data.objects)-prior;assert len(extracted)==1
  old=extracted.pop();old.name='ARCHIVE_ORIGIN_'+obj.name;archive(old,'ARCHIVE_TYRE_TEXT_ORIGIN_20260930')
  assert world_triangles(obj)==keep,'Unrelated tyre geometry changed during native separation'
  removed.append({'wheel':index,'mesh':obj.name,'removedTriangles':sum(before.values())-sum(keep.values()),'unchangedOtherPositionTriangles':True})
with bpy.data.libraries.load(str(OUT/'lettering-components.blend'),link=False) as (available,incoming):incoming.objects=[o for o in available.objects if o.startswith('EXPORT_BL_Tyre_')]
assert len(incoming.objects)==EXPECTED
for obj in incoming.objects:bpy.context.scene.collection.objects.link(obj)
# Appended datablocks need graph evaluation before matrix_world is trustworthy.
bpy.context.view_layer.update();expectedMatrices={r['name']:Matrix(r['worldMatrix']) for r in rows}
for obj in incoming.objects:
 obj.name=obj['originalEmbossName'];world=obj.matrix_world.copy()
 assert max(abs(world[r][c]-expectedMatrices[obj.name][r][c]) for r in range(4) for c in range(4))<2e-6,('Appended glyph transform mismatch',obj.name)
 obj.parent=bpy.data.objects[f'wheels_pivot_{2+7*obj["tyreIndex"]:03d}'];obj.matrix_world=world
bpy.context.view_layer.update()
for obj in incoming.objects:assert max(abs(obj.matrix_world[r][c]-expectedMatrices[obj.name][r][c]) for r in range(4) for c in range(4))<2e-6,('Reparented glyph transform mismatch',obj.name)
assert len([o for o in bpy.data.objects if o.name.startswith('BL_Tyre_') and '_emboss_' in o.name])==EXPECTED
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MAZ543A_Textured.blend'),compress=True)
report={'status':'CANDIDATE_NOT_PROMOTED','legend':LEGEND,'glyphs':rows,'oldGlyphTrianglesRemoved':removed,'scope':'Only existing tyre legend transform/face direction/surface attachment; source fonts and old misplaced geometry retained; no tyre-size or historical-fitment calibration, no browser parity or whole-vehicle acceptance'}
assert all(hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest for name,digest in input_hashes.items()),'Input native files changed'
report['input_native_sha256']=input_hashes
report['input_native_directory']=str(SOURCE.relative_to(ROOT)) if SOURCE.is_relative_to(ROOT) else str(SOURCE)
report['input_files_unchanged']=True
(OUT/'lettering-verification.json').write_text(json.dumps(report,indent=2));print('TYPOGRAPHY_NATIVE_CANDIDATE',len(rows),len(removed))
