"""Relocate the existing photo-fitted searchlight; preserve authored topology/UVs.

Run only through the MAZ543 Hub, with the two original native files as inputs.
The destination is a photographic fit, not an original factory dimension.
"""
import bpy, json, os, hashlib
from pathlib import Path
from mathutils import Vector

OUT = Path(os.environ['HUB_OUTPUT_DIR'])
DELTA = Vector((-1.60, -1.93, 0.0))  # Blender Z up; browser left becomes +Z.
OLD = {'housing':(512, (-3.51, 2.755, -1.15), (-3.33, 2.995, -.91)),
       'lens':(512, (-3.527, 2.772, -1.133), (-3.517, 2.978, -.927)),
       'stand':(256, (-3.455, 2.665, -1.065), (-3.385, 2.815, -.995))}

def bounds(obj, indices=None):
    vertices = obj.data.vertices if indices is None else [obj.data.vertices[i] for i in indices]
    ps = [obj.matrix_world @ v.co for v in vertices]
    ps = [[p.x,p.z,-p.y] for p in ps]
    return {'min':[min(p[i] for p in ps) for i in range(3)],
            'max':[max(p[i] for p in ps) for i in range(3)]}

def components(obj):
    neighbors=[[] for v in obj.data.vertices]
    for e in obj.data.edges:
        a,b=e.vertices;neighbors[a].append(b);neighbors[b].append(a)
    seen=set()
    for i in range(len(neighbors)):
        if i in seen:continue
        stack=[i];seen.add(i);ids=[]
        while stack:
            j=stack.pop();ids.append(j)
            for k in neighbors[j]:
                if k not in seen:seen.add(k);stack.append(k)
        yield ids

def same_bounds(actual,lo,hi):
    return max(abs(a-b) for a,b in zip(actual['min']+actual['max'],list(lo)+list(hi))) < 1e-5

def move(obj):
    old=obj.matrix_world.copy()
    obj.parent=bpy.data.objects['cab_pivot_005']
    obj.matrix_world=old
    obj.matrix_world.translation += DELTA
    obj['searchlightPlacement']='Driver-side front roof edge; photographic fit, exact dimensions uncalibrated'
    bpy.context.view_layer.update()

report={'scope':'Searchlight relocation only; 16 full vehicle gates OPEN',
        'source':'museum-front.jpg / museum-front-oblique.jpg; MAZ543A photo set',
        'destinationBrowserCenter':[-5.02,2.875,.90],
        'dimensionStatus':'photo-fitted, not factory calibrated','files':[]}

for filename in ['MAZ543A_Master.blend','MAZ543A_Textured.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(Path(filename).resolve()))
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()
    before={o.name:o.matrix_world.copy() for o in bpy.data.objects}
    row={'file':filename,'parts':[]}
    if filename.endswith('Master.blend'):
        targets=[bpy.data.objects['BL_Searchlight_'+name] for name in OLD]
    else:
        found={}
        for obj in list(bpy.data.objects):
            if obj.type!='MESH' or obj.parent!=bpy.data.objects['cab_pivot_001']:continue
            for ids in components(obj):
                for kind,(count,lo,hi) in OLD.items():
                    if len(ids)==count and same_bounds(bounds(obj,ids),lo,hi):
                        assert kind not in found,('ambiguous',kind)
                        found[kind]=(obj,ids)
        assert set(found)==set(OLD),list(found)
        targets=[]
        for kind,(obj,ids) in found.items():
            bpy.ops.object.select_all(action='DESELECT')
            obj.hide_set(False);obj.select_set(True);bpy.context.view_layer.objects.active=obj
            # Blender's native Separate retains UVs, material slots and corner normals.
            chosen=set(ids)
            for v in obj.data.vertices:v.select=v.index in chosen
            for e in obj.data.edges:e.select=all(i in chosen for i in e.vertices)
            for p in obj.data.polygons:p.select=all(i in chosen for i in p.vertices)
            existing=set(bpy.data.objects)
            bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
            new=set(bpy.data.objects)-existing
            assert len(new)==1,(kind,len(new))
            part=new.pop();part.name='BL_Searchlight_'+kind;targets.append(part)
    for obj in targets:
        b0=bounds(obj);uv_before=[tuple(v.uv) for l in obj.data.uv_layers for v in l.data]
        vertices_before=[tuple(v.co) for v in obj.data.vertices]
        move(obj)
        assert vertices_before==[tuple(v.co) for v in obj.data.vertices]
        assert uv_before==[tuple(v.uv) for l in obj.data.uv_layers for v in l.data]
        b1=bounds(obj)
        for i,d in enumerate([-1.6,0,1.93]):
            for key in ['min','max']:assert abs(b1[key][i]-b0[key][i]-d)<2e-6
        row['parts'].append({'name':obj.name,'parent':obj.parent.name,'before':b0,'after':b1,'vertices':len(obj.data.vertices),'uvUnchanged':True,'localGeometryUnchanged':True})
    changed={o.name for o in targets}
    for name,m in before.items():
        if name not in changed:assert bpy.data.objects[name].matrix_world==m,name
    row['otherObjectTransformsUnchanged']=True
    note=bpy.data.texts.get('SEARCHLIGHT_PLACEMENT_20260930.md') or bpy.data.texts.new('SEARCHLIGHT_PLACEMENT_20260930.md')
    note.clear();note.write('Existing searchlight moved as one rigid assembly from right/rear to left/front roof. Native topology, materials and UVs retained. Destination is fitted to photographs, not a measured factory dimension. No optical/electrical operation acceptance. Baked AO still needs review after relocation. All 16 whole vehicle gates remain OPEN.')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/filename),compress=True)
    report['files'].append(row)
    if filename.endswith('Textured.blend'):
        excluded={'D12A_525A','S543_COOLING','S543_SUSPENSION','S543_STARTING','C5_STARTER','C5_FLYWHEEL_RING','MZN_PREOIL','STARTING_ENGINE_MOUNT','S543_CARDAN','S543_TRANSMISSION'}
        def allowed(o):
            while o:
                if o.name in excluded:return False
                o=o.parent
            return True
        root=bpy.data.objects['MAZ543_REFERENCE_CHASSIS']
        def descendants(o):
            for c in o.children:yield c;yield from descendants(c)
        bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
        selected=[o for o in descendants(root) if allowed(o)]
        for o in selected:o.hide_set(False);o.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.ops.export_scene.gltf(filepath=str(OUT/'maz543a-blender.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_extras=True,export_animations=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
        report['exportSelectedObjects']=len(selected)+1

(OUT/'searchlight-correction-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('SEARCHLIGHT_CORRECTION_VERIFIED',flush=True)
