import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const rows=[];
for(const hz of [4000,8000,16000]){
  const d=JSON.parse(await fs.readFile(`outputs/converter-freewheel-contact-diagnostic${hz===4000?'':`-${hz}hz`}.json`,'utf8'));
  assert.equal(d.stepSeconds,1/hz);
  rows.push({hz,omegaAt1_2Seconds:d.summary.at1200ms.v[3],minimumGapM:d.summary.minimumGapM,
    maximumEnergyExcessJ:d.summary.maximumEnergyExcess,supportBalanceNm:d.summary.supportBalanceNm});
}
for(const r of rows)r.relativeOmegaDifferenceTo16000Hz=Math.abs(r.omegaAt1_2Seconds-rows[2].omegaAt1_2Seconds)/Math.abs(rows[2].omegaAt1_2Seconds);
assert.ok(rows[0].relativeOmegaDifferenceTo16000Hz<.0001);
const report={rows,limits:'Numerical convergence of this fitted contact bench only; not factory dynamics or full operating-envelope acceptance.'};
await fs.writeFile('outputs/converter-freewheel-timestep-comparison.json',JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
