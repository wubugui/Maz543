import fs from 'node:fs/promises';import ts from 'typescript';
await fs.mkdir('work/compiled',{recursive:true});
await fs.writeFile('work/compiled/starting.mjs',ts.transpileModule(await fs.readFile('lib/starting.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText);
const {initialStarting,advanceStarting}=await import('../work/compiled/starting.mjs');
let s=initialStarting();let c={running:true,startMode:'guided',batteryOn:false,preoilHeld:false,starterHeld:false,fuelEnabled:true,throttle:0,gear:0};
for(let i=0;i<1200;i++){s=advanceStarting(s,c,1/60);if(i%60===0)console.log((i/60).toFixed(0),s.stage,Math.round(s.omega*60/(2*Math.PI)),s.oilPressure/98066.5,s.shift,s.mesh,Math.round(s.current),s.combustion);}
