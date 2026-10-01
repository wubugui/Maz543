// Native-to-Draco geometry and rest-pose transport, not browser or vehicle acceptance.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import * as T from 'three';
const dir='work/cloud-va180-web-20261001';
const input=process.argv[2]??`${dir}/native-export.glb`;
const output=process.argv[3]??`${dir}/native-transport.json`;
const threshold=2e-5;
await fs.mkdir('work/cloud-tyre-audit',{recursive:true});
await fs.copyFile('public/draco/draco_wasm_wrapper.js','work/cloud-tyre-audit/draco-wrapper.cjs');
const factory=createRequire(import.meta.url)('../work/cloud-tyre-audit/draco-wrapper.cjs');
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
const bytes=await fs.readFile(input);assert.equal(bytes.readUInt32LE(0),0x46546c67);assert.equal(bytes.readUInt32LE(8),bytes.length);
const length=bytes.readUInt32LE(12),j=JSON.parse(bytes.subarray(20,20+length)),bin=28+length;
const index=new Map(j.nodes.map((n,i)=>[n.name,i]));assert.equal(index.size,j.nodes.length,'Duplicate node names');
const reference=JSON.parse(await fs.readFile(`${dir}/native-world-reference.json`,'utf8'));
const refBytes=await fs.readFile(`${dir}/native-world-reference.bin`);assert.equal(refBytes.length,reference.bytes);
const parents=new Map();j.nodes.forEach((n,i)=>(n.children??[]).forEach(c=>{assert.ok(!parents.has(c),'Multiple parents');parents.set(c,i);}));
const local=i=>{const n=j.nodes[i];return n.matrix?new T.Matrix4().fromArray(n.matrix):new T.Matrix4().compose(new T.Vector3(...(n.translation??[0,0,0])),new T.Quaternion(...(n.rotation??[0,0,0,1])),new T.Vector3(...(n.scale??[1,1,1])));};
const worlds=new Map();function world(i){if(worlds.has(i))return worlds.get(i);const m=local(i);if(parents.has(i))m.premultiply(world(parents.get(i)));worlds.set(i,m);return m;}
function decode(p){
 const ext=p.extensions?.KHR_draco_mesh_compression;assert.ok(ext,'Uncompressed primitive needs an explicit decoder');
 const v=j.bufferViews[ext.bufferView],raw=bytes.subarray(bin+(v.byteOffset??0),bin+(v.byteOffset??0)+v.byteLength);
 const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(raw,raw.length);
 const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());
 const attribute=decoder.GetAttributeByUniqueId(mesh,ext.attributes.POSITION),values=new draco.DracoFloat32Array();
 decoder.GetAttributeFloatForAllPoints(mesh,attribute,values);const points=[];
 for(let k=0;k<values.size();k+=3)points.push(new T.Vector3(values.GetValue(k),values.GetValue(k+1),values.GetValue(k+2)));
 const triangles=mesh.num_faces();draco.destroy(values);draco.destroy(mesh);draco.destroy(buffer);draco.destroy(decoder);return {points,triangles};
}
function boundedNearest(a,b){
 // All points within threshold must lie in one of these 27 grid cells.
 const grid=new Map(),cell=p=>[Math.floor(p.x/threshold),Math.floor(p.y/threshold),Math.floor(p.z/threshold)];
 for(const p of b){const key=cell(p).join(',');if(!grid.has(key))grid.set(key,[]);grid.get(key).push(p);}
 let maximum=0,outside=0;
 for(const p of a){const c=cell(p);let best=Infinity;
  for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)for(const q of grid.get([c[0]+x,c[1]+y,c[2]+z].join(','))??[])best=Math.min(best,p.distanceToSquared(q));
  if(best>threshold**2)outside++;if(Number.isFinite(best))maximum=Math.max(maximum,Math.sqrt(best));
 }
 return {maximumFiniteNeighbourErrorM:maximum,outsideThreshold:outside};
}
// Boundary-crossing, duplicate and deliberate-failure controls for the grid.
assert.equal(boundedNearest([new T.Vector3(threshold*.999,0,0)],[new T.Vector3(threshold*1.001,0,0)]).outsideThreshold,0);
assert.equal(boundedNearest([new T.Vector3(0,0,0)],[new T.Vector3(threshold*1.1,0,0)]).outsideThreshold,1);
assert.equal(boundedNearest([new T.Vector3(-threshold*.001,0,0)],[new T.Vector3(threshold*.001,0,0),new T.Vector3(threshold*.001,0,0)]).outsideThreshold,0);
const rows=[],failures=[];
for(const r of reference.parts){
 const i=index.get(r.name);assert.notEqual(i,undefined,r.name+' absent');const n=j.nodes[i];assert.notEqual(n.mesh,undefined,r.name+' has no mesh');
 let triangles=0;const points=[];
 for(const primitive of j.meshes[n.mesh].primitives){const d=decode(primitive);triangles+=d.triangles;for(const p of d.points)points.push(p.applyMatrix4(world(i)));}
 const expected=[];for(let k=0;k<r.vertices;k++){const o=r.byteOffset+k*12;expected.push(new T.Vector3(refBytes.readFloatLE(o),refBytes.readFloatLE(o+4),refBytes.readFloatLE(o+8)));}
 const forward=boundedNearest(points,expected),reverse=boundedNearest(expected,points);
 const row={name:r.name,sourceType:r.source_type,nativeVertices:r.vertices,decodedVertices:points.length,nativeTriangles:r.triangles,decodedTriangles:triangles,forward,reverse};rows.push(row);
 if(triangles!==r.triangles||forward.outsideThreshold||reverse.outsideThreshold)failures.push(r.name);
}
const poses=[];
for(const [name,p]of Object.entries(reference.node_poses)){
 const i=index.get(name);assert.notEqual(i,undefined,name+' pose node absent');
 const expectedLocal=new T.Matrix4().set(...p.local_gltf_matrix_rows.flat()),expectedWorld=new T.Matrix4().set(...p.world_gltf_matrix_rows.flat());
 const delta=(a,b)=>Math.max(...a.elements.map((x,k)=>Math.abs(x-b.elements[k])));
 const row={name,localError:delta(local(i),expectedLocal),worldError:delta(world(i),expectedWorld),parent:j.nodes[parents.get(i)]?.name??null};poses.push(row);
 if(row.localError>2e-6||row.worldError>2e-6||row.parent!==p.parent)failures.push(name+' pose/parent');
}
assert.equal(rows.filter(r=>r.sourceType==='FONT'&&r.name.startsWith('VA180 B4 /')).length,7,'Seven actual observed-text outline nodes');
const report={status:failures.length?'FAIL_NATIVE_CAB_TRANSPORT':'PASS_NATIVE_CAB_TRANSPORT_ONLY',input,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),nativeSourceSHA256:reference.source_sha256,thresholdM:threshold,failures,rows,poses,
 scope:'Actual Draco decoding, bidirectional vertex distance within20um, triangle counts and saved-native node rest poses/parents. Does not validate appearance, native UV equivalence, button dynamics, browser rendering or factory accuracy.',wholeVehicleAcceptance:'16 OPEN'};
await fs.writeFile(output,JSON.stringify(report,null,2)+'\n');console.log(report.status,{parts:rows.length,poses:poses.length,failures});assert.equal(failures.length,0,'Native cab transport mismatch');
