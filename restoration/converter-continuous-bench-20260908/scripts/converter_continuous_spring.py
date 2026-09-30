"""Round-wire helix generated from the solver's physical coil length.
Local X is the roller axis. Shared mesh can be instanced around both rows.
"""
import math
from mathutils import Vector
SEGMENTS=160;SIDES=12
def geometry(fit,cy,cz,length):
    rho=fit['innerRadius']+fit['rollerRadius'];wire=fit['springWireRadius']
    base=Vector((0,rho,fit['springBaseZ']));axis=(Vector((0,cy,cz))-base).normalized()
    reference=-fit['springBaseZ']-fit['rollerRadius']-wire
    turn=math.tau*fit['springTurns'];radius=math.sqrt(fit['springRadius']**2+(reference**2-length**2)/turn**2)
    u=Vector((1,0,0));v=axis.cross(u).normalized();points=[]
    for i in range(SEGMENTS+1):
        t=i/SEGMENTS;a=turn*t;radial=math.cos(a)*u+math.sin(a)*v
        tangent=(length*axis+turn*radius*(-math.sin(a)*u+math.cos(a)*v)).normalized()
        normal=tangent.cross(radial).normalized();centre=base+t*length*axis+radius*radial
        for j in range(SIDES):
            b=math.tau*j/SIDES;points.append(tuple(centre+wire*(math.cos(b)*radial+math.sin(b)*normal)))
    faces=[]
    for i in range(SEGMENTS):
        for j in range(SIDES):
            a=i*SIDES+j;b=i*SIDES+(j+1)%SIDES;faces.append((a,b,b+SIDES,a+SIDES))
    faces += [tuple(range(SIDES-1,-1,-1)),tuple(SEGMENTS*SIDES+j for j in range(SIDES))]
    return points,faces
