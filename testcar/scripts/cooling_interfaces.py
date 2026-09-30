"""Shared four-bolt fan-drive interface, reconstructed from catalog 13.5.

543-1308606 appears at both Cardan ends. Four holes are visible in the
exploded drawing; M8x1 fasteners are listed in installation 13.1. The 74 mm
PCD, 100 mm outside diameter and clearances below are fitted, not measured.
This does not establish compatibility between every MAZ-543 production year.
"""
import bpy
import bmesh
import math
from mathutils import Vector

PCD = .074
OUTER_RADIUS = .050
HOLE_RADIUS = .0043
SOURCE = 'MAZ-catalog-13.5 / 13.1; mating interface inferred for 543-1308606'
STATUS = 'Four holes source-visible; 74 mm PCD, 100 mm OD, 8.6 mm clearance, thickness and register fitted. Not measured CAD.'


def build_flange(name, parent, material, x0, x1, bore):
    n = 128
    vertices = []
    for x in [x0, x1]:
        for r in [OUTER_RADIUS, bore]:
            vertices += [(x, -r*math.sin(j*math.tau/n), r*math.cos(j*math.tau/n)) for j in range(n)]
    faces = []
    for j in range(n):
        k = (j+1) % n
        faces += [(j,k,k+2*n,j+2*n), (n+j,3*n+j,3*n+k,n+k),
                  (j,n+j,n+k,k), (2*n+j,2*n+k,3*n+k,3*n+j)]
    data = bpy.data.meshes.new(name+'_mesh')
    data.from_pydata(vertices, [], faces)
    data.update()
    bm=bmesh.new();bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data);bm.free()
    ob=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(ob)
    ob.parent=parent;data.materials.append(material)
    for j in range(4):
        a=math.pi/4+j*math.pi/2
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=HOLE_RADIUS, depth=(x1-x0)+.020)
        cut=bpy.context.object;cut.name='TEMP_cardan_bolt_drill'
        cut.parent=parent
        cut.location=Vector(((x0+x1)/2,-PCD/2*math.sin(a),PCD/2*math.cos(a)))
        cut.rotation_euler.y=math.pi/2
        bpy.context.view_layer.update()
        bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('Through drilled M8 clearance - fitted','BOOLEAN')
        mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cut,do_unlink=True)
    mod=ob.modifiers.new('Machined edge break - fitted','BEVEL')
    mod.width=.00045;mod.segments=3
    mod=ob.modifiers.new('Weighted machining normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    ob['sourceId']=SOURCE;ob['dimensionStatus']=STATUS
    ob['cardanInterface']=True;ob['boltHoles']=4;ob['fittedPCDmm']=PCD*1000
    ob['matingPart']='543-1308606';ob['fittedAxialFaces']=[x0,x1]
    ob['fittedBoreRadius']=bore
    return ob
