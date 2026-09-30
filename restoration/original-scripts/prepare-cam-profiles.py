"""MAZ fig. 7/9 counts; reconstructed module, pressure angle and spline sizes.
Triangulate real annular sections, and check the paired 22-tooth spur mesh.
"""
import sys,math,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from math import pi,cos,sin
S=json.loads((ROOT/'work/d12-poses.json').read_text())['spec']

def radial(n,minor,major,rect=False,width=.22):
 p=[]
 for k in range(n):
  steps=[(-.5,minor),(-width,minor),(-width,major),(width,major),(width,minor),(.5,minor)] if rect else [(-.5,minor),(0,major),(.5,minor)]
  for u,r in steps:
   a=(k+u)*2*pi/n;q=(r*cos(a),r*sin(a))
   if not p or math.dist(q,p[-1])>1e-10:p.append(q)
 if math.dist(p[-1],p[0])<1e-10:p.pop()
 return p

def section(outer,inner):
 poly=Polygon(outer,[inner]);assert poly.is_valid
 points=outer+inner;ids={tuple(p):i for i,p in enumerate(points)}
 faces=[[ids[tuple(p)] for p in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(poly).geoms]
 return {'vertices':points,'faces':faces,'outer':len(outer)}

def spur(n,module,thin=.000025):
 rp=module*n/2;rb=rp*cos(pi/9);ra=rp+module;rr=rp-1.25*module;inv=math.tan(pi/9)-pi/9;p=[]
 for k in range(n):
  a=k*2*pi/n;half=pi/(2*n)-thin/rp;p.append((rr*cos(a-pi/n),rr*sin(a-pi/n)))
  start=max(rr,rb)
  for sign,order in [(-1,range(17)),(1,range(16,-1,-1))]:
   for j in order:
    r=start+(ra-start)*j/16;t=math.acos(min(1,rb/r));q=a+sign*(half+inv-(math.tan(t)-t));p.append((r*cos(q),r*sin(q)))
 return p

module=2*S['valveOffset']/22;outer=spur(22,module)
# Generate root clearance against the mate's swept tooth tips. A straight line
# from the base circle to a root valley is not a conjugate dedendum.
base=Polygon(outer);cuts=[]
for j in range(361):
 a=j/360*2*pi/22
 mate=rotate(base,pi-pi/22-a,origin=(0,0),use_radians=True)
 mate=rotate(translate(mate,xoff=2*S['valveOffset']),-a,origin=(0,0),use_radians=True)
 hit=base.intersection(mate)
 if not hit.is_empty:cuts.append(hit)
if cuts:
 cut=unary_union(cuts)
 cut=unary_union([rotate(cut,k*2*pi/22,origin=(0,0),use_radians=True) for k in range(22)])
 base=base.difference(cut.buffer(.000008)).simplify(.0000003,preserve_topology=True)
outer=list(base.exterior.coords)[:-1]
small=radial(41,.01994,.02064);hole=radial(41,.02002,.02072)
male=radial(10,.0139,.0155,True);female=radial(10,.01397,.01557,True,width=.225)
circle=lambda r:[(r*cos(j*2*pi/96),r*sin(j*2*pi/96)) for j in range(96)]
sections={'spur':section(outer,hole),'sleeve':section(small,female),'shaftSpline':section(male,circle(.008))}
poses=json.loads((ROOT/'work/d12-poses.json').read_text())['frames'][0]['pose']
for bank in ['L','R']:
 for kind in ['intake','exhaust']:
  p=poses[f'D12_cam_{bank}_{kind}']['p'];q=poses[f'D12_cam_{bank}_{"exhaust" if kind=="intake" else "intake"}']['p']
  a=math.atan2(q[2]-p[2],q[1]-p[1])-(pi/22 if kind=='exhaust' else 0)
  sections[f'spur_{bank}_{kind}']=section([(y*cos(a)-z*sin(a),y*sin(a)+z*cos(a)) for y,z in outer],hole)
A=Polygon(outer);B=rotate(A,pi-pi/22,origin=(0,0),use_radians=True);worst=0
for j in range(1441):
 angle=j/1440*2*pi/22
 a=rotate(A,angle,origin=(0,0),use_radians=True)
 b=translate(rotate(B,-angle,origin=(0,0),use_radians=True),xoff=2*S['valveOffset'])
 worst=max(worst,a.intersection(b).area)
assert worst<1e-13,worst
result={'module':module,'pressureAngleDeg':20,'flankThinning':.000025,'meshSamples':1441,'maxIntersectionArea':worst,'sections':sections}
(ROOT/'work/cam-profiles.json').write_text(json.dumps(result));print('CAM_PROFILES',{'samples':1441,'intersectionArea':worst,'module':module})

# Replace the previous failed raw-download hashes only after image verification.
from PIL import Image
folder=Path('D:/maz543-references/engine/timing');names=[('0317','1973-maz-fig7-gear-scheme'),('0323','1973-maz-valve-text'),('0329','1973-maz-valve-phases'),('0336','1973-maz-fig9-cam-assembly'),('0343','1973-maz-cam-caption')]
base='https://sinref.ru/avtomobili/MAZ/011-Maz-543-shassi-tehopisanie-1973-g-04600_raznie_13/'
entries=[]
for number,name in names:
 path=folder/(name+'.jpg');im=Image.open(path);im.verify()
 entries.append({'file':path.name,'url':base+'000/'+number+'.jpg','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'viewed':True,'format':'JPEG','dimensions':Image.open(path).size,'acquisition':'Browser pageAssets from the normally rendered manual chapter; no manual cookie transfer'})
(folder/'primary-pages-manifest.json').write_text(json.dumps(entries,indent=2))
