"""Watertight stepped friction surfaces from a noded planar subdivision.
Spiral/radial channels are source-specified; local dimensions are fitted.
"""
import math
from collections import defaultdict
from shapely.geometry import LineString
from shapely.ops import unary_union,polygonize
from shapely import constrained_delaunay_triangles,set_precision

def grooved_surface(footprint,steel,ri,ro,thickness,spec,depth,lining):
    half=thickness/2;floor=half-depth;core=half-lining
    assert 0<core<floor<half
    paths=[];cuts=[]
    for j in range(spec['radialCount']):
        a=(j+.37)*math.tau/spec['radialCount']
        points=[((ri-.004)*math.cos(a),(ri-.004)*math.sin(a)),((ro+.004)*math.cos(a),(ro+.004)*math.sin(a))]
        paths.append({'kind':'radial','points':points,'width':spec['radialWidth']})
        cuts.append(LineString(points).buffer(spec['radialWidth']/2,cap_style='flat'))
    # Extend past both open edges, with a constant Archimedean pitch.
    sweep=math.tau*spec['spiralTurns'];extension=.004/(ro-ri)
    count=spec['spiralTurns']*240
    points=[]
    for j in range(count+1):
        u=-extension+(1+2*extension)*j/count;r=ri+(ro-ri)*u;a=sweep*u
        points.append((r*math.cos(a),r*math.sin(a)))
    paths.append({'kind':'spiral','points':points,'width':spec['spiralWidth']})
    cuts.append(LineString(points).buffer(spec['spiralWidth']/2,cap_style='flat',join_style='mitre'))
    # One shared noded edge graph prevents T junctions between groove floors,
    # islands, steps and the splined plate perimeter.
    footprint=set_precision(footprint,1e-9);mask=set_precision(unary_union(cuts),1e-9)
    graph=unary_union([footprint.boundary,mask.boundary])
    cells=[p for p in polygonize(graph) if footprint.covers(p.representative_point())]
    cells.sort(key=lambda p:(p.centroid.x,p.centroid.y,p.area))
    heights=[floor if mask.covers(p.representative_point()) else half for p in cells]
    vertices=[];faces=[];materials=[];ids={};edges=defaultdict(list)
    def vertex(x,p):
        key=(round(x,10),round(p[0],10),round(p[1],10))
        if key not in ids:ids[key]=len(vertices);vertices.append(key)
        return ids[key]
    def add(points,material=0):
        face=[vertex(x,p) for x,p in points]
        assert len(set(face))==len(face)
        faces.append(face);materials.append(material)
    for i,(cell,height) in enumerate(zip(cells,heights)):
        for tri in constrained_delaunay_triangles(cell).geoms:
            points=list(tri.exterior.coords)[:-1]
            add([(height,p) for p in points]);add([(-height,p) for p in reversed(points)])
        for ring in [cell.exterior,*cell.interiors]:
            ps=list(ring.coords)
            for a,b in zip(ps,ps[1:]):
                a=tuple(round(v,10) for v in a);b=tuple(round(v,10) for v in b)
                if a==b:continue
                edges[tuple(sorted((a,b)))].append(i)
    for (a,b),owners in edges.items():
        assert len(owners)<=2
        hs=sorted(set(heights[i] for i in owners))
        if len(owners)==1:
            height=hs[0];levels=sorted(set([-height,-floor,-core,core,floor,height]))
            levels=[x for x in levels if -height<=x<=height]
            for lo,hi in zip(levels,levels[1:]):add([(lo,a),(lo,b),(hi,b),(hi,a)],1 if lo>=-core and hi<=core else 0)
        elif len(hs)==2:
            lo,hi=hs
            add([(lo,a),(lo,b),(hi,b),(hi,a)]);add([(-hi,a),(-hi,b),(-lo,b),(-lo,a)])
    lands=unary_union([p for p,h in zip(cells,heights) if h==half]);grooves=footprint.difference(lands)
    contact=lands.intersection(steel);area=contact.area;moment=0
    # Seven-point degree-five triangle quadrature of radius for uniform load.
    quadrature=[((1/3,1/3,1/3),.225)]
    for a,b,w in [(.05971587178977,.470142064105115,.132394152788506),(.797426985353087,.101286507323456,.125939180544827)]:
        quadrature.extend([((a,b,b),w),((b,a,b),w),((b,b,a),w)])
    for tri in constrained_delaunay_triangles(contact).geoms:
        pts=list(tri.exterior.coords)[:-1]
        moment+=tri.area*sum(w*math.hypot(sum(q[j]*pts[j][0] for j in range(3)),sum(q[j]*pts[j][1] for j in range(3))) for q,w in quadrature)
    return {'vertices':vertices,'faces':faces,'materials':materials,'paths':paths,
            'metrics':{'area':area,'meanRadius':moment/area,'grooveArea':grooves.area,'depth':depth,'liningThickness':lining},
            'cells':len(cells),'limits':'Fitted two-sided channels and bonded lining geometry. No oil-film, thermal, wear or factory dimensions solved.'}
