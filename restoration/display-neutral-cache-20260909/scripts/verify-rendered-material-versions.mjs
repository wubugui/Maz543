import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import * as T from 'three';
import {DisplayFrameCache} from '../lib/displayFrameCache.ts';
const scene=new T.Scene(),camera=new T.PerspectiveCamera(),revision={};
const glass=new T.MeshStandardMaterial({transparent:true,side:T.DoubleSide,opacity:.4});
const geometry=new T.BoxGeometry(),a=new T.Mesh(geometry,glass),b=new T.Mesh(geometry,glass);
scene.add(a,b);const cache=new DisplayFrameCache(true);
assert.equal(cache.needsRender(scene,camera,revision),true);
// The exact stock r183 renderObject two-pass material mutations, twice because
// this material is shared by two objects. No WebGL or pixel assertion here.
function renderGlass(){for(const mesh of [a,b]){const m=mesh.material;m.side=T.BackSide;m.needsUpdate=true;m.side=T.FrontSide;m.needsUpdate=true;m.side=T.DoubleSide;}}
renderGlass();cache.acknowledgeRenderedVersions();
assert.equal(cache.needsRender(scene,camera,revision),false);
glass.needsUpdate=true;assert.equal(cache.needsRender(scene,camera,revision),true,'application program update remains detected');
renderGlass();cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(scene,camera,revision),false);
glass.opacity=.3;assert.equal(cache.needsRender(scene,camera,revision),true,'opacity remains detected');
renderGlass();glass.opacity=.2;cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(scene,camera,revision),true,'non-version changes during render remain detected');
renderGlass();cache.acknowledgeRenderedVersions();a.position.x=1e-30;assert.equal(cache.needsRender(scene,camera,revision),true,'no motion epsilon');
renderGlass();cache.acknowledgeRenderedVersions();glass.needsUpdate=true;cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(scene,camera,revision),true,'odd unexpected increment is not acknowledged');
glass.onBeforeRender=()=>{};cache.needsRender(scene,camera,revision);renderGlass();cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(scene,camera,revision),true,'custom material hooks remain conservative');
glass.onBeforeRender=T.Material.prototype.onBeforeRender;b.onAfterRender=()=>{};cache.needsRender(scene,camera,revision);renderGlass();cache.acknowledgeRenderedVersions();assert.equal(cache.needsRender(scene,camera,revision),true,'one custom object hook protects every shared material reference');
const report={passed:true,sharedDoubleSidedMaterial:true,applicationProgramUpdate:true,opacityDuringRender:true,noMotionEpsilon:true,unexpectedVersionConservative:true,customMaterialHookConservative:true,customSharedObjectHookConservative:true,limits:'Stock renderer bookkeeping unit test; real browser and raster validation separate.'};
await fs.writeFile('outputs/suspension-reference/material-version-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
