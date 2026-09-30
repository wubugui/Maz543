import * as T from 'three';

const sourceMaterials=new WeakMap<T.Material,T.Material>();
type Item={groupOrder:number;renderOrder:number;material:T.Material;materialVariant?:number;z:number;id:number};
type MaterialWithId=T.Material&{id:number};

/** Same r183 opaque comparator, with cloned display materials retaining their
 * source's ordering key. Installed only in the ordered-batch experiment. */
export function orderedBatchOpaqueSort(a:Item,b:Item){
  const am=(sourceMaterials.get(a.material)??a.material) as MaterialWithId;
  const bm=(sourceMaterials.get(b.material)??b.material) as MaterialWithId;
  return a.groupOrder-b.groupOrder||a.renderOrder-b.renderOrder||am.id-bm.id||(a.materialVariant??0)-(b.materialVariant??0)||a.z-b.z||a.id-b.id;
}
export function registerBatchMaterial(display:T.Material,source:T.Material){sourceMaterials.set(display,source);}

type Member={mesh:T.Mesh;instance:number;active:boolean};
type DrawItem={index:number;z:number};
/** Use original JS world matrices and original geometry bounds for culling and
 * sort keys. A material is eligible only if every visible source draw can be
 * represented in one batch; DisplayBatches enforces that separate invariant. */
export function attachOrderedBatchDraws(batch:T.BatchedMesh,members:Member[],sourceOrder:Map<T.Object3D,number>){
  const byInstance=new Map(members.map(member=>[member.instance,member]));
  const projection=new T.Matrix4(),frustum=new T.Frustum(),position=new T.Vector4();
  let shadowPass=false;
  const previous=batch.onBeforeRender;
  batch.perObjectFrustumCulled=false;
  batch.setCustomSort(rawItems=>{
    // r183 supplies index; @types/three currently omits it from this callback.
    const items=rawItems as (typeof rawItems[number]&DrawItem)[];
    for(const item of items){if(!Number.isInteger(item.index)||!byInstance.has(item.index))throw new Error('Unexpected r183 batch draw index');const mesh=byInstance.get(item.index)!.mesh;
      if(shadowPass)item.z=sourceOrder.get(mesh)!;
      else{if(!mesh.geometry.boundingSphere)mesh.geometry.computeBoundingSphere();const c=mesh.geometry.boundingSphere!.center;position.set(c.x,c.y,c.z,1).applyMatrix4(mesh.matrixWorld).applyMatrix4(projection);item.z=position.z;}
    }
    items.sort((a,b)=>a.z-b.z||byInstance.get(a.index)!.mesh.id-byInstance.get(b.index)!.mesh.id);
  });
  batch.onBeforeRender=function(renderer,scene,camera,geometry,material,group){
    shadowPass=scene===null;
    projection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(projection,camera.coordinateSystem,camera.reversedDepth);
    for(const member of members)batch.setVisibleAt(member.instance,member.active&&(!member.mesh.frustumCulled||frustum.intersectsObject(member.mesh)));
    previous.call(this,renderer,scene,camera,geometry,material,group);
  };
  return ()=>{batch.onBeforeRender=previous;batch.setCustomSort(null);};
}
