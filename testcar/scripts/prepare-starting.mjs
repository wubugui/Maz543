import fs from 'node:fs/promises';import ts from 'typescript';
await fs.mkdir('work/compiled',{recursive:true});
for(const name of ['cooling','starting'])await fs.writeFile(`work/compiled/${name}.mjs`,ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace("from './cooling'","from './cooling.mjs'"));
const {STARTING,initialStarting,advanceStarting,startingPose}=await import('../work/compiled/starting.mjs');
const {COOLING,coolingPose}=await import('../work/compiled/cooling.mjs');
let s=initialStarting();const frames=[{frame:0,pose:startingPose(s)}],coolFrames=[{frame:0,pose:coolingPose(s.cooling,s.angle)}];
const c={running:true,startMode:'guided',batteryOn:false,preoilHeld:false,starterHeld:false,fuelEnabled:true,throttle:0,gear:0};
for(let i=1;i<=600;i++){if(i>420)c.running=false;s=advanceStarting(s,c,1/60);frames.push({frame:i,pose:startingPose(s),rpm:s.omega*60/(Math.PI*2),stage:s.stage,shift:s.shift,mesh:s.mesh});coolFrames.push({frame:i,pose:coolingPose(s.cooling,s.angle)});}
await fs.writeFile('work/cooling-poses.json',JSON.stringify({spec:COOLING,frames:coolFrames}));
await fs.writeFile('work/starting-poses.json',JSON.stringify({spec:STARTING,frames}));
console.log('Prepared causal preoil / crank / fire / overrun / stop sequence: 601 frames.');

for(const name of ['d12-timing','d12'])await fs.writeFile(`work/compiled/${name}.mjs`,ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace("from './d12-timing'","from './d12-timing.mjs'"));
const {d12Pose}=await import('../work/compiled/d12.mjs');
await fs.writeFile('work/starting-engine-poses.json',JSON.stringify(frames.map(f=>({frame:f.frame,pose:d12Pose(f.pose.C5_FLYWHEEL_RING.rx)}))));
