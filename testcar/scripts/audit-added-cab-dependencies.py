"""Fail-closed dependency audit of the145 newly included original-cab objects.

Reuses the exact reviewed guard functions without executing its older261-scope
workflow. NODES and SUBSURF remain explicitly unsupported; their native settings
and node graphs are inventoried for a subsequent narrowly reviewed extension.
"""
import ast, bpy, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'outputs/cloud-va180-panel-fit-20261001/MAZ543A_Master.blend'
SCOPE = ROOT/'work/cloud-original-cab-contact-location-20261001/location-report.json'
DOORS = ROOT/'work/cloud-cab-door-dependencies-20261001/inventory.json'
GUARD = ROOT/'scripts/audit-candidate-cab-static-dependencies.py'
OUT = ROOT/'work/cloud-added-cab-dependencies-20261001'
OUT.mkdir(parents=True,exist_ok=True)
EXPECTED = '8e962d6dc2565974be8a0e96930606599ddbf6098780951dc96cbb9e13e3fd70'
sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==EXPECTED and bpy.app.version[:3]==(4,5,13)
scope,doors = (json.loads(p.read_text()) for p in (SCOPE,DOORS))
assert scope['source_sha256']==doors['source_sha256']==EXPECTED
names=scope['fixed_names']; assert len(names)==len(set(names))==145
assert not set(names)&{x['name'] for x in doors['fixed_geometry']}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
BUTTON='VA180 B4 / BUTTON PRESS REVIEW — travel is fitted'
moving={o.name for d in doors['doors'] for o in [bpy.data.objects[d['hinge']],*bpy.data.objects[d['hinge']].children_recursive]}
checks={};cache={};exceptions=[]
functions=['structural_transform_issues','held_button_driver','audit']
tree=ast.parse(GUARD.read_text());selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions]
assert [n.name for n in selected]==functions
exec(compile(ast.Module(body=selected,type_ignores=[]),str(GUARD),'exec'),globals())
fixed=[{'name':name,'issues':audit(bpy.data.objects[name])} for name in names]
issues=sorted({i for row in fixed for i in row['issues']})

def value(v):
    if isinstance(v,bpy.types.ID):return {'id_type':v.bl_rna.identifier,'id_name':v.name,'library':v.library.filepath if v.library else None}
    if v is None or isinstance(v,(str,bool,int,float)):return v
    try:return [value(x) for x in v]
    except TypeError:return {'rna_type':getattr(getattr(v,'bl_rna',None),'identifier',type(v).__name__)}

def animation(block):
    ad=getattr(block,'animation_data',None)
    if not ad:return None
    return {'action':ad.action.name if ad.action else None,'nla_tracks':len(ad.nla_tracks),
            'drivers':[{'data_path':f.data_path,'array_index':f.array_index,'expression':f.driver.expression,
                        'variables':[{'name':v.name,'type':v.type,'targets':[{'id':value(t.id),'data_path':getattr(t,'data_path',None)} for t in v.targets]} for v in f.driver.variables]} for f in ad.drivers]}

node_trees={}
def inventory_tree(nt):
    if not nt:return None
    if nt.name in node_trees:return nt.name
    record={'name':nt.name,'type':nt.bl_idname,'library':nt.library.filepath if nt.library else None,
            'animation':animation(nt),'nodes':[],'links':[],'interface':[]}
    node_trees[nt.name]=record
    for item in nt.interface.items_tree:
        row={'name':item.name,'item_type':item.item_type,'identifier':getattr(item,'identifier',None)}
        for prop in ['in_out','socket_type','default_value','attribute_domain','hide_value']:
            if hasattr(item,prop):row[prop]=value(getattr(item,prop))
        record['interface'].append(row)
    for n in nt.nodes:
        row={'name':n.name,'type':n.bl_idname,'mute':n.mute,'properties':{},'inputs':[],'outputs':[]}
        for prop in n.bl_rna.properties:
            if prop.identifier in {'rna_type','name','label','location','dimensions','width','height','width_hidden','select','parent','inputs','outputs','internal_links','id_data'}:continue
            if prop.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER'}:
                try:row['properties'][prop.identifier]=value(getattr(n,prop.identifier))
                except (AttributeError,TypeError):row['properties'][prop.identifier]={'unreadable':True}
        for direction in ['inputs','outputs']:
            for socket in getattr(n,direction):
                row[direction].append({'name':socket.name,'identifier':socket.identifier,'type':socket.bl_idname,
                    'enabled':socket.enabled,'is_linked':socket.is_linked,
                    'default_value':value(getattr(socket,'default_value',None))})
        child=getattr(n,'node_tree',None)
        if child:row['nested_tree']=inventory_tree(child)
        record['nodes'].append(row)
    for link in nt.links:
        record['links'].append({'from_node':link.from_node.name,'from_socket':link.from_socket.identifier,
            'to_node':link.to_node.name,'to_socket':link.to_socket.identifier,'is_valid':link.is_valid,'is_muted':link.is_muted})
    return nt.name

unsupported=[]
def modifier_properties(m):
    try:return {k:value(m[k]) for k in m.keys()}
    except TypeError:return {'id_properties_supported':False}

for name in sorted({r['object'] for r in checks.values()}):
    o=bpy.data.objects[name]
    for m in o.modifiers:
        if not m.show_viewport or m.type not in {'NODES','SUBSURF'}:continue
        row={'object':name,'object_type':o.type,'parent':o.parent.name if o.parent else None,
             'modifier':m.name,'modifier_type':m.type,'show_viewport':m.show_viewport,'show_render':m.show_render,
             'object_animation':animation(o),'settings':{},'custom_properties':modifier_properties(m)}
        for prop in m.bl_rna.properties:
            if prop.identifier in {'rna_type','name','id_data','node_group'}:continue
            if prop.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER'}:
                try:row['settings'][prop.identifier]=value(getattr(m,prop.identifier))
                except (AttributeError,TypeError):row['settings'][prop.identifier]={'unreadable':True}
        if m.type=='NODES':row['node_tree']=inventory_tree(m.node_group)
        unsupported.append(row)

report={'status':'SCOPED_ADDED_CAB_DEPENDENCY_FAIL_CLOSED' if issues else 'SCOPED_ADDED_CAB_DEPENDENCY_ELIGIBLE',
        'source_sha256':EXPECTED,'source_sha256_after':sha(SOURCE),'scope_sha256':sha(SCOPE),'door_scope_sha256':sha(DOORS),
        'guard_sha256':sha(GUARD),'guard_functions_reused_unchanged':functions,
        'blender_version':bpy.app.version_string,'frame':0,'fixed':fixed,'dependency_checks':checks,
        'issues':issues,'unsupported_modifier_inventory':unsupported,'node_trees':node_trees,
        'source_saved':False,'geometry_modified':False,'eligibility_accepted':not issues,'whole_vehicle_acceptance':'16 OPEN',
        'limits':['Only the 145 selected fixed objects and their recursive references','NODES and SUBSURF are not whitelisted by being present or looking static',
                  'A node graph inventory does not itself prove eligibility','Prior frozen separation and sampled poses are not native continuous clearance']}
assert report['source_sha256_after']==EXPECTED
(OUT/'dependency-report.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
print('ADDED_DEPENDENCY',report['status'],'fixed',len(fixed),'checks',len(checks),'issues',len(issues),'unsupported',len(unsupported),flush=True)
for issue in issues:print('DEPENDENCY_OPEN',issue,flush=True)
for key,nt in node_trees.items():print('NODE_GRAPH',key,len(nt['nodes']),len(nt['links']),sorted({n['type'] for n in nt['nodes']}),flush=True)
