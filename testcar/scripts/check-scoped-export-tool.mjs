import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
const dir='work/scoped-export-tool-check';await fs.mkdir(dir,{recursive:true});
const source='public/models/maz543a-blender.glb',original=await fs.readFile(source),len=original.readUInt32LE(12),j=JSON.parse(original.subarray(20,20+len)),binStart=28+len;
function encode(json){const text=Buffer.from(JSON.stringify(json)),pad=(4-text.length%4)%4,head=Buffer.from(original.subarray(0,20));head.writeUInt32LE(text.length+pad,12);const b=Buffer.concat([head,text,Buffer.alloc(pad,32),original.subarray(20+len)]);b.writeUInt32LE(b.length,8);return b;}
const cases=[];
const moved=structuredClone(j),node=moved.nodes.find(x=>x.name==='BL_Searchlight_housing');node.translation=[...(node.translation??[0,0,0])];node.translation[0]+=.001;cases.push(['unrelated-transform',encode(moved),'transform']);
const mesh=j.nodes.find(x=>x.name.includes('Tyre_rubber')&&x.mesh!==undefined),primitive=j.meshes[mesh.mesh].primitives[0],geometry=Buffer.from(original),view=j.bufferViews[primitive.extensions.KHR_draco_mesh_compression.bufferView];geometry[binStart+(view.byteOffset??0)+20]^=1;cases.push(['unrelated-geometry-byte',geometry,'geometry bytes']);
const texture=Buffer.from(original),iv=j.bufferViews[j.images[0].bufferView];texture[binStart+(iv.byteOffset??0)+40]^=1;cases.push(['embedded-texture-byte',texture,'textures']);
const results=[];
for(const [name,bytes,message]of cases){const result=dir+'/'+name+'.glb',config=dir+'/'+name+'.json';await fs.writeFile(result,bytes);await fs.writeFile(config,JSON.stringify({source,result}));const r=spawnSync(process.execPath,['scripts/verify-scoped-body-export.mjs',config],{encoding:'utf8'});assert.notEqual(r.status,0,name+' unexpectedly accepted');assert.ok(r.stderr.includes(message),name+' rejected for unexpected reason');results.push({name,rejected:true,reasonContains:message});}
await fs.writeFile(dir+'/negative-controls.json',JSON.stringify({status:'PASS',cases:results,scope:'Temporary asset copies only; original production model never mutated'},null,2));console.log(JSON.stringify(results));
