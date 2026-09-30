"""Reconstructed spur/internal involutes. No factory tooth or cutter claim."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/pythonlibs'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
from math import sin,cos,pi,acos,tan

def outline(teeth,module,internal=False,thin=.000025):
    rp=module*teeth/2;rb=rp*cos(pi/9);iv=tan(pi/9)-pi/9
    tip=rp-module if internal else rp+module
    root=rp+1.25*module if internal else rp-1.25*module
    points=[]
    for k in range(teeth):
        a=2*pi*k/teeth
        points.append((root*cos(a-pi/teeth),root*sin(a-pi/teeth)))
        radii=[root+(tip-root)*j/16 for j in range(17)]
        for sign,rr in [(-1,radii),(1,list(reversed(radii)))]:
            for r in rr:
                t=acos(min(1,rb/r));inv=tan(t)-t
                half=pi/(2*teeth)+(inv-iv if internal else iv-inv)
                half-=thin/rp
                angle=a+sign*half
                points.append((r*cos(angle),r*sin(angle)))
    poly=Polygon(points)
    assert poly.is_valid
    return poly

def annulus_data(outside,inside):
    exterior=list(outside.exterior.coords)[:-1]
    interior=list(inside.exterior.coords)[:-1]
    poly=Polygon(exterior,[interior]);assert poly.is_valid
    points=exterior+interior;ids={tuple(p):i for i,p in enumerate(points)}
    cap=[[ids[tuple(p)] for p in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(poly).geoms]
    return points,cap,len(exterior)

def circle(radius,n=96):return Polygon([(radius*cos(j*2*pi/n),radius*sin(j*2*pi/n)) for j in range(n)])
