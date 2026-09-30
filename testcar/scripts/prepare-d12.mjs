import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import ts from 'typescript';
await fs.mkdir('work/compiled',{recursive:true});
for(const name of ['d12-timing','d12']){
 const code=await fs.readFile(`lib/${name}.ts`,'utf8');
 await fs.writeFile(`work/compiled/${name}.mjs`,ts.transpileModule(code,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace("from './d12-timing'","from './d12-timing.mjs'"));
}
const {D12,D12_TIMING,WATER_PUMP,d12Pose,crankPinPhase,firingPhase}=await import(pathToFileURL(path.resolve('work/compiled/d12.mjs')));
const frames=Array.from({length:121},(_,i)=>({frame:i*2+1,angle:i/120*Math.PI*4,pose:d12Pose(i/120*Math.PI*4)}));
const firePhases=Object.fromEntries(['L','R'].flatMap(b=>Array.from({length:6},(_,i)=>[b+(i+1),firingPhase(b,i)])));
await fs.writeFile('work/d12-poses.json',JSON.stringify({spec:D12,timing:D12_TIMING,waterPump:WATER_PUMP,pinPhases:Array.from({length:6},(_,i)=>crankPinPhase(i)),firePhases,frames}));
console.log(`Prepared ${Object.keys(frames[0].pose).length} independent joint transforms across a 720-degree cycle.`);
