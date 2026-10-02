// Preserve the existing production surfaces during a scoped native correction.
// This is an asset packaging step, separate from the read-only verifier.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {verifyLocalTransform} from './scoped-body-transforms.mjs';
import {assertPackedDoorPositionPrecision} from './cab-door-position-precision.mjs';
const config=process.argv[2]?JSON.parse(await fs.readFile(process.argv[2],'utf8')):null;
if(config)assert.ok(config.report,'Scoped packaging must declare its own report path');
const sourcePath=config?.source??'../restoration/searchlight-correction-20260930/maz543a-blender.glb';
const candidatePath=config?.candidate??'work/searchlight-correction-20260930/maz543a-blender.glb';
const outputPath=config?.output??'public/models/maz543a-blender.glb';
async function read(file){const bytes=await fs.readFile(file),length=bytes.readUInt32LE(12);return {bytes,j:JSON.parse(bytes.subarray(20,20+length)),start:28+length};}
const before=await read(sourcePath),candidate=await read(candidatePath);
// Check the actual retained/native door streams before any packaging mutation or write.
const doorPositionPrecision=await assertPackedDoorPositionPrecision(before,candidate,config);
const changed=new Set(config?.changedMeshes??['BL_Merged_cab_pivot_001_Headlamp_prismatic_glass','BL_Merged_cab_pivot_001_OD_green_aged_enamel','BL_Merged_cab_pivot_001_Phosphated_steel']);
const j=candidate.j,binLength=j.buffers[0].byteLength;
const chunks=[candidate.bytes.subarray(candidate.start,candidate.start+binLength)];let offset=binLength;
function append(bytes){const pad=(4-offset%4)%4;if(pad){chunks.push(Buffer.alloc(pad));offset+=pad;}const start=offset;chunks.push(bytes);offset+=bytes.length;return start;}
const views=new Map(),accessors=new Map(),meshes=new Map();
function view(id){
  if(views.has(id))return views.get(id);
  const v=before.j.bufferViews[id],data=before.bytes.subarray(before.start+(v.byteOffset??0),before.start+(v.byteOffset??0)+v.byteLength);
  const index=j.bufferViews.length;j.bufferViews.push({...structuredClone(v),buffer:0,byteOffset:append(data)});views.set(id,index);return index;
}
function accessor(id){
  if(accessors.has(id))return accessors.get(id);
  const a=structuredClone(before.j.accessors[id]);
  if(a.bufferView!==undefined)a.bufferView=view(a.bufferView);
  if(a.sparse){a.sparse.indices.bufferView=view(a.sparse.indices.bufferView);a.sparse.values.bufferView=view(a.sparse.values.bufferView);}
  const index=j.accessors.length;j.accessors.push(a);accessors.set(id,index);return index;
}
function mesh(id,targetNode){
  const key=id+':'+(config?.changedMaterialNodes?.[targetNode.name]??'');
  if(meshes.has(key))return meshes.get(key);
  const m=structuredClone(before.j.meshes[id]);
  for(const [primitiveIndex,p]of m.primitives.entries()){
    if(p.indices!==undefined)p.indices=accessor(p.indices);
    for(const name of Object.keys(p.attributes))p.attributes[name]=accessor(p.attributes[name]);
    for(const target of p.targets??[])for(const name of Object.keys(target))target[name]=accessor(target[name]);
    const ext=p.extensions?.KHR_draco_mesh_compression;if(ext)ext.bufferView=view(ext.bufferView);
    if(p.material!==undefined){
      const expected=config?.changedMaterialNodes?.[targetNode.name];
      if(expected){const candidateMaterial=j.meshes[targetNode.mesh].primitives[primitiveIndex].material;assert.equal(j.materials[candidateMaterial].name,expected,'Unapproved material replacement');p.material=candidateMaterial;}
      else {const mat=before.j.materials[p.material],found=j.materials.findIndex(x=>x.name===mat.name);assert.ok(found>=0,mat.name);assert.deepEqual(j.materials[found],mat,'material changed '+mat.name);p.material=found;}
    }
  }
  const index=j.meshes.length;j.meshes.push(m);meshes.set(key,index);return index;
}
let preserved=0;
for(const n of j.nodes){
  const old=before.j.nodes.find(x=>x.name===n.name);
  if(n.mesh===undefined||changed.has(n.name)||(config?config.newMeshes?.includes(n.name):n.name.startsWith('BL_Searchlight_')))continue;
  assert.ok(old&&old.mesh!==undefined,'Unexpected new/modified mesh '+n.name);
  verifyLocalTransform(old,n,config?.rebasedNodes?.[n.name]);
  n.mesh=mesh(old.mesh,n);preserved++;
}
// Drop unused primitive descriptors and their accessors/views. Keep every
// referenced original byte stream and all three new lamp/merged-cab streams.
const meshIds=new Set(j.nodes.filter(n=>n.mesh!==undefined).map(n=>n.mesh));
const meshMap=new Map([...meshIds].map((id,i)=>[id,i]));j.meshes=[...meshIds].map(id=>j.meshes[id]);for(const n of j.nodes)if(n.mesh!==undefined)n.mesh=meshMap.get(n.mesh);
const accessorIds=new Set(),viewIds=new Set(j.images.map(i=>i.bufferView));
for(const m of j.meshes)for(const p of m.primitives){
  if(p.indices!==undefined)accessorIds.add(p.indices);for(const id of Object.values(p.attributes))accessorIds.add(id);
  for(const t of p.targets??[])for(const id of Object.values(t))accessorIds.add(id);
  if(p.extensions?.KHR_draco_mesh_compression)viewIds.add(p.extensions.KHR_draco_mesh_compression.bufferView);
}
for(const id of accessorIds){const a=j.accessors[id];if(a.bufferView!==undefined)viewIds.add(a.bufferView);if(a.sparse){viewIds.add(a.sparse.indices.bufferView);viewIds.add(a.sparse.values.bufferView);}}
const accessorMap=new Map([...accessorIds].map((id,i)=>[id,i]));j.accessors=[...accessorIds].map(id=>j.accessors[id]);
const viewMap=new Map([...viewIds].map((id,i)=>[id,i]));
const fullBin=Buffer.concat(chunks),newChunks=[];let packedOffset=0;
j.bufferViews=[...viewIds].map(id=>{const v=j.bufferViews[id],pad=(4-packedOffset%4)%4;if(pad){newChunks.push(Buffer.alloc(pad));packedOffset+=pad;}const start=packedOffset;newChunks.push(fullBin.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength));packedOffset+=v.byteLength;return {...v,byteOffset:start};});
for(const a of j.accessors){if(a.bufferView!==undefined)a.bufferView=viewMap.get(a.bufferView);if(a.sparse){a.sparse.indices.bufferView=viewMap.get(a.sparse.indices.bufferView);a.sparse.values.bufferView=viewMap.get(a.sparse.values.bufferView);}}
for(const i of j.images)i.bufferView=viewMap.get(i.bufferView);
for(const m of j.meshes)for(const p of m.primitives){if(p.indices!==undefined)p.indices=accessorMap.get(p.indices);for(const k of Object.keys(p.attributes))p.attributes[k]=accessorMap.get(p.attributes[k]);for(const t of p.targets??[])for(const k of Object.keys(t))t[k]=accessorMap.get(t[k]);if(p.extensions?.KHR_draco_mesh_compression)p.extensions.KHR_draco_mesh_compression.bufferView=viewMap.get(p.extensions.KHR_draco_mesh_compression.bufferView);}
j.buffers=[{byteLength:packedOffset}];
const json=Buffer.from(JSON.stringify(j)),jsonPad=(4-json.length%4)%4,bin=Buffer.concat(newChunks),binPad=(4-bin.length%4)%4;
const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+jsonPad+bin.length+binPad,8);header.writeUInt32LE(json.length+jsonPad,12);header.writeUInt32LE(0x4e4f534a,16);
const binHeader=Buffer.alloc(8);binHeader.writeUInt32LE(bin.length+binPad,0);binHeader.writeUInt32LE(0x004e4942,4);
const output=Buffer.concat([header,json,Buffer.alloc(jsonPad,32),binHeader,bin,Buffer.alloc(binPad)]);
await fs.writeFile(outputPath,output);
const report={doorPositionPrecision,preservedMeshNodes:preserved,nativeCandidate:candidatePath,source:sourcePath,output:outputPath,sha256:crypto.createHash('sha256').update(output).digest('hex'),bytes:output.length,changedMeshes:[...changed],scope:config?.scope??'Only new lamp and three separated cab material streams are taken from the new native export. Unchanged production surfaces retain their original compressed byte streams.'};
await fs.writeFile(config?.report??'outputs/searchlight-correction-20260930/stream-preservation.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
