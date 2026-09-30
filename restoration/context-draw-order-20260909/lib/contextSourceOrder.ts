import type {Material,Object3D} from 'three';

type Item={groupOrder:number;renderOrder:number;material:Material;materialVariant?:number;z:number;id:number;object:Object3D};

/** Audit-only alternative to allocation-time IDs in r183's stock comparators.
 * Keeps group/render precedence, material cohorts, exact depth and variant.
 * Source scene traversal supplies material cohort order and exact-depth ties.
 * No depth epsilon, geometry modification, culling or precision reduction. */
export function createContextSourceOrder(scene:Object3D){
  const materials=new Map<Material,number>(),objects=new Map<Object3D,number>();
  scene.traverse(object=>{
    objects.set(object,objects.size);
    const material=(object as Object3D&{material?:Material|Material[]}).material;
    if(material)for(const value of Array.isArray(material)?material:[material])if(!materials.has(value))materials.set(value,materials.size);
  });
  // Postprocessing full-screen scenes are outside the vehicle source tree.
  // Their original order is retained; the actual trace verifies these passes.
  const materialRank=(material:Material)=>materials.get(material)??materials.size+(material as Material&{id:number}).id;
  const objectRank=(item:Item)=>objects.get(item.object)??objects.size+item.id;
  return {
    opaque:(a:Item,b:Item)=>a.groupOrder-b.groupOrder||a.renderOrder-b.renderOrder||materialRank(a.material)-materialRank(b.material)||(a.materialVariant??0)-(b.materialVariant??0)||a.z-b.z||objectRank(a)-objectRank(b),
    transparent:(a:Item,b:Item)=>a.groupOrder-b.groupOrder||a.renderOrder-b.renderOrder||b.z-a.z||objectRank(a)-objectRank(b),
    materialCount:materials.size,objectCount:objects.size,
  };
}
