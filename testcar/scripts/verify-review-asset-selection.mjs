// Pure configuration and delivered-file checks; deliberately no browser/GPU claim.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import ts from 'typescript';
import * as T from 'three';
import {registerHooks} from 'node:module';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const source=await fs.readFile(path.join(root,'lib/reviewVehicleAsset.ts'),'utf8');
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {selectReviewVehicleAsset,PRODUCTION_VEHICLE_ASSET,reviewCandidateMetadata}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const cases=[
 ['',true,'production'],['',false,'production'],['?quality=full',true,'production'],
 ['?asset-review=tyre-v2',true,'tyre-v2'],['?asset-review=tyre-v2&quality=full&debug-handle=1',true,'tyre-v2'],
 ['?asset-review=tyre-v2',false,'production'],['?asset-review=tyre-v2&render-worker=1',true,'production'],
 ['?asset-review=tyre-v2&worker-build=1',true,'production'],['?asset-review=tyre-v2&render-worker=0',true,'tyre-v2'],
 ['?asset-review=unknown',true,'production'],['?asset-review=',true,'production'],
 ['?asset-review=tyre-v2&asset-review=tyre-v2',true,'production'],['?asset-review=tyre-v2&asset-review=../../secret',true,'production'],
 ['?asset-review=https://example.invalid/model.glb',true,'production'],['?asset-review=../../model.glb',true,'production'],
 ];
const results=cases.map(([search,development,kind])=>{const got=selectReviewVehicleAsset(search,development);assert.equal(got.kind,kind);if(kind==='production'){assert.equal(got.url,PRODUCTION_VEHICLE_ASSET.url);assert.equal(got.exportFilename,PRODUCTION_VEHICLE_ASSET.exportFilename);if(search.includes('asset-review='))assert.ok(got.notice?.includes('生产资产'),'Rejected review selection must identify production');}else{assert.ok(got.url.startsWith('/models/review/'));assert.ok(got.exportFilename.includes('CANDIDATE'));assert.ok(got.notice.includes('未替换生产'));}return {search,development,kind:got.kind,url:got.url};});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const production=await fs.readFile(path.join(root,'public/models/maz543a-blender.glb'));
const candidate=await fs.readFile(path.join(root,'public/models/review/maz543a-tyre-v2.glb'));
const portable=await fs.readFile(path.join(root,'outputs/cloud-tyre-lettering-portable-20260930/maz543a-blender-portable-reexport-v2.glb'));
assert.equal(production.subarray(0,4).toString(),'glTF');assert.equal(candidate.subarray(0,4).toString(),'glTF');
assert.equal(hash(production),PRODUCTION_VEHICLE_ASSET.sha256);assert.equal(hash(candidate),selectReviewVehicleAsset('?asset-review=tyre-v2',true).sha256);assert.ok(candidate.equals(portable));
const runtime=await fs.readFile(path.join(root,'lib/vehicleViewport.ts'),'utf8'),ui=await fs.readFile(path.join(root,'components/workshop.tsx'),'utf8');
assert.ok(runtime.includes('loadNative(reviewAsset.url)'));assert.ok(runtime.includes('a.download=reviewAsset.exportFilename'));
assert.ok(runtime.includes('renderedRoot.userData.reviewCandidate=reviewCandidateMetadata(reviewAsset)'));assert.ok(ui.includes('reviewAsset.notice&&'));
registerHooks({resolve(specifier,context,next){try{return next(specifier,context);}catch(error){if(specifier.startsWith('.')&&!/\.[a-z]+$/i.test(specifier))return next(specifier+'.ts',context);throw error;}}});
const {exportGLBBlob}=await import('../lib/export-model.ts');
const metadataExports=[];
for(const asset of [PRODUCTION_VEHICLE_ASSET,selectReviewVehicleAsset('?asset-review=tyre-v2',true)]){
 // A metadata-only unit fixture through the real exporter, never a replacement vehicle test.
 const object=new T.Group();object.name='MAZ543_REFERENCE_CHASSIS';const metadata=reviewCandidateMetadata(asset);if(metadata)object.userData.reviewCandidate=metadata;
 const prior=JSON.stringify(object.userData),blob=await exportGLBBlob(object,new Map()),bytes=Buffer.from(await blob.arrayBuffer());
 assert.equal(bytes.subarray(0,4).toString(),'glTF');assert.equal(bytes.readUInt32LE(8),bytes.length);
 const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12))),node=json.nodes.find(n=>n.name===object.name);assert.ok(node);assert.deepEqual(node.extras?.reviewCandidate,metadata);assert.equal(JSON.stringify(object.userData),prior);
 metadataExports.push({kind:asset.kind,bytes:bytes.length,exportedMetadata:node.extras?.reviewCandidate??null,sourceMetadataUnchanged:true});
}
const baselineRef='aa04cfd6a30c7ca47f8c5004a9c8adde2b4bbe15';
const oldRuntime=execFileSync('git',['show',baselineRef+':testcar/lib/vehicleViewport.ts'],{cwd:root,encoding:'utf8'});
function poseBlock(text){const start=text.indexOf('      model.update(latest.current,t);'),end=text.indexOf('      if(gpuTimer&&pendingTimers.length',start);assert.ok(start>=0&&end>start);return text.slice(start,end);}
assert.equal(poseBlock(runtime),poseBlock(oldRuntime),'Mechanical presentation changed during asset-selector integration');
const mechanicalSources=[];
for(const file of ['mechanics.ts','mechanicalTimeline.ts','starting.ts','suspension.ts','transmission.ts','transmissionDynamics.ts','transmissionHydraulics.ts','cooling.ts']){const now=await fs.readFile(path.join(root,'lib',file)),before=execFileSync('git',['show',baselineRef+':testcar/lib/'+file],{cwd:root});assert.ok(now.equals(before),file);mechanicalSources.push({file,sha256:hash(now)});}
const report={status:'PASS_SELECTION_AND_FILE_CHECKS_ONLY',baselineRef,metadataOnlyRealExporterChecks:metadataExports,mechanicalPoseBlockSHA256:hash(poseBlock(runtime)),mechanicalPoseCharacters:poseBlock(runtime).length,unchangedMechanicalSources:mechanicalSources,cases:results,productionSHA256:hash(production),candidateSHA256:hash(candidate),portableCopyExact:true,browserRuntime:'NOT_RUN_ACCESS_BLOCKED',scope:'Actual selector, file bytes, unchanged mechanical sources, static wiring and real exporter metadata-only fixtures; not a full vehicle export, rendered UI, picking, motion, performance or WebGL test.'};
const out=path.join(root,'outputs/cloud-review-entry-20260930');await fs.mkdir(out,{recursive:true});await fs.writeFile(path.join(out,'selection-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({...report,cases:results.length},null,2));
