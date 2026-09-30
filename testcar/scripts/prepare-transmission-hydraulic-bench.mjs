import fs from 'node:fs/promises';
import ts from 'typescript';
await fs.mkdir('work/hydraulics',{recursive:true});
for(const name of ['cooling','starting','suspension','transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics','mechanics']){
  let js=ts.transpileModule(await fs.readFile(`lib/${name}.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
  js=js.replace(/from '\.\/([^']+)'/g,"from './$1.mjs'");await fs.writeFile(`work/hydraulics/${name}.mjs`,js);
}
const {INITIAL,INITIAL_TELEMETRY,advance}=await import('../work/hydraulics/mechanics.mjs');
const {planetaryPose,CLUTCH_PACKS,CLUTCH_CONTACT}=await import('../work/hydraulics/transmission.mjs');
let t={...INITIAL_TELEMETRY};const samples=[];
function control(time){const gear=time<4?0:time<8?1:time<10?0:time<14?2:time<16?0:time<20?3:time<22?0:time<26?-1:0;return {...INITIAL,running:time<26,throttle:50,gear,brake:time>=8&&gear===0?100:0};}
for(let i=0;i<=7200;i++){
  const c=control(i/240);
  if(i%16===0){const travels=Object.fromEntries(Object.entries(t.transmission.hydraulics.boosters).map(([n,b])=>[n,b.travel]));
    samples.push({frame:i/4,time:i/240,gear:c.gear,rpm:t.rpm,speed:t.speed,mainPressure:t.transmission.hydraulics.mainPressure,
      boosters:t.transmission.hydraulics.boosters,slip:t.transmission.clutchSlip,torque:t.transmission.clutchTorque,
      pose:planetaryPose(t.transmission.inputAngle,t.transmission.outputAngle,c.gear,travels)});
  }
  if(i<7200)t=advance(t,c,1/240);
}
await fs.writeFile('work/hydraulics/native-bench.json',JSON.stringify({samples,clutches:CLUTCH_PACKS,contact:CLUTCH_CONTACT,limits:'30 seconds, 240 Hz coupled integration, 15 Hz native samples. Fitted physics including passive converter approximation; no factory performance acceptance.'}));
console.log('Prepared',samples.length,'native hydraulic samples');
