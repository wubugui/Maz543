from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
archives=[ROOT.parent/'restoration/display-neutral-cache-20260909',ROOT.parent/'restoration/display-asset-precision-20260909',ROOT.parent/'restoration/render-worker-and-blob-20260909']
names=['lib/mechanics.ts','lib/mechanicalTimeline.ts','lib/starting.ts','lib/suspension.ts','lib/transmission.ts','lib/transmissionDynamics.ts','lib/transmissionHydraulics.ts','lib/cooling.ts','lib/export-model.ts','lib/binaryGltfBlob.ts','lib/exportTangents.ts']
rows=[]
for name in names:
 baseline=next((folder/name for folder in archives if (folder/name).is_file()),None)
 assert baseline is not None,name
 current=(ROOT/name).read_bytes();assert current==baseline.read_bytes(),name
 rows.append({'file':name,'baseline':str(baseline),'sha256':hashlib.sha256(current).hexdigest()})
def section(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
old=(archives[0]/'lib/vehicleViewport.ts').read_text(encoding='utf8');current=(ROOT/'lib/vehicleViewport.ts').read_text(encoding='utf8')
pose_start='      model.update(latest.current,t);';pose_end='      const profileUpdateEnd='
pose=section(current,pose_start,pose_end);assert pose==section(old,pose_start,pose_end)
config_start='    renderer.setPixelRatio(';config_end='    const renderInspection='
assert section(current,config_start,config_end)==section(old,config_start,config_end)
report={'passed':True,'unchangedFiles':rows,'unchangedPoseBlock':{'characters':len(pose),'sha256':hashlib.sha256(pose.encode()).hexdigest()},'rendererQualitySettingsUnchanged':True,'limits':'Source comparison against the latest applicable immutable checkpoints. Does not establish calibrated physical fidelity, cross-context pixels, hardware memory release or dynamic performance.'}
(ROOT/'outputs/directional-shadow-cache/source-integrity.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'passed':True,'unchangedFiles':len(rows),'unchangedPoseCharacters':len(pose)}))
