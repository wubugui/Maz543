import * as T from 'three';
import {AUTHORITATIVE_PART_LAYER} from './displayInstances';
import {applyExactBatchShader,attachExactBatchMatrices} from './exactBatchMatrices';
import {attachOrderedBatchDraws,registerBatchMaterial} from './orderedBatchDraws';

type Member={mesh:T.Mesh;mask:number;instance:number;geometry:number;signature:string;active:boolean};
type Batch={mesh:T.BatchedMesh;members:Member[];sourceMaterial:T.MeshStandardMaterial;sourceFrustumCulled:boolean;exact?:ReturnType<typeof attachExactBatchMatrices>;orderedDispose?:()=>void;materialVersion?:number};
const attributeIds=new WeakMap<object,number>();let nextAttributeId=1;
function attributeSignature(a:T.BufferAttribute|T.InterleavedBufferAttribute){let id=attributeIds.get(a);if(id===undefined){id=nextAttributeId++;attributeIds.set(a,id);}return `${id}:${a instanceof T.InterleavedBufferAttribute?a.data.version:a.version}`;}
function signature(g:T.BufferGeometry){return [g.uuid,g.index?attributeSignature(g.index):'',...Object.keys(g.attributes).sort().map(k=>`${k}:${attributeSignature(g.attributes[k])}`)].join('|');}
function ordinary(m:T.Mesh){const mat=m.material,g=m.geometry;
  return m.constructor===T.Mesh&&mat instanceof T.MeshStandardMaterial&&!mat.transparent&&mat.opacity===1&&!(mat instanceof T.MeshPhysicalMaterial&&mat.transmission>0)&&!mat.clippingPlanes?.length&&!mat.wireframe&&mat.allowOverride&&
    mat.onBeforeCompile===T.Material.prototype.onBeforeCompile&&!m.morphTargetInfluences&&!Object.keys(g.morphAttributes).length&&m.userData.s543Role!=='torsion'&&
    !m.customDepthMaterial&&!m.customDistanceMaterial&&m.onBeforeRender===T.Object3D.prototype.onBeforeRender&&m.onAfterRender===T.Object3D.prototype.onAfterRender&&
    m.layers.mask===1&&m.renderOrder===0&&g.drawRange.start===0&&g.drawRange.count===Infinity&&
    Object.values(g.attributes).every(a=>a instanceof T.BufferAttribute);
}
function supportedTransform(m:T.Matrix4){const e=m.elements;
  const aa=e[0]**2+e[1]**2+e[2]**2,bb=e[4]**2+e[5]**2+e[6]**2,cc=e[8]**2+e[9]**2+e[10]**2;
  return aa>0&&bb>0&&cc>0&&m.determinant()>0&&
    Math.abs(e[0]*e[4]+e[1]*e[5]+e[2]*e[6])/Math.sqrt(aa*bb)<1e-12&&
    Math.abs(e[0]*e[8]+e[1]*e[9]+e[2]*e[10])/Math.sqrt(aa*cc)<1e-12&&
    Math.abs(e[4]*e[8]+e[5]*e[9]+e[6]*e[10])/Math.sqrt(bb*cc)<1e-12;
}

/** CAD-style presentation separate from authoritative part nodes. Each unique
 * geometry is copied verbatim into a material batch. Each part keeps its own
 * transform and per-camera/per-shadow frustum test. No topology simplification.
 * Unsupported or edited parts automatically retain the ordinary draw path.
 */
export class DisplayBatches{
  readonly root=new T.Group();
  private source:T.Object3D;
  private batches:Batch[]=[];
  private preserveOrder=false;
  stats={instances:0,batches:0,savedDrawsPerPass:0,bufferBytes:0,orderRejectedInstances:0,unallocatedSplitGroups:0,unallocatedSourceOnlyGroups:0};
  constructor(source:T.Object3D,options:{exactMatrices?:boolean;preserveOrder?:boolean}={}){
    this.source=source;this.root.name='DISPLAY_ONLY_MATERIAL_BATCHES';
    this.preserveOrder=!!options.preserveOrder;
    if(this.preserveOrder&&!options.exactMatrices)throw new Error('Ordered batches require exact source matrices');
    if(this.preserveOrder)source.updateWorldMatrix(true,true);
    const sourceOnlyMaterials=new Set<T.Material>();
    if(this.preserveOrder)source.traverse(object=>{if(!(object instanceof T.Mesh))return;
      let supported=ordinary(object)&&supportedTransform(object.matrixWorld);
      for(let parent=object.parent;parent;parent=parent.parent)if(parent instanceof T.Group&&parent.renderOrder!==0)supported=false;
      if(!supported)for(const material of Array.isArray(object.material)?object.material:[object.material])sourceOnlyMaterials.add(material);
    });
    const sourceOrder=new Map<T.Object3D,number>();source.traverse(object=>sourceOrder.set(object,sourceOrder.size));
    const groups=new Map<string,T.Mesh[]>();
    source.traverse(o=>{if(!(o instanceof T.Mesh)||!ordinary(o))return;
      for(let p=o.parent;p;p=p.parent)if(p instanceof T.Group&&p.renderOrder!==0)return;
      const layout=Object.keys(o.geometry.attributes).sort().map(k=>{const a=o.geometry.attributes[k];return `${k}:${a.itemSize}:${a.normalized}:${a.array.constructor.name}`;}).join('|');
      const key=[(o.material as T.Material).uuid,+o.castShadow,+o.receiveShadow,+o.frustumCulled,!!o.geometry.index,layout].join(':');
      const list=groups.get(key)??[];list.push(o);groups.set(key,list);
    });
    const materialGroupCounts=new Map<T.Material,number>();
    for(const meshes of groups.values()){const material=meshes[0].material as T.Material;materialGroupCounts.set(material,(materialGroupCounts.get(material)??0)+1);}
    for(const meshes of groups.values()){
      if(meshes.length<2)continue;
      const geometries=[...new Set(meshes.map(m=>m.geometry))],first=meshes[0];
      // Such a material cannot share one globally ordered draw while both
      // layouts are visible. Keep it entirely on the source path and avoid
      // allocating unused copies. Hidden modes may miss an optimization, never
      // a source part; current visibility is still checked again in sync().
      if(this.preserveOrder&&materialGroupCounts.get(first.material as T.Material)!==1){this.stats.unallocatedSplitGroups++;continue;}
      if(this.preserveOrder&&sourceOnlyMaterials.has(first.material as T.Material)){this.stats.unallocatedSourceOnlyGroups++;continue;}
      const vertices=geometries.reduce((n,g)=>n+g.attributes.position.count,0),indices=geometries.reduce((n,g)=>n+(g.index?.count??0),0);
      const batchMaterial=options.exactMatrices?(first.material as T.MeshStandardMaterial).clone():first.material as T.MeshStandardMaterial;
      if(options.exactMatrices)applyExactBatchShader(batchMaterial);
      if(this.preserveOrder)registerBatchMaterial(batchMaterial,first.material as T.Material);
      const mesh=new T.BatchedMesh(meshes.length,vertices,indices,batchMaterial);
      mesh.name='DISPLAY_BATCH_'+(first.material as T.Material).name;
      mesh.castShadow=first.castShadow;mesh.receiveShadow=first.receiveShadow;
      // Individual culling uses each original geometry's bounds. Disable only
      // the redundant aggregate test, whose cached bound would otherwise stale.
      mesh.frustumCulled=false;mesh.perObjectFrustumCulled=first.frustumCulled;
      const ids=new Map(geometries.map(g=>[g,mesh.addGeometry(g)]));
      const members=meshes.map(m=>({mesh:m,mask:m.layers.mask,instance:mesh.addInstance(ids.get(m.geometry)!),geometry:ids.get(m.geometry)!,signature:signature(m.geometry),active:false}));
      this.stats.bufferBytes+=Object.values(mesh.geometry.attributes).reduce((n,a)=>n+a.array.byteLength,0)+(mesh.geometry.index?.array.byteLength??0);
      const orderedDispose=this.preserveOrder?attachOrderedBatchDraws(mesh,members,sourceOrder):undefined;
      const exact=options.exactMatrices?attachExactBatchMatrices(mesh,members):undefined;
      this.stats.bufferBytes+=exact?.extraBytes??0;
      this.batches.push({mesh,members,sourceMaterial:first.material as T.MeshStandardMaterial,sourceFrustumCulled:first.frustumCulled,exact,orderedDispose});this.root.add(mesh);
    }
  }
  setEnabled(enabled:boolean){
    this.root.visible=enabled;
    for(const {members} of this.batches)for(const m of members)m.mesh.layers.mask=enabled&&m.active?(1<<AUTHORITATIVE_PART_LAYER):m.mask;
  }
  sync(){
    this.setEnabled(false);this.source.updateWorldMatrix(true,true);
    this.stats.instances=0;this.stats.batches=0;this.stats.savedDrawsPerPass=0;
    for(const batch of this.batches){let count=0;
      if(batch.exact){const material=batch.mesh.material as T.MeshStandardMaterial;material.copy(batch.sourceMaterial);if(batch.materialVersion!==batch.sourceMaterial.version){material.needsUpdate=true;batch.materialVersion=batch.sourceMaterial.version;}}
      for(const m of batch.members){const o=m.mesh;
        let visible=true;for(let p:T.Object3D|null=o;p;p=p.parent){if(!p.visible){visible=false;break;}if(this.preserveOrder&&p instanceof T.Group&&p.renderOrder!==0){visible=false;break;}}
        m.active=visible&&o.material===batch.sourceMaterial&&ordinary(o)&&o.castShadow===batch.mesh.castShadow&&o.receiveShadow===batch.mesh.receiveShadow&&
          o.frustumCulled===batch.sourceFrustumCulled&&signature(o.geometry)===m.signature&&supportedTransform(o.matrixWorld);
        batch.mesh.setVisibleAt(m.instance,m.active);
        if(m.active){batch.mesh.setMatrixAt(m.instance,o.matrixWorld);count++;}
      }
      batch.mesh.visible=count>0;
      if(count){this.stats.instances+=count;this.stats.batches++;this.stats.savedDrawsPerPass+=Math.max(0,count-1);}
    }
    if(this.preserveOrder){
      const visibleByMaterial=new Map<T.Material,Set<T.Mesh>>();
      this.source.traverseVisible(object=>{if(!(object instanceof T.Mesh)||!(object.layers.mask&1))return;
        for(const material of Array.isArray(object.material)?object.material:[object.material]){if(!material.visible)continue;let set=visibleByMaterial.get(material);if(!set){set=new Set();visibleByMaterial.set(material,set);}set.add(object);}
      });
      this.stats.instances=0;this.stats.batches=0;this.stats.savedDrawsPerPass=0;this.stats.orderRejectedInstances=0;
      for(const batch of this.batches){const visible=visibleByMaterial.get(batch.sourceMaterial)??new Set<T.Mesh>();const active=batch.members.filter(member=>member.active);
        // Splitting one material into multiple draws can interleave source depth
        // order. Keep every source mesh ordinary unless this batch covers all.
        const complete=active.length===visible.size&&active.every(member=>visible.has(member.mesh));
        if(!complete){this.stats.orderRejectedInstances+=active.length;for(const member of batch.members){member.active=false;batch.mesh.setVisibleAt(member.instance,false);}}
        const count=complete?active.length:0;batch.mesh.visible=count>0;
        if(count){this.stats.instances+=count;this.stats.batches++;this.stats.savedDrawsPerPass+=Math.max(0,count-1);}
      }
    }
    this.setEnabled(true);
  }
  /** One-time audit: compares ALL copied attribute components and re-based
   * indices to authoritative buffers. No sampling or geometry tolerance. */
  auditGeometry(){let geometries=0,components=0,indices=0,mismatches=0;
    for(const batch of this.batches){const checked=new Set<number>();
      for(const m of batch.members){if(checked.has(m.geometry))continue;checked.add(m.geometry);geometries++;
        const range=batch.mesh.getGeometryRangeAt(m.geometry)!;
        for(const [name,a] of Object.entries(m.mesh.geometry.attributes)){
          const b=batch.mesh.geometry.attributes[name];
          for(let i=0;i<a.array.length;i++){components++;if(!Object.is(a.array[i],b.array[range.vertexStart*a.itemSize+i]))mismatches++;}
        }
        const a=m.mesh.geometry.index,b=batch.mesh.geometry.index;
        if(a&&b)for(let i=0;i<a.count;i++){indices++;if(a.array[i]!==b.array[range.indexStart+i]-range.vertexStart)mismatches++;}
      }
    }
    return {geometries,components,indices,mismatches,exactCopy:mismatches===0};
  }
  dispose(){this.setEnabled(false);for(const b of this.batches){b.exact?.dispose();b.orderedDispose?.();if(b.exact)(b.mesh.material as T.Material).dispose();b.mesh.dispose();}this.batches=[];this.root.removeFromParent();this.root.clear();}
}
