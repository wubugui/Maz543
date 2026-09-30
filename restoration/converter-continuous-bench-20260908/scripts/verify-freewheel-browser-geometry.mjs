import fs from 'node:fs/promises';import ts from 'typescript';import assert from 'node:assert/strict';
import {validateBytes} from 'gltf-validator';
const src=await fs.readFile('lib/converterFreewheelGeometry.ts','utf8');
await fs.writeFile('work/freewheel-contact/converterFreewheelGeometry.mjs',ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const {freewheelCoilPositions}=await import('../work/freewheel-contact/converterFreewheelGeometry.mjs');
const d=JSON.parse(await fs.readFile('public/models/maz543a-freewheel-bench.json','utf8'));
const reference=await fs.readFile('work/freewheel-contact/browser-coil-reference.bin');const count=1932;
let maxNativeErrorM=0;assert.equal(reference.length,d.samples.length*count*12);
for(let i=0;i<d.samples.length;i++){
  const s=d.samples[i],[y,z,,angle]=s.q,c=Math.cos(angle),sn=Math.sin(angle),p=freewheelCoilPositions(d.fit,c*y+sn*z,-sn*y+c*z,s.springLength);
  assert.equal(p.length,count*3);
  for(let k=0;k<count*3;k++)maxNativeErrorM=Math.max(maxNativeErrorM,Math.abs(p[k]-reference.readFloatLE((i*count*3+k)*4)));
}
assert.ok(maxNativeErrorM<3e-8,`native/browser coil parity ${maxNativeErrorM}`);
const glb=await fs.readFile('public/models/maz543a-freewheel-bench.glb');
const validation=await validateBytes(new Uint8Array(glb),{maxIssues:50});assert.equal(validation.issues.numErrors,0);
const jsonBytes=glb.readUInt32LE(12),g=JSON.parse(glb.subarray(20,20+jsonBytes)),binOffset=28+jsonBytes;
const node=g.nodes.find(n=>n.name==='CV_front_engagement_spring_0'),primitive=g.meshes[node.mesh].primitives[0],accessor=g.accessors[primitive.attributes.POSITION],view=g.bufferViews[accessor.bufferView];assert.equal(accessor.count,count);
const start=binOffset+(view.byteOffset??0)+(accessor.byteOffset??0),stride=view.byteStride??12;
const order=[];let maxExportErrorM=0;
for(let k=0;k<count;k++){
  const p=[0,1,2].map(j=>glb.readFloatLE(start+k*stride+j*4));let best=-1,dist=Infinity;
  for(let j=0;j<count;j++){
    const error=Math.hypot(...p.map((x,a)=>x-reference.readFloatLE((j*3+a)*4)));
    if(error<dist){dist=error;best=j;}
  }
  maxExportErrorM=Math.max(maxExportErrorM,dist);order.push(best);
}
assert.equal(new Set(order).size,count);assert.ok(maxExportErrorM<3e-8);
d.coilVertexOrder=order;await fs.writeFile('public/models/maz543a-freewheel-bench.json',JSON.stringify(d));
const report={nativeStates:d.samples.length,nativeVerticesCompared:count*d.samples.length,maxNativeErrorM,maxExportErrorM,uniqueMappedVertices:new Set(order).size,glTF:validation.issues};
await fs.writeFile('outputs/freewheel-browser-geometry.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
