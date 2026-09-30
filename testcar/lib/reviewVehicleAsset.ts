/** Explicit development-only asset review. Never changes the ordinary production selection. */
export type ReviewVehicleAsset={kind:'production'|'tyre-v2';url:string;sha256:string;exportFilename:string;notice:string|null};
export const PRODUCTION_VEHICLE_ASSET:Readonly<ReviewVehicleAsset>=Object.freeze({
 kind:'production',url:'/models/maz543a-blender.glb?v=rear-box-frame-20260930',
 sha256:'4aa0a22875cae080211dcd49e02249c9ff0eb27f385a51246b0ecc79ca379698',
 exportFilename:'MAZ543-reference-current-pose.glb',notice:null,
});
export function selectReviewVehicleAsset(search:string,development:boolean):Readonly<ReviewVehicleAsset>{
 const query=new URLSearchParams(search),requested=query.getAll('asset-review');
 if(requested.length===0)return PRODUCTION_VEHICLE_ASSET;
 if(requested.length!==1||requested[0]!=='tyre-v2')return {...PRODUCTION_VEHICLE_ASSET,notice:'候选参数无效，当前选择生产资产。'};
 if(!development||query.get('render-worker')==='1'||query.get('worker-build')==='1')return {...PRODUCTION_VEHICLE_ASSET,notice:'候选审查仅支持开发环境的普通显示；当前选择生产资产。'};
 return {kind:'tyre-v2',url:'/models/review/maz543a-tyre-v2.glb?v=a97860806ba1ff70',
  sha256:'a97860806ba1ff70b61cd7a01ac173f0f461c380704ab06246cd9352660ac422',
  exportFilename:'MAZ543-CANDIDATE-tyre-v2-current-pose.glb',
  notice:'候选审查：轮胎字样 v2｜未替换生产模型；网页、写实及整车验收仍未通过。'};
}

export function reviewCandidateMetadata(asset:Readonly<ReviewVehicleAsset>){
 return asset.kind==='production'?undefined:{id:asset.kind,sourceSHA256:asset.sha256,status:'UNACCEPTED_CANDIDATE'};
}
