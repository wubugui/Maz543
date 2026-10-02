#!/usr/bin/env python3
"""Independently certify strict crossings of the reported binary64 triangles.

Uses exact rational arithmetic and coordinate-axis intervals, without NumPy,
Blender, BVH, normalized plane distances or the original floating predicate.
This verifies the recorded triangles; native identity is established separately.
"""
import argparse,hashlib,json,math
from fractions import Fraction as F
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--witnesses',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
add=lambda a,b:tuple(x+y for x,y in zip(a,b))
sub=lambda a,b:tuple(x-y for x,y in zip(a,b))
mul=lambda a,s:tuple(x*s for x in a)
dot=lambda a,b:sum(x*y for x,y in zip(a,b))
cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
frac=lambda x:[str(x.numerator),str(x.denominator)]
def section(T,d):
 points=[]
 for i in range(3):
  j=(i+1)%3
  if d[i]==0:points.append(T[i])
  if d[i]*d[j]<0:points.append(add(T[i],mul(sub(T[j],T[i]),d[i]/(d[i]-d[j]))))
 assert len(points)==2
 return points
def bary(T,q):
 e1,e2=sub(T[1],T[0]),sub(T[2],T[0]);d=sub(q,T[0]);n=cross(e1,e2);den=dot(n,n)
 v=dot(cross(d,e2),n)/den;w=dot(cross(e1,d),n)/den
 return 1-v-w,v,w
rows=[]
for w in json.loads(a.witnesses.read_text()):
 A=[tuple(F(v) for v in q) for q in w['step_triangle_world_m']]
 B=[tuple(F(v) for v in q) for q in w['wheel_triangle_world_m']]
 na=cross(sub(A[1],A[0]),sub(A[2],A[0]));nb=cross(sub(B[1],B[0]),sub(B[2],B[0]))
 assert dot(na,na)>0 and dot(nb,nb)>0
 da=[dot(sub(q,B[0]),nb) for q in A];db=[dot(sub(q,A[0]),na) for q in B]
 assert min(da)<0<max(da) and min(db)<0<max(db)
 direction=cross(na,nb);axis=max(range(3),key=lambda i:abs(direction[i]));assert direction[axis]!=0
 sa=sorted(section(A,da),key=lambda q:q[axis]);sb=sorted(section(B,db),key=lambda q:q[axis])
 lo,hi=max(sa[0][axis],sb[0][axis]),min(sa[1][axis],sb[1][axis]);assert hi>lo
 def at(s,v):return add(s[0],mul(sub(s[1],s[0]),(v-s[0][axis])/(s[1][axis]-s[0][axis])))
 ea,eb=(at(sa,lo),at(sa,hi)),(at(sb,lo),at(sb,hi));assert ea==eb
 q=mul(add(*ea),F(1,2));ba,bb=bary(A,q),bary(B,q)
 assert all(x>0 for x in ba+bb)
 assert dot(sub(q,A[0]),na)==0 and dot(sub(q,B[0]),nb)==0
 for T,b in ((A,ba),(B,bb)):
  assert tuple(sum(b[i]*T[i][j] for i in range(3)) for j in range(3))==q
 flq=w['shared_interior_point_world_m'];delta=math.sqrt(sum(float(F(flq[i])-q[i])**2 for i in range(3)));assert delta<1e-10
 payload={'segment':[[frac(v) for v in e] for e in ea],'point':[frac(v) for v in q],
  'step_barycentric':[frac(v) for v in ba],'wheel_barycentric':[frac(v) for v in bb]}
 rows.append({'step':w['step'],'wheel':w['wheel'],'step_triangle_index':w['step_triangle_index'],
  'wheel_triangle_index':w['wheel_triangle_index'],'exact_binary64_triangle_crossing_verified':True,
  'exact_two_plane_and_reconstruction_residuals_zero':True,'exact_segment_constructions_identical':True,
  'exact_barycentric_min':frac(min(ba+bb)),'exact_shared_point':payload['point'],
  'exact_certificate_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
  'floating_report_point_to_exact_midpoint_delta_m':delta,
  'exact_segment_length_m_as_float':math.sqrt(sum(float(x-y)**2 for x,y in zip(*ea)))})
r={'status':'ALL_RECORDED_WITNESSES_HAVE_EXACT_RATIONAL_STRICT_CROSSINGS',
 'witness_file_sha256':sha(a.witnesses),'script_sha256':sha(__file__),'count':len(rows),'witnesses':rows,
 'limit':'Certifies intersection of the exact binary64 triangle coordinates printed in the native report; does not itself re-read Blender geometry or establish physical solids.'}
a.out.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');print(r['status'],len(rows))
