// Purpose-specific preservation gate; existing generic production gates are unchanged.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import * as T from 'three';
const dir='work/cloud-va180-web-20261001',config=JSON.parse(await fs.readFile(`${dir}/pack-config.json`,'utf8'));
async function read(p){const b=await fs.readFile(p),length=b.readUInt32LE(12);assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(8),b.length);return {b,j:JSON.parse(b.subarray(20,20+length)),bin:28+length};}
const old=await read(config.source),now=await read(config.output),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(old.b),config.baselineSHA256);
const reference=JSON.parse(await fs.readFile(config.nativeReference,'utf8'));
assert.equal(reference.source_sha256,config.nativeSourceSHA256);
const bufferHash=(x,id)=>{const v=x.j.bufferViews[id];assert.equal(v.buffer,0);return hash(x.b.subarray(x.bin+(v.byteOffset??0),x.bin+(v.byteOffset??0)+v.byteLength));};
assert.deepEqual(now.j.images.map(i=>bufferHash(now,i.bufferView)),old.j.images.map(i=>bufferHash(old,i.bufferView)),'Ordered embedded images changed');
assert.deepEqual(now.j.textures,old.j.textures,'Texture-to-image/sampler bindings changed');
assert.deepEqual(now.j.samplers,old.j.samplers,'Original sampler definitions changed');
const index=x=>new Map(x.j.nodes.map((n,i)=>[n.name,i]));const oi=index(old),ni=index(now);
assert.equal(oi.size,old.j.nodes.length);assert.equal(ni.size,now.j.nodes.length);
assert.deepEqual(new Set([...oi.keys()].filter(n=>!ni.has(n))),new Set(['cab_0066','cab_0067','cab_0068']));
const expectedNew=Object.keys(reference.node_poses).filter(n=>!oi.has(n));
assert.deepEqual(new Set([...ni.keys()].filter(n=>!oi.has(n))),new Set(expectedNew));
const posed=new Set(['cab_pivot_004','BL_Left_driver_steering_column_retained']);
assert.deepEqual(new Set(Object.keys(config.posedLocalNodes)),posed);
const movedMeshes=new Set(['cab_0029','cab_0030','cab_0031']);
assert.deepEqual(new Set(config.posedWorldMeshNodes),movedMeshes);
const changed=new Set(['cab_0064','BL_Left_driver_steering_column_retained']);
assert.deepEqual(new Set(config.changedMeshes),changed);
function graph(x){
 const parents=new Map(),worlds=new Map();x.j.nodes.forEach((n,i)=>(n.children??[]).forEach(c=>parents.set(c,i)));
 const local=i=>{const n=x.j.nodes[i];return n.matrix?new T.Matrix4().fromArray(n.matrix):new T.Matrix4().compose(new T.Vector3(...(n.translation??[0,0,0])),new T.Quaternion(...(n.rotation??[0,0,0,1])),new T.Vector3(...(n.scale??[1,1,1])));};
 function world(i){if(worlds.has(i))return worlds.get(i);const m=local(i);if(parents.has(i))m.premultiply(world(parents.get(i)));worlds.set(i,m);return m;}
 return {parents,local,world};
}
const a=graph(old),b=graph(now),near=(m,n)=>assert.ok(Math.max(...m.elements.map((v,i)=>Math.abs(v-n.elements[i])))<2e-6,'Unapproved pose deviation');
const fromRows=rows=>new T.Matrix4().set(...rows.flat());
let preserved=0;
for(const [name,i]of ni){
 if(!oi.has(name))continue;
 const beforeIndex=oi.get(name),before=old.j.nodes[beforeIndex],after=now.j.nodes[i];
 assert.equal(now.j.nodes[b.parents.get(i)]?.name,old.j.nodes[a.parents.get(beforeIndex)]?.name,name+' parent changed');
 if(posed.has(name))near(b.local(i),fromRows(reference.node_poses[name].local_gltf_matrix_rows));
 else for(const key of ['translation','rotation','scale','matrix'])assert.deepEqual(after[key],before[key],name+' local '+key);
 if(before.mesh===undefined){assert.equal(after.mesh,undefined,name+' gained geometry');continue;}
 assert.notEqual(after.mesh,undefined,name+' lost geometry');if(changed.has(name))continue;
 if(movedMeshes.has(name))near(b.world(i),fromRows(reference.node_poses[name].world_gltf_matrix_rows));else near(b.world(i),a.world(beforeIndex));
 const p=old.j.meshes[before.mesh].primitives,q=now.j.meshes[after.mesh].primitives;assert.equal(p.length,q.length,name+' primitive count');
 for(let k=0;k<p.length;k++){
  assert.deepEqual(Object.keys(q[k].attributes).sort(),Object.keys(p[k].attributes).sort(),name+' attributes');
  const x=p[k].extensions?.KHR_draco_mesh_compression,y=q[k].extensions?.KHR_draco_mesh_compression;assert.ok(x&&y,name+' compression absent');
  assert.deepEqual(y.attributes,x.attributes);assert.equal(bufferHash(now,y.bufferView),bufferHash(old,x.bufferView),name+' geometry stream changed');
  assert.equal(now.j.accessors[q[k].indices].count,old.j.accessors[p[k].indices].count,name+' index count');
  assert.deepEqual(now.j.materials[q[k].material],old.j.materials[p[k].material],name+' material changed');
  for(const field of ['mode','targets'])assert.deepEqual(q[k][field],p[k][field],name+' '+field);
 }
 preserved++;
}
const report={status:'PASS_SCOPED_CAB_PRESERVATION',source:config.source,result:config.output,resultSHA256:hash(now.b),preservedMeshNodes:preserved,reencodedOldMeshes:[...changed],declaredPosedNodes:[...posed],newNodes:expectedNew.length,removedObsoleteNodes:['cab_0066','cab_0067','cab_0068'],orderedImageBytesTextureBindingsAndSamplersUnchanged:true,
 limits:'Two re-encoded meshes and added geometry require native transport checks; glyphs/buttons are static in this GLB. No whole-car appearance, re-encoded UV/pixel identity, browser rendering or acceptance claim.',wholeVehicleAcceptance:'16 OPEN'};
await fs.writeFile(`${dir}/preservation.json`,JSON.stringify(report,null,2)+'\n');console.log(report);
