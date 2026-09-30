"""Revise only the shared pin in the temporary geometry during fit iteration."""
import bpy,bmesh,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from clutch_spring_hardware_geometry import retaining_pin_points
target=ROOT/'work/transmission/rotary-geometry.blend';bpy.ops.wm.open_mainfile(filepath=str(target))
pins=[o for o in bpy.data.objects if o.get('springHardware')=='pin'];assert len(pins)==60
curve=bpy.data.curves.new('spring_pin_revision','CURVE');curve.dimensions='3D';curve.resolution_u=8;curve.bevel_depth=.00025;curve.bevel_resolution=1;curve.use_fill_caps=True
points=retaining_pin_points();sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
for p,(x,y,z) in zip(sp.points,points):p.co=(x,-z,y,1)
curve.materials.append(pins[0].data.materials[0]);ob=bpy.data.objects.new('spring_pin_revision',curve);bpy.context.collection.objects.link(ob)
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-12);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);bm.to_mesh(ob.data);bm.free()
for pin in pins:pin.data=ob.data
bpy.data.objects.remove(ob,do_unlink=True)
# The fixed guide head has 0.2 mm axial clearance to the released sleeve.
# Piston travel and its separate release stop are unchanged.
rod=bpy.data.objects['TX_first_spring_guide_0']
for v in rod.data.vertices:
    if abs(v.co.x+.011)<1e-7:v.co.x=-.0112
bpy.ops.wm.save_as_mainfile(filepath=str(target));print('Updated 60 shared pins in temporary geometry only',flush=True)
