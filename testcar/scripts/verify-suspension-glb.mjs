import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
const bytes=await fs.readFile('public/models/maz543a-suspension.glb'),json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
const poses=JSON.parse(await fs.readFile('work/suspension-poses.json','utf8')),nodes=new Map(json.nodes.map(n=>[n.name,n]));
for(const name of Object.keys(poses.rest))assert.ok(nodes.has(name),`Missing joint ${name}`);
assert.equal(json.nodes.filter(n=>n.extras?.s543Role==='torsion').length,16);
assert.ok(json.images.length>=2,'Blender-baked surface maps must be embedded');
for(const [name,pose] of Object.entries(poses.rest)){const p=nodes.get(name).translation||[0,0,0];assert.ok(p.every((v,i)=>Math.abs(v-pose.p[i])<1e-5),`Not neutral: ${name}`);}
const report=await validateBytes(new Uint8Array(bytes),{uri:'maz543a-suspension.glb',maxIssues:5000});
await fs.writeFile('outputs/suspension-gltf-validation.json',JSON.stringify(report,null,2));assert.equal(report.issues.numErrors,0,JSON.stringify(report.issues.messages));
const parts=JSON.parse(await fs.readFile('outputs/suspension-parts-register.json','utf8'));
assert.ok(parts.every(p=>p.source&&p.dimensions),'Every authored part needs its reference and dimensional status');
const summary={bytes:bytes.length,nodes:json.nodes.length,meshes:json.meshes.length,joints:Object.keys(poses.rest).length,authoredParts:parts.length,errors:report.issues.numErrors,warnings:report.issues.numWarnings};
await fs.writeFile('outputs/suspension-asset-verification.json',JSON.stringify(summary,null,2));console.log(summary);
