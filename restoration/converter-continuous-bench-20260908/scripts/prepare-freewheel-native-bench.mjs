import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import ts from 'typescript';
import assert from 'node:assert/strict';
const source=await fs.readFile('lib/converterFreewheel.ts','utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
assert.equal(await fs.readFile('work/freewheel-contact/converterFreewheel.mjs','utf8'),js,'rerun contact diagnostic after solver edits');
const {initialFreewheel}=await import('../work/freewheel-contact/converterFreewheel.mjs');
const raw=await fs.readFile('outputs/converter-freewheel-contact-diagnostic.json');
const d=JSON.parse(raw),samples=[{...initialFreewheel(d.fit),frame:0,torque:-2},...d.rows.map(r=>({...r,frame:Math.round(r.time*100)}))];
samples.forEach((s,i)=>assert.equal(s.frame,i));
const hash=x=>createHash('sha256').update(x).digest('hex');
await fs.writeFile('work/freewheel-contact/native-bench.json',JSON.stringify({fit:d.fit,fps:100,samples,
  solverSha256:hash(source),diagnosticSha256:hash(raw),sourceBlendSha256:hash(await fs.readFile('outputs/MAZ543A_Converter_Freewheels.blend')),
  limits:'Two independent rows replay the same external-torque test. Fitted symmetric roller contact, steel density/friction and spring parameters. No converter-fluid torques or vehicle operating trace.'},null,2));
console.log('Prepared',samples.length,'coupled native states');
