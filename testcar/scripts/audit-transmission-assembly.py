"""Audit evaluated native geometry, separating candidate crossings from contacts.
BVH overlaps are investigation candidates, not an assertion of penetration depth.
Clutch clearances are measured from actual axial mesh extents.
"""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
geometry_only='--geometry-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/('work/transmission/rotary-geometry.blend' if geometry_only else 'outputs/MAZ543A_Transmission.blend')))
DATA=json.loads((ROOT/'work/transmission/poses.json').read_text());MOVERS=set(DATA['samples'][0]['pose'])
root=bpy.data.objects['S543_TRANSMISSION'];all_objects=list(root.children_recursive)

def body(ob):
    while ob and ob!=root:
        if ob.name in MOVERS or (ob.animation_data and ob.animation_data.action):return ob.name
        ob=ob.parent
    return 'fixed'

def geometry(ob,dg):
    evaluated=ob.evaluated_get(dg);mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
    vs=[evaluated.matrix_world@v.co for v in mesh.vertices]
    triangles=[tuple(t.vertices) for t in mesh.loop_triangles]
    tree=BVHTree.FromPolygons(vs,triangles,all_triangles=True)
    lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)]
    evaluated.to_mesh_clear()
    return {'name':ob.name,'body':body(ob),'lo':lo,'hi':hi,'tree':tree}

report={'clutches':[],'crossingCandidates':[],'limits':'BVH intersections are candidates only; seals and designed interfaces require interpretation. Axial clutch gaps use evaluated mesh bounds. This is not a complete solid-containment or load audit.'}
for frame in [0,120,240,360,480]:
    bpy.context.scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get()
    if geometry_only:
        for name,pose in DATA['samples'][frame]['pose'].items():
            ob=bpy.data.objects[name];ob.rotation_euler.x=pose['rx']
            if 'p' in pose:ob.location=(pose['p'][0],-pose['p'][2],pose['p'][1])
            if 'springTravel' in pose:
                spring=next(o for o in ob.children if o.type=='MESH' and o.data.shape_keys)
                # The same geometric morph law as the runtime, without baking actions.
                contact=DATA['contact'];travel=pose['springTravel'];pack=DATA['clutches'][pose['springPack']]
                max_travel=contact['pistonGap']+(pack['count']-1)*contact['plateGap'];sweep=contact['springTurns']*math.tau
                arc2=contact['springLength']**2+(contact['springRadius']*sweep)**2
                radius=math.sqrt(arc2-(contact['springLength']-travel)**2)/sweep
                end=math.sqrt(arc2-(contact['springLength']-max_travel)**2)/sweep
                for key,value in [('Pitch',travel/max_travel),('Radius',(radius-contact['springRadius'])/(end-contact['springRadius']))]:spring.data.shape_keys.key_blocks[key].value=value
        bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    gs=[geometry(o,dg) for o in all_objects if o.type in {'MESH','CURVE'}]
    index={g['name']:g for g in gs}
    for name,direction in [('first',-1),('second',1),('direct',1),('reverse',1)]:
        plates=sorted([g for g in gs if g['name'].startswith('TX_'+name+'_disc_')],key=lambda g:g['lo'][0])
        piston=index['TX_'+name+'_annular_piston']
        gaps=[b['lo'][0]-a['hi'][0] for a,b in zip(plates,plates[1:])]
        facegap=plates[0]['lo'][0]-piston['hi'][0] if direction==1 else piston['lo'][0]-plates[-1]['hi'][0]
        stop=index.get('TX_'+name+'_reaction_stop')
        stopgap=(stop['lo'][0]-plates[-1]['hi'][0] if direction==1 else plates[0]['lo'][0]-stop['hi'][0]) if stop else None
        report['clutches'].append({'frame':frame,'pack':name,'discCount':len(plates),'pistonToDiscMM':facegap*1000,'minInterDiscMM':min(gaps)*1000,'maxInterDiscMM':max(gaps)*1000,'stopGapMM':None if stopgap is None else stopgap*1000,'totalRemainingGapMM':(sum(gaps)+facegap)*1000})
    if frame in [0,120,240,360,480]:
        for i,a in enumerate(gs):
            for b in gs[i+1:]:
                if a['body']==b['body']:continue
                spans=[min(a['hi'][k],b['hi'][k])-max(a['lo'][k],b['lo'][k]) for k in range(3)]
                if min(spans)<1e-6:continue
                overlap=a['tree'].overlap(b['tree'])
                if overlap:report['crossingCandidates'].append({'frame':frame,'a':a['name'],'b':b['name'],'bodyA':a['body'],'bodyB':b['body'],'trianglePairs':len(overlap),'overlappingAABBAxialMM':spans[0]*1000})
nominal_pairs=[]
for name in ['first','second','reverse']:
    outer='29_moving' if name=='first' else 'outer_moving';inner='31_fixed' if name=='first' else 'inner_fixed'
    nominal_pairs += [(f'TX_{name}_booster_outer_bore',f'TX_{name}_piston_seal_{outer}'),
                      (f'TX_{name}_annular_piston',f'TX_{name}_piston_seal_{inner}')]
nominal_pairs += [('TX_direct_annular_piston','TX_direct_piston_seal_inner_fixed'),
                 ('TX_direct_body46_sleeve','TX_direct_piston_seal_outer_moving')]
nominal_pairs += [('TX_direct_body46_sleeve',f'TX_direct_feed_seal_{j}') for j in range(2)]
allowed={frozenset(pair) for pair in nominal_pairs}
# A rigid part called "seal_land" is not an elastomer. Match exact pairs,
# never exempt candidates merely because their names contain "seal".
report['unexpectedCrossings']=[x for x in report['crossingCandidates'] if frozenset((x['a'],x['b'])) not in allowed]
(ROOT/('work/transmission/direct-area-assembly-audit.json' if geometry_only else 'outputs/transmission-assembly-audit.json')).write_text(json.dumps(report,indent=2))
print(json.dumps({'clutches':report['clutches'],'candidateCount':len(report['crossingCandidates']),'candidates':report['crossingCandidates'][:35]},indent=2),flush=True)
assert not report['unexpectedCrossings'],'Unexpected rigid crossings; inspect the saved assembly audit'
