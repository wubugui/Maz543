from pathlib import Path
from collections import Counter
import json

root=Path(__file__).resolve().parents[1]
folder=root/'outputs/context-draw-order'
captures={p.stem:json.loads(p.read_text(encoding='utf8')) for p in folder.glob('*-trace.json')}

def material_order(data):
    aliases={}
    for obj in data['sourceOrder']:
        for slot,material in enumerate(obj['materials']):
            aliases.setdefault(material['id'],[]).append((obj['sceneId'],slot,material['name']))
    return [aliases[key] for key in sorted(aliases)]

def segments(sequence):
    result=[]
    for row in sequence:
        key=row[5:10]
        if not result or result[-1]['pass']!=key:result.append({'pass':key,'rows':[]})
        result[-1]['rows'].append(row)
    return result

comparisons={}
names=list(captures)
for index,a_name in enumerate(names):
    for b_name in names[index+1:]:
        a,b=captures[a_name],captures[b_name]
        fields=['width','height','pixelRatio','meshes','draws','triangles','view','ao','sceneInputSha256','noiseSha256','pixelSha256','drawSequenceSha256']
        equality={field:a['report'][field]==b['report'][field] for field in fields}
        aa,bb=segments(a['sequence']),segments(b['sequence'])
        rows=[]
        for i,(left,right) in enumerate(zip(aa,bb)):
            x,y=left['rows'],right['rows']
            divergence=next((j for j,(u,v) in enumerate(zip(x,y)) if u!=v),None)
            rows.append({'segment':i,'mainPass':left['pass'],'otherPass':right['pass'],'counts':[len(x),len(y)],
              'sameMembers':Counter(json.dumps(row) for row in x)==Counter(json.dumps(row) for row in y),
              'firstDifferentDraw':divergence,'mainExample':x[divergence] if divergence is not None else None,
              'otherExample':y[divergence] if divergence is not None else None})
        materials_a,materials_b=material_order(a),material_order(b)
        first_material=next((i for i,(x,y) in enumerate(zip(materials_a,materials_b)) if x!=y),None)
        comparisons[a_name+' vs '+b_name]={'equal':equality,'segmentCounts':[len(aa),len(bb)],'segments':rows,
          'sameRelativeMaterialAllocationOrder':materials_a==materials_b,
          'firstMaterialOrderDifference':first_material,
          'materialOrderExamples':None if first_material is None else [materials_a[first_material][:3],materials_b[first_material][:3]]}

report={'comparisons':comparisons,'limits':'Finite complete-frame traces with raw allocation IDs excluded from frame hashes. Sequence/membership and input subset comparison does not itself prove the cause of pixel differences or physical/model fidelity.','goal':'ACTIVE','wholeVehicleGates':'16 OPEN'}
(folder/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'comparisons':{name:{'samePixels':row['equal']['pixelSha256'],
 'sameRecordedInputs':all(row['equal'][key] for key in ['width','height','pixelRatio','view','ao','sceneInputSha256','noiseSha256']),
 'sameSequence':row['equal']['drawSequenceSha256'],'sameRelativeMaterialAllocationOrder':row['sameRelativeMaterialAllocationOrder'],
 'differentSegments':[part['segment'] for part in row['segments'] if part['firstDifferentDraw'] is not None]}
 for name,row in comparisons.items()}},ensure_ascii=False,indent=2))
