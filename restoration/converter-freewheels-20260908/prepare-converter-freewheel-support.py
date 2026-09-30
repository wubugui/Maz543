"""Watertight flange section with bore and six mounting holes; workspace Python."""
from pathlib import Path
import math,json
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
ROOT=Path(__file__).resolve().parents[1]
def circle(r,n,cy=0,cz=0):return [(cy+r*math.cos(j*math.tau/n),cz+r*math.sin(j*math.tau/n)) for j in range(n)]
loops=[circle(.081,144),circle(.031,96)]
loops += [circle(.0026,32,.072*math.cos(j*math.pi/3),.072*math.sin(j*math.pi/3)) for j in range(6)]
p=Polygon(loops[0],loops[1:]);assert p.is_valid
points=[];indices={}
def index(v):
    key=tuple(round(a,12) for a in v)
    if key not in indices:indices[key]=len(points);points.append(v)
    return indices[key]
rings=[[index(v) for v in loop] for loop in loops]
caps=[];area=0
for tri in constrained_delaunay_triangles(p).geoms:
    assert p.covers(tri);area+=tri.area;caps.append([index(v) for v in list(tri.exterior.coords)[:-1]])
assert abs(area-p.area)<1e-12
out=ROOT/'work/transmission/converter-freewheel-support.json'
out.write_text(json.dumps({'points':points,'caps':caps,'rings':rings,'areaM2':area}),encoding='utf8')
print('Prepared',len(points),'section vertices',len(caps),'triangles')
