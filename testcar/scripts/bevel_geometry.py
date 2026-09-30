"""Spherical-involute bevel surfaces, reconstructed dimensions.

Source: The spherical involute bevel gear: its geometry, kinematic behavior
and standardization (2011), equations 4, 8–11. No MAZ cutter data is implied.
The gnomonic section allows the mate's three-dimensional swept root envelope
to be cut on the common sphere before radial lofting. This is not Tredgold.
"""
import math,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'work/pythonlibs'))
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely.affinity import rotate
from math import pi,sin,cos,tan,sqrt,acos,asin,atan,atan2

def involute(gamma,base):
    if gamma<=base:return 0.
    chi=acos(min(1.,cos(gamma)/cos(base)))
    return chi/sin(base)-acos(min(1.,tan(base)/tan(gamma)))

def profile(n,delta,module,R,thin=.000025):
    base=asin(sin(delta)*cos(pi/9));tip=delta+atan(module/R);root=delta-atan(1.25*module/R)
    inv=involute(delta,base);half=pi/(2*n)-thin/(R*sin(delta));pts=[]
    for k in range(n):
        a=k*2*pi/n;pts.append((tan(root)*cos(a-pi/n),tan(root)*sin(a-pi/n)))
        start=max(base,root)
        for sign,order in [(-1,range(25)),(1,range(24,-1,-1))]:
            for j in order:
                gamma=start+(tip-start)*j/24;phi=a+sign*(half+inv-involute(gamma,base))
                pts.append((tan(gamma)*cos(phi),tan(gamma)*sin(phi)))
    p=Polygon(pts);assert p.is_valid
    return p,base

def rotated_section(poly,a,b,sigma):
    # B axis is RotZ(sigma) X. Orient B, express in A's rotating frame, clip
    # the far hemisphere and project onto x=1. This uses visible gear surfaces,
    # not an unrelated planar involute test in place of the conical mesh.
    points=[];ca,sa,cb,sb,cs,ss=cos(a),sin(a),cos(b),sin(b),cos(sigma),sin(sigma)
    for y,z in list(poly.exterior.coords)[:-1]:
        length=sqrt(1+y*y+z*z);x,y,z=1/length,y/length,z/length
        y,z=cb*y-sb*z,sb*y+cb*z
        x,y=cs*x-ss*y,ss*x+cs*y
        y,z=ca*y+sa*z,-sa*y+ca*z
        points.append((x,y,z))
    clipped=[];eps=.005
    for p,q in zip(points,points[1:]+points[:1]):
        pin=p[0]>=eps;qin=q[0]>=eps
        if pin:clipped.append(p)
        if pin!=qin:
            f=(eps-p[0])/(q[0]-p[0]);clipped.append(tuple(p[i]+f*(q[i]-p[i]) for i in range(3)))
    if len(clipped)<3:return Polygon()
    return Polygon([(y/x,z/x) for x,y,z in clipped]).buffer(0)

def pair(n,N,sigma,module,thin=.000025):
    d=atan2(sin(sigma),N/n+cos(sigma));D=sigma-d;R=module*n/(2*sin(d))
    A,ba=profile(n,d,module,R,thin);B,bb=profile(N,D,module,R,thin)
    def relieve(actor,mate,na,nb,base):
        cuts=[];maxcone=0
        root=max(base,min(atan(math.hypot(y,z)) for y,z in actor.exterior.coords)+.0001)
        root_region=Point(0,0).buffer(tan(root),quad_segs=256)
        for j in range(361):
            a=j/360*2*pi/na;b=pi-pi/nb-na/nb*a
            # An intersection at this gear's tip is the other gear's root
            # defect. Correct each member only inside its own root region.
            inter=actor.intersection(rotated_section(mate,a,b,sigma)).intersection(root_region)
            if not inter.is_empty and inter.area>1e-16:
                cuts.append(inter)
                for g in [inter] if inter.geom_type=='Polygon' else getattr(inter,'geoms',[]):
                    if g.geom_type=='Polygon':maxcone=max(maxcone,*[atan(math.hypot(y,z)) for y,z in g.exterior.coords])
        if cuts:
            # Clearance cuts must stay at the roots, never conceal an incorrect
            # contact law by shaving away load-carrying pitch/tip flanks.
            assert maxcone<root+1e-10
            cut=unary_union(cuts);cut=unary_union([rotate(cut,k*2*pi/na,origin=(0,0),use_radians=True) for k in range(na)])
            actor=actor.difference(cut.buffer(.000008/R)).simplify(.000005/R,preserve_topology=True)
        assert actor.geom_type=='Polygon' and actor.is_valid
        return actor
    Ar=relieve(A,B,n,N,ba);Br=relieve(B,A,N,n,bb)
    maximum=0
    for j in range(721):
        a=j/720*2*pi/n;b=pi-pi/N-n/N*a
        maximum=max(maximum,Ar.intersection(rotated_section(Br,a,b,sigma)).area)
    assert maximum<1e-12,('spherical interference',n,N,maximum)
    return {'n':n,'N':N,'shaftAngle':sigma,'delta':d,'Delta':D,'module':module,'R':R,'thin':thin,'innerScale':.76,
            'A':list(Ar.exterior.coords)[:-1],'B':list(Br.exterior.coords)[:-1],'gnomonicOverlap':maximum,'samples':721,
            'method':'Spherical involute and conjugate swept root relief; MAZ tooth counts, fitted dimensions'}

if __name__=='__main__':
    results={}
    for name,n,N,angle,module in [('crank',27,18,90,.004),('cam_lower',12,18,30,.0025),('cam_upper',12,24,90,.003),('injection',12,36,90,.0026),('generator',21,18,90,.0028),('fuel_feed',11,21,90,.0025)]:
        print('GENERATING',name,flush=True);p=pair(n,N,angle*pi/180,module);results[name]=p
        print('BEVEL_OK',name,{'points':[len(p['A']),len(p['B'])],'overlap':p['gnomonicOverlap']},flush=True)
    (ROOT/'work/bevel-profiles.json').write_text(json.dumps(results))
