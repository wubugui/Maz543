/** Explicit development-only asset review. Never changes the ordinary production selection. */
export type ReviewVehicleAsset={kind:'production'|'tyre-v2'|'hood-tyre-v1'|'left-driver-v1'|'cab-va180-v1';url:string;sha256:string;exportFilename:string;notice:string|null};
export const PRODUCTION_VEHICLE_ASSET:Readonly<ReviewVehicleAsset>=Object.freeze({
 kind:'production',url:'/models/maz543a-blender.glb?v=rear-box-frame-20260930',
 sha256:'4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698',
 exportFilename:'MAZ543-reference-current-pose.glb',notice:null,
});
export function selectReviewVehicleAsset(search:string,development:boolean):Readonly<ReviewVehicleAsset>{
 const query=new URLSearchParams(search),requested=query.getAll('asset-review');
 if(requested.length===0)return PRODUCTION_VEHICLE_ASSET;
 if(requested.length!==1||!['tyre-v2','hood-tyre-v1','left-driver-v1','cab-va180-v1'].includes(requested[0]))return {...PRODUCTION_VEHICLE_ASSET,notice:'候选参数无效，当前选择生产资产。'};
 if(!development||query.get('render-worker')==='1'||query.get('worker-build')==='1')return {...PRODUCTION_VEHICLE_ASSET,notice:'候选审查仅支持开发环境的普通显示；当前选择生产资产。'};
 if(requested[0]==='cab-va180-v1')return {kind:'cab-va180-v1',url:'/models/review/maz543a-cab-va180-v1.glb?v=fde04e480978d065',
  sha256:'fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e',
  exportFilename:'MAZ543-CANDIDATE-cab-va180-v1-current-pose.glb',
  notice:'候选审查：双舱面板、VA180外观与拟合方向柱｜未替换生产模型；仪表与按钮为静态外观，装配干涉、网页和整车验收仍开放。'};
 if(requested[0]==='left-driver-v1')return {kind:'left-driver-v1',url:'/models/review/maz543a-left-driver-v1.glb?v=ccccdd56fed79d3a7',
  sha256:'ccccdd56fed79d3a77166652beda8c32b02fca820050723f80cd97f99915b1dc',
  exportFilename:'MAZ543-CANDIDATE-left-driver-v1-current-pose.glb',
  notice:'候选审查：驾驶控制移回左舱｜未替换生产模型；局部位置仍为拟合，踏板与杆件身份、网页和整车验收尚未通过。'};
 if(requested[0]==='hood-tyre-v1')return {kind:'hood-tyre-v1',url:'/models/review/maz543a-hood-tyre-v1.glb?v=58deabf47ce2a18d',
  sha256:'58deabf47ce2a18dc4cba2dc6ff9ac29576183ff0a7e00a93e305fcc01df304f',
  exportFilename:'MAZ543-CANDIDATE-hood-tyre-v1-current-pose.glb',
  notice:'候选审查：拟合盖面与轮胎字样｜未替换生产模型；锁扣干涉、原生派生UV与整车验收仍未通过，网页尚未验证。'};
 return {kind:'tyre-v2',url:'/models/review/maz543a-tyre-v2.glb?v=a97860806ba1ff70',
  sha256:'a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422',
  exportFilename:'MAZ543-CANDIDATE-tyre-v2-current-pose.glb',
  notice:'候选审查：轮胎字样 v2｜未替换生产模型；网页、写实及整车验收仍未通过。'};
}

export function reviewCandidateMetadata(asset:Readonly<ReviewVehicleAsset>){
 return asset.kind==='production'?undefined:{id:asset.kind,sourceSHA256:asset.sha256,status:'UNACCEPTED_CANDIDATE'};
}

/** Apply after the ordinary source-pose copy, so repeated frames cannot accumulate it. */
export function applyReviewNativePoseOffset(target:{name:string;position:{z:number};quaternion?:{x:number;y:number;z:number;w:number;set:(x:number,y:number,z:number,w:number)=>unknown}},asset:Readonly<ReviewVehicleAsset>){
 if(target.name!=='cab_pivot_004')return;
 if(asset.kind==='left-driver-v1'||asset.kind==='cab-va180-v1')target.position.z+=2.05;
 if(asset.kind!=='cab-va180-v1'||!target.quaternion)return;
 // Legacy model.update produces Qy(spin) * Qz(+0.3), from Euler XYZ.
 // Remove that rest tilt on the right, then apply the independently verified
 // native candidate rest tilt on the left: Qnew * Qspin. This keeps the wheel
 // normal fixed on its column while the spokes spin around local Y.
 // Values are normalized rotations from the production/candidate GLB nodes.
 const oldZ=0.14943814209799677,oldW=0.9887710764814568;
 const newZ=-0.14943811296121257,newW=0.988771080885051;
 const q=target.quaternion,x=q.x,y=q.y,z=q.z,w=q.w;
 const sx=x*oldW-y*oldZ,sy=y*oldW+x*oldZ,sz=z*oldW-w*oldZ,sw=w*oldW+z*oldZ;
 q.set(newW*sx-newZ*sy,newW*sy+newZ*sx,newW*sz+newZ*sw,newW*sw-newZ*sz);
}
