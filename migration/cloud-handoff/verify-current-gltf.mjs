import fs from 'node:fs';
import validator from '../../testcar/node_modules/gltf-validator/index.js';
const file=new URL('../../testcar/public/models/maz543a-blender.glb',import.meta.url);
const result=await validator.validateBytes(new Uint8Array(fs.readFileSync(file)),{uri:'maz543a-blender.glb'});
console.log(JSON.stringify({errors:result.issues.numErrors,warnings:result.issues.numWarnings,infos:result.issues.numInfos,hints:result.issues.numHints},null,2));
if(result.issues.numErrors||result.issues.numWarnings)process.exitCode=1;
