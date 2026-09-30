from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
old=(ROOT/'work/render-worker-refactor/viewer-before.tsx').read_text(encoding='utf8')
new=(ROOT/'lib/vehicleViewport.ts').read_text(encoding='utf8')
def section(text,start,end):
 return text[text.index(start):text.index(end,text.index(start))]
start='      model.update(latest.current,t);';end='      if(gpuTimer&&pendingTimers.length'
old_pose=section(old,start,end);new_pose=section(new,start,end)
assert old_pose==new_pose,'Mechanical pose and display transform block changed'
archive=ROOT.parent/'restoration/simulation-clock-worker-20260909'
files=['lib/mechanics.ts','lib/mechanicalTimeline.ts','lib/starting.ts','lib/suspension.ts','lib/transmission.ts','lib/transmissionDynamics.ts','lib/transmissionHydraulics.ts','lib/cooling.ts']
rows=[]
for name in files:
 before=(archive/name).read_bytes();after=(ROOT/name).read_bytes();assert before==after,name
 rows.append({'file':name,'sha256':hashlib.sha256(after).hexdigest(),'unchanged':True})
report={'passed':True,'unchangedPoseBlock':{'characters':len(new_pose),'sha256':hashlib.sha256(new_pose.encode()).hexdigest()},'mechanicalSources':rows,'limits':'Source preservation and native asset hashes do not replace cross-context pixel comparison, calibration or full vehicle acceptance. Worker host, scheduling and export diagnostics are separate changes.'}
(ROOT/'outputs/render-worker-evidence/source-integrity.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'passed':True,'poseCharacters':len(new_pose),'unchangedMechanicalSources':len(rows)}))
