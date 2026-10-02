"""Independent analytic controls for the final Float64 proximity helper.
Extract only the pure numerical function with AST; never execute Blender authoring.
"""
import ast,hashlib,json,math
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
path=root/'repair-and-verify-native-frame.py';src=path.read_text();tree=ast.parse(src)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='directed')
env={'np':np,'samples':lambda s:s[0]};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),env)
fn=env['directed'];results=[]
def check(label,tri,p,expected,tol=2e-11):
 result=fn((np.asarray([p],dtype=np.float64),), (np.asarray(tri,dtype=np.float64),np.asarray([[0,1,2]],dtype=np.int32),None,None))['max_distance_m']
 assert abs(result-expected)<=tol,(label,result,expected)
 results.append({'test':label,'expected_m':expected,'actual_m':result,'absolute_error_m':abs(result-expected)})
tri=np.array([[0.,0,0],[1,0,0],[0,1,0]])
for label,p,expected in [('inside',[.25,.25,0],0),('above',[.25,.25,2],2),('below',[.25,.25,-3],3),('outside_hypotenuse',[1,1,0],math.sqrt(.5)),('beyond_vertex',[2,0,0],1),('on_edge',[.5,.5,0],0),('on_vertex',[0,0,0],0)]:
 check(label,tri,p,expected);check(label+'_reverse',tri[[2,1,0]],p,expected)
rng=np.random.default_rng(543)
for j in range(200):
 q,_=np.linalg.qr(rng.normal(size=(3,3)));u=q[:,0];v=q[:,1];n=np.cross(u,v)
 origin=rng.uniform(-6,6,3);length=rng.uniform(.01,2.5);width=rng.uniform(.00001,.12)
 tt=np.array([origin,origin+u*length,origin+v*width]);height=rng.uniform(-.05,.05)
 pp=.5*tt[0]+.2*tt[1]+.3*tt[2]+height*n
 check(f'rotated_thin_interior_{j}',tt,pp,abs(height),5e-10)
 # Translate and reverse without changing the expected Euclidean distance.
 check(f'translated_reversed_{j}',tt[[2,1,0]]+np.array([2,-1,.7]),pp+np.array([2,-1,.7]),abs(height),5e-10)
try:fn((np.array([[0.,0,0]]),),(np.zeros((3,3)),np.array([[0,1,2]]),None,None));raise AssertionError('degenerate-only target was accepted')
except AssertionError as e:
 assert str(e)=='No nondegenerate target triangles',str(e)
out={'status':'ANALYTIC_DISTANCE_CONTROLS_PASS','script_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'test_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'numeric_tests':len(results),'all_degenerate_target_rejected':True,'maximum_absolute_error_m':max(x['absolute_error_m'] for x in results),'tests':results,'scope':'Analytic finite point-to-triangle helper controls; not geometry or Hausdorff certification'}
(root/'distance-helper-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='tests'}))
