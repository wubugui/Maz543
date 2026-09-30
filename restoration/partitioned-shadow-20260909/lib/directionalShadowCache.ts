import * as T from 'three';

type Value=number|string|boolean|null;
export type ShadowAssessment={refresh:boolean;eligible:boolean;casters:number;signatureValues:number;reasons:string[]};

/** Conservative cache for this viewer's single stock directional depth map.
 * Model-view/morph values are compared at full JS precision, without epsilon.
 * Authoritative transforms and attributes are never rounded or edited.
 * Unsupported shader paths always request an ordinary full update.
 * assess() is not a commit: call commit() only after a successful shadow draw. */
export class DirectionalShadowCache{
  private previous:Value[]=[];private current:Value[]=[];private valid=false;private eligible=false;
  private map:T.RenderTarget|null=null;
  private mapTextures:T.Texture[]=[];
  private readonly onMapDispose=()=>this.invalidate();
  private ids=new WeakMap<object,number>();private nextId=1;
  private matrix=new T.Matrix4();
  private versions:{material:T.Material;index:number;version:number}[]=[];
  get hasStoredMap(){return this.valid&&this.map!==null;}
  private identity(object:object){let id=this.ids.get(object);if(id===undefined){id=this.nextId++;this.ids.set(object,id);}return id;}
  invalidate(){this.valid=false;this.eligible=false;}
  assess(scene:T.Scene,camera:T.Camera,light:T.DirectionalLight,renderer:Pick<T.WebGLRenderer,'shadowMap'|'capabilities'|'localClippingEnabled'>,includeCaster?:(mesh:T.Mesh)=>boolean):ShadowAssessment{
    scene.updateMatrixWorld(true);light.target.updateMatrixWorld(true);
    this.versions.length=0;
    const values=this.current;values.length=0;const reasons=new Set<string>();let casters=0;
    const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>();
    const add=(...entries:Value[])=>values.push(...entries);
    const matrix=(value:T.Matrix4)=>{for(const entry of value.elements){if(!Number.isFinite(entry))reasons.add('nonfinite matrix');add(entry);}};
    const attribute=(value:T.BufferAttribute|T.InterleavedBufferAttribute|undefined)=>{
      if(!value){add(null);return;}
      add(this.identity(value),value.count,value.itemSize,value.normalized,value.array.constructor.name);
      if(value instanceof T.InterleavedBufferAttribute)add(this.identity(value.data),value.data.version,value.data.stride,value.offset);
      else add(value.version,value.gpuType);
    };
    const texture=(value:T.Texture|null|undefined)=>{
      if(!value){add(null);return;}add(value.id);if(textures.has(value))return;textures.add(value);
      add('texture',value.version,this.identity(value.source),value.source.version,value.channel,value.wrapS,value.wrapT,value.minFilter,value.magFilter,value.anisotropy,value.format,value.type,value.internalFormat,value.generateMipmaps,value.flipY,value.premultiplyAlpha,value.unpackAlignment,value.colorSpace,value.matrixAutoUpdate);
      // Include both authored transform parameters and explicitly supplied matrix.
      add(value.offset.x,value.offset.y,value.repeat.x,value.repeat.y,value.center.x,value.center.y,value.rotation,...value.matrix.elements);
      if(value instanceof T.VideoTexture)reasons.add('video texture');
      if(value.isRenderTargetTexture)reasons.add('render target texture');
    };
    const material=(value:T.Material)=>{
      add(this.identity(value));if(materials.has(value))return;materials.add(value);
      const m=value as T.MeshStandardMaterial;
      this.versions.push({material:value,index:values.length+1,version:value.version});
      add('material',value.version,value.visible,value.side,value.shadowSide,m.wireframe??false,m.wireframeLinewidth??1,(value as T.LineBasicMaterial).linewidth??1,value.alphaTest,value.alphaToCoverage,value.alphaHash);
      texture(m.map);texture(m.alphaMap);
      if(m.displacementMap)reasons.add('displacement');
      if(value instanceof T.ShaderMaterial)reasons.add('custom shader material');
      if(value.onBeforeCompile!==T.Material.prototype.onBeforeCompile||value.onBeforeRender!==T.Material.prototype.onBeforeRender)reasons.add('material callback');
      if(value.alphaHash)reasons.add('alpha hash');
      if(renderer.localClippingEnabled&&value.clipShadows&&value.clippingPlanes?.length)reasons.add('shadow clipping');
    };
    const geometry=(value:T.BufferGeometry)=>{
      add(value.id);if(geometries.has(value))return;geometries.add(value);
      add('geometry',value.drawRange.start,value.drawRange.count,value.morphTargetsRelative);attribute(value.index??undefined);
      if(value.boundingSphere)add(value.boundingSphere.center.x,value.boundingSphere.center.y,value.boundingSphere.center.z,value.boundingSphere.radius);else add(null);
      const names=Object.keys(value.attributes).sort();add(names.length);for(const name of names){add(name);attribute(value.attributes[name]);}
      const morphNames=Object.keys(value.morphAttributes).sort();add(morphNames.length);
      for(const name of morphNames){const attributes=value.morphAttributes[name as keyof typeof value.morphAttributes]??[];add(name,attributes.length);for(const item of attributes)attribute(item);}
      add(value.groups.length);for(const group of value.groups)add(group.start,group.count,group.materialIndex??0);
    };
    if(!renderer.shadowMap.enabled)reasons.add('shadows disabled');
    if(renderer.shadowMap.type!==T.PCFShadowMap&&renderer.shadowMap.type!==T.BasicShadowMap)reasons.add('unsupported shadow map type');
    if(renderer.capabilities.logarithmicDepthBuffer||renderer.capabilities.reversedDepthBuffer)reasons.add('nonstandard depth');
    scene.traverseVisible(object=>{
      if(object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender)reasons.add('render callback');
      if(object instanceof T.Mesh||object instanceof T.Line||object instanceof T.Points)for(const m of Array.isArray(object.material)?object.material:[object.material]){
        if(m.onBeforeRender!==T.Material.prototype.onBeforeRender)reasons.add('material render callback');
      }
    });
    let shadowLights=0;scene.traverseVisible(object=>{if(object instanceof T.Light&&object.castShadow&&object.layers.test(camera.layers)){shadowLights++;if(object!==light)reasons.add('additional shadow light');}});
    if(shadowLights!==1||!light.castShadow)reasons.add('not one active shadow light');
    const shadow=light.shadow;
    if(!shadow.autoUpdate)reasons.add('manually managed shadow');
    // Same public matrix update used by Three's directional shadow pass.
    shadow.updateMatrices(light);
    add('shadow',light.id,renderer.shadowMap.type,camera.layers.mask,shadow.mapSize.x,shadow.mapSize.y,shadow.bias,shadow.normalBias,shadow.radius,shadow.camera.near,shadow.camera.far);
    add(shadow.camera.up.x,shadow.camera.up.y,shadow.camera.up.z,shadow.camera.coordinateSystem,+shadow.camera.reversedDepth);
    const viewport=shadow.getViewport(0);add(viewport.x,viewport.y,viewport.z,viewport.w);
    if(shadow.map)add(shadow.map.width,shadow.map.height,shadow.map.samples,this.identity(shadow.map.texture),shadow.map.texture.version,shadow.map.depthTexture?this.identity(shadow.map.depthTexture):null,shadow.map.depthTexture?.version??null);
    add(...light.matrixWorld.elements,...light.target.matrixWorld.elements);matrix(shadow.camera.projectionMatrix);
    const frustum=shadow.getFrustum();
    scene.traverseVisible(object=>{
      if(!object.layers.test(camera.layers)||!object.castShadow)return;
      if(!(object instanceof T.Mesh)){if(object instanceof T.Line||object instanceof T.Points)reasons.add('non-mesh shadow caster');return;}
      // Optional subset is only for the isolated partitioned-shadow experiment.
      // Its caller must separately assess the complete scene for eligibility.
      if(includeCaster&&!includeCaster(object))return;
      // All casters enter the signature, even outside the shadow frustum. This
      // avoids trusting a previous outside result when bounds/poses change.
      if(object.frustumCulled)frustum.intersectsObject(object); // Match lazy boundingSphere creation before snapshot.
      const sourceMaterials=Array.isArray(object.material)?object.material:[object.material];
      if(!sourceMaterials.some(item=>item.visible))return;
      casters++;add('mesh',object.id,object.frustumCulled);geometry(object.geometry);
      add(sourceMaterials.length);for(const item of sourceMaterials)material(item);
      this.matrix.multiplyMatrices(shadow.camera.matrixWorldInverse,object.matrixWorld);matrix(this.matrix);
      const influences=object.morphTargetInfluences??[];add(influences.length,object.geometry.morphTargetsRelative?1:1-influences.reduce((sum,value)=>sum+value,0));for(const value of influences)add(value);
      if(object instanceof T.InstancedMesh){add('instances',object.count);attribute(object.instanceMatrix);attribute(object.instanceColor??undefined);if(object.morphTexture)reasons.add('instanced morph texture');}
      if(object instanceof T.SkinnedMesh)reasons.add('skinned caster');
      if(object instanceof T.BatchedMesh)reasons.add('batched caster');
      if(object.constructor!==T.Mesh)reasons.add('specialized caster');
      if(object.customDepthMaterial)reasons.add('custom depth material');
      if(object.onBeforeShadow!==T.Object3D.prototype.onBeforeShadow||object.onAfterShadow!==T.Object3D.prototype.onAfterShadow)reasons.add('shadow callback');
    });
    if(values.some(value=>typeof value==='number'&&Number.isNaN(value)))reasons.add('NaN input');
    this.eligible=reasons.size===0;
    const same=this.valid&&this.map===shadow.map&&values.length===this.previous.length&&values.every((value,i)=>Object.is(value,this.previous[i]));
    return {refresh:!this.eligible||!shadow.map||shadow.needsUpdate||!same,eligible:this.eligible,casters,signatureValues:values.length,reasons:[...reasons]};
  }
  commit(map:T.RenderTarget|null){
    if(!this.eligible||!map){this.valid=false;return;}
    // Only accept the stock renderer's temporary DoubleSide material versions.
    // All callbacks that could change inputs during rendering fail eligibility.
    for(const {material:m,index,version} of this.versions){const delta=m.version-version;if(m.transparent&&m.side===T.DoubleSide&&!m.forceSinglePass&&delta>0&&delta%2===0)this.current[index]=m.version;}
    if(this.map!==map||this.mapTextures[0]!==map.texture||(this.mapTextures[1]??null)!==map.depthTexture){
      this.map?.removeEventListener('dispose',this.onMapDispose);for(const texture of this.mapTextures)texture.removeEventListener('dispose',this.onMapDispose);
      this.map=map;map.addEventListener('dispose',this.onMapDispose);this.mapTextures=[map.texture,...(map.depthTexture?[map.depthTexture]:[])];
      for(const texture of this.mapTextures)texture.addEventListener('dispose',this.onMapDispose);
    }
    this.valid=true;const old=this.previous;this.previous=this.current;this.current=old;
  }
  render(scene:T.Scene,camera:T.Camera,light:T.DirectionalLight,renderer:T.WebGLRenderer,render:()=>void){
    const assessment=this.assess(scene,camera,light,renderer);
    if(renderer.clippingPlanes.length){assessment.eligible=false;assessment.refresh=true;assessment.reasons.push('global clipping');this.eligible=false;}
    assessment.refresh ||= renderer.shadowMap.needsUpdate;
    const previousAuto=renderer.shadowMap.autoUpdate;
    renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=assessment.refresh;
    try{render();if(!renderer.shadowMap.needsUpdate)this.commit(light.shadow.map);else this.invalidate();}
    catch(error){this.invalidate();throw error;}
    finally{renderer.shadowMap.autoUpdate=previousAuto;}
    return assessment;
  }
  dispose(){this.map?.removeEventListener('dispose',this.onMapDispose);for(const texture of this.mapTextures)texture.removeEventListener('dispose',this.onMapDispose);this.mapTextures=[];this.map=null;this.invalidate();this.previous.length=0;this.current.length=0;}
}
