"""Re-cap the fitted lower pair for the upper gearbox's 35 mm gear shaft."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
p=json.loads((ROOT/'work/cooling-lower-bevel.json').read_text())
for member in ['A','B']:
    outline=p[member];delta=p['delta' if member=='A' else 'Delta'];p['caps'][member]=[]
    for scale in [p['innerScale'],1]:
        x=p['R']*scale*math.cos(delta);r=.0175/x
        hole=[(r*math.cos(j*math.tau/96),r*math.sin(j*math.tau/96)) for j in range(96)]
        points=[tuple(v) for v in outline]+hole;ids={v:i for i,v in enumerate(points)};poly=Polygon(outline,[hole]);assert poly.is_valid
        p['caps'][member].append([[ids[tuple(v)] for v in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(poly).geoms])
p['method']='Fitted 20:32 upper pair; no original tooth-count claim. 35 mm journal nominal envelope from parts catalog.'
(ROOT/'work/cooling-upper-bevel.json').write_text(json.dumps(p));print('UPPER_CAPS_READY')
