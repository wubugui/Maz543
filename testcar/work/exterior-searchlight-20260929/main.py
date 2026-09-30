import bpy, json, os
from pathlib import Path
from mathutils import Vector

out=Path(os.environ['HUB_OUTPUT_DIR'])
def y_up(v):return [v.x,v.z,-v.y]
def bounds(points):
    return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]} if points else None
report={'coordinate_system':'x front negative, y up, z vehicle left positive','files':[]}
for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()))
    bpy.context.view_layer.update()
    row={'file':filename,'objects':[],'lamp_region_components':[]}
    for obj in bpy.data.objects:
        if 'Searchlight' in obj.name or 'crowned_roof' in obj.name or obj.name in ['cab_pivot_001','cab_pivot_005']:
            row['objects'].append({'name':obj.name,'parent':obj.parent.name if obj.parent else None,'type':obj.type,'matrix_world':[list(r) for r in obj.matrix_world],'bounds':bounds([y_up(obj.matrix_world@Vector(v)) for v in obj.bound_box]) if obj.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type} for m in obj.modifiers]})
        if obj.type!='MESH':continue
        points=[y_up(obj.matrix_world@v.co) for v in obj.data.vertices]
        if not any(-3.7<p[0]<-3.1 and p[1]>2.66 and -1.25<p[2]<-.8 for p in points):continue
        neighbors=[[] for _ in points]
        for edge in obj.data.edges:
            a,b=edge.vertices;neighbors[a].append(b);neighbors[b].append(a)
        seen=set()
        for i,p in enumerate(points):
            if i in seen:continue
            stack=[i];seen.add(i);component=[]
            while stack:
                j=stack.pop();component.append(j)
                for k in neighbors[j]:
                    if k not in seen:seen.add(k);stack.append(k)
            ps=[points[j] for j in component]
            if any(-3.7<p[0]<-3.1 and p[1]>2.66 and -1.25<p[2]<-.8 for p in ps):
                row['lamp_region_components'].append({'object':obj.name,'parent':obj.parent.name if obj.parent else None,'vertices':len(component),'bounds':bounds(ps),'materials':[m.name for m in obj.data.materials]})
    report['files'].append(row)
(out/'searchlight-native-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('SEARCHLIGHT_AUDIT_COMPLETE',flush=True)
