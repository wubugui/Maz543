import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
const root=process.cwd(),out=path.join(root,'outputs/tangent-audit');await fs.mkdir(out,{recursive:true});
await fs.mkdir('work/tangent-audit',{recursive:true});await fs.copyFile('public/draco/draco_wasm_wrapper.js','work/tangent-audit/draco-wrapper.cjs');
const require=createRequire(import.meta.url),factory=require(path.join(root,'work/tangent-audit/draco-wrapper.cjs'));
const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
async function glb(file){const bytes=await fs.readFile(file),jsonSize=bytes.readUInt32LE(12);return {bytes,json:JSON.parse(bytes.subarray(20,20+jsonSize).toString()),binaryOffset:28+jsonSize};}
function accessor(asset,id){const a=asset.json.accessors[id],v=asset.json.bufferViews[a.bufferView],size={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];assert.equal(a.componentType,5126);const result=new Float32Array(a.count*size),offset=asset.binaryOffset+(v.byteOffset??0)+(a.byteOffset??0),stride=v.byteStride??size*4;for(let i=0;i<a.count;i++)for(let j=0;j<size;j++)result[i*size+j]=asset.bytes.readFloatLE(offset+i*stride+j*4);return result;}
function decode(asset,primitive,keepQuantized=false){
 const extension=primitive.extensions.KHR_draco_mesh_compression,v=asset.json.bufferViews[extension.bufferView],bytes=asset.bytes.subarray(asset.binaryOffset+(v.byteOffset??0),asset.binaryOffset+(v.byteOffset??0)+v.byteLength);
 const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(bytes,bytes.length);if(keepQuantized)decoder.SkipAttributeTransform(draco.GENERIC);
 const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());const attributes={},quantization={};
 for(const [name,uniqueId] of Object.entries(extension.attributes)){
  const attribute=decoder.GetAttributeByUniqueId(mesh,uniqueId),values=new draco.DracoFloat32Array();decoder.GetAttributeFloatForAllPoints(mesh,attribute,values);
  const array=new Float32Array(values.size());for(let i=0;i<array.length;i++)array[i]=values.GetValue(i);attributes[name]={array,size:attribute.num_components()};draco.destroy(values);
  const transform=new draco.AttributeQuantizationTransform();if(transform.InitFromAttribute(attribute))quantization[name]={bits:transform.quantization_bits(),range:transform.range(),min:Array.from({length:attribute.num_components()},(_,i)=>transform.min_value(i))};draco.destroy(transform);
 }
 const indices=new Uint32Array(mesh.num_faces()*3),face=new draco.DracoInt32Array();for(let i=0;i<mesh.num_faces();i++){decoder.GetFaceFromMesh(mesh,i,face);for(let j=0;j<3;j++)indices[i*3+j]=face.GetValue(j);}draco.destroy(face);draco.destroy(mesh);draco.destroy(buffer);draco.destroy(decoder);return {attributes,indices,quantization};
}
const exported=await glb('outputs/render-worker-evidence/whole-current-pose.glb'),cases=[
 ['maz543a-blender.glb','BL_Merged_body_OD_green_aged_enamel'],['maz543a-blender.glb','BL_Merged_body_Rubber_window_seals'],['maz543a-cooling.glb','COOL_upper_input_flange_0']
];
const cache=new Map(),rows=[];
for(const [file,name] of cases){
 if(!cache.has(file))cache.set(file,await glb('public/models/'+file));const asset=cache.get(file),node=asset.json.nodes.find(n=>n.name===name);assert.ok(node,name);
 const primitive=asset.json.meshes[node.mesh].primitives[0],source=decode(asset,primitive),tangent=source.attributes.TANGENT.array,uv=source.attributes.TEXCOORD_0.array;
 const outputNode=exported.json.nodes.find(n=>n.name===name),outputPrimitive=exported.json.meshes[outputNode.mesh].primitives[0],outputTangent=accessor(exported,outputPrimitive.attributes.TANGENT);
 const equal=tangent.length===outputTangent.length&&Buffer.from(tangent.buffer).equals(Buffer.from(outputTangent.buffer));
 let min=Infinity,max=0,nonUnit=0;const tiny=[];
 for(let i=0;i<tangent.length/4;i++){const length=Math.hypot(...tangent.subarray(i*4,i*4+3));min=Math.min(min,length);max=Math.max(max,length);if(Math.abs(length-1)>1e-4)nonUnit++;if(length<.01)tiny.push(i);}
 const samples=[];for(const index of tiny.slice(0,8)){
  const determinants=[];for(let i=0;i<source.indices.length;i+=3){const tri=source.indices.subarray(i,i+3);if(!tri.includes(index))continue;const [a,b,c]=tri;determinants.push((uv[b*2]-uv[a*2])*(uv[c*2+1]-uv[a*2+1])-(uv[b*2+1]-uv[a*2+1])*(uv[c*2]-uv[a*2]));}
  samples.push({vertex:index,tangent:Array.from(tangent.subarray(index*4,index*4+4)),incidentUvDeterminants:determinants});
 }
 const quantized=decode(asset,primitive,true);rows.push({file,name,vertices:tangent.length/4,triangles:source.indices.length/3,decodedMatchesExportExactly:equal,quantization:quantized.quantization.TANGENT,rawTinySample:tiny.length?Array.from(quantized.attributes.TANGENT.array.subarray(tiny[0]*4,tiny[0]*4+4)):[],minimumLength:min,maximumLength:max,nonUnitAt1e4:nonUnit,tinyCount:tiny.length,samples});
 for(const semantic of ['POSITION','NORMAL','TANGENT','TEXCOORD_0'])await fs.writeFile(path.join(out,`${name}-${semantic}.bin`),new Uint8Array(source.attributes[semantic].array.buffer));
 await fs.writeFile(path.join(out,`${name}-indices.bin`),new Uint8Array(source.indices.buffer));
}
await fs.writeFile(path.join(out,'decoded-source-report.json'),JSON.stringify({cases:rows,limits:'Directly decodes the current native GLB with the same shipped Draco WASM. No native or runtime asset changes. UV determinants describe decoded triangles; original Blender loop tangents require a separate check.'},null,2));
console.log(JSON.stringify(rows.map(({samples,...row})=>row),null,2));
