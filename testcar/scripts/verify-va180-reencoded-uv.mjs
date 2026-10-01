// Joint position+UV triangle-corner comparison across both re-encoded old meshes.
import fs from 'node:fs/promises';import assert from 'node:assert/strict';import crypto from 'node:crypto';import {createRequire} from 'node:module';import path from 'node:path';
const dir='work/cloud-va180-uv-20261001',native=JSON.parse(await fs.readFile(`${dir}/native-corner-uv.json`,'utf8'));
assert.equal(native.source_sha256,'6e406ecadc638130a631e12accebcd9d46de7bdc7c85ca582f0f10d28babe266');
const bytes=await fs.readFile('public/models/review/maz543a-cab-va180-v1.glb');const sha=crypto.createHash('sha256').update(bytes).digest('hex');assert.equal(sha,'fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e');
const length=bytes.readUInt32LE(12),j=JSON.parse(bytes.subarray(20,20+length)),bin=28+length;
await fs.copyFile('public/draco/draco_wasm_wrapper.js',`${dir}/draco-wrapper.cjs`);
const factory=createRequire(import.meta.url)(path.resolve(`${dir}/draco-wrapper.cjs`));const draco=await factory({wasmBinary:await fs.readFile('public/draco/draco_decoder.wasm')});
const positionTolerance=2e-5,uvTolerance=.5/(2**12-1)+2e-7; // official Blender addon default: 12 UV bits, observed [0,1] range
function compare(a,b){
 let best=null;
 for(let shift=0;shift<3;shift++){
  let p=0,u=0;
  for(let k=0;k<3;k++){const x=a[k],y=b[(k+shift)%3];p=Math.max(p,Math.hypot(...x.p.map((v,i)=>v-y.p[i])));u=Math.max(u,...x.uv.map((v,i)=>Math.abs(v-y.uv[i])));}
  if(p<=positionTolerance&&u<=uvTolerance&&(!best||u<best.u))best={p,u};
 }
 return best;
}
const control=[{p:[0,0,0],uv:[0,0]},{p:[1,0,0],uv:[1,0]},{p:[0,1,0],uv:[0,1]}];
assert.ok(compare(control,[control[1],control[2],control[0]]));
let bad=structuredClone(control);bad[0].uv[0]+=.01;assert.equal(compare(control,bad),null);
bad=structuredClone(control);bad[0].p[0]+=.001;assert.equal(compare(control,bad),null);
assert.equal(compare(control,[control[0],control[2],control[1]]),null,'Reversed winding must fail');
const results=[];
for(const ref of native.meshes){
 assert.equal(ref.uv_layers.length,1);assert.equal(ref.uv_layers[0].active_render,true);
 assert.ok(ref.uv_layers[0].corners.every(p=>p.every(v=>v>=0&&v<=1)));
 const triangles=ref.triangles.map(t=>t.map(l=>({p:ref.positions_local_gltf[ref.corner_vertex_indices[l]],uv:ref.uv_layers[0].corners[l]})));
 const center=t=>[0,1,2].map(k=>t.reduce((s,p)=>s+p.p[k],0)/3),cell=p=>p.map(x=>Math.floor(x/positionTolerance));
 const grid=new Map();triangles.forEach((t,i)=>{const key=cell(center(t)).join(',');if(!grid.has(key))grid.set(key,[]);grid.get(key).push(i);});
 const n=j.nodes.find(n=>n.name===ref.name);assert.ok(n);const used=new Set();let maxP=0,maxUV=0,decodedCount=0;const unmatched=[];
 for(const primitive of j.meshes[n.mesh].primitives){
  const ext=primitive.extensions.KHR_draco_mesh_compression,v=j.bufferViews[ext.bufferView],raw=bytes.subarray(bin+(v.byteOffset??0),bin+(v.byteOffset??0)+v.byteLength);
  const decoder=new draco.Decoder(),mesh=new draco.Mesh(),buffer=new draco.DecoderBuffer();buffer.Init(raw,raw.length);const status=decoder.DecodeBufferToMesh(buffer,mesh);assert.ok(status.ok(),status.error_msg());
  function attr(name,width){const a=decoder.GetAttributeByUniqueId(mesh,ext.attributes[name]),values=new draco.DracoFloat32Array();assert.equal(a.num_components(),width);decoder.GetAttributeFloatForAllPoints(mesh,a,values);const out=[];for(let i=0;i<values.size();i+=width)out.push(Array.from({length:width},(_,k)=>values.GetValue(i+k)));draco.destroy(values);return out;}
  const positions=attr('POSITION',3),uv=attr('TEXCOORD_0',2),indices=new draco.DracoInt32Array();
  for(let f=0;f<mesh.num_faces();f++){
   decoder.GetFaceFromMesh(mesh,f,indices);const t=Array.from({length:3},(_,i)=>({p:positions[indices.GetValue(i)],uv:uv[indices.GetValue(i)]}));
   const c=cell(center(t));let found=null;
   for(let x=-1;x<=1&&!found;x++)for(let y=-1;y<=1&&!found;y++)for(let z=-1;z<=1&&!found;z++)for(const i of grid.get([c[0]+x,c[1]+y,c[2]+z].join(','))??[]){if(used.has(i))continue;const m=compare(t,triangles[i]);if(m){found={i,...m};break;}}
   if(found){used.add(found.i);maxP=Math.max(maxP,found.p);maxUV=Math.max(maxUV,found.u);}else unmatched.push(decodedCount);
   decodedCount++;
  }
  for(const o of [indices,mesh,buffer,decoder])draco.destroy(o);
 }
 results.push({name:ref.name,nativeTriangles:triangles.length,decodedTriangles:decodedCount,matchedTriangles:used.size,unmatchedTriangles:unmatched,unmatchedNativeTriangles:triangles.length-used.size,maxCornerPositionErrorM:maxP,maxUVCoordinateError:maxUV});
}
const pass=results.every(r=>r.nativeTriangles===r.decodedTriangles&&r.matchedTriangles===r.nativeTriangles&&r.unmatchedTriangles.length===0);
const report={status:pass?'PASS_TWO_REENCODED_MESH_UV_CORNERS':'FAIL_TWO_REENCODED_MESH_UV_CORNERS',sourceSHA256:native.source_sha256,glbSHA256:sha,positionToleranceM:positionTolerance,uvTolerance,uvBits:12,uvConvention:'Native V flipped to glTF, no modulo wrap or seam averaging',matching:'Bijective triangle assignment with joint position+UV corners and cyclic winding only',results,controls:['cyclic reorder accepted','UV corruption rejected','position corruption rejected','reversed winding rejected'],limits:'Only both inherited re-encoded mesh position/UV triangle corners at static pose. Not pixel equality, material appearance, actual browser rendering or whole-vehicle acceptance.',wholeVehicleAcceptance:'16 OPEN'};
await fs.writeFile(`${dir}/uv-comparison.json`,JSON.stringify(report,null,2)+'\n');console.log(report);assert.ok(pass);
