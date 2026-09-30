import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const root=process.cwd(),out='outputs/tangent-audit';
const require=createRequire(import.meta.url);
const factory=require(path.join(root,'work/tangent-audit/draco-wrapper.cjs'));
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
async function read(file){const bytes=await fs.readFile(file),size=bytes.readUInt32LE(12);return {bytes,json:JSON.parse(bytes.subarray(20,20+size)),offset:28+size};}
function accessor(asset,id){
 const a=asset.json.accessors[id],v=asset.json.bufferViews[a.bufferView],size={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];
 const Type={5126:Float32Array,5125:Uint32Array,5123:Uint16Array,5121:Uint8Array}[a.componentType];assert.ok(Type);assert.ok(!a.sparse);
 const array=new Type(a.count*size),bytes=new Uint8Array(array.buffer),width=Type.BYTES_PER_ELEMENT,base=asset.offset+(v.byteOffset??0)+(a.byteOffset??0);
 for(let i=0;i<a.count;i++)bytes.set(asset.bytes.subarray(base+i*(v.byteStride??size*width),base+i*(v.byteStride??size*width)+size*width),i*size*width);
 return {array,size};
}
function plain(asset,p){return {attributes:Object.fromEntries(Object.entries(p.attributes).map(([name,id])=>[name,accessor(asset,id)])),indices:accessor(asset,p.indices).array};}
function decode(asset,p){
 const ext=p.extensions.KHR_draco_mesh_compression,v=asset.json.bufferViews[ext.bufferView],bytes=asset.bytes.subarray(asset.offset+(v.byteOffset??0),asset.offset+(v.byteOffset??0)+v.byteLength);
 const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(bytes,bytes.length);
 const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());const attributes={};
 for(const [name,id] of Object.entries(ext.attributes)){
  const attribute=decoder.GetAttributeByUniqueId(mesh,id),values=new draco.DracoFloat32Array();decoder.GetAttributeFloatForAllPoints(mesh,attribute,values);
  const array=new Float32Array(values.size());for(let i=0;i<array.length;i++)array[i]=values.GetValue(i);
  attributes[name]={array,size:attribute.num_components()};draco.destroy(values);
 }
 const indices=new Uint32Array(mesh.num_faces()*3),face=new draco.DracoInt32Array();for(let i=0;i<mesh.num_faces();i++){decoder.GetFaceFromMesh(mesh,i,face);for(let j=0;j<3;j++)indices[i*3+j]=face.GetValue(j);}
 draco.destroy(face);draco.destroy(mesh);draco.destroy(buffer);draco.destroy(decoder);return {attributes,indices};
}
// Compare complete float-bit corner records, preserving UV/normal/tangent seams,
// face winding and multiplicity. Only cyclic face rotation and storage order
// are ignored; no rounding, tolerance, geometric welding or face removal.
function canonical(data,names){
 const count=data.attributes.POSITION.array.length/3,vertices=[];
 for(let i=0;i<count;i++)vertices.push(names.map(name=>{const {array,size}=data.attributes[name];return Buffer.from(array.buffer,array.byteOffset+i*size*4,size*4).toString('hex');}).join(''));
 const faces=[];for(let i=0;i<data.indices.length;i+=3){const [a,b,c]=Array.from(data.indices.subarray(i,i+3),index=>vertices[index]);faces.push([a+b+c,b+c+a,c+a+b].sort()[0]);}
 const hash=list=>crypto.createHash('sha256').update(list.sort().join('\n')).digest('hex');
 return {vertices:count,uniqueVertexRecords:new Set(vertices).size,triangles:faces.length,vertexMultisetSha256:hash(vertices),uniqueVertexRecordsSha256:hash([...new Set(vertices)]),orientedCornerMultisetSha256:hash(faces)};
}
const plainAsset=await read(`${out}/native-samples-plain.glb`),compressed=await read(`${out}/native-samples-draco-lossless.glb`),rows=[];
for(const node of plainAsset.json.nodes.filter(n=>n.mesh!==undefined)){
 const other=compressed.json.nodes.find(n=>n.name===node.name);assert.ok(other,node.name);
 const a=plainAsset.json.meshes[node.mesh],b=compressed.json.meshes[other.mesh];assert.equal(a.primitives.length,b.primitives.length);
 for(let i=0;i<a.primitives.length;i++){
  const source=plain(plainAsset,a.primitives[i]),decoded=decode(compressed,b.primitives[i]),names=Object.keys(source.attributes).sort();assert.deepEqual(Object.keys(decoded.attributes).sort(),names);
  for(const name of names){assert.ok(source.attributes[name].array instanceof Float32Array);assert.equal(source.attributes[name].size,decoded.attributes[name].size);}
  const baseline=canonical(source,names),candidate=canonical(decoded,names);
  const surfaceAttributesBitExact=baseline.triangles===candidate.triangles&&baseline.orientedCornerMultisetSha256===candidate.orientedCornerMultisetSha256;
  const uniqueVertexRecordsBitExact=baseline.uniqueVertexRecordsSha256===candidate.uniqueVertexRecordsSha256;
  rows.push({node:node.name,primitive:i,attributes:names,baseline,candidate,surfaceAttributesBitExact,uniqueVertexRecordsBitExact,vertexStorageIdentical:baseline.vertexMultisetSha256===candidate.vertexMultisetSha256,additionalDuplicateVertexRecords:candidate.vertices-baseline.vertices});
 }
}
const report={plainBytes:plainAsset.bytes.length,compressedBytes:compressed.bytes.length,rows,limits:'Two native source objects only. Zero quantization is verified against the same Blender uncompressed glTF export, not against every Blender internal value. Complete oriented triangle-corner attribute records are compared with multiplicity; duplicate vertex storage and connectivity are not claimed identical. Source zero tangents are not repaired. No runtime asset replaced.'};
await fs.writeFile(`${out}/lossless-draco-verification.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));assert.ok(rows.every(row=>row.surfaceAttributesBitExact&&row.uniqueVertexRecordsBitExact));
