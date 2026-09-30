import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {DisplayFrameCache} from '../lib/displayFrameCache.ts';

// Preserve the real pre-change implementation, not a rewritten test oracle.
const saved=new URL('../../restoration/shared-display-signatures-20260929/displayFrameCache.before.ts',import.meta.url);
const fixture=new URL('../work/shared-display-signatures-20260929/displayFrameCache.before.ts',import.meta.url);
await fs.copyFile(saved,fixture);
const {DisplayFrameCache:Before}=await import(fixture.href);

function assembly(count,geometryCount=24,materialCount=8){
  const scene=new T.Scene(),camera=new T.PerspectiveCamera(),root=new T.Group();scene.add(root);
  const geometries=Array.from({length:geometryCount},()=>new T.BoxGeometry());
  const materials=Array.from({length:materialCount},()=>new T.MeshStandardMaterial());
  const meshes=Array.from({length:count},(_,i)=>{
    const mesh=new T.Mesh(geometries[i%geometryCount],materials[i%materialCount]);
    mesh.name=`part_${i}`;mesh.position.set(i%100,Math.floor(i/100),0);root.add(mesh);return mesh;
  });
  return {scene,camera,root,geometries,materials,meshes};
}

const a=assembly(96),before=new Before(true),after=new DisplayFrameCache(true);
let revision={},comparisons=0;
function check(label,options={}){
  const expected=before.needsRender(a.scene,a.camera,revision,options);
  const actual=after.needsRender(a.scene,a.camera,revision,options);
  assert.equal(actual,expected,label);comparisons++;
}
check('initial');check('unchanged');
let seed=1234567;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
for(let i=0;i<600;i++){
  const mesh=a.meshes[random()%a.meshes.length],material=a.materials[random()%a.materials.length];
  switch(i%12){
    case 0:mesh.position.x+=(random()%2?1:-1)*1e-12;break;
    case 1:mesh.visible=!mesh.visible;break;
    case 2:mesh.material=a.materials[random()%a.materials.length];break;
    case 3:mesh.geometry=a.geometries[random()%a.geometries.length];break;
    case 4:material.roughness=(random()%100)/100;break;
    case 5:material.needsUpdate=true;break;
    case 6:mesh.geometry.attributes.position.needsUpdate=true;break;
    case 7:mesh.morphTargetInfluences=[(random()%100)/100];break;
    case 8:mesh.renderOrder=random()%5;break;
    case 9:a.camera.position.z+=.0001;break;
    case 10:a.root.visible=!a.root.visible;break;
    case 11:revision={};break;
  }
  check(`mutation ${i}`);check(`stable ${i}`);
}
a.root.visible=true;a.meshes.forEach(m=>m.visible=true);check('reveal all');
a.materials[0].map=new T.Texture();check('shared texture inserted');
a.materials[0].map.needsUpdate=true;check('shared texture upload');check('stable texture');
a.meshes.at(-1).geometry.setAttribute('position',a.meshes.at(-1).geometry.attributes.position.clone());check('shared attribute replacement');
a.meshes[0].material=[a.materials[0],a.materials[1]];check('material array inserted');
a.meshes[0].material.reverse();check('material slot order');
a.camera.position.x+=1;check('camera fast path',{cameraFastPath:true});
a.materials[0].opacity=.45;check('rebase after skipped scan',{cameraFastPath:true});check('stable rebase',{cameraFastPath:true});

// Shared resource edits are read only once, but every owner must retain its
// identity and every callback owner must veto renderer-version forgiveness.
const s=assembly(8,1,1),glass=s.materials[0];glass.transparent=true;glass.side=T.DoubleSide;
const cache=new DisplayFrameCache();const rev={};
cache.needsRender(s.scene,s.camera,rev);
for(const m of s.meshes){glass.needsUpdate=true;glass.needsUpdate=true;}
cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(s.scene,s.camera,rev),false);
s.meshes.at(-1).onAfterRender=()=>{};
cache.needsRender(s.scene,s.camera,rev);glass.needsUpdate=true;glass.needsUpdate=true;cache.acknowledgeRenderedVersions();
assert.equal(cache.needsRender(s.scene,s.camera,rev),true,'last shared owner hook prevents forgiveness');

// Performance scope: synthetic CPU signature work only, not rasterization,
// real vehicle FPS, GPU timings, or a visual fidelity acceptance claim.
const large=assembly(3043,600,67),oldCache=new Before(),newCache=new DisplayFrameCache(),largeRevision={};
for(let i=0;i<40;i++){oldCache.needsRender(large.scene,large.camera,largeRevision);newCache.needsRender(large.scene,large.camera,largeRevision);}
const oldTimes=[],newTimes=[];
const timed=(candidate,output)=>{const start=performance.now();candidate.needsRender(large.scene,large.camera,largeRevision);output.push(performance.now()-start);};
for(let i=0;i<120;i++){
  if(i%2){timed(oldCache,oldTimes);timed(newCache,newTimes);}else{timed(newCache,newTimes);timed(oldCache,oldTimes);}
}
const stats=times=>{const sorted=[...times].sort((a,b)=>a-b);return {medianMs:sorted[Math.floor(sorted.length/2)],p95Ms:sorted[Math.floor(sorted.length*.95)],meanMs:times.reduce((a,b)=>a+b,0)/times.length};};
const oldSignature=oldCache.previous.length,newSignature=newCache.previous.length;
assert.ok(newSignature<oldSignature,'shared data occupies fewer signature values');
const report={passed:true,comparisons,sharedCallbackProtection:true,syntheticBenchmark:{meshes:3043,geometries:600,materials:67,samples:120,before:stats(oldTimes),after:stats(newTimes),signatureValues:{before:oldSignature,after:newSignature}},limits:'Node CPU benchmark of constructed assembly; real vehicle GPU/FPS and pixel comparisons remain unverified.'};
await fs.writeFile(new URL('../outputs/shared-display-signatures-20260929/signature-tests.json',import.meta.url),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
