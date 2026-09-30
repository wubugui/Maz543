"""Triangulate conical gear ends without filling undercut root concavities."""
import json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
gears=json.loads((ROOT/'work/d12-poses.json').read_text())['timing']['gears']
profiles=json.loads((ROOT/'work/bevel-profiles.json').read_text());result={}
for id,g in gears.items():
 if g['kind']!='bevel':continue
 p=profiles[g['profile']];outline=p[g['member']];caps=[]
 delta=p['delta' if g['member']=='A' else 'Delta']
 for scale in [p['innerScale'],1]:
  R=p['R']*scale;x=R*math.cos(delta);r=g['bore']/x
  hole=[(r*math.cos(j*2*math.pi/96),r*math.sin(j*2*math.pi/96)) for j in range(96)]
  poly=Polygon(outline,[hole]);assert poly.is_valid,(id,'bore outside root')
  points=[tuple(v) for v in outline]+hole;ids={v:i for i,v in enumerate(points)}
  faces=[[ids[tuple(v)] for v in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(poly).geoms]
  caps.append(faces)
 result[id]=caps
(ROOT/'work/timing-caps.json').write_text(json.dumps(result));print('TIMING_CAPS',len(result))
