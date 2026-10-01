"""Independent exact-rational vertical-slab union oracle and adversarial tests.
No third-party packages. Does not modify the assessed module.
"""
from fractions import Fraction as F
import importlib.util, itertools, math, json, random, hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'work/cloud-side-rivet-attachment-20261001/coverage-controls'
OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('coverage_under_test', BASE/'convex_coverage.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FP=[(-2,-1),(-1,-2),(1,-2),(2,-1),(2,1),(1,2),(-1,2),(-2,1)]

def rational(poly): return [tuple(F(x) for x in p) for p in poly]
def edges(poly): return list(zip(poly,poly[1:]+poly[:1]))
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def shoelace(p): return abs(sum(cross(a,b) for a,b in edges(p)))/2

def interval(poly,x):
    ys=[]
    for a,b in edges(poly):
        if min(a[0],b[0]) < x < max(a[0],b[0]):
            ys.append(a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]))
    return (min(ys),max(ys)) if ys else None

def exact_areas(fp,tris):
    """Integrate exact cross-section lengths on slabs of a line arrangement.
    Breakpoints include all vertices and proper segment intersections. On each
    slab the union's upper and lower endpoints are affine, so midpoint integral
    is exact. Entirely separate from convex polygon subtraction in target.
    """
    fp=rational(fp); tris=[rational(t) for t in tris]
    all_edges=list(itertools.chain.from_iterable(edges(p) for p in [fp]+tris))
    xs={p[0] for poly in [fp]+tris for p in poly}
    for (a,b),(c,d) in itertools.combinations(all_edges,2):
        r,s=sub(b,a),sub(d,c); den=cross(r,s)
        if not den: continue
        t=cross(sub(c,a),s)/den; u=cross(sub(c,a),r)/den
        if 0<t<1 and 0<u<1: xs.add(a[0]+t*r[0])
    xs=sorted(xs); union=summed=overlap=F(0)
    for xa,xb in zip(xs,xs[1:]):
        x=(xa+xb)/2; boundary=interval(fp,x)
        if boundary is None: continue
        ints=[]
        for tri in tris:
            seg=interval(tri,x)
            if seg:
                lo,hi=max(seg[0],boundary[0]),min(seg[1],boundary[1])
                if hi>lo: ints.append((lo,hi))
        summed+=(xb-xa)*sum((hi-lo for lo,hi in ints),F(0))
        overlap+=(xb-xa)*sum((max(F(0), min(a[1],b[1])-max(a[0],b[0])) for a,b in itertools.combinations(ints,2)),F(0))
        current=None; length=F(0)
        for lo,hi in sorted(ints):
            if current is None: current=(lo,hi)
            elif lo<=current[1]: current=(current[0],max(current[1],hi))
            else: length+=current[1]-current[0]; current=(lo,hi)
        if current: length+=current[1]-current[0]
        union+=(xb-xa)*length
    return {'footprint_area':shoelace(fp),'covered_union_area':union,'uncovered_area':shoelace(fp)-union,'summed_clipped_support_area':summed,'pairwise_overlap_area_sum':overlap}

def clip_fixture(poly,a,b):
    """Exact clipping only to construct a tiled fixture; not the area oracle."""
    out=[]; p=poly[-1]; dp=cross(sub(b,a),sub(p,a))
    for q in poly:
        dq=cross(sub(b,a),sub(q,a))
        if (dp<0<dq) or (dq<0<dp):
            t=dp/(dp-dq); out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
        if dq>=0 and (not out or q!=out[-1]): out.append(q)
        p,dp=q,dq
    if len(out)>1 and out[0]==out[-1]: out.pop()
    return out

def tiles_with_hole():
    coords=list(map(F,[-2,-1,0,.25,.5,1,2])); tris=[]; fp=rational(FP)
    for x0,x1 in zip(coords,coords[1:]):
        for y0,y1 in zip(coords,coords[1:]):
            if x0==y0==F(1,4) and x1==y1==F(1,2): continue
            p=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
            for a,b in edges(fp):
                if p: p=clip_fixture(p,a,b)
            for i in range(1,len(p)-1):
                tri=[p[0],p[i],p[i+1]]
                if shoelace(tri)>0: tris.append([[float(x) for x in pt] for pt in tri])
    return tris

def transform(poly,scale=1,offset=0): return [(x*scale+offset,y*scale+offset) for x,y in poly]
def summary(r): return {k:r[k] for k in ['numerical_coverage_pass','rejection_reasons','footprint_area','uncovered_area','covered_union_area','summed_clipped_support_area','pairwise_overlap_area_sum','duplicate_clipped_region_pairs','area_accounting_violation']}

def main():
    results=[]
    def run(name,fp,tris,expected_pass=None,oracle=True,allow_invalid=False,**kw):
        row={'name':name,'kwargs':kw}
        try:
            r=m.assess_coverage(fp,tris,**kw); row['result']=summary(r)
            if expected_pass is not None: assert r['numerical_coverage_pass']==expected_pass,(name,row)
            if oracle:
                exact=exact_areas(fp,tris); row['exact_areas']={k:str(v) for k,v in exact.items()}
                for k,v in exact.items(): assert math.isclose(r[k],float(v),rel_tol=1e-9,abs_tol=1e-12),(name,k,r[k],v)
        except Exception as e:
            row['exception']=type(e).__name__+': '+str(e)
            if not isinstance(e,m.InvalidGeometry) or not allow_invalid: row['audit_failure']=True
        results.append(row)
        print(name,json.dumps(row.get('result',row.get('exception'))),flush=True)
        return row
    fan=[[FP[0],FP[i],FP[i+1]] for i in range(1,7)]
    hole=tiles_with_hole()
    assert not any(F(1,4)<F(p[0])<F(1,2) and F(1,4)<F(p[1])<F(1,2) for p in [(0,0)]+FP)
    run('full_tiling',FP,fan,True)
    run('empty_support',FP,[],False)
    run('center_and_corners_clear_interior_hole',FP,hole,False)
    run('duplicate_triangle_cannot_mask_hole',FP,hole+[hole[0]]*3,False)
    run('reversed_winding_full',list(reversed(FP)),[list(reversed(t)) for t in fan],True)
    run('reversed_winding_hole',list(reversed(FP)),[list(reversed(t)) for t in hole],False)
    for offset in [1e9,2**40,2**48]:
        run('large_offset_full_'+str(offset),transform(FP,offset=offset),[transform(t,offset=offset) for t in fan],True)
        run('large_offset_hole_'+str(offset),transform(FP,offset=offset),[transform(t,offset=offset) for t in hole],False)
    for scale in [1e-155,1e-160,1e-161,1e-162]:
        run('tiny_scale_hole_'+str(scale),transform(FP,scale),[transform(t,scale) for t in hole],False,oracle=False,allow_invalid=True,area_tolerance=0)
        run('tiny_scale_full_'+str(scale),transform(FP,scale),[transform(t,scale) for t in fan],None,oracle=False,allow_invalid=True,area_tolerance=0)
    malformed=[]
    p=FP.copy();p[2]=p[0];malformed.append(('duplicate_fp_vertex',p,fan))
    p=FP.copy();p[2]=(0,0);malformed.append(('concave_fp',p,fan))
    malformed.append(('crossed_octagon',FP[::2]+FP[1::2],fan))
    malformed.append(('nonfinite_triangle',FP,[[(0,0),(1,0),(0,float('nan'))]]))
    malformed.append(('degenerate_triangle',FP,[[(0,0),(1,1),(2,2)]]))
    for name,fp,tris in malformed:
        row=run(name,fp,tris,oracle=False,allow_invalid=True)
        if not row.get('exception','').startswith('InvalidGeometry'): row['audit_failure']=True
    rng=random.Random(99731)
    for n in range(30):
        tris=[]
        for _ in range(rng.randrange(1,9)):
            while True:
                t=[(rng.randrange(-24,25)/8,rng.randrange(-24,25)/8) for _ in range(3)]
                if len(set(t))==3 and shoelace(rational(t))>0: break
            tris.append(t)
        run('random_oracle_%02d'%n,FP,tris,None)
    out={'module_sha256':hashlib.sha256((BASE/'convex_coverage.py').read_bytes()).hexdigest(),'results':results}
    (OUT/'oracle-results.json').write_text(json.dumps(out,indent=2))
    failures=sum(bool(r.get('audit_failure')) for r in results)
    print('AUDIT_FAILURES',failures)
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
