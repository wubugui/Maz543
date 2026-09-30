import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import * as T from 'three';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {installContextAuditNoise} from '../lib/contextFrameAudit.ts';
const scene=new T.Scene(),camera=new T.PerspectiveCamera(),a=new GTAOPass(scene,camera),b=new GTAOPass(scene,camera);
const ordinaryRandom=Math.random,ordinaryRecipe=GTAOPass.prototype._generateNoise;
const magic=a.gtaoNoiseTexture,oldTexture=a.pdNoiseTexture;let disposed=0;oldTexture.addEventListener('dispose',()=>disposed++);
const candidate=installContextAuditNoise(a),second=installContextAuditNoise(b);
assert.equal(Math.random,ordinaryRandom,'production random source untouched');assert.equal(GTAOPass.prototype._generateNoise,ordinaryRecipe,'Three prototype untouched');
assert.equal(disposed,1);assert.equal(a.gtaoNoiseTexture,magic);assert.equal(a.pdMaterial.uniforms.tNoise.value,a.pdNoiseTexture);
assert.deepEqual(candidate,second,'separately constructed contexts have identical audit noise');
let seed=0x543a2026,reference;
// Controlled synchronous test of the installed stock recipe with the same RNG.
try{Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/0x100000000;};reference=ordinaryRecipe.call(a);}
finally{Math.random=ordinaryRandom;}
assert.deepEqual(candidate,reference.image.data,'all bytes equal actual installed r183 recipe');
for(const key of ['format','type','wrapS','wrapT','minFilter','magFilter','generateMipmaps','flipY','colorSpace'])assert.equal(a.pdNoiseTexture[key],reference[key],key);
const result={passed:true,bytes:candidate.length,sha256:createHash('sha256').update(candidate).digest('hex'),actualStockRecipeByteEquivalent:true,ordinaryRandomAndPrototypeUntouched:true,oldOwnedNoiseReleased:true,limits:'Audit input generator only. Complete main/worker RGBA, scene and actual draw-sequence fingerprints are browser evidence.'};
reference.dispose();a.dispose();b.dispose();await fs.mkdir('outputs/context-frame-audit',{recursive:true});await fs.writeFile('outputs/context-frame-audit/noise-tests.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
