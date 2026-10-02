"""Read actual original node graphs only; no frame advance, construction or save."""
import ast,hashlib,importlib.util,json,math,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
import numpy as np
repo=Path('/workspace/scratch/a29d03198654/Maz543')
source=repo/'testcar/outputs/cloud-va180-textured-20261001/MAZ543A_Textured.blend'
expected='6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266'
out=Path(sys.argv[sys.argv.index('--')+1]);sha=lambda b:hashlib.sha256(b).hexdigest()
report={'status':'READ_IN_PROGRESS','source_sha256':expected,'constructed':False,'saved_model':False,'rendered':False,'timeline_advanced':False}
try:
 assert source.stat().st_size==99960163 and sha(source.read_bytes())==expected
 assert bpy.app.version==(4,5,13) and bpy.app.build_hash==b'daeeeca98fb0'
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 helper=Path('/workspace/scratch/a29d03198654/maz-textured-front-wheel-trial-20261002/intake-helper-source.py')
 assert sha(helper.read_bytes())=='e093cb1f0d1f66d3c399b345daea9f6d563abceee940d0f64c8f49e7f97aa289'
 H=dict(bpy=bpy,np=np,json=json,math=math,hashlib=hashlib,sha=sha,issues=[])
 tree=ast.parse(helper.read_bytes());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='main'],type_ignores=[]),str(helper),'exec'),H)
 guard_path=repo/'testcar/scripts/cab_static_local_modifier_guard.py'
 assert sha(guard_path.read_bytes())=='dc94191941cb254961727831399177eec2a064b8c1964b1b458dcbcba66c63ed'
 spec=importlib.util.spec_from_file_location('cab_static_graph_read_guard',guard_path);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
 bpy.ops.wm.open_mainfile(filepath=str(source));assert bpy.context.scene.frame_current==0 and bpy.context.scene.frame_subframe==0;bpy.context.view_layer.update()
 ident={o.name:o.as_pointer() for o in bpy.data.objects};matrices={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects}
 def ad(block):
  a=getattr(block,'animation_data',None)
  if a is None:return None
  return {'action':a.action.name if a.action else None,'action_paths':[(f.data_path,f.array_index) for f in H['curves_of'](a.action)] if a.action else [],'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'simple':f.driver.is_simple_expression} for f in a.drivers],'nla':len(a.nla_tracks)}
 def node_tree(t,seen):
  assert t and t.as_pointer() not in seen,'Missing/cyclic nested node tree'
  seen=seen|{t.as_pointer()}
  record=H['node_tree_record'](t)
  record.update(animation=ad(t),interface=[H['rna_values'](x) for x in t.interface.items_tree],custom={k:H['value_record'](t[k]) for k in t.keys()},linked_library=t.library.filepath if t.library else None)
  record['nested']={n.name:node_tree(n.node_tree,seen) for n in t.nodes if getattr(n,'node_tree',None)}
  record['node_type_counts']={typ:sum(n.bl_idname==typ for n in t.nodes) for typ in sorted({n.bl_idname for n in t.nodes})}
  return record
 rows=[]
 for o in bpy.data.objects:
  for m in o.modifiers:
   if m.type!='NODES':continue
   rows.append({'object':o.name,'object_animation':ad(o),'data_animation':ad(o.data),'parent':o.parent.name if o.parent else None,'constraints':[H['rna_values'](x) for x in o.constraints],
    'modifier':H['rna_values'](m),'modifier_custom':{k:H['value_record'](m[k]) for k in m.keys()},'bakes':len(m.bakes),'node_group':node_tree(m.node_group,set()),
    'existing_stationary_modifier_clause_only':guard.modifier_issues(o,m,fixed_context=True,depsgraph_mode='VIEWPORT')})
 assert len(rows)==9,len(rows)
 report.update(nodes=rows,scene_animation=ad(bpy.context.scene),handlers={n:len(getattr(bpy.app.handlers,n)) for n in ['frame_change_pre','frame_change_post','depsgraph_update_pre','depsgraph_update_post']},cache_files=[x.name for x in bpy.data.cache_files],rigidbody_world=bool(bpy.context.scene.rigidbody_world),rna_issues=H['issues'])
 assert not H['issues'],H['issues']
 assert ident=={o.name:o.as_pointer() for o in bpy.data.objects} and matrices=={o.name:[list(r) for r in o.matrix_world] for o in bpy.data.objects}
 assert sha(source.read_bytes())==expected
 report.update(status='ACTUAL_NODE_READ_COMPLETE_NO_TIMELINE_QUALIFICATION',source_unchanged=True,original_object_identity_and_matrices_unchanged=len(ident),scope_limit='Existing stationary modifier results are local clauses only, not whole-object/upstream or arbitrary-frame qualifications. Actual graph records do not by themselves authorize timeline execution.')
except BaseException as exc:
 report.update(status='NODE_READ_FAILED',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc());out.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n');raise
else:
 out.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n');print(report['status'],flush=True)
