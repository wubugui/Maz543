"""Fitted conical geometry; tooth counts are NOT established by the MAZ catalog."""
import json,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bevel_geometry import pair
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
p=pair(32,20,math.pi/2,.0038,.00006)
p['method']='Spherical involute with swept root relief; 32/20 counts and 3.8 mm module fitted to diagram envelope, not original specifications'
caps={}
for member,bore in [('A',.025),('B',.0175)]:
    outline=p[member];delta=p['delta' if member=='A' else 'Delta'];caps[member]=[]
    for scale in [p['innerScale'],1]:
        x=p['R']*scale*math.cos(delta);r=bore/x
        hole=[(r*math.cos(j*math.tau/96),r*math.sin(j*math.tau/96)) for j in range(96)]
        points=[tuple(v) for v in outline]+hole;ids={v:i for i,v in enumerate(points)};poly=Polygon(outline,[hole]);assert poly.is_valid
        caps[member].append([[ids[tuple(v)] for v in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(poly).geoms])
p['caps']=caps
(ROOT/'work/cooling-lower-bevel.json').write_text(json.dumps(p));print('COOLING_LOWER_PROFILES',p['gnomonicOverlap'],[len(p[k]) for k in ['A','B']],flush=True)
