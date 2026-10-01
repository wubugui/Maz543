// Read-only verification. This tool never changes assets or runtime objects.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {verifyLocalTransform,worldMatrices,verifyClosedWorldGeometry} from './scoped-body-transforms.mjs';
const config=JSON.parse(await fs.readFile(process.argv[2],'utf8'));
async function read(p){const b=await fs.readFile(p);assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(8),b.length);const len=b.readUInt32LE(12);return {b,j:JSON.parse(b.subarray(20,20+len)),bin:28+len};}
const old=await read(config.source),now=await read(config.output),native=await read(config.candidate);
const nativeNodes=new Map(native.j.nodes.map(n=>[n.name,n]));
const changed=new Set(config.changedMeshes??[]),added=new Set(config.newNodes??[]),removed=new Set(config.removedNodes??[]);
const digest=(x,id)=>{const v=x.j.bufferViews[id];assert.equal(v.buffer,0);return crypto.createHash('sha256').update(x.b.subarray(x.bin+(v.byteOffset??0),x.bin+(v.byteOffset??0)+v.byteLength)).digest('hex');};
const hashes=x=>(x.j.images??[]).map(i=>{assert.ok(i.bufferView!==undefined,'external image unverified');return digest(x,i.bufferView)}).sort();
assert.deepEqual(hashes(now),hashes(old),'original embedded textures changed');
function parents(j){const m=new Map();for(const n of j.nodes)for(const i of n.children??[])m.set(j.nodes[i].name,n.name);return m;}
const op=parents(old.j),np=parents(now.j),on=new Map(old.j.nodes.map(n=>[n.name,n])),nn=new Map(now.j.nodes.map(n=>[n.name,n]));
const nativeParents=parents(native.j);
const ow=worldMatrices(old.j),nw=worldMatrices(now.j);
assert.equal(on.size,old.j.nodes.length,'duplicate source names');assert.equal(nn.size,now.j.nodes.length,'duplicate result names');
assert.deepEqual(new Set([...on.keys()].filter(n=>!nn.has(n))),removed,'unapproved missing nodes');
assert.deepEqual(new Set([...nn.keys()].filter(n=>!on.has(n))),added,'unapproved new nodes');
for(const name of added){
 const n=nn.get(name),r=nativeNodes.get(name);assert.ok(r,name+' native node missing');
 assert.equal(np.get(name),nativeParents.get(name),name+' native parent');
 for(const k of ['translation','rotation','scale','matrix'])assert.deepEqual(n[k],r[k],name+' native transform');
}
for(const name of changed)assert.ok(on.get(name)?.mesh!==undefined&&nn.get(name)?.mesh!==undefined,'changed mesh must exist in both assets: '+name);
let preserved=0,triangles=0;
for(const n of now.j.nodes){
 if(n.mesh!==undefined)for(const p of now.j.meshes[n.mesh].primitives)triangles+=now.j.accessors[p.indices].count/3;
 const before=on.get(n.name);if(!before)continue;
 const latch=/^BL_Front_cover_latch_(-?0\.46)$/.exec(n.name);
 if(latch){
  assert.ok(changed.has(n.name),'Reparenting allowed only for declared diagnostic latch');
  assert.equal(np.get(n.name),'BL_R3_latch_release_pivot_'+latch[1]);
  verifyClosedWorldGeometry(ow.get(n.name),nw.get(n.name));
 }else{
  verifyLocalTransform(before,n);
  assert.equal(np.get(n.name),op.get(n.name),n.name+' parent changed');
 }
 if(before.mesh===undefined){assert.equal(n.mesh,undefined,n.name+' gained mesh');continue;}
 assert.ok(n.mesh!==undefined,n.name+' lost mesh');if(changed.has(n.name))continue;
 verifyClosedWorldGeometry(ow.get(n.name),nw.get(n.name));
 const a=old.j.meshes[before.mesh].primitives,b=now.j.meshes[n.mesh].primitives;assert.equal(b.length,a.length,n.name+' primitives');
 for(let i=0;i<a.length;i++){
  assert.deepEqual(Object.keys(b[i].attributes).sort(),Object.keys(a[i].attributes).sort(),n.name+' attributes');
  for(const k of ['mode','targets'])assert.deepEqual(b[i][k],a[i][k],n.name+' '+k);
  assert.equal(now.j.accessors[b[i].indices].count,old.j.accessors[a[i].indices].count,n.name+' index count');
  const ad=a[i].extensions?.KHR_draco_mesh_compression,bd=b[i].extensions?.KHR_draco_mesh_compression;assert.ok(ad&&bd,n.name+' compressed stream missing');
  assert.deepEqual(bd.attributes,ad.attributes,n.name+' Draco attribute mapping');assert.equal(digest(now,bd.bufferView),digest(old,ad.bufferView),n.name+' original geometry bytes changed');
  const allowedMaterial=config.changedMaterialNodes?.[n.name];
  if(allowedMaterial){
   const mat=now.j.materials[b[i].material];assert.equal(mat.name,allowedMaterial,n.name+' material replacement');
   const spec=config.materialSpecs?.[n.name]??{baseColorFactor:[.008,.011,.009,1],metallicFactor:0,roughnessFactor:.78};
   assert.equal(mat.normalTexture,undefined,'Scoped plain material has unexpected normal map');
   assert.equal(mat.pbrMetallicRoughness?.baseColorTexture,undefined,'Scoped plain material has unexpected color map');
   const pbr=mat.pbrMetallicRoughness;
   assert.ok(spec.baseColorFactor?.length===4&&spec.baseColorFactor.every(x=>Number.isFinite(x)&&x>=0&&x<=1),'Invalid material color specification');
   for(const k of ['metallicFactor','roughnessFactor']){const value=spec[k];assert.ok(Number.isFinite(value)&&value>=0&&value<=1,'Invalid material '+k);assert.ok(Math.abs(pbr[k]-value)<1e-6,'Scoped material '+k);}
   const expected=spec.baseColorFactor;assert.ok(expected.every((x,k)=>Math.abs(pbr.baseColorFactor[k]-x)<1e-6),'Scoped material color');
  }else assert.deepEqual(now.j.materials[b[i].material],old.j.materials[a[i].material],n.name+' material definition changed');
 }
 preserved++;
}
// New and deliberately changed meshes must retain the actual native export's
// compressed streams and material definitions; packing cannot substitute them.
let nativeStreams=0;
for(const name of [...changed,...config.newMeshes]){
 const n=nn.get(name),r=nativeNodes.get(name);assert.ok(n&&r,name);
 for(const k of ['translation','rotation','scale','matrix'])assert.deepEqual(n[k],r[k],name+' native transform');
 const a=now.j.meshes[n.mesh].primitives,b=native.j.meshes[r.mesh].primitives;assert.equal(a.length,b.length);
 for(let i=0;i<a.length;i++){
  const ae=a[i].extensions.KHR_draco_mesh_compression,be=b[i].extensions.KHR_draco_mesh_compression;
  assert.deepEqual(ae.attributes,be.attributes);
  assert.equal(digest(now,ae.bufferView),digest(native,be.bufferView),name+' native bytes');
  assert.deepEqual(now.j.materials[a[i].material],native.j.materials[b[i].material],name+' native material');nativeStreams++;
 }
}
const report={nativeStreams,status:'PASS for declared scope only',source:config.source,result:config.output,preservedMeshNodes:preserved,changedMeshes:[...changed],newNodes:[...added],removedNodes:[...removed],declaredHingeRebases:config.rebasedNodes??{},changedMaterialNodes:config.changedMaterialNodes??{},unchangedTransformsAndParents:false,declaredDiagnosticLatchReparents:2,closedLatchWorldMatricesPreserved:true,closedWorldGeometryPreservedForOriginalUnchangedStreams:true,embeddedTexturesUnchanged:true,effectiveTriangles:triangles,fullVehicleAcceptance:'16 OPEN',limits:'Changed surfaces require separate native geometry/clearance, browser and photographic verification; this does not certify factory dimensions or FPS.'};
await fs.writeFile(config.output.replace('.glb','-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
