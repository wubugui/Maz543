"""Generate fitted involute/conjugate root profiles and verify planar clearance.
Requires Shapely in work/pythonlibs. Parameters are NOT factory gear dimensions.
"""
import sys,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
from shapely.ops import unary_union
from shapely.affinity import rotate,translate
from math import pi,cos,sin
S=json.loads((ROOT/'work/starting-poses.json').read_text())['spec']
def gear(n,m,thin):
 rp=m*n/2;rb=rp*cos(math.radians(20));ra=rp+m;rr=rp-1.25*m;iv=math.tan(math.radians(20))-math.radians(20);p=[]
 for k in range(n):
  a=k*2*pi/n;half=pi/(2*n)-thin/rp;p.append((rr*cos(a-pi/n),rr*sin(a-pi/n)))
  r0=max(rr,rb)
  for sign,rs in [(-1,[r0,r0+(ra-r0)*.25,r0+(ra-r0)*.5,r0+(ra-r0)*.75,ra]),(1,[ra,r0+(ra-r0)*.75,r0+(ra-r0)*.5,r0+(ra-r0)*.25,r0])]:
   for r in rs:
    t=math.acos(min(1,rb/r));iv2=math.tan(t)-t;ang=a+sign*(half+iv-iv2);p.append((r*cos(ang),r*sin(ang)))
  p.append((rr*cos(a+pi/n),rr*sin(a+pi/n)))
 return Polygon(p).buffer(0)
def cap_data(profile,bore):
 outer=list(profile.exterior.coords)[:-1];inner=[(bore*cos(k*2*pi/96),bore*sin(k*2*pi/96)) for k in range(96)];points=outer+inner
 ids={tuple(p):i for i,p in enumerate(points)};annulus=Polygon(outer,[inner]);assert annulus.is_valid
 triangles=constrained_delaunay_triangles(annulus)
 faces=[[ids[tuple(p)] for p in list(t.exterior.coords)[:-1]] for t in triangles.geoms]
 return {'sectionVertices':points,'capTriangles':faces,'outerCount':len(outer)}
def generate(name,n,N,m,centre,thin,clearance):
 ratio=N/n;phi=math.atan2(centre[1],centre[0]);A=(ratio+1)*phi+pi-pi/n
 pin=gear(n,m,thin);ring=gear(N,m,thin);cuts=[]
 for i in range(721):
  a=i/720*2*pi/N;pa=A-ratio*a;r=rotate(ring,a,origin=(0,0),use_radians=True);r=translate(r,xoff=-centre[0],yoff=-centre[1]);r=rotate(r,-pa,origin=(0,0),use_radians=True)
  inter=r.intersection(pin)
  if not inter.is_empty:cuts.append(inter)
 cut=unary_union(cuts);cut=unary_union([rotate(cut,k*2*pi/n,origin=(0,0),use_radians=True) for k in range(n)])
 profile=pin.difference(cut.buffer(clearance)).simplify(.000001,preserve_topology=True)
 assert profile.geom_type=='Polygon'
 if n==N:ring=profile
 areas=[]
 for i in range(4401):
  a=i/4400*2*pi/ratio;pa=A-ratio*a;r=rotate(ring,a,origin=(0,0),use_radians=True);q=translate(rotate(profile,pa,origin=(0,0),use_radians=True),xoff=centre[0],yoff=centre[1]);areas.append(r.intersection(q).area)
 result={'method':'20 degree involute with conjugate-generated root relief; reconstructed, not original dimensions','clearance':clearance,'flankThinning':thin,'samples':4401,'maximumIntersectionArea':max(areas),'profile':list(profile.exterior.coords)[:-1]}
 result.update(cap_data(profile,.012 if n==11 else .008))
 (ROOT/('work/'+name+'-profile.json')).write_text(json.dumps(result));print(name,len(profile.exterior.coords),'vertices; max intersection',max(areas)*1e6,'mm2',flush=True);assert max(areas)<1e-13
 return {k:v for k,v in result.items() if k not in ['profile','sectionVertices','capTriangles']}
results={'C5':generate('c5-pinion',11,132,S['module'],(S['starterPosition'][1]-.07,S['starterPosition'][2]),.00025,.000018),'MZN':generate('mzn-gear',12,12,.034/12,(.034,0),.00004,.000012)}
(ROOT/'outputs/starting-gear-clearance.json').write_text(json.dumps(results,indent=2))

ring=gear(132,S['module'],.00025);(ROOT/'work/c5-ring-profile.json').write_text(json.dumps(cap_data(ring,.298)))
