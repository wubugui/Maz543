// Decoded geometry transport only. Does not approve the vehicle or preserve production streams.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import * as T from 'three';
const dir=process.env.MAZ_COMPOSITE_EXPORT_DIR??'work/cloud-left-driver-export-20261001';
await fs.mkdir('work/cloud-tyre-audit',{recursive:true});
await fs.copyFile('public/draco/draco_wasm_wrapper.js','work/cloud-tyre-audit/draco-wrapper.cjs');
const factory=createRequire(import.meta.url)('../work/cloud-tyre-audit/draco-wrapper.cjs');
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
const bytes=await fs.readFile(process.env.MAZ_COMPOSITE_GLB??dir+'/native-export.glb'),length=bytes.readUInt32LE(12);
const after={bytes,j:JSON.parse(bytes.subarray(20,20+length)),start:28+length};
const index=new Map(after.j.nodes.map((n,i)=>[n.name,i]));assert.equal(index.size,after.j.nodes.length);
const reference=JSON.parse(await fs.readFile(dir+'/driver-world-reference.json','utf8')),refBytes=await fs.readFile(dir+'/driver-world-reference.bin');
const view=(a,id)=>{const v=a.j.bufferViews[id];return a.bytes.subarray(a.start+(v.byteOffset??0),a.start+(v.byteOffset??0)+v.byteLength);};
const parent=new Map();after.j.nodes.forEach((n,i)=>(n.children??[]).forEach(c=>parent.set(c,i)));


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
 assert.ok(r.name.startsWith('BL_Left_driver_')||['cab_0029','cab_0030','cab_0031'].includes(r.name));
 if(r.name.startsWith('cab_'))assert.equal(after.j.nodes[parent.get(i)]?.name,'cab_pivot_004');
 let triangles=0;const points=[];
 for(const p of after.j.meshes[n.mesh].primitives){const d=decode(p);triangles+=d.triangles;points.push(...d.points.map(v=>v.applyMatrix4(matrix(i))));}
 assert.equal(triangles,r.triangles,r.name+' triangle count');
 const expected=[];for(let k=0;k<r.vertices;k++){const off=r.byteOffset+k*12;expected.push(new T.Vector3(refBytes.readFloatLE(off),refBytes.readFloatLE(off+4),refBytes.readFloatLE(off+8)));}
 const error=Math.max(deviation(points,expected),deviation(expected,points));rows.push({name:r.name,decodedVertices:points.length,nativeVertices:r.vertices,triangles,maxWorldVertexDeviationM:error});
}
assert.equal(rows.length,10,'Seven controls and three wheel meshes');

const report={status:rows.some(r=>r.maxWorldVertexDeviationM>=2e-5)?'FAIL_NATIVE_DRIVER_TO_DRACO_TRANSPORT':'PASS_NATIVE_DRIVER_TO_DRACO_TRANSPORT_ONLY',sha256:crypto.createHash('sha256').update(bytes).digest('hex'),results:rows,maxWorldVertexDeviationM:Math.max(...rows.map(r=>r.maxWorldVertexDeviationM)),scope:'Actual Draco decoding and saved-native vertex correspondence, triangle counts and driver-part identity. No production-stream preservation, whole-car shape comparison, browser rendering or UV acceptance.',all16VehicleGates:'OPEN'};
await fs.writeFile(dir+'/driver-transport-verification.json',JSON.stringify(report,null,2));console.log(report.status,rows.length,report.maxWorldVertexDeviationM);assert.ok(rows.every(r=>r.maxWorldVertexDeviationM<2e-5),'Driver transport exceeds unchanged 20 micrometre threshold');
