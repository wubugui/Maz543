from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/viewport-lifecycle-audit'
original=json.loads((folder/'after-main-to-worker.json').read_text(encoding='utf8'))
fixed=json.loads((folder/'after-fixed-main-exit.json').read_text(encoding='utf8'))
def owners(data):
 result={}
 for event in data['events']:result.setdefault(event['page'],[]).append(event)
 return result
rows=[]
for owner,events in owners(fixed).items():
 hides=[event for event in events if event['event']=='pagehide']
 if not hides:continue
 hide=hides[-1];following=[event for event in events if event['time']>=hide['time']]
 names=[event['event'] for event in following]
 completed=next((event for event in following if event['event']=='main-viewport-disposed'),None)
 rows.append({'owner':owner,'persisted':hide['details']['persisted'],'exitEvents':names,
  'documentOwnerRelease':any(event['event']=='viewport-owner-release' and event['details'].get('reason')=='document-exit' for event in following),
  'mainDisposerReturned':completed is not None,'mainDisposeMs':None if completed is None else completed['time']-hide['time'],
  'renderWorkerDisposalAckDuringExit':'render-worker-disposed-ack' in names})
baseline=[events for events in owners(original).values() if any(event['event']=='pagehide' for event in events)]
assert len(baseline)==1
assert not any(event['event']=='viewer-effect-cleanup' for event in baseline[0])
main=next(row for row in rows if row['mainDisposerReturned']);assert main['documentOwnerRelease'] and not main['persisted']
worker=next(row for row in rows if 'render-client-stop' in row['exitEvents']);assert worker['documentOwnerRelease'] and not worker['persisted']
snapshots=[event for event in fixed['events'] if event['event']=='snapshot']
report={'baselineNonPersistedExitSkippedReactCleanup':True,'fixedExits':rows,'snapshots':snapshots,
 'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','limits':'Actual ordinary main document release completed; experimental render client exit cleanup started. No hard-navigation worker disposal ack, real BFCache restoration, GC-normalized live heap, isolated GPU memory or sustained FPS proof.'}
(folder/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'baselineNonPersistedExitSkippedReactCleanup':True,'fixedExits':rows},ensure_ascii=False,indent=2))
