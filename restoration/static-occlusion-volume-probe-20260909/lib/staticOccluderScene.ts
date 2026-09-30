import * as T from 'three';

export type OccluderObservation={mesh:T.Mesh;stableFrames:number;triangles:number;values:unknown[]};
const same=(a:unknown[],b:unknown[])=>a.length===b.length&&a.every((v,i)=>Object.is(v,b[i]));

export function opaqueDepthMaterial(material:T.Material){
 const m=material as T.MeshStandardMaterial,p=Object.getPrototypeOf(material);
 return (p===T.MeshStandardMaterial.prototype||p===T.MeshPhysicalMaterial.prototype||p===T.MeshNormalMaterial.prototype)&&
  !material.transparent&&!(material as T.MeshPhysicalMaterial).transmission&&material.depthWrite&&material.depthTest&&material.depthFunc===T.LessEqualDepth&&
  !material.stencilWrite&&!material.alphaTest&&!material.alphaHash&&!material.alphaToCoverage&&!material.polygonOffset&&!m.displacementMap&&!m.wireframe&&!material.clippingPlanes?.length&&
  (!material.precision||material.precision==='highp')&&Object.entries(m.defines??{}).every(([key,value])=>(key==='STANDARD'||key==='PHYSICAL')&&value==='')&&
  material.onBeforeCompile===T.Material.prototype.onBeforeCompile&&material.onBeforeRender===T.Material.prototype.onBeforeRender;
}

/** Two identical observed frames means a candidate for this snapshot only,
 * never proof that a part will stay fixed in a later mechanical frame. */
export class StaticOccluderObservations{
 private previous=new WeakMap<T.Mesh,{values:unknown[];stableFrames:number;frame:number}>();private frame=0;
 observe(scene:T.Scene,camera:T.Camera){
  this.frame++;const rows:OccluderObservation[]=[];let unsupported=0;
  scene.traverseVisible(object=>{
   if(!object.layers.test(camera.layers)||!(object instanceof T.Mesh))return;
   const materials=Array.isArray(object.material)?object.material:[object.material],visible=materials.filter(m=>m.visible);
   if(!visible.length)return;
   if(Object.getPrototypeOf(object)!==T.Mesh.prototype||object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender||visible.some(m=>!opaqueDepthMaterial(m))||!object.matrixWorld.elements.every(Number.isFinite)||!(object.morphTargetInfluences??[]).every(Number.isFinite)){unsupported++;return;}
   const geometry:T.BufferGeometry=object.geometry,values:unknown[]=[geometry,object.frustumCulled,geometry.drawRange.start,geometry.drawRange.count,geometry.morphTargetsRelative,...object.matrixWorld.elements,...camera.matrixWorldInverse.elements,...camera.projectionMatrix.elements,...(object.morphTargetInfluences??[])];
   const attribute=(a:T.BufferAttribute|T.InterleavedBufferAttribute|null)=>{
    if(!a){values.push(null);return;}values.push(a,a.array,a.array?.buffer,a.itemSize,a.count,a.normalized);
    if(a instanceof T.InterleavedBufferAttribute)values.push(a.data,a.data.version,a.data.stride,a.offset);else values.push(a.version,a.gpuType);
   };
   attribute(geometry.index);for(const name of Object.keys(geometry.attributes).sort()){values.push(name);attribute(geometry.attributes[name]);}
   for(const name of Object.keys(geometry.morphAttributes).sort()){const list=geometry.morphAttributes[name as keyof typeof geometry.morphAttributes]??[];values.push(name,list.length);for(const a of list)attribute(a);}
   values.push(geometry.groups.length);for(const group of geometry.groups)values.push(group.start,group.count,group.materialIndex);
   for(const material of materials)values.push(material,material.visible,material.side,material.precision,material.depthFunc,material.depthWrite,material.depthTest);
   const previous=this.previous.get(object),stableFrames=previous?.frame===this.frame-1&&same(previous.values,values)?previous.stableFrames+1:1;
   this.previous.set(object,{values,stableFrames,frame:this.frame});
   const count=geometry.index?.count??geometry.attributes.position?.count??0;
   const triangles=Array.isArray(object.material)?geometry.groups.reduce((sum,group)=>{
    const material=materials[group.materialIndex??0];if(!material?.visible)return sum;
    const first=Math.max(geometry.drawRange.start,group.start),last=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group.start+group.count);return sum+Math.max(0,Math.floor((last-first)/3));
   },0):Math.max(0,Math.floor((Math.min(count,geometry.drawRange.start+geometry.drawRange.count)-geometry.drawRange.start)/3));
   rows.push({mesh:object,stableFrames,triangles,values});
  });
  return {rows,unsupported};
 }
 clear(){this.previous=new WeakMap();}
}

/** Owned objects/materials only. Authoritative geometry and attributes remain
 * shared read-only and MUST NOT be disposed with the diagnostic scene. */
export function createStaticOccluderScene(rows:OccluderObservation[]){
 const scene=new T.Scene(),materials=new Map<string,T.MeshNormalMaterial>(),clones:T.Mesh[]=[];
 const normal=(source:T.Material)=>{
  const key=`${source.side}/${source.visible}`;let material=materials.get(key);
  if(!material){material=new T.MeshNormalMaterial({side:source.side,colorWrite:false,depthWrite:true,depthTest:true,depthFunc:T.LessEqualDepth,blending:T.NoBlending,visible:source.visible});materials.set(key,material);}return material;
 };
 for(const {mesh:source} of rows){
  const mesh=new T.Mesh(source.geometry,Array.isArray(source.material)?source.material.map(normal):normal(source.material));
  mesh.name=source.name;mesh.matrixAutoUpdate=false;mesh.matrixWorldAutoUpdate=false;mesh.matrix.copy(source.matrixWorld);mesh.matrixWorld.copy(source.matrixWorld);
  mesh.frustumCulled=source.frustumCulled;mesh.layers.mask=source.layers.mask;
  if(source.morphTargetInfluences)mesh.morphTargetInfluences=[...source.morphTargetInfluences];
  scene.add(mesh);clones.push(mesh);
 }
 let disposed=false;
 return {scene,clones,dispose(){if(disposed)return;disposed=true;scene.clear();clones.length=0;for(const material of materials.values())material.dispose();materials.clear();}};
}
