"""Constrained planar triangulation for the photographed cab lower relief."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon,LineString
from shapely.ops import split
from shapely import constrained_delaunay_triangles

def rounded(points,radius,steps):
    result=[]
    for i,(x,y) in enumerate(points):
        before=points[i-1];after=points[(i+1)%len(points)]
        a=math.dist(before,(x,y));b=math.dist(after,(x,y));r=min(radius,a*.25,b*.25)
        p=(x+(before[0]-x)*r/a,y+(before[1]-y)*r/a);q=(x+(after[0]-x)*r/b,y+(after[1]-y)*r/b)
        for k in range(steps+1):
            t=k/steps;result.append(((1-t)**2*p[0]+2*(1-t)*t*x+t*t*q[0],(1-t)**2*p[1]+2*(1-t)*t*y+t*t*q[1]))
    return result
outer=rounded([(.08,2.66),(.85,2.66),(.97,2.53),(.99,1.29),(.88,1.17),(.21,1.17),(.21,1.90),(.04,2.30)],.065,6)
inner=rounded([(.16,2.54),(.80,2.54),(.86,2.45),(.90,2.07),(.83,2.015),(.32,2.015),(.13,2.23),(.13,2.43)],.055,6)
panel=Polygon(outer,[inner]);assert panel.is_valid
pieces=split(panel,LineString([(-1,1.94),(2,1.94)]));vs=[];fs=[];lookup={};area=0
def index(p,depth):
    key=(round(p[0],9),round(p[1],9),depth)
    if key not in lookup:lookup[key]=len(vs);vs.append([p[0],p[1],depth])
    return lookup[key]
for piece in pieces.geoms:
    for tri in constrained_delaunay_triangles(piece).geoms:
        area+=tri.area;points=list(tri.exterior.coords)[:3]
        fs.append([index(p,0) for p in points]);fs.append([index(p,-.045) for p in reversed(points)])
for ring in [outer,inner]:
    boundary=[]
    for a,b in zip(ring,ring[1:]+ring[:1]):
        boundary.append(a)
        if (a[1]-1.94)*(b[1]-1.94)<0:
            f=(1.94-a[1])/(b[1]-a[1]);boundary.append((a[0]+f*(b[0]-a[0]),1.94))
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):fs.append([index(a,0),index(b,0),index(b,-.045),index(a,-.045)])
assert abs(area-panel.area)<1e-10
edges={}
for f in fs:
    for a,b in zip(f,f[1:]+f[:1]):
        e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
assert all(n==2 for n in edges.values()),'Unclosed panel triangulation'
(ROOT/'work/cab-front-profile.json').write_text(json.dumps({'vertices':vs,'faces':fs,'area':area,'nonManifoldEdges':0}))
print('CAB_PANEL_PREPARED',len(vs),'vertices',len(fs),'faces; area',area)
