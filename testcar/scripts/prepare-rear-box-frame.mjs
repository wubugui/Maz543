import fs from 'node:fs';
const helpers=fs.readFileSync('scripts/hub-front-assembly-model.py','utf8').split("report={'scope'")[0];
fs.writeFileSync('scripts/hub-rear-box-frame.py',helpers+fs.readFileSync('scripts/hub-rear-box-frame-body.py','utf8'));
const dir='work/rear-box-frame-20260930';fs.mkdirSync(dir,{recursive:true});
fs.writeFileSync(dir+'/config.json',JSON.stringify({script:'scripts/hub-rear-box-frame.py',name:'MAZ543A actual rear boxes between axles and scoped dark frame',files:[{file_id:'87d83d96b97bc85043bac0d4bf143a01',path:'MAZ543A_Master.blend'},{file_id:'5f977cc236876cc1dd6bfbced3ff91e2',path:'MAZ543A_Textured.blend'}]}));
if(!fs.existsSync(dir+'/baseline.glb'))fs.copyFileSync('public/models/maz543a-blender.glb',dir+'/baseline.glb');
