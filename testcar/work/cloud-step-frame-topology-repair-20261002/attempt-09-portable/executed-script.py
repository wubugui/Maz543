"""Exact native empty-scene replay and modifier-stage diagnostics, no asset save."""
import argparse,sys,json,hashlib,math,time,traceback
from pathlib import Path
from collections import Counter
import bpy,numpy as np
parser=argparse.ArgumentParser(description='Portable empty-scene step-frame verification; never save a native asset')
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--original-script',type=Path,required=True)
parser.add_argument('--original-layout-report',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
cli=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
REPO=cli.repo.resolve();OUT=cli.out.resolve()
assert not OUT.is_relative_to(REPO),'Output directory must remain outside repository'
OUT.mkdir(parents=True,exist_ok=False)
script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
source=cli.original_script.resolve()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='b295070b1d492c0d376ee732586003928bb94f12db503dbfc089dca93d152812'
assert bpy.app.version[:3]==(4,5,13)
assert not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Launch with --disable-autoexec'
report={'status':'IN_PROGRESS','script_sha256':script_sha,'original_script_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'stages':[], 'autoexec_disabled_at_entry':not bpy.context.preferences.filepaths.use_scripts_auto_execute, 'portable_input_paths':{'repo':str(REPO),'original_script':str(source),'original_layout_report':str(cli.original_layout_report.resolve()),'out':str(OUT)}}
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
def quality(snap):
 from mathutils.bvhtree import BVHTree
 import bmesh
 v,t,_,_=snap
 unique,inv=np.unique(v,axis=0,return_inverse=True)
 canon=np.sort(inv[t],axis=1)
 tree=BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.)
 candidates=[(i,j) for i,j in tree.overlap(tree) if i<j and not set(map(int,t[i]))&set(map(int,t[j]))]
 ev=bpy.data.objects['CORRECTED_FRAME__native_difference'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();bm=bmesh.new();bm.from_mesh(m)
 try:nonmanifold=sum(not z.is_manifold for z in bm.verts)
 finally:bm.free();ev.to_mesh_clear()
 edges={tuple(sorted((int(row[j]),int(row[(j+1)%3])))) for row in t for j in range(3)}
 return {'duplicate_triangle_coordinate_sets':len(canon)-len(np.unique(canon,axis=0)),'unused_vertices':len(v)-len(np.unique(t)),'bmesh_nonmanifold_vertices':nonmanifold,'euler_characteristic':len(v)-len(edges)+len(t),'nonincident_triangle_bvh_candidates':len(candidates),'nonincident_bvh_examples':candidates[:10],'bvh_epsilon_m':0}

def samples(snap):
 v,t,_,_=snap
 edges=np.asarray(sorted({tuple(sorted((int(row[j]),int(row[(j+1)%3])))) for row in t for j in range(3)}))
 return np.concatenate([v,v[t].mean(axis=1),v[edges].mean(axis=1)])

def directed(a,b):
 # Exhaustive Float64 point/triangle distance, avoids low-precision BVH nearest
 # instability on long thin/coplanar triangles. No geometry is edited.
 v,t,_,_=b;tri=v[t];nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n2=np.einsum('ij,ij->i',nn,nn);good=np.sqrt(n2)>=1e-14
 tri=tri[good];nn=nn[good];n2=n2[good];assert len(tri)>0,'No nondegenerate target triangles';pts=samples(a);out=[]
 for start in range(0,len(pts),64):
  pp=pts[start:start+64,None,:];aa=tri[None,:,0,:];bb=tri[None,:,1,:];cc=tri[None,:,2,:]
  area0=np.einsum('pij,ij->pi',np.cross(bb-pp,cc-pp),nn)
  area1=np.einsum('pij,ij->pi',np.cross(cc-pp,aa-pp),nn)
  area2=np.einsum('pij,ij->pi',np.cross(aa-pp,bb-pp),nn)
  inside=(area0>=0)&(area1>=0)&(area2>=0)
  signed=np.einsum('pij,ij->pi',pp-aa,nn)
  best=np.where(inside,signed*signed/n2[None,:],np.inf)
  for j in range(3):
   origin=tri[None,:,j,:];edge=tri[:,(j+1)%3,:]-tri[:,j,:];edge2=np.einsum('ij,ij->i',edge,edge)
   assert np.all(edge2>0)
   param=np.clip(np.einsum('pij,ij->pi',pp-origin,edge)/edge2[None,:],0,1)
   residual=pp-(origin+param[:,:,None]*edge[None,:,:])
   best=np.minimum(best,np.einsum('pij,pij->pi',residual,residual))
  out.extend(np.sqrt(np.min(best,axis=1)).tolist())
 dist=np.asarray(out)
 return {'sample_count':len(pts),'max_distance_m':float(dist.max()),'mean_distance_m':float(dist.mean()),'p99_distance_m':float(np.quantile(dist,.99)),'target_degenerate_triangles_omitted_from_query_only':len(t)-len(tri),'method':'Exhaustive Float64 triangle plane projection when inside plus all three clamped edge projections; no BVH distance approximation'}

def volume(snap):
 v,t,_,_=snap;q=v[t]-v.mean(axis=0)
 return float(np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2])).sum()/6)

def compare(a,b):
 av,bv=volume(a),volume(b)
 ab=np.asarray([a[0].min(0),a[0].max(0)]);bb=np.asarray([b[0].min(0),b[0].max(0)])
 return {'a_to_b':directed(a,b),'b_to_a':directed(b,a),'bounds_difference_m':(bb-ab).tolist(),'max_abs_bounds_difference_m':float(abs(bb-ab).max()),'a_signed_volume_m3':av,'b_signed_volume_m3':bv,'signed_volume_delta_m3':bv-av,'signed_volume_delta_percent':100*(bv-av)/av}

def plane_section(snap,axis,position):
 v,t,_,_=snap;points=[]
 for tri in v[t]:
  for k in range(3):
   p,q=tri[k],tri[(k+1)%3];d0=p[axis]-position;d1=q[axis]-position
   if d0==0:points.append(p)
   if d0*d1<0:points.append(p+(q-p)*(-d0)/(d1-d0))
 return np.array(points)

def section_dimensions(points,haxis,center,width):
 pts=points[abs(points[:,haxis]-center)<=width/2+2e-6]
 assert len(pts)>0
 low,high=pts[:,haxis].min(),pts[:,haxis].max();bottom,top=pts[:,2].min(),pts[:,2].max()
 at_top=pts[abs(pts[:,2]-top)<1e-8,haxis]
 return {'section_width_m':float(high-low),'section_height_m':float(top-bottom),'top_flat_setback_left_m':float(at_top.min()-low),'top_flat_setback_right_m':float(high-at_top.max()),'section_intersection_points_evaluated':len(pts)}

try:
 # Execute unchanged original source through native scene construction; stop before rendering setup.
 prefix=source.read_text().split('# Native Cycles renders, explicit color management and lighting.')[0]
 saved=sys.argv;sys.argv=['blender','--','--repo',str(REPO),'--out',str(OUT/'original-prefix'),'--view','oblique']
 g={'__file__':str(source),'__name__':'__native_source_prefix__'}
 exec(compile(prefix,str(source),'exec'),g);sys.argv=saved
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Autoexec preference unexpectedly enabled after factory-empty replay'
 report['autoexec_disabled_after_original_prefix']=True
 base=g['base'];bevel=g['bevel'];report['original_bevel_settings']=settings(bevel);write()
 audit(base,'original_exact_empty_scene')
 original_bad=snapshot(base)
 bevel.show_viewport=False;original_unbeveled=snapshot(base);audit(base,'original_boolean_union_unbeveled')
 P=g['P'];cube=g['cube'];col=g['col_tools'];yc=P['y_center'];fw=P['frame_rect_section_width'];fh=P['frame_rect_section_height'];xmin,xmax=P['x_frame'];zc=P['z_frame_center']
 report['params_m']=P;report['parameter_provenance']=g['PARAMETER_PROVENANCE']
 report['recipe_equivalence']='For ideal real-valued boxes: subtract four open inter-rail gaps from the common outer box. The remainder is exactly the original union of two longitudinal rails and three full-width ties. Cutter Z/X overshoot is outside that outer box, so it cannot alter the intended envelope.'
 corrected=cube('CORRECTED_FRAME__native_difference',((xmin+xmax)/2,yc,zc),(xmax-xmin,P['width'],fh),None,col)
 corrected['scope']='Fitted frame envelope only. Tyre-placement conflict remains FAILED. Not a certified solid.'
 stations=P['x_stations'];ranges=[(xmin-.01,stations[0]-fw/2),(stations[0]+fw/2,stations[1]-fw/2),(stations[1]+fw/2,stations[2]-fw/2),(stations[2]+fw/2,xmax+.01)]
 for i,(x0,x1) in enumerate(ranges):
  tool=cube(f'CORRECTED_TOOL__interrail_opening_{i+1}',((x0+x1)/2,yc,zc),(x1-x0,P['width']-2*fw,fh+.02),None,col)
  m=corrected.modifiers.new(f'Editable exact difference {i+1}','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=tool
  tool.hide_set(True);tool.hide_render=True;tool.display_type='WIRE'
 unb=snapshot(corrected);unb_row=audit(corrected,'corrected_native_unbeveled')
 b=corrected.modifiers.new('Intended fitted 2 mm bevel','BEVEL');b.width=P['frame_bevel_display_fit'];b.segments=3;b.affect='EDGES';b.limit_method='ANGLE';b.angle_limit=math.radians(30);b.use_clamp_overlap=True
 b.miter_outer='MITER_SHARP';b.miter_inner='MITER_SHARP';b.vmesh_method='ADJ';b.offset_type='OFFSET';b.profile=.5;b.loop_slide=True
 final=snapshot(corrected);final_row=audit(corrected,'corrected_native_beveled')
 report['corrected_bevel_settings']=settings(b)
 report['corrected_modifier_stack']=[{'name':m.name,'type':m.type,'operation':getattr(m,'operation',None),'solver':getattr(m,'solver',None)} for m in corrected.modifiers]
 report['construction_only_cutter_overshoot_m']={'z_each_end':.01,'x_beyond_outer_ends':.01,'purpose':'Avoid exactly coplanar cutter caps; removed region outside frame has no intended shape effect; not a hardware dimension'}
 report['nominal_unbeveled_frame_volume']={'formula':'2*L*rail_width*height + 3*tie_width*(total_width-2*rail_width)*height','value_m3':2*(xmax-xmin)*fw*fh+3*fw*(P['width']-2*fw)*fh,'actual_original_unbeveled_m3':volume(original_unbeveled),'actual_corrected_unbeveled_m3':volume(unb),'set_equivalence_scope':'Nominal real-valued rectangular intervals before bevel only; actual Float32 geometry compared separately','opening_x_intervals_m':ranges}
 report['native_geometry_readback']=quality(final)
 report['surface_comparisons']={
  'same_ideal_unbeveled_frame':compare(original_unbeveled,unb),
  'actual_old_degenerate_frame_to_corrected_beveled':compare(original_bad,final),
  'intended_bevel_effect_on_clean_same_frame':compare(unb,final),
 }
 report['regular_sections']=[]
 for xx in (-4.6,-3.5):
  pts=plane_section(final,0,xx)
  for side in (-1,1):
   ymid=yc+side*(P['width']/2-fw/2)
   section=section_dimensions(pts,1,ymid,fw)
   report['regular_sections'].append(dict(location=f'long rail y side {side}, x={xx}',**section))
 pts=plane_section(final,1,yc)
 for xx in stations:report['regular_sections'].append(dict(location=f'transverse tie x={xx}, y={yc}',**section_dimensions(pts,0,xx,fw)))
 def passes(row):
  return row['exact_duplicate_vertices_world']==0 and row['exact_duplicate_vertices_local']==0 and row['crossnorm_lt_1e_14']==0 and row['raw_index_topology']['components']==1 and row['raw_index_topology']['edge_incidence_not_two']==0 and row['raw_index_topology']['edge_winding_imbalance']==0 and row['exact_weld_topology']['edge_incidence_not_two']==0 and row['signed_volume_m3']>0
 q=report['native_geometry_readback'];sections=report['regular_sections']
 checks={
  'unchanged_empty_scene_original_defect_reproduced':report['stages'][0]['exact_duplicate_vertices_world']==366 and report['stages'][0]['crossnorm_lt_1e_14']==1461 and report['stages'][0]['exact_weld_topology']['edge_incidence_not_two']==418,
  'original_degenerate_frame_rejected':not passes(report['stages'][0]),
  'corrected_unbeveled_target_topology':passes(unb_row),
  'corrected_beveled_target_topology':passes(final_row),
  'zero_duplicate_triangle_coordinate_sets':q['duplicate_triangle_coordinate_sets']==0,
  'no_unused_evaluated_vertices':q['unused_vertices']==0,
  'all_native_bmesh_vertices_manifold':q['bmesh_nonmanifold_vertices']==0,
  'no_nonincident_bvh_surface_candidates':q['nonincident_triangle_bvh_candidates']==0,
  'genus_two_euler_characteristic':q['euler_characteristic']==-2,
  'same_ideal_unbeveled_envelope_within_2um':report['surface_comparisons']['same_ideal_unbeveled_frame']['max_abs_bounds_difference_m']<2e-6,
  'finite_unbeveled_surface_samples_within_2um':max(report['surface_comparisons']['same_ideal_unbeveled_frame']['a_to_b']['max_distance_m'],report['surface_comparisons']['same_ideal_unbeveled_frame']['b_to_a']['max_distance_m'])<2e-6,
  'nominal_14mm_by_47mm_sections_within_2um':all(abs(x['section_width_m']-fw)<2e-6 and abs(x['section_height_m']-fh)<2e-6 for x in sections),
  'intended_2mm_top_flat_setbacks_within_2um':all(max(abs(x['top_flat_setback_left_m']-.002),abs(x['top_flat_setback_right_m']-.002))<2e-6 for x in sections),
  'no_weld_or_delete_cleanup_in_final_recipe':all(m.type in {'BOOLEAN','BEVEL'} for m in corrected.modifiers),
 }
 original_layout=cli.original_layout_report.resolve()
 assert hashlib.sha256(original_layout.read_bytes()).hexdigest()=='032e788adbc4db4e3987a7736687acf79ab830665ba95b05e7302d89f0d8c6ea'
 original_data=json.loads(original_layout.read_text())
 checks['original_fitted_params_and_provenance_unchanged']=P==original_data['params_m'] and g['PARAMETER_PROVENANCE']==original_data['parameter_provenance']
 report['original_layout_report_sha256']='032e788adbc4db4e3987a7736687acf79ab830665ba95b05e7302d89f0d8c6ea'
 report['checks']=checks
 report['limits']=[
  'Targeted evaluated-surface topology checks only; not a certified geometric solid, absence-of-self-contact proof, structural strength or manufacturing qualification.',
  'BVH nonincident check skips triangle pairs sharing any vertex; it is supplemental and does not independently certify all possible adjacent-face overlaps.',
  'Surface comparison samples all vertices, unique triangulated-edge midpoints and triangle centroids using exhaustive Float64 point/triangle distances; this is not a global Hausdorff bound or exact-arithmetic proof.',
  'Degenerate triangles are filtered only for nearest-surface diagnostic distance evaluation, never removed from a native mesh or hidden from counts/acceptance.',
  '2um dimensional guard applies to inherited Float32 envelope/section comparison only; zero duplicates and fixed crossnorm>=1e-14 requirements were not relaxed.',
  'Native three-segment bevel approximates the fitted 2mm/profile0.5 shape; this is not a factory radius.',
  'Source vehicle is never loaded; original fitted stations, rails and tread parameters/provenance are unchanged.',
  'No blend/GLB save, export or render. No repository write or publication.',
  'Known second-tread conflict with front tyre/hub/rim remains FAILED, all six original closed-contact pairs and all16 whole-vehicle gates OPEN.',
 ]
 report['vehicle_loaded']=False;report['asset_saved_or_exported']=False;report['fitted_station_or_placement_changes']=False;report['intentional_shape_change']='Original bevel was effectively collapsed; corrected native recipe realizes the existing fitted 2mm bevel. Actual evaluated surface and volume change, quantified separately.'
 report['original_prefix_note']='Unchanged original source stopped before render setup; its auxiliary IN_PROGRESS file is a deliberately interrupted prefix, not this native process terminal record.'
 assert all(checks.values()),checks
 report['status']='BOUNDED_NATIVE_FRAME_TOPOLOGY_CORRECTION_PASS_NOT_SOLID_OR_INSTALLATION_CERTIFICATION'
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute,'Autoexec preference unexpectedly enabled at completion'
 report['autoexec_disabled_before_completion']=True
 report['script_sha256_end']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();write()
except Exception:
 report['status']='FAILED';report['error']=traceback.format_exc();write();raise
