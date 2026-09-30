// Compare actual decoded attributes and oriented triangles, without relying on encoded order.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
await fs.mkdir('work/cloud-tyre-audit',{recursive:true});
await fs.copyFile('public/draco/draco_wasm_wrapper.js','work/cloud-tyre-audit/draco-wrapper.cjs');
const require=createRequire(import.meta.url);
const draco=await require('../work/cloud-tyre-audit/draco-wrapper.cjs')({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
async function read(path){const b=await fs.readFile(path),n=b.readUInt32LE(12);return {b,j:JSON.parse(b.subarray(20,20+n)),start:28+n};}
const a=await read(process.argv[2]??'outputs/cloud-tyre-lettering-portable-20260930/maz543a-blender-candidate.glb');
const b=await read(process.argv[3]??'work/cloud-tyre-reproduce/maz543a-blender-candidate.glb');
function bytes(asset,p){const v=asset.j.bufferViews[p.extensions.KHR_draco_mesh_compression.bufferView];return asset.b.subarray(asset.start+(v.byteOffset??0),asset.start+(v.byteOffset??0)+v.byteLength);}
function fingerprint(asset,p){
 const e=p.extensions.KHR_draco_mesh_compression,d=new draco.Decoder(),m=new draco.Mesh(),buf=new draco.DecoderBuffer(),data=bytes(asset,p);buf.Init(data,data.length);const status=d.DecodeBufferToMesh(buf,m);assert.ok(status.ok());
 const keys=Object.keys(e.attributes).sort(),arrays=[];
 for(const key of keys){const attr=d.GetAttributeByUniqueId(m,e.attributes[key]),v=new draco.DracoFloat32Array();d.GetAttributeFloatForAllPoints(m,attr,v);arrays.push({key,components:attr.num_components(),v});}
 const width=arrays.reduce((s,x)=>s+x.components,0),vertices=[];
 for(let i=0;i<m.num_points();i++){const tuple=Buffer.alloc(width*4);let offset=0;for(const x of arrays)for(let j=0;j<x.components;j++,offset+=4)tuple.writeFloatLE(x.v.GetValue(i*x.components+j),offset);vertices.push(hash(tuple));}
 const surfaceVertices=[];for(let i=0;i<m.num_points();i++){const values=[];for(const x of arrays)if(x.key!=='TANGENT')for(let j=0;j<x.components;j++)values.push(x.v.GetValue(i*x.components+j));surfaceVertices.push(hash(values.join(',')));}
 const face=new draco.DracoInt32Array(),triangles=[],surfaceTriangles=[];
 for(let i=0;i<m.num_faces();i++){d.GetFaceFromMesh(m,i,face);const v=[0,1,2].map(j=>vertices[face.GetValue(j)]);const w=[0,1,2].map(j=>surfaceVertices[face.GetValue(j)]);surfaceTriangles.push([w.join(''),[w[1],w[2],w[0]].join(''),[w[2],w[0],w[1]].join('')].sort()[0]);triangles.push([v.join(''),[v[1],v[2],v[0]].join(''),[v[2],v[0],v[1]].join('')].sort()[0]);}
 const attributeMultisets={},tangentValues=new Map();
 for(const x of arrays){const values=[];for(let i=0;i<m.num_points();i++){const tuple=[];for(let j=0;j<x.components;j++)tuple.push(x.v.GetValue(i*x.components+j));const text=tuple.join(',');values.push(text);if(x.key==='TANGENT')tangentValues.set(text,(tangentValues.get(text)??0)+1);}attributeMultisets[x.key]=hash(values.sort().join(';'));}
 const result={surfaceWithoutTangents:hash(surfaceTriangles.sort().join('')),_tangentValues:tangentValues,attributeMultisets,attributes:arrays.map(x=>[x.key,x.components]),vertices:m.num_points(),triangles:m.num_faces(),vertexAttributeMultiset:hash(vertices.sort().join('')),orientedTriangleAttributeMultiset:hash(triangles.sort().join(''))};
 for(const x of arrays)draco.destroy(x.v);draco.destroy(face);draco.destroy(m);draco.destroy(buf);draco.destroy(d);return result;
}
const nodes=new Map(b.j.nodes.map(n=>[n.name,n]));let identical=0;const changed=[];
for(const n of a.j.nodes){if(n.mesh===undefined)continue;const other=nodes.get(n.name);assert.ok(other);const pa=a.j.meshes[n.mesh].primitives,pb=b.j.meshes[other.mesh].primitives;assert.equal(pa.length,pb.length);
 for(let i=0;i<pa.length;i++){if(hash(bytes(a,pa[i]))===hash(bytes(b,pb[i]))){identical++;continue;}const fa=fingerprint(a,pa[i]),fb=fingerprint(b,pb[i]);const tangentDifference=[];for(const key of new Set([...fa._tangentValues.keys(),...fb._tangentValues.keys()])){const delta=(fa._tangentValues.get(key)??0)-(fb._tangentValues.get(key)??0);if(delta)tangentDifference.push({tuple:key.split(',').map(Number),beforeMinusAfter:delta});}delete fa._tangentValues;delete fb._tangentValues;changed.push({node:n.name,primitive:i,tangentDifference,before:fa,after:fb,equal:JSON.stringify(fa)===JSON.stringify(fb)});}
}
const report={byteIdentical:a.b.equals(b.b),identicalPrimitiveStreams:identical,changedStreams:changed,allChangedStreamsDecodedExactlyEqual:changed.every(x=>x.equal),scope:'Float32 decoded vertex attribute multisets and oriented triangle-attribute multisets; not browser runtime or factory accuracy.'};
await fs.writeFile(process.env.MAZ_REEXPORT_REPORT??'work/cloud-tyre-reproduce/reexport-comparison.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));assert.ok(report.allChangedStreamsDecodedExactlyEqual,'Re-export decoded attributes differ; investigate rather than claim bitwise reproduction');
