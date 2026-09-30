import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {chromium} from 'file:///E:/Maz543/external/codex-dependencies/node/node_modules/playwright/index.mjs';
const dir='outputs/front-assembly-20260930';
const reportPath=process.argv[2]??dir+'/runtime-door-registration.json';
const nativeFile=process.argv[3];
let expected;
if(nativeFile){const report=JSON.parse(await fs.readFile(nativeFile,'utf8'));const source=report.files.find(f=>f.file==='MAZ543A_Textured.blend');assert.ok(source);expected=source.doors.map(d=>({name:d.hinge,...d.closedWorldBounds}));}
else {const native=JSON.parse(await fs.readFile('work/front-assembly-20260930/front-assembly-audit.json','utf8'))['MAZ543A_Master.blend'];expected=['cab_pivot_002','cab_pivot_003','cab_pivot_006','cab_pivot_007'].map(name=>{const rows=native.filter(o=>o.parent===name);assert.ok(rows.length);return {name,min:[0,1,2].map(i=>Math.min(...rows.map(o=>o.bounds.min[i]))),max:[0,1,2].map(i=>Math.max(...rows.map(o=>o.bounds.max[i])))};});}
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--no-proxy-server']});
try{const p=await browser.newPage({viewport:{width:1600,height:1000}});await p.goto('http://localhost:3000/?quality=full&debug-handle=1',{timeout:120000});await p.waitForFunction(()=>window.__maz?.nativeMeshes.length>2500,null,{timeout:180000});await p.waitForTimeout(10000);
const actual=await p.evaluate(names=>{const {root,T}=window.__maz;root().updateMatrixWorld(true);return names.map(name=>{const o=root().getObjectByName(name),b=new T.Box3().setFromObject(o);return {name,min:b.min.toArray(),max:b.max.toArray(),matrixWorld:o.matrixWorld.elements.slice()};});},expected.map(x=>x.name));
const rows=actual.map((o,i)=>({native:expected[i],runtime:o,maxBoundsDifferenceM:Math.max(...o.min.map((x,k)=>Math.abs(x-expected[i].min[k])),...o.max.map((x,k)=>Math.abs(x-expected[i].max[k])))}));
const report={scope:'Read-only actual closed runtime door surfaces vs supplied native original door surface bounds',rows,status:rows.every(x=>x.maxBoundsDifferenceM<.002)?'PASS closed surface registration':'FAIL closed surface registration',limits:'This does not replace a matched dynamic hinge/geometry sweep'};
report.source=nativeFile??'Original first mesh-only space audit';await fs.writeFile(reportPath,JSON.stringify(report,null,2));console.log(JSON.stringify(report));}finally{await browser.close();}
