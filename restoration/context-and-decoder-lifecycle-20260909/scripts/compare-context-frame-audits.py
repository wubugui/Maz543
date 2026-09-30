from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/context-frame-audit'
reports={}
for path in sorted(folder.glob('*-ax.txt')):
    if path.name=='final-normal-ax.txt':continue
    text=path.read_text(encoding='utf8')
    if 'text {\n  "gpu"' not in text:continue
    data,_=json.JSONDecoder().raw_decode(text[text.index('text {')+5:])
    if 'pixelSha256' not in data:continue
    name=path.name.removesuffix('-ax.txt');reports[name]=data
    (folder/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
comparisons={}
for pose in ['perspective','side','side-door']:
    a,b=reports.get('main-'+pose),reports.get('worker-'+pose)
    if not a or not b:continue
    keys=['width','height','pixelRatio','meshes','draws','triangles','view','ao','sceneInputSha256','drawSequenceSha256','noiseSha256','pixelSha256']
    rows={key:a[key]==b[key] for key in keys}
    blank=hashlib.sha256(bytes(a['width']*a['height']*4)).hexdigest()
    comparisons[pose]={'equal':rows,'mainReadbackError':a['readbackError'],'workerReadbackError':b['readbackError'],
      'mainFrameSource':a['frameSource'],'workerFrameSource':b['frameSource'],
      'allZeroBufferRejected':a['pixelSha256']!=blank and b['pixelSha256']!=blank,
      'samePixels':rows['pixelSha256'],'sameViewAndInputs':all(rows[key] for key in ['width','height','pixelRatio','view','ao','sceneInputSha256','noiseSha256'])}
summary={'comparisons':comparisons,'captures':list(reports),'goal':'ACTIVE','wholeVehicleGates':'16 OPEN',
 'limits':'Current actual RGBA SHA-256 equality only at tested identical-input poses. Not all interactions, all shader inputs, production lifecycle, GPU memory release or dynamic FPS evidence. Geometry layouts/pose fingerprints do not replace complete source asset verification.'}
(folder/'comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary,indent=2))
