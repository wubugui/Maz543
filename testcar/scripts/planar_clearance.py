"""Small numerical 2D convex-projection distance helpers; no mesh authoring."""
from math import hypot

EPS=1e-12
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
    pts=sorted(set(tuple(map(float,p)) for p in points))
    if len(pts)<=1:return pts
    def chain(seq):
        result=[]
        for p in seq:
            while len(result)>=2 and cross(result[-2],result[-1],p)<=0:result.pop()
            result.append(p)
        return result
    return chain(pts)[:-1]+chain(reversed(pts))[:-1]
def edges(poly):
    return [(poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly))]
def point_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy
    t=0 if d==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d))
    q=(a[0]+t*dx,a[1]+t*dy)
    return hypot(p[0]-q[0],p[1]-q[1]),q
def inside(p,poly):
    if len(poly)<3 or abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in edges(poly)))<EPS:
        return any(point_segment(p,a,b)[0]<=EPS for a,b in edges(poly))
    values=[cross(a,b,p) for a,b in edges(poly)]
    return min(values)>=-EPS or max(values)<=EPS
def intersects(a,b,c,d):
    ab_c,ab_d=cross(a,b,c),cross(a,b,d);cd_a,cd_b=cross(c,d,a),cross(c,d,b)
    if ((ab_c>EPS and ab_d<-EPS) or (ab_c<-EPS and ab_d>EPS)) and ((cd_a>EPS and cd_b<-EPS) or (cd_a<-EPS and cd_b>EPS)):return True
    return any(abs(v)<=EPS and point_segment(p,x,y)[0]<=EPS for v,p,x,y in [(ab_c,c,a,b),(ab_d,d,a,b),(cd_a,a,c,d),(cd_b,b,c,d)])
def distance(a,b):
    """Nonempty convex polygons, including degenerate points/segments."""
    assert a and b
    if inside(a[0],b) or inside(b[0],a):return 0.0
    result=float('inf')
    for p,q in edges(a):
        for r,s in edges(b):
            if intersects(p,q,r,s):return 0.0
            result=min(result,point_segment(p,r,s)[0],point_segment(q,r,s)[0],point_segment(r,p,q)[0],point_segment(s,p,q)[0])
    return result

if __name__=='__main__':
    from math import isclose,cos,sin
    square=hull([(0,0),(1,0),(1,1),(0,1)])
    controls=[('separated',square,hull([(2,0),(3,0),(3,1),(2,1)]),1),
              ('contained',square,hull([(.2,.2),(.4,.2),(.2,.4)]),0),
              ('edge crossing',square,hull([(-1,.4),(2,.4),(2,.6),(-1,.6)]),0),
              ('touching',square,hull([(1,1),(2,1),(1,2)]),0),
              ('vertical-face projection',square,hull([(2,.2),(2,.8),(2,.5)]),1),
              ('point projection',square,[(2,2)],2**.5),
              ('collinear disjoint',[(0,0),(1,0)],[(2,0),(3,0)],1)]
    for name,a,b,expected in controls:
        assert isclose(distance(a,b),expected,abs_tol=1e-10),name
        assert isclose(distance(b,a),expected,abs_tol=1e-10),name
        angle=.713;c,s=cos(angle),sin(angle)
        transform=lambda p:(12.3+c*p[0]-s*p[1],-7.2+s*p[0]+c*p[1])
        assert isclose(distance(hull(map(transform,a)),hull(map(transform,b))),expected,abs_tol=1e-10),name
    print('PLANAR_CLEARANCE_CONTROLS',len(controls),'with symmetry and rigid transforms passed')
