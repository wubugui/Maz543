/** Explicit development-only asset review. Never changes the ordinary production selection. */
export type ReviewVehicleAsset={kind:'production'|'tyre-v2'|'hood-tyre-v1'|'left-driver-v1';url:string;sha256:string;exportFilename:string;notice:string|null};
export const PRODUCTION_VEHICLE_ASSET:Readonly<ReviewVehicleAsset>=Object.freeze({
 kind:'production',url:'/models/maz543a-blender.glb?v=rear-box-frame-20260930',
 sha256:'4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698',
 exportFilename:'MAZ543-reference-current-pose.glb',notice:null,
});
export function selectReviewVehicleAsset(search:string,development:boolean):Readonly<ReviewVehicleAsset>{
 const query=new URLSearchParams(search),requested=query.getAll('asset-review');
 if(requested.length===0)return PRODUCTION_VEHICLE_ASSET;
 if(requested.length!==1||!['tyre-v2','hood-tyre-v1','left-driver-v1'].includes(requested[0]))return {...PRODUCTION_VEHICLE_ASSET,notice:'候选参数无效，当前选择生产资产。'};
 if(!development||query.get('render-worker')==='1'||query.get('worker-build')==='1')return {...PRODUCTION_VEHICLE_ASSET,notice:'候选审查仅支持开发环境的普通显示；当前选择生产资产。'};
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
export function applyReviewNativePoseOffset(target:{name:string;position:{z:number}},asset:Readonly<ReviewVehicleAsset>){
 if(asset.kind==='left-driver-v1'&&target.name==='cab_pivot_004')target.position.z+=2.05;
}
