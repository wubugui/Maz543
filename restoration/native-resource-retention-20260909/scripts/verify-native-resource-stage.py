from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/native-resource-retention'
before=json.loads((folder/'before-census.json').read_text())
after=json.loads((folder/'after-census.json').read_text())
assert after['releasedGeometries']==30
assert before['referenced']==after['after']['referenced']
assert after['after']['orphaned']['geometries']==0
archive=root.parent/'restoration/context-draw-order-20260909/outputs/context-draw-order/main-canonical-side-trace.json'
old=json.loads(archive.read_text())['report'];new=json.loads((folder/'full-side-frame.json').read_text())
keys=['width','height','pixelRatio','meshes','draws','triangles','view','ao','sceneInputSha256','noiseSha256','pixelSha256','drawSequenceSha256']
comparison={key:old[key]==new[key] for key in keys};assert all(comparison.values())
report={'passed':True,'beforeGeometryBufferBytes':before['owned']['geometryBufferBytes'],'afterGeometryBufferBytes':after['after']['owned']['geometryBufferBytes'],
 'removedExclusiveBufferReferencesBytes':before['owned']['geometryBufferBytes']-after['after']['owned']['geometryBufferBytes'],
 'retainedResourceCensusUnchanged':True,'frameComparison':comparison,'frameBaseline':str(archive),
 'goal':'ACTIVE','wholeVehicleGates':'16 OPEN','limits':'One complete identical-input fixed-sort side pose and resource identity/buffer census. Does not prove immediate GC/driver release, all poses or improved dynamic FPS.'}
(folder/'verified-stage.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
