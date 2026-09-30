"""Independent contact-area readback from saved Blender cap triangles."""
import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/('work/transmission' if '--geometry-only' in sys.argv else 'outputs')
data=json.loads((folder/'clutch-groove-native-caps.json').read_text(encoding='utf-8'))
profiles=json.loads((ROOT/'work/transmission/clutch-splines.json').read_text(encoding='utf-8'));rows=[]
def integral(a,b,c,depth=3):
    if depth:
        ab=tuple((x+y)/2 for x,y in zip(a,b));bc=tuple((x+y)/2 for x,y in zip(b,c));ca=tuple((x+y)/2 for x,y in zip(c,a))
        return sum(integral(*t,depth-1) for t in [(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
    area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
    return area*math.hypot((a[0]+b[0]+c[0])/3,(a[1]+b[1]+c[1])/3)
for name,caps in data.items():
    lands=unary_union([Polygon(t) for t in caps['landTriangles']]);steel=unary_union([Polygon(t) for t in caps['steelTriangles']])
    contact=lands.intersection(steel);moment=sum(integral(*list(t.exterior.coords)[:3]) for t in constrained_delaunay_triangles(contact).geoms)
    radius=moment/contact.area;expected=profiles[name]['frictionGrooved']['metrics']
    area_error=abs(contact.area-expected['area']);radius_error=abs(radius-expected['meanRadius'])
    assert area_error<2e-8,(name,area_error)
    assert radius_error<2e-7,(name,radius_error)
    rows.append({'pack':name,'nativeContactAreaM2':contact.area,'nativeMeanRadiusM':radius,'areaErrorM2':area_error,'radiusErrorM':radius_error})
report={'packs':rows,'limits':'Native face triangles intersected with native steel counterface; independent subdivided-centroid radius integration. Uniform land pressure is assumed, not measured.'}
(folder/'clutch-groove-area-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
