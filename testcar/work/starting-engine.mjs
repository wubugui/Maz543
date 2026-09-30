import fs from 'node:fs/promises';import ts from 'typescript';
await fs.writeFile('work/compiled/d12.mjs',ts.transpileModule(await fs.readFile('lib/d12.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const {d12Pose}=await import('./compiled/d12.mjs');const data=JSON.parse(await fs.readFile('work/starting-poses.json','utf8'));
await fs.writeFile('work/starting-engine-poses.json',JSON.stringify(data.frames.map(f=>({frame:f.frame,pose:d12Pose(f.pose.C5_FLYWHEEL_RING.rx)}))));
