// Actual Draco asset QA; this does not execute a browser.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import * as T from 'three';
import {validateBytes} from 'gltf-validator';
const dir=process.env.MAZ_LETTERING_DIR??'outputs/cloud-tyre-lettering-portable-20260930';
await fs.mkdir('work/cloud-tyre-audit',{recursive:true});
await fs.copyFile('public/draco/draco_wasm_wrapper.js','work/cloud-tyre-audit/draco-wrapper.cjs');
const factory=createRequire(import.meta.url)('../work/cloud-tyre-audit/draco-wrapper.cjs');
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
async function read(path){const bytes=await fs.readFile(path),length=bytes.readUInt32LE(12);return {bytes,j:JSON.parse(bytes.subarray(20,20+length)),start:28+length};}
const before=await read('public/models/maz543a-blender.glb'),after=await read(process.env.MAZ_CANDIDATE_GLB??dir+'/maz543a-blender-candidate.glb');
const config=JSON.parse(await fs.readFile(dir+'/pack-config.json','utf8'));
const reference=JSON.parse(await fs.readFile(dir+'/glyph-world-reference.json','utf8')),refBytes=await fs.readFile(dir+'/glyph-world-reference.bin');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const view=(a,id)=>{const v=a.j.bufferViews[id];return a.bytes.subarray(a.start+(v.byteOffset??0),a.start+(v.byteOffset??0)+v.byteLength);};
const textures=a=>a.j.images.map(i=>digest(view(a,i.bufferView))).sort();
assert.deepEqual(textures(before),textures(after),'Embedded texture bytes changed');
const changed=new Set(config.changedMeshes),newNames=new Set(config.newMeshes),index=new Map(after.j.nodes.map((n,i)=>[n.name,i]));
assert.equal(index.size,after.j.nodes.length,'Duplicate node names');
let unchanged=0;
for(const old of before.j.nodes){
 const n=after.j.nodes[index.get(old.name)];assert.ok(n,old.name);
 for(const key of ['matrix','translation','rotation','scale'])assert.deepEqual(n[key],old[key],old.name+' transform '+key);
 if(old.mesh===undefined||changed.has(old.name))continue;
 const a=before.j.meshes[old.mesh].primitives,b=after.j.meshes[n.mesh].primitives;assert.equal(a.length,b.length);
 for(let i=0;i<a.length;i++)assert.equal(digest(view(before,a[i].extensions.KHR_draco_mesh_compression.bufferView)),digest(view(after,b[i].extensions.KHR_draco_mesh_compression.bufferView)),old.name+' compressed bytes');
 unchanged++;
}
assert.deepEqual(new Set(after.j.nodes.filter(n=>!before.j.nodes.some(o=>o.name===n.name)).map(n=>n.name)),newNames);
const parent=new Map();after.j.nodes.forEach((n,i)=>(n.children??[]).forEach(c=>parent.set(c,i)));
const originalIndex=new Map(before.j.nodes.map((n,i)=>[n.name,i])),originalParent=new Map();before.j.nodes.forEach((n,i)=>(n.children??[]).forEach(c=>originalParent.set(c,i)));
const glyphCounts=Array(8).fill(0);
const world=new Map();function matrix(i){if(world.has(i))return world.get(i);const n=after.j.nodes[i],m=n.matrix?new T.Matrix4().fromArray(n.matrix):new T.Matrix4().compose(new T.Vector3(...(n.translation??[0,0,0])),new T.Quaternion(...(n.rotation??[0,0,0,1])),new T.Vector3(...(n.scale??[1,1,1])));if(parent.has(i))m.premultiply(matrix(parent.get(i)));world.set(i,m);return m;}
function decode(primitive){
 const e=primitive.extensions.KHR_draco_mesh_compression,bytes=view(after,e.bufferView),decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(bytes,bytes.length);
 const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());
 const attribute=decoder.GetAttributeByUniqueId(mesh,e.attributes.POSITION),values=new draco.DracoFloat32Array();decoder.GetAttributeFloatForAllPoints(mesh,attribute,values);
 const points=[];for(let i=0;i<values.size();i+=3)points.push(new T.Vector3(values.GetValue(i),values.GetValue(i+1),values.GetValue(i+2)));
 const triangles=mesh.num_faces();draco.destroy(values);draco.destroy(mesh);draco.destroy(buffer);draco.destroy(decoder);return {points,triangles};
}
function deviation(a,b){let max=0;for(const p of a){let best=Infinity;for(const q of b)best=Math.min(best,p.distanceToSquared(q));max=Math.max(max,best);}return Math.sqrt(max);}
const rows=[];
for(const r of reference.parts){
 const i=index.get(r.name);assert.ok(i!==undefined,r.name);const n=after.j.nodes[i];
 const match=/^BL_Tyre_(\d+)_emboss_(\d+)$/.exec(r.name);assert.ok(match,r.name);const tyre=Number(match[1]);assert.ok(tyre>=0&&tyre<8);glyphCounts[tyre]++;
 const spinName='wheels_pivot_'+String(2+7*tyre).padStart(3,'0'),carrierName='wheels_pivot_'+String(1+7*tyre).padStart(3,'0'),rubberName='BL_Merged_'+spinName+'_Tyre_rubber';
 const spin=index.get(spinName),carrier=index.get(carrierName);assert.equal(parent.get(i),spin,r.name+' actual spin parent');assert.equal(parent.get(spin),carrier,r.name+' carrier parent');assert.equal(after.j.nodes[parent.get(carrier)]?.name,'wheels');assert.equal(n.extras?.tyreIndex,tyre);
 assert.equal(parent.get(index.get(rubberName)),spin,'Glyph and existing rubber must share a spin');assert.ok(originalIndex.has(spinName)&&originalIndex.has(rubberName));assert.equal(before.j.nodes[originalParent.get(originalIndex.get(rubberName))]?.name,spinName,'Production spin identity');
 let triangles=0;const points=[];
 for(const p of after.j.meshes[n.mesh].primitives){const d=decode(p);triangles+=d.triangles;points.push(...d.points.map(v=>v.applyMatrix4(matrix(i))));}
 assert.equal(triangles,r.triangles,r.name+' triangle count');
 const expected=[];for(let k=0;k<r.vertices;k++){const off=r.byteOffset+k*12;expected.push(new T.Vector3(refBytes.readFloatLE(off),refBytes.readFloatLE(off+4),refBytes.readFloatLE(off+8)));}
 const error=Math.max(deviation(points,expected),deviation(expected,points));assert.ok(error<2e-5,r.name+' asset/source vertex mismatch '+error);rows.push({name:r.name,spinParent:spinName,carrierParent:carrierName,tyreIndex:tyre,decodedVertices:points.length,nativeVertices:r.vertices,triangles,maxWorldVertexDeviationM:error});
}
assert.deepEqual(glyphCounts,Array(8).fill(18),'Exactly eighteen glyphs per original wheel spin');
// A separate, conservative longitudinal separating-plane test on decoded bytes.
// This is conditional on the reviewed fixed-X, zero-rear-steering motion contract.
function descendants(i){return [i,...(after.j.nodes[i].children??[]).flatMap(descendants)];}
const wheelEnvelopes=[];
for(const [wheel,axleX] of [[4,2.42],[5,2.42],[6,4.62],[7,4.62]]){
 const spinId=index.get(`wheels_pivot_${String(2+7*wheel).padStart(3,'0')}`);assert.ok(spinId!==undefined);
 const spinWorld=matrix(spinId),inverse=spinWorld.clone().invert();assert.ok(Math.abs(spinWorld.elements[12]-axleX)<1e-6);
 assert.ok([0,1,2,4,5,6,8,9,10].every(k=>Math.abs(spinWorld.elements[k]-([0,5,10].includes(k)?1:0))<1e-6),'Unsupported wheel rest axes or scale');
 let radius=0,meshNodes=0;
 for(const id of descendants(spinId)){
  const n=after.j.nodes[id];if(n.mesh===undefined)continue;assert.ok(n.skin===undefined);meshNodes++;
  for(const p of after.j.meshes[n.mesh].primitives){assert.ok(!p.targets?.length,'Deforming wheel requires another envelope');for(const v of decode(p).points){v.applyMatrix4(matrix(id)).applyMatrix4(inverse);radius=Math.max(radius,Math.hypot(v.x,v.y));}}
 }
 wheelEnvelopes.push({wheel,axleX,radialEnvelopeM:radius,meshNodes,minX:axleX-radius,maxX:axleX+radius});
}
const rearEnvelopes=[];
for(const [name,id] of index){
 if(!name.startsWith('BL_RearRestoration_'))continue;const n=after.j.nodes[id];if(n.mesh===undefined)continue;let min=Infinity,max=-Infinity;
 for(const p of after.j.meshes[n.mesh].primitives)for(const v of decode(p).points){v.applyMatrix4(matrix(id));min=Math.min(min,v.x);max=Math.max(max,v.x);}
 rearEnvelopes.push({name,minX:min,maxX:max});
}
assert.equal(rearEnvelopes.length,12);
const envelopePairs=rearEnvelopes.flatMap(part=>wheelEnvelopes.map(w=>({part:part.name,wheel:w.wheel,gapM:Math.max(part.minX-w.maxX,w.minX-part.maxX)-.00004})));
const longitudinalEnvelope={status:envelopePairs.every(p=>p.gapM>0)?'PASS_CONDITIONAL_SEPARATION':'INCONCLUSIVE',minimumGapM:Math.min(...envelopePairs.map(p=>p.gapM)),wheelEnvelopes,rearEnvelopes,conditions:'Current assembled rigid meshes, fixed longitudinal axle positions, zero rear steering, arbitrary wheel spin/camber and transverse/vertical suspension motion. Excludes deformation, axle fore/aft flex, other parts and actual browser-runtime validation.'};
const validated=await validateBytes(new Uint8Array(after.bytes),{uri:'maz543a-blender-candidate.glb'});assert.equal(validated.issues.numErrors,0);assert.equal(validated.issues.numWarnings,0);
const report={status:'PASS_SCOPED_ASSET_CHECKS',sha256:digest(after.bytes),bytes:after.bytes.length,unchangedCompressedMeshNodes:unchanged,unchangedEmbeddedTextures:after.j.images.length,longitudinalEnvelope,glyphMeshes:rows.length,glyphParentBindingsVerified:rows.length,glyphsPerWheel:glyphCounts,maxNativeAssetDeviationM:Math.max(...rows.map(r=>r.maxWorldVertexDeviationM)),gltfErrors:validated.issues.numErrors,gltfWarnings:validated.issues.numWarnings,parts:rows,limits:'Decoded asset under standard glTF world matrices, not an actual browser-render/runtime test. No factory geometry, typography, physical load or whole-vehicle acceptance.'};
const reportPath=process.env.MAZ_REPORT_PATH??'work/cloud-tyre-audit/asset-verification.json';
await fs.writeFile(reportPath,JSON.stringify(report,null,2));console.log(JSON.stringify({...report,parts:undefined},null,2));
