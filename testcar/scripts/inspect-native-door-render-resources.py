import bpy,json,hashlib,sys,argparse,os
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);src=Path(a.candidate);out=Path(a.out)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
expected='3b230c12077828102776eb70e5e87aaa47b8b72f5e681589745ad8610a18c03f';assert sha(src)==expected
bpy.ops.wm.open_mainfile(filepath=str(src));assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
sc=bpy.context.scene;sc.frame_set(0);bpy.context.view_layer.update();cab=bpy.data.objects['cab'];scope=set(cab.children_recursive)|{cab};extra=[o for o in bpy.data.objects if o.type in {'MESH','CURVE','FONT','SURFACE','META'} and o not in scope and o.name.startswith(('cab_','BL_Front_','BL_Door_'))];scope.update(extra)
materials={m for o in scope if hasattr(o.data,'materials') for m in o.data.materials if m};image_use={}
def scan(nt,owner,seen):
 if not nt or nt.as_pointer() in seen:return
 seen.add(nt.as_pointer())
 for n in nt.nodes:
  if n.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} and n.image:image_use.setdefault(n.image.name,[]).append({'owner':owner,'node':n.name})
  if n.type=='GROUP':scan(n.node_tree,owner,seen)
for m in materials:scan(m.node_tree,m.name,set())
images=[]
for im in bpy.data.images:
 ab=bpy.path.abspath(im.filepath,library=im.library);packed=bool(im.packed_file or len(im.packed_files));external=im.source in {'FILE','MOVIE','SEQUENCE','TILED'} and not packed
 images.append({'name':im.name,'source':im.source,'filepath':im.filepath,'resolved':ab,'packed':packed,'external':external,'exists':os.path.isfile(ab) if external else None,'size':list(im.size),'in_scope_material_nodes':image_use.get(im.name,[])})
fonts=[]
for f in bpy.data.fonts:
 ab=bpy.path.abspath(f.filepath,library=f.library);builtin=f.filepath=='<builtin>';packed=bool(f.packed_file);external=not (builtin or packed)
 fonts.append({'name':f.name,'filepath':f.filepath,'resolved':ab,'builtin':builtin,'packed':packed,'external':external,'exists':os.path.isfile(ab) if external else None,'scope_objects':[o.name for o in scope if o.type=='FONT' and f in {o.data.font,o.data.font_bold,o.data.font_italic,o.data.font_bold_italic}]})
r={'status':'READ_ONLY_RESOURCE_AUDIT','candidate_sha256':expected,'autoexec_enabled':bpy.context.preferences.filepaths.use_scripts_auto_execute,'frame':sc.frame_current,'blender':bpy.app.version_string,'images':images,'fonts':fonts,'missing_images':[x for x in images if x['external'] and not x['exists']],'missing_fonts':[x for x in fonts if x['external'] and not x['exists']],'materials':sorted(m.name for m in materials),'root_descendants':len(cab.children_recursive),'included_extra_geometry':sorted(o.name for o in extra),'scope_geometry':[{'name':o.name,'type':o.type,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_get':o.hide_get(),'visible_camera':o.visible_camera,'materials':[m.name if m else None for m in o.data.materials],'bounds':[list(o.matrix_world@__import__('mathutils').Vector(v)) for v in o.bound_box]} for o in sorted(scope,key=lambda o:o.name) if o.type in {'MESH','CURVE','FONT','SURFACE','META'}],'libraries':[{'name':l.name,'filepath':l.filepath,'exists':os.path.isfile(bpy.path.abspath(l.filepath))} for l in bpy.data.libraries],'source_saved':False}
assert sha(src)==expected;r['candidate_sha256_after']=sha(src);out.write_text(json.dumps(r,indent=2)+'\n');print('AUDIT_WRITTEN',out,flush=True)
