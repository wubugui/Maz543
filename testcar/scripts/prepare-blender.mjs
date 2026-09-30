import fs from 'node:fs/promises';
import path from 'node:path';
import ts from 'typescript';
import { pathToFileURL } from 'node:url';
const cwd=process.cwd(),out=path.join(cwd,'work','compiled');await fs.mkdir(out,{recursive:true});
for(const name of ['cooling','starting','suspension','transmission','clutchSurfaceMetrics','transmissionHydraulics','transmissionDynamics','mechanics','maz543','export-model']){
 const text=await fs.readFile(path.join(cwd,'lib',`${name}.ts`),'utf8');
 let js=ts.transpileModule(text,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
 js=js.replace("from './cooling'","from './cooling.mjs'").replace("from './transmission'","from './transmission.mjs'").replace("from './transmissionHydraulics'","from './transmissionHydraulics.mjs'").replace("from './clutchSurfaceMetrics'","from './clutchSurfaceMetrics.mjs'").replace("from './transmissionDynamics'","from './transmissionDynamics.mjs'").replace("from './mechanics'","from './mechanics.mjs'").replace("from './suspension'","from './suspension.mjs'").replace("from './starting'","from './starting.mjs'");await fs.writeFile(path.join(out,`${name}.mjs`),js);
}
globalThis.FileReader=class { result=null;onloadend=null;onerror=null;readAsArrayBuffer(blob){blob.arrayBuffer().then(b=>{this.result=b;this.onloadend?.();}).catch(e=>this.onerror?.(e));}readAsDataURL(blob){blob.arrayBuffer().then(b=>{this.result=`data:${blob.type};base64,${Buffer.from(b).toString('base64')}`;this.onloadend?.();}).catch(e=>this.onerror?.(e));}};
const {createMAZ543}=await import(pathToFileURL(path.join(out,'maz543.mjs')));
const {exportGLB}=await import(pathToFileURL(path.join(out,'export-model.mjs')));
const {INITIAL,INITIAL_TELEMETRY}=await import(pathToFileURL(path.join(out,'mechanics.mjs')));
const model=createMAZ543();model.update(INITIAL,INITIAL_TELEMETRY);
await fs.writeFile(path.join(cwd,'work','mechanical-seed.glb'),Buffer.from(await exportGLB(model.root,model.originalMaterials)));
const groups=model.parts.map(p=>({id:p.id,pivots:[],meshes:[]}));
for(const g of groups){const part=model.parts.find(p=>p.id===g.id);part.group.traverse(o=>{if(o.isMesh)g.meshes.push({name:o.name,material:model.originalMaterials.get(o.name)?.name});else g.pivots.push({name:o.name,position:o.position.toArray()});});}
await fs.writeFile(path.join(cwd,'work','mechanical-manifest.json'),JSON.stringify({groups,wheels:model.wheels.map(w=>({carrier:w.carrier.name,spin:w.spin.name,hub:w.hub.name,brake:w.brake.name,x:w.x,side:w.side})),doors:model.doors.map(d=>({name:d.group.name,side:d.side})),pistons:model.pistons.map(p=>({name:p.piston.name,rod:p.rod.name,bank:p.bank,phase:p.phase,x:p.x}))},null,2));
console.log('Exported mechanical seed and named pivot manifest.');model.dispose();
