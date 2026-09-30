import fs from 'node:fs/promises';
import {validateBytes} from 'gltf-validator';
const report=await validateBytes(await fs.readFile('work/rear-box-frame-20260930/packaged.glb'),{uri:'maz543a-blender.glb'});
await fs.writeFile('outputs/rear-box-frame-20260930/gltf-validation.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos}));
if(report.issues.numErrors||report.issues.numWarnings)throw Error('Native candidate export requires repair');
