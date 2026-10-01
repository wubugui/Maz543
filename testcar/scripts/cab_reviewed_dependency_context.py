"""Compose the unchanged strict dependency rules with one exact local clause.

The old checker stays intact. Its pinned functions are reused with a single
explicit unsupported-modifier branch extended for reviewed stationary profiles.
The caller must still bind the source SHA, frame, scope and view-layer domain.
"""
import ast, hashlib
from pathlib import Path
import bpy
import cab_static_local_modifier_guard as local_guard

BASE_PATH = Path(__file__).with_name('audit-candidate-cab-static-dependencies.py')
BASE_SHA256 = '0ca53737b57995ca86bc01612f60175e36cf2199d04edd55017f94ab1c9e1a51'

def make_context(moving):
    source = BASE_PATH.read_bytes().decode('utf-8')
    assert hashlib.sha256(source.encode('utf-8')).hexdigest() == BASE_SHA256
    old = "  else:issues.append(o.name+': unsupported active modifier '+m.type)"
    new = """  elif hinge is None and m.type in {'NODES','SUBSURF'}:
   local_issues=local_guard.modifier_issues(o,m,fixed_context=True,depsgraph_mode=bpy.context.evaluated_depsgraph_get().mode)
   local_modifier_checks.append({'object':o.name,'modifier':m.name,'type':m.type,'issues':local_issues})
   issues.extend(local_issues)
  else:issues.append(o.name+': unsupported active modifier '+m.type)"""
    assert source.count(old) == 1, 'Pinned unsupported branch not found exactly once'
    code = ast.parse(source.replace(old,new,1))
    names = ['structural_transform_issues','held_button_driver','audit']
    functions = [n for n in code.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert [n.name for n in functions] == names
    context = {'bpy':bpy,'local_guard':local_guard,
               'BUTTON':'VA180 B4 / BUTTON PRESS REVIEW — travel is fitted',
               'moving':set(moving),'checks':{},'cache':{},'exceptions':[],
               'local_modifier_checks':[]}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(BASE_PATH),'exec'),context)
    return context
