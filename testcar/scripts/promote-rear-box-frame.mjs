import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const dir='work/rear-box-frame-20260930',backup='../restoration/rear-box-frame-20260930',out='outputs/rear-box-frame-20260930';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const verification=JSON.parse(fs.readFileSync(out+'/export-verification.json')),validation=JSON.parse(fs.readFileSync(out+'/gltf-validation.json'));
assert.equal(verification.status,'PASS for declared scope only');assert.equal(validation.issues.numErrors,0);assert.equal(validation.issues.numWarnings,0);
const task=JSON.parse(fs.readFileSync(dir+'/task-result.json'));assert.equal(task.state,'succeeded');
for(const n of ['MAZ543A_Master.blend','MAZ543A_Textured.blend'])assert.equal(sha(dir+'/'+n),task.result.files.find(f=>f.relative_path===n).sha256);
const changes=[
 ['public/models/maz543a-blender.glb',dir+'/packaged.glb','4544afcc653c87f6fb40be1c9c21483aeeff87b989d46e366e1a1d220076bfe2'],
 ['outputs/MAZ543A_Master.blend',dir+'/MAZ543A_Master.blend','bf997f4c465255907310d0dd0a8d6bed38ca331a5edab9bccfd2314a5f5b6579'],
 ['outputs/MAZ543A_Textured.blend',dir+'/MAZ543A_Textured.blend','14b88267725824a7f0a7bedc2bf5145ca794fb08a637d0fdeb2dba98bbacd542'],
];
for(const[p,next,old]of changes)assert.ok([old,sha(next)].includes(sha(p)),'Unexpected active asset change: '+p);
fs.mkdirSync(backup,{recursive:true});
for(const[p,next,old]of changes){const b=backup+'/'+p.split('/').at(-1);if(!fs.existsSync(b)){assert.equal(sha(p),old,'Cannot reconstruct prior backup from promoted asset');fs.copyFileSync(p,b);}else assert.equal(sha(b),old,'Existing backup changed');fs.copyFileSync(next,p);}
const loader='lib/vehicleViewport.ts',text=fs.readFileSync(loader,'utf8');assert.ok(text.includes('front-cab-hinge-rubber-upper-mirrors-20260930')||text.includes('rear-box-frame-20260930'));fs.writeFileSync(loader,text.replaceAll('front-cab-hinge-rubber-upper-mirrors-20260930','rear-box-frame-20260930'));
const meta='public/models/model-info.json',j=JSON.parse(fs.readFileSync(meta));j.front_restoration.rearBoxFrame={hubTask:'48aad07d-787d-4401-a723-f6317dd5a894',scope:'Original eight box pieces archived and retained duplicates moved -1.57m to center3.52m between axles3/4; four fitted native mounting pads; three frame objects use explicit dark enamel',preservation:'260 unaffected compressed streams and three embedded images retained; original box dimensions retained; glTF0 errors/0 warnings',nativeMountInterfaces:16,sha256:sha(changes[0][0]),status:'Browser verification pending; factory dims, internal/lid mechanics, suspension travel and full undercarriage paint OPEN'};fs.writeFileSync(meta,JSON.stringify(j,null,2));
console.log(JSON.stringify({promoted:true,sha256:sha(changes[0][0]),backup}));
