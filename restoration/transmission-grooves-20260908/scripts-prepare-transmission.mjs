import fs from 'node:fs/promises';
import ts from 'typescript';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const dir=path.resolve('work/transmission');await fs.mkdir(dir,{recursive:true});
const js=ts.transpileModule(await fs.readFile('lib/transmission.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
await fs.writeFile(path.join(dir,'transmission.mjs'),js);
const {PLANETARY,CLUTCH_PACKS,CLUTCH_CONTACT,DIRECT_BOOSTER,planetaryPose,gearboxRatio}=await import(pathToFileURL(path.join(dir,'transmission.mjs')));
const samples=[];let input=0,carrier=0;
for(let frame=0;frame<=600;frame++){
  const gear=[0,1,2,3,-1][Math.min(4,Math.floor(frame/120))];
  if(frame&&gear){input+=6/60;carrier+=6/60/gearboxRatio(gear);}
  samples.push({frame,gear,input,carrier,pose:planetaryPose(input,carrier,gear)});
}
const meshSamples=Array.from({length:241},(_,i)=>planetaryPose(i/240*2*Math.PI/PLANETARY.sun41,0,0));
await fs.writeFile(path.join(dir,'poses.json'),JSON.stringify({spec:PLANETARY,clutches:CLUTCH_PACKS,contact:CLUTCH_CONTACT,directBooster:DIRECT_BOOSTER,samples,meshSamples,limits:'Selection and rigid gearing only; native inspection input is 6 rad/s, not a vehicle operating trace.'}));
console.log(`Prepared ${samples.length} native poses.`);
