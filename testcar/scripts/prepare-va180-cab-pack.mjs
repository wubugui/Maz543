import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const dir='work/cloud-va180-web-20261001';
const source='public/models/review/maz543a-left-driver-v1.glb';
const candidate=`${dir}/native-export.glb`;
const read=async p=>{const b=await fs.readFile(p);return {b,j:JSON.parse(b.subarray(20,20+b.readUInt32LE(12)))};};
const old=await read(source),raw=await read(candidate),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(old.b),'ccccdd56fed79d3a77166652beda8c32b02fca820050723f80cd97f99915b1dc');
const reference=JSON.parse(await fs.readFile(`${dir}/native-world-reference.json`,'utf8'));
const transport=JSON.parse(await fs.readFile(`${dir}/native-transport.json`,'utf8'));
assert.equal(transport.status,'PASS_NATIVE_CAB_TRANSPORT_ONLY');assert.equal(transport.sha256,hash(raw.b));
const names=new Set(old.j.nodes.map(n=>n.name)),now=new Set(raw.j.nodes.map(n=>n.name));
const newNodes=Object.keys(reference.node_poses).filter(n=>!names.has(n));
assert.deepEqual(new Set([...now].filter(n=>!names.has(n))),new Set(newNodes),'Unapproved new nodes');
const removedNodes=['cab_0066','cab_0067','cab_0068'];
assert.deepEqual(new Set([...names].filter(n=>!now.has(n))),new Set(removedNodes));
const changedMeshes=['cab_0064','BL_Left_driver_steering_column_retained'];
const newMeshes=reference.parts.map(r=>r.name).filter(n=>!names.has(n));
const nativeUsed=new Set([...newMeshes,...changedMeshes]);
const polygonChecks=reference.export_only_native_triangulation.filter(r=>nativeUsed.has(r.object));
assert.ok(polygonChecks.every(r=>r.world_ngon_nonplanarity_m<2e-6&&r.degenerate_ngons===0),'Re-triangulated changed face is not numerically planar');
const poses=Object.fromEntries(['cab_pivot_004','BL_Left_driver_steering_column_retained'].map(n=>[n,reference.node_poses[n]]));
const config={source,candidate,output:`${dir}/packed-candidate.glb`,report:`${dir}/pack-report.json`,
 changedMeshes,newMeshes,newNodes,removedNodes,posedLocalNodes:poses,
 posedWorldMeshNodes:['cab_0029','cab_0030','cab_0031'],nativeReference:`${dir}/native-world-reference.json`,
 baselineSHA256:hash(old.b),rawSHA256:hash(raw.b),nativeSourceSHA256:reference.source_sha256,
 exportPreparation:{nativeConvertedObjects:reference.export_only_converted_objects.length,changedTriangulatedObjects:polygonChecks.length,maxChangedNgonNonplanarityM:Math.max(...polygonChecks.map(r=>r.world_ngon_nonplanarity_m))},
 scope:'Partial cab-panel/VA180 candidate. Exactly two old meshes are re-encoded, three obsolete generic instrument nodes omitted, declared steering rest pose changed. Other original streams/materials/textures are retained. Four seat regions retain native UVs; re-encoded GLB UV/pixel identity is not certified. All16 OPEN.'};
await fs.writeFile(`${dir}/pack-config.json`,JSON.stringify(config,null,2)+'\n');console.log('CAB_PACK_CONFIG',{changedMeshes,newMeshes:newMeshes.length,newNodes:newNodes.length,removedNodes,exportPreparation:config.exportPreparation});
