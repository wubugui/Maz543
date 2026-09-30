import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const factory=require('../work/tangent-audit/draco-wrapper.cjs');
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
const read=async f=>{const bytes=await fs.readFile(f),j=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));return {bytes,j,start:28+bytes.readUInt32LE(12)};};
const before=await read('../restoration/searchlight-correction-20260930/maz543a-blender.glb');
const after=await read('public/models/maz543a-blender.glb');
const digestView=(x,id)=>{const v=x.j.bufferViews[id];return crypto.createHash('sha256').update(x.bytes.subarray(x.start+(v.byteOffset??0),x.start+(v.byteOffset??0)+v.byteLength)).digest('hex');};
const textures=x=>x.j.images.map(i=>digestView(x,i.bufferView)).sort();
assert.deepEqual(textures(after),textures(before),'embedded textures must be unchanged');
const newNames=new Set(after.j.nodes.map(n=>n.name));
const obsoleteRoots=['drive_0002','drive_pivot_002','drive_pivot_007','drive_pivot_012'];
const obsolete=new Set();
function visit(i){obsolete.add(before.j.nodes[i].name);for(const j of before.j.nodes[i].children??[])visit(j);}
for(const name of obsoleteRoots){const i=before.j.nodes.findIndex(n=>n.name===name);assert.ok(i>=0);visit(i);}
const missing=before.j.nodes.filter(n=>!newNames.has(n.name)).map(n=>n.name);
assert.deepEqual(new Set(missing),obsolete,'only the old transmission placeholders already removed by the runtime may be absent');
const triangles=(x,n)=>n.mesh===undefined?0:x.j.meshes[n.mesh].primitives.reduce((s,p)=>s+x.j.accessors[p.indices].count/3,0);
const beforeTriangles=before.j.nodes.filter(n=>!obsolete.has(n.name)).reduce((s,n)=>s+triangles(before,n),0);
const afterTriangles=after.j.nodes.reduce((s,n)=>s+triangles(after,n),0);
assert.equal(afterTriangles,beforeTriangles,'all effective body triangles must remain');
const modified=new Set(['BL_Merged_cab_pivot_001_Headlamp_prismatic_glass','BL_Merged_cab_pivot_001_OD_green_aged_enamel','BL_Merged_cab_pivot_001_Phosphated_steel']);
function cornerHash(x,p){
  const ext=p.extensions.KHR_draco_mesh_compression,v=x.j.bufferViews[ext.bufferView];
  const bytes=x.bytes.subarray(x.start+(v.byteOffset??0),x.start+(v.byteOffset??0)+v.byteLength);
  const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(bytes,bytes.length);
  const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());
  const names=Object.keys(ext.attributes).sort(),attrs=[];
  for(const name of names){const attr=decoder.GetAttributeByUniqueId(mesh,ext.attributes[name]),values=new draco.DracoFloat32Array();decoder.GetAttributeFloatForAllPoints(mesh,attr,values);const a=new Float32Array(values.size());for(let i=0;i<a.length;i++)a[i]=values.GetValue(i);attrs.push({name,a,size:attr.num_components()});draco.destroy(values);}
  const vertices=[];for(let i=0;i<mesh.num_points();i++)vertices.push(crypto.createHash('sha256').update(Buffer.concat(attrs.map(({a,size})=>Buffer.from(a.buffer,i*size*4,size*4)))).digest('hex'));
  const face=new draco.DracoInt32Array(),faces=[];
  for(let i=0;i<mesh.num_faces();i++){decoder.GetFaceFromMesh(mesh,i,face);const [a,b,c]=[0,1,2].map(j=>vertices[face.GetValue(j)]);faces.push([a+b+c,b+c+a,c+a+b].sort()[0]);}
  const result={names,triangles:faces.length,hash:crypto.createHash('sha256').update(faces.sort().join('\n')).digest('hex')};
  draco.destroy(face);draco.destroy(mesh);draco.destroy(buffer);draco.destroy(decoder);return result;
}
let unchangedMeshes=0;const reorderedCompression=[];
for(const old of before.j.nodes){
  if(obsolete.has(old.name))continue;
  const n=after.j.nodes.find(n=>n.name===old.name);assert.ok(n,old.name);
  for(const key of ['translation','rotation','scale','matrix'])assert.deepEqual(n[key],old[key],`${old.name} ${key}`);
  if(old.mesh!==undefined&&!modified.has(old.name)){
    const a=before.j.meshes[old.mesh].primitives,b=after.j.meshes[n.mesh].primitives;
    assert.equal(a.length,b.length,old.name);
    for(let i=0;i<a.length;i++){
      if(digestView(before,a[i].extensions.KHR_draco_mesh_compression.bufferView)!==digestView(after,b[i].extensions.KHR_draco_mesh_compression.bufferView)){
        assert.deepEqual(cornerHash(after,b[i]),cornerHash(before,a[i]),`${old.name} decoded oriented surface attributes`);
        reorderedCompression.push(old.name);
      }
    }
    unchangedMeshes++;
  }
}
const native=JSON.parse(await fs.readFile('outputs/searchlight-correction-20260930/native-verification.json','utf8'));
const browser=JSON.parse(await fs.readFile('outputs/searchlight-correction-20260930/after/browser-evidence.json','utf8'));
assert.equal(browser.parts.length,3);assert.equal(browser.httpStatus,200);assert.deepEqual(browser.errors,[]);
let maxDeviation=0;
for(const p of browser.parts){
  const n=native.files[1].parts.find(x=>x.name===p.name);assert.equal(p.parent,n.parent);
  for(const key of ['min','max'])for(let i=0;i<3;i++)maxDeviation=Math.max(maxDeviation,Math.abs(p[key][i]-n.after[key][i]));
}
assert.ok(maxDeviation<1e-5,'native/browser lamp geometry mismatch');
const report={status:'PASS for scoped checks only',fullVehicleAcceptance:'16 OPEN',missingObsoleteNodes:missing.length,effectiveBodyTriangles:afterTriangles,unchangedSurfaceMeshNodes:unchangedMeshes,reorderedCompression,embeddedTexturesUnchanged:true,nativeBrowserMaxDeviationM:maxDeviation,renderer:browser.renderer,dimensionStatus:'photo-fitted, not factory calibrated'};
await fs.writeFile('outputs/searchlight-correction-20260930/export-parity.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
