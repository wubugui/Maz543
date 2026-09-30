import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {Vector3,Box3,Mesh} from 'three';
import {validateBytes} from 'gltf-validator';
const bytes=await fs.readFile('public/models/maz543a-strip-study.glb');
const data=JSON.parse(await fs.readFile('public/models/maz543a-strip-study.json','utf8'));
const study=JSON.parse(await fs.readFile('work/freewheel-contact/strip-spring-study.json','utf8'));
const reference=await fs.readFile('work/freewheel-contact/strip-browser-reference.bin');
const hash=b=>createHash('sha256').update(b).digest('hex');
assert.equal(data.modelSha256,hash(bytes));
assert.equal(data.nativeSha256,hash(await fs.readFile('outputs/MAZ543A_Converter_CurvedStripStudy.blend')));
const validation=await validateBytes(new Uint8Array(bytes),{maxIssues:40});assert.equal(validation.issues.numErrors,0);assert.equal(validation.issues.numWarnings,0);
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
gltf.scene.updateMatrixWorld(true);assert.equal(gltf.animations.length,0);
let offset=0,maxNativeDistanceM=0,comparedVertices=0;const states=[];
for(const row of data.rows){
  const ob=gltf.scene.getObjectByName(`CS_equilibrium_${String(row.index).padStart(2,'0')}`);assert.ok(ob instanceof Mesh);
  const count=row.nativeVertexCount,p=ob.geometry.getAttribute('position'),covered=new Set();let stateError=0;
  for(let k=0;k<p.count;k++){
    const point=new Vector3().fromBufferAttribute(p,k).applyMatrix4(ob.matrixWorld);let best=-1,distance=Infinity;
    for(let j=0;j<count;j++){
      const d=Math.hypot(point.x-reference.readFloatLE(offset+j*12),point.y-reference.readFloatLE(offset+j*12+4),point.z-reference.readFloatLE(offset+j*12+8));
      if(d<distance){distance=d;best=j;}
    }
    covered.add(best);stateError=Math.max(stateError,distance);comparedVertices++;
  }
  assert.equal(covered.size,count);assert.ok(stateError<3e-8,`${row.index}: ${stateError}`);
  for(const [a,b] of [['forceN','forceN'],['energyJ','energyJ'],['stressPa','maximumIncrementalBendingStressPa']])assert.equal(row[a],study.rows[row.index][b]);
  assert.ok(Math.hypot(row.rollerPosition[1]-study.rows[row.index].centre[0],row.rollerPosition[2]-study.rows[row.index].centre[1])<1e-8);
  states.push({index:row.index,nativeVertices:count,exportedVertices:p.count,maxNativeDistanceM:stateError});maxNativeDistanceM=Math.max(maxNativeDistanceM,stateError);offset+=count*12;
}
assert.equal(offset,reference.length);assert.equal(states.length,26);
const roller=gltf.scene.getObjectByName('CS_roller_12_5x22'),size=new Box3().setFromObject(roller).getSize(new Vector3());
assert.ok(Math.abs(size.x-.022)<1e-8&&Math.abs(size.y-.0125)<1e-8&&Math.abs(size.z-.0125)<1e-8);
const report={modelSha256:data.modelSha256,nativeSha256:data.nativeSha256,independentEquilibria:states.length,comparedVertices,maxNativeDistanceM,rollerSizeM:size.toArray(),states,glTF:validation.issues,
  limits:'Saved static equilibria only. No interpolated motion, factory seating, strength or vehicle acceptance.'};
await fs.writeFile('outputs/converter-strip-browser-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify({independentEquilibria:states.length,comparedVertices,maxNativeDistanceM,rollerSizeM:size.toArray(),glTF:validation.issues},null,2));
