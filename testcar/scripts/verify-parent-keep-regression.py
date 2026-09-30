"""Exercise the real legacy helper without executing the full vehicle generator.

Only isolates its AST function definition; no replacement helper is substituted.
Uses disposable native primitives/fonts and never opens or rewrites vehicle files.
"""
import ast, bpy, json, math, os
from pathlib import Path
from mathutils import Matrix, Vector, Euler
source=Path(__file__).with_name('blender-model.py')
module=ast.parse(source.read_text())
function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='parent_keep')
namespace={'bpy':bpy}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
helper=namespace['parent_keep']
bpy.ops.wm.read_factory_settings(use_empty=True)
parent=bpy.data.objects.new('RegressionParent',None);bpy.context.collection.objects.link(parent)
parent.location=(2.42,-1.24,.72);parent.rotation_euler=(.12,-.24,.31)
rows=[]
for kind,as_name in [('FONT',False),('FONT',True),('MESH',False),('CURVE',True)]:
    if kind=='FONT':
        data=bpy.data.curves.new('RegressionFont','FONT');data.body='VI-203'
    elif kind=='CURVE':
        data=bpy.data.curves.new('RegressionCurve','CURVE');data.dimensions='3D'
        s=data.splines.new('POLY');s.points.add(1);s.points[0].co=(0,0,0,1);s.points[1].co=(1,0,0,1)
    else:
        bpy.ops.mesh.primitive_cube_add();data=bpy.context.object.data.copy();bpy.data.objects.remove(bpy.context.object,do_unlink=True)
    obj=bpy.data.objects.new('Regression_'+kind,data);bpy.context.collection.objects.link(obj)
    # Deliberately leave the newly assigned transform unevaluated, as the old producer did.
    location=Vector((2.68,-1.547,.93));rotation=Euler((1.2,.3,-.7));scale=Vector((1.,1.,1.))
    obj.location=location;obj.rotation_euler=rotation;obj.scale=scale
    expected=Matrix.LocRotScale(location,rotation.to_quaternion(),scale)
    helper(obj,parent.name if as_name else parent)
    bpy.context.view_layer.update()
    error=max(abs(obj.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))
    rows.append({'kind':kind,'parent_by_name':as_name,'world_matrix_max_abs_error':error})
report={'source':str(source.relative_to(source.parents[2])),'checks':rows,'threshold':2e-6,'passed':all(r['world_matrix_max_abs_error']<2e-6 for r in rows),'scope':'Disposable native objects; actual helper AST only; no full generator run or vehicle acceptance.'}
Path(os.environ['MAZ_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
if not report['passed']:raise RuntimeError('Real parent_keep failed freshly assigned transform retention')
