import * as T from 'three';

// Display-only layer. Authoritative nodes retain their names, hierarchy,
// geometry, poses and visibility; selection also enables this layer.
export const AUTHORITATIVE_PART_LAYER=31;
type Member={mesh:T.Mesh;mask:number};
type Batch={mesh:T.InstancedMesh;members:Member[]};

/** Reuses existing BufferGeometry objects only. No welding, decimation,
 * tessellation change, quantization or changes to the mechanical graph.
 * Transparent, clipped, deforming and custom-rendered parts use normal draws.
 * The presentation root MUST be outside the exported authoritative root.
 */
export class DisplayInstances{
  readonly root=new T.Group();
  private candidates:Member[]=[];
  private batches=new Map<string,Batch>();
  private source:T.Object3D;
  stats={instances:0,batches:0,savedDrawsPerPass:0};
  constructor(source:T.Object3D){
    this.source=source;this.root.name='DISPLAY_ONLY_INSTANCES';
    const geometries=new Map<T.BufferGeometry,T.Mesh[]>();
    source.traverse(o=>{if(o.constructor!==T.Mesh)return;const m=o as T.Mesh;
      if(m.morphTargetInfluences||Object.keys(m.geometry.morphAttributes).length||m.customDepthMaterial||m.customDistanceMaterial||m.onBeforeRender!==T.Object3D.prototype.onBeforeRender||m.onAfterRender!==T.Object3D.prototype.onAfterRender)return;
      const list=geometries.get(m.geometry)??[];list.push(m);geometries.set(m.geometry,list);
    });
    for(const list of geometries.values())if(list.length>1)for(const mesh of list)this.candidates.push({mesh,mask:mesh.layers.mask});
  }
  setEnabled(enabled:boolean){
    this.root.visible=enabled;
    for(const batch of this.batches.values())for(const {mesh,mask} of batch.members)mesh.layers.mask=enabled?(1<<AUTHORITATIVE_PART_LAYER):mask;
  }
  sync(){
    this.setEnabled(false);this.source.updateWorldMatrix(true,true);
    const groups=new Map<string,Member[]>();
    for(const member of this.candidates){const m=member.mesh,mat=m.material;
      if(!(mat instanceof T.MeshStandardMaterial)||mat.transparent||mat.opacity!==1||mat.clippingPlanes?.length||!mat.visible||m.layers.mask!==1)continue;
      let visible=true;for(let o:T.Object3D|null=m;o;o=o.parent)if(!o.visible){visible=false;break;}if(!visible)continue;
      // Instanced normal transforms do not support shear or reflection.
      const e=m.matrixWorld.elements,a=new T.Vector3(e[0],e[1],e[2]),b=new T.Vector3(e[4],e[5],e[6]),c=new T.Vector3(e[8],e[9],e[10]);
      const ab=a.length()*b.length(),ac=a.length()*c.length(),bc=b.length()*c.length();
      if(!ab||!ac||!bc||m.matrixWorld.determinant()<=0||Math.abs(a.dot(b))/ab>1e-12||Math.abs(a.dot(c))/ac>1e-12||Math.abs(b.dot(c))/bc>1e-12)continue;
      const key=[m.geometry.uuid,mat.uuid,+m.castShadow,+m.receiveShadow,m.renderOrder,+m.frustumCulled].join(':');
      const list=groups.get(key)??[];list.push(member);groups.set(key,list);
    }
    for(const batch of this.batches.values()){batch.mesh.visible=false;batch.members=[];}
    this.stats={instances:0,batches:0,savedDrawsPerPass:0};
    for(const [key,members] of groups){if(members.length<2)continue;const first=members[0].mesh;let batch=this.batches.get(key);
      if(!batch||batch.mesh.instanceMatrix.count<members.length){
        if(batch){batch.mesh.removeFromParent();batch.mesh.dispose();}
        const mesh=new T.InstancedMesh(first.geometry,first.material,members.length);
        mesh.name='DISPLAY_'+first.name;mesh.castShadow=first.castShadow;mesh.receiveShadow=first.receiveShadow;mesh.renderOrder=first.renderOrder;mesh.frustumCulled=first.frustumCulled;
        mesh.instanceMatrix.setUsage(T.DynamicDrawUsage);this.root.add(mesh);batch={mesh,members:[]};this.batches.set(key,batch);
      }
      batch.members=members;batch.mesh.visible=true;batch.mesh.count=members.length;
      members.forEach(({mesh},i)=>batch!.mesh.setMatrixAt(i,mesh.matrixWorld));
      batch.mesh.instanceMatrix.needsUpdate=true;batch.mesh.computeBoundingSphere();
      this.stats.instances+=members.length;this.stats.batches++;this.stats.savedDrawsPerPass+=members.length-1;
    }
    this.setEnabled(true);
  }
  dispose(){this.setEnabled(false);for(const batch of this.batches.values())batch.mesh.dispose();this.batches.clear();this.root.removeFromParent();this.root.clear();}
}
