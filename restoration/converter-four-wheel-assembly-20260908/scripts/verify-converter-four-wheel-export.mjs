import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {Vector3,Mesh} from 'three';
import {validateBytes} from 'gltf-validator';
const data=JSON.parse(await fs.readFile('public/models/maz543a-converter-assembly.json','utf8'));
const bytes=await fs.readFile('public/models/maz543a-converter-assembly.glb');
const reference=await fs.readFile('work/transmission/converter-four-wheel-reference.bin');
const hash=b=>createHash('sha256').update(b).digest('hex');
assert.equal(hash(bytes),data.modelSha256);assert.equal(hash(await fs.readFile('outputs/MAZ543A_Converter_FourWheelAssembly.blend')),data.nativeSha256);
const validation=await validateBytes(new Uint8Array(bytes),{maxIssues:20});assert.equal(validation.issues.numErrors,0);assert.equal(validation.issues.numWarnings,0);
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
gltf.scene.updateMatrixWorld(true);assert.equal(gltf.animations.length,0);
const rows=[];const cell=1e-6;let compared=0,maxError=0;
for(const part of data.parts){
  const ob=gltf.scene.getObjectByName(part.name);assert.ok(ob instanceof Mesh,part.name);assert.equal(ob.parent.name,part.parent);
  const bins=new Map(),points=[];
  for(let j=0;j<part.vertices;j++){
    const p=[0,1,2].map(k=>reference.readFloatLE(part.byteOffset+j*12+k*4));points.push(p);
    const key=p.map(v=>Math.floor(v/cell)).join(',');if(!bins.has(key))bins.set(key,[]);bins.get(key).push(j);
  }
  const position=ob.geometry.getAttribute('position'),covered=new Set();let error=0;
  for(let j=0;j<position.count;j++){
    const v=new Vector3().fromBufferAttribute(position,j).applyMatrix4(ob.matrixWorld),p=v.toArray(),base=p.map(v=>Math.floor(v/cell));let nearest=-1,distance=Infinity;
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++)for(const k of bins.get([base[0]+x,base[1]+y,base[2]+z].join(','))??[]){
      const d=Math.hypot(...p.map((v,a)=>v-points[k][a]));if(d<distance){distance=d;nearest=k;}
    }
    assert.ok(distance<1e-7,`${part.name}: ${distance}`);covered.add(nearest);error=Math.max(error,distance);compared++;
  }
  assert.equal(covered.size,part.vertices,part.name);maxError=Math.max(maxError,error);
  rows.push({name:part.name,nativeVertices:part.vertices,exportedVertices:position.count,maxErrorM:error});
}
assert.equal(rows.length,180);
// The static input/thrust and output/driven-disc topology must survive export.
function ancestor(name,root){let ob=gltf.scene.getObjectByName(name);while(ob){if(ob.name===root)return true;ob=ob.parent;}return false;}
for(const name of ['CA_01_input_shaft','CA_08_thrust_disc','CA_05_lockup_piston'])assert.ok(ancestor(name,'CA_pump'));
for(const name of ['CA_07_driven_disc_carrier','CA_15_turbine_shaft'])assert.ok(ancestor(name,'CA_turbine'));
assert.ok(ancestor('CA_13_shared_inner_race','CA_fixed_support'));
const report={meshes:rows.length,comparedVertices:compared,maxNativeErrorM:maxError,modelSha256:data.modelSha256,nativeSha256:data.nativeSha256,glTF:validation.issues,rows,
  limits:'Export and rigid assembly hierarchy only; no fluid dynamics, freewheel trajectory, factory geometry or full-vehicle acceptance.'};
await fs.writeFile('outputs/converter-four-wheel-export-verification.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({meshes:rows.length,compared,maxError,glTF:validation.issues},null,2));
