import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
const source='work/cab-hinge-rebase-20260930/verification-config.json',config=JSON.parse(await fs.readFile(source,'utf8')),dir='work/cab-hinge-export-tool-check';await fs.mkdir(dir,{recursive:true});
const bytes=await fs.readFile(config.result),len=bytes.readUInt32LE(12),original=JSON.parse(bytes.subarray(20,20+len)),bin=bytes.subarray(28+len);
const check=p=>spawnSync(process.execPath,['scripts/verify-scoped-body-export.mjs',p],{encoding:'utf8'});
assert.equal(check(source).status,0,'Actual scoped rebase baseline failed');
function encode(j){const text=Buffer.from(JSON.stringify(j)),pad=(4-text.length%4)%4,h=Buffer.alloc(20);h.writeUInt32LE(0x46546c67);h.writeUInt32LE(2,4);h.writeUInt32LE(28+text.length+pad+bin.length,8);h.writeUInt32LE(text.length+pad,12);h.writeUInt32LE(0x4e4f534a,16);const b=Buffer.alloc(8);b.writeUInt32LE(bin.length);b.writeUInt32LE(0x004e4942,4);return Buffer.concat([h,text,Buffer.alloc(pad,32),b,bin]);}
const cases=[
 ['uncompensated-child',j=>{j.nodes.find(n=>n.name==='BL_Door_-1_0_handle').translation[0]+=.001;},'hinge rebase'],
 ['wrong-axis-preserved-closed-shape',j=>{const n=j.nodes.find(n=>n.name==='cab_pivot_002');n.translation[0]+=.001;for(const i of n.children)j.nodes[i].translation[0]-=.001;},'hinge rebase'],
 ['white-rubber-fallback',j=>{const mat=j.materials.find(m=>m.name==='MAZ543A_Front_window_rubber');mat.pbrMetallicRoughness.baseColorFactor=[1,1,1,1];},'Scoped material color'],
];
const results=[];for(const[name,mutate,reason]of cases){const j=structuredClone(original);mutate(j);const result=dir+'/'+name+'.glb',cfg=dir+'/'+name+'.json';await fs.writeFile(result,encode(j));await fs.writeFile(cfg,JSON.stringify({...config,result,report:undefined}));const r=check(cfg);assert.notEqual(r.status,0,name+' was accepted');assert.ok((r.stdout+r.stderr).includes(reason),name+' wrong rejection reason');results.push({name,rejected:true,reason});}
await fs.writeFile(dir+'/negative-controls.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results));
