"""Exact native empty-scene replay and modifier-stage diagnostics, no asset save."""
import sys,json,hashlib,math,time,traceback
from pathlib import Path
from collections import Counter
import bpy,numpy as np
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve().parents[2]
OUT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT.mkdir(exist_ok=False)
script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
source=ROOT/'maz-step-layout-study-20261001/build-step-layout-study.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812'
assert bpy.app.version[:3]==(4,5,13)
report={'status':'IN_PROGRESS','script_sha256':script_sha,'original_script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'stages':[]}
def write(): (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
write()

def snapshot(o):
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);m=ev.to_mesh()
 try:
  v=np.empty((len(m.vertices),3),dtype=np.float64);m.vertices.foreach_get('co',v.ravel());local=v.copy();w=np.asarray(ev.matrix_world,dtype=np.float64);v=v@w[:3,:3].T+w[:3,3]
  m.calc_loop_triangles();t=np.empty((len(m.loop_triangles),3),dtype=np.int32);m.loop_triangles.foreach_get('vertices',t.ravel())
  return v,t,local,len(m.polygons)
 finally:ev.to_mesh_clear()

def topology(v,t,weld):
 if weld:u,inv=np.unique(v,axis=0,return_inverse=True);tt=inv[t]
 else:u=v;tt=t
 edges=Counter();ori=Counter();adj=[set() for _ in u]
 for tri in tt:
  for j in range(3):
   p,q=map(int,(tri[j],tri[(j+1)%3]));edges[tuple(sorted((p,q)))]+=1;ori[(p,q)]+=1;adj[p].add(q);adj[q].add(p)
 seen=set();components=0
 for j in range(len(u)):
  if j in seen:continue
  components+=1;seen.add(j);todo=[j]
  while todo:
   for n in adj[todo.pop()]:
    if n not in seen:seen.add(n);todo.append(n)
 return {'components':components,'edge_incidence_not_two':sum(n!=2 for n in edges.values()),'edge_winding_imbalance':sum(ori[(p,q)]!=ori[(q,p)] for p,q in edges),'self_edges':sum(p==q for p,q in edges)}

def audit(o,label):
 v,t,local,faces=snapshot(o);q=v[t];c=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
 z=q-v.mean(axis=0);vol=np.einsum('ij,ij->i',z[:,0],np.cross(z[:,1],z[:,2])).sum()/6
 row={'label':label,'vertices':len(v),'faces':faces,'triangles':len(t),'exact_duplicate_vertices_world':len(v)-len(np.unique(v,axis=0)),'exact_duplicate_vertices_local':len(v)-len(np.unique(local,axis=0)),
 'crossnorm_eq_zero':int(sum(c==0)),'crossnorm_lt_1e_14':int(sum(c<1e-14)),'min_crossnorm_m2':float(c.min()),'raw_index_topology':topology(v,t,False),'exact_weld_topology':topology(v,t,True),'bounds_m':[v.min(0).tolist(),v.max(0).tolist()],'signed_volume_m3':float(vol),'vertex_triangle_signature':hashlib.sha256(v.tobytes()+t.tobytes()).hexdigest()}
 report['stages'].append(row);write();print(json.dumps(row),flush=True)
 return row

def settings(m):
 keys=['width','segments','affect','limit_method','angle_limit','use_clamp_overlap','miter_outer','miter_inner','vmesh_method','harden_normals','loop_slide','offset_type','profile']
 return {k:getattr(m,k) for k in keys}
try:
 # Execute unchanged original source through native scene construction; stop before rendering setup.
 prefix=source.read_text().split('# Native Cycles renders, explicit color management and lighting.')[0]
 saved=sys.argv;sys.argv=['blender','--','--repo',str(ROOT/'Maz543'),'--out',str(OUT/'original-prefix'),'--view','oblique']
 g={'__file__':str(source),'__name__':'__native_source_prefix__'}
 exec(compile(prefix,str(source),'exec'),g);sys.argv=saved
 base=g['base'];bevel=g['bevel'];report['original_bevel_settings']=settings(bevel);write()
 audit(base,'original_exact_empty_scene')
 P=g['P'];cube=g['cube'];col=g['col_tools'];yc=P['y_center'];fw=P['frame_rect_section_width'];fh=P['frame_rect_section_height'];xmin,xmax=P['x_frame'];zc=P['z_frame_center']
 # Native constructive difference: same ideal union of two rails and three ties,
 # represented by outer box minus its four open inter-rail spaces.
 corrected=cube('CORRECTED_NATIVE_FRAME',((xmin+xmax)/2,yc,zc),(xmax-xmin,P['width'],fh),None,col)
 stations=P['x_stations'];ranges=[(xmin-.01,stations[0]-fw/2),(stations[0]+fw/2,stations[1]-fw/2),(stations[1]+fw/2,stations[2]-fw/2),(stations[2]+fw/2,xmax+.01)]
 for i,(x0,x1) in enumerate(ranges):
  tool=cube(f'DIFFERENCE_OPENING_{i}',((x0+x1)/2,yc,zc),(x1-x0,P['width']-2*fw,fh+.02),None,col)
  m=corrected.modifiers.new(f'Native through opening {i}','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=tool;tool.hide_set(True);tool.hide_render=True
  audit(corrected,f'difference_prefix_{i+1}')
 b=corrected.modifiers.new('Intended 2 mm bevel','BEVEL');b.width=P['frame_bevel_display_fit'];b.segments=3;b.affect='EDGES';b.limit_method='ANGLE';b.angle_limit=math.radians(30);b.use_clamp_overlap=True
 audit(corrected,'difference_frame_beveled_2mm')
 report['corrected_modifiers']=[{'name':m.name,'type':m.type} for m in corrected.modifiers]
 report['aperture_ranges_fitted_derived_m']=ranges
 report['status']='DIAGNOSIS_COMPLETE_NOT_ACCEPTANCE';report['script_sha256_end']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();write()
except Exception:
 report['status']='FAILED';report['error']=traceback.format_exc();write();raise
