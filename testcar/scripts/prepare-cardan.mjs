import fs from 'node:fs/promises';import ts from 'typescript';
await fs.mkdir('work/compiled',{recursive:true});
await fs.writeFile('work/compiled/cardan.mjs',ts.transpileModule(await fs.readFile('lib/cardan.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const {CARDAN,cardanPose}=await import('../work/compiled/cardan.mjs');
const {COOLING}=await import('../work/compiled/cooling.mjs');
const starting=JSON.parse(await fs.readFile('work/starting-poses.json','utf8'));
const frames=starting.frames.map(f=>({frame:f.frame,pose:cardanPose(f.pose.C5_FLYWHEEL_RING.rx*COOLING.lowerTeeth[0]/COOLING.lowerTeeth[1])}));
await fs.writeFile('work/cardan-poses.json',JSON.stringify({spec:CARDAN,frames}));
console.log('Cardan poses',frames.length,Object.keys(frames[0].pose).length);
