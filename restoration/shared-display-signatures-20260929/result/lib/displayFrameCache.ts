import * as T from 'three';

// Every texture property MeshStandardMaterial / MeshPhysicalMaterial (r183)
// passes to its program, in declaration order.
const STANDARD_TEXTURE_SLOTS=['map','lightMap','aoMap','emissiveMap','bumpMap','normalMap','displacementMap','roughnessMap','metalnessMap','alphaMap','envMap',
  'anisotropyMap','clearcoatMap','clearcoatRoughnessMap','clearcoatNormalMap','iridescenceMap','iridescenceThicknessMap','sheenColorMap','sheenRoughnessMap','transmissionMap','thicknessMap','specularIntensityMap','specularColorMap'] as const;

/** Conservative display invalidation for this viewer. Compares the complete
 * visible presentation at full JS numeric precision: no position epsilon,
 * rounding, frozen physics or reduced tessellation. Invisible mechanisms keep
 * solving independently. Unknown custom rendering should call invalidate().
 */
export class DisplayFrameCache{
  readonly diagnose:boolean;
  lastChange:{kind:string;index?:number;before?:number;after?:number;object?:string}|null=null;
  constructor(diagnose=false){this.diagnose=diagnose;}
  private previous:number[]=[];
  private current:number[]=[];
  private revision:unknown;
  private valid=false;
  private doubleSidedVersions:{material:T.Material;index:number;version:number}[]=[];
  private customRenderMaterials=new Set<T.Material>();
  /** Three r183 renders transparent DoubleSide materials in two passes and
   * increments their version twice per draw, restoring side afterwards. Accept
   * only these stock-renderer version changes after a successful draw. All
   * presentation values and subsequent application updates remain compared. */
  acknowledgeRenderedVersions(){
    for(const entry of this.doubleSidedVersions){
      const m=entry.material,delta=m.version-entry.version;
      if(m.transparent&&m.side===T.DoubleSide&&!m.forceSinglePass&&delta>0&&delta%2===0&&!this.customRenderMaterials.has(m)&&m.onBeforeRender===T.Material.prototype.onBeforeRender){
        this.previous[entry.index]=m.version;
      }
    }
  }
  private ids=new WeakMap<object,number>();
  private nextId=1;
  private identity(o:object){let id=this.ids.get(o);if(id===undefined){id=this.nextId++;this.ids.set(o,id);}return id;}
  /** Which comparison produced the latest result: 'camera' is the fast path;
   * 'rebase' is a full pass reporting a change only because no baseline existed. */
  lastPath:'camera'|'full'|'rebase'='full';
  private lastCamera=new Float64Array(33);
  private hasLastCamera=false;
  /** True when this call is the camera's first differing pose since the last
   * call. Always records the pose, so both paths keep the same baseline. */
  private cameraMoved(camera:T.Camera){
    const e=camera.matrixWorld.elements,p=camera.projectionMatrix.elements,last=this.lastCamera;let moved=!this.hasLastCamera;
    for(let i=0;i<16;i++){if(!Object.is(last[i],e[i])){moved=true;last[i]=e[i];}if(!Object.is(last[16+i],p[i])){moved=true;last[16+i]=p[i];}}
    if(last[32]!==camera.layers.mask){moved=true;last[32]=camera.layers.mask;}
    this.hasLastCamera=true;return moved;
  }
  invalidate(){this.valid=false;}
  /** With cameraFastPath, a moved camera always changes the image, so the
   * full presentation traversal is skipped and the next full check starts a
   * fresh baseline (conservatively reporting one change). */
  needsRender(scene:T.Scene,camera:T.Camera,revision:unknown,options:{cameraFastPath?:boolean}={}){
    camera.updateMatrixWorld(true);
    if(this.cameraMoved(camera)&&options.cameraFastPath){this.valid=false;this.lastPath='camera';if(this.diagnose)this.lastChange={kind:'camera fast path'};return true;}
    this.lastPath=this.valid?'full':'rebase';
    scene.updateMatrixWorld(true);
    const values=this.current;values.length=0;
    this.doubleSidedVersions.length=0;
    this.customRenderMaterials.clear();
    const ranges:{start:number;end:number;name:string}[]=[];
    // Assemblies share resources across many parts. Keep each part's resource
    // reference in the signature, but read each resource's current state once
    // per comparison. These sets are intentionally not retained across frames:
    // direct material edits and attribute replacements must remain observable.
    const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>();
    const matrix=(m:T.Matrix4)=>{for(const v of m.elements)values.push(v);};
    matrix(camera.matrixWorld);matrix(camera.projectionMatrix);values.push(camera.layers.mask);
    if(this.diagnose)ranges.push({start:0,end:values.length,name:'camera'});
    scene.traverseVisible(o=>{
      const start=values.length;
      values.push(o.id,o.layers.mask,o.renderOrder,+o.castShadow,+o.receiveShadow);matrix(o.matrixWorld);
      if(o instanceof T.Mesh||o instanceof T.Line||o instanceof T.Points){
        const g=o.geometry;values.push(g.id);
        if(!geometries.has(g)){
          geometries.add(g);values.push(g.index?this.identity(g.index):0,g.index?.version??-1,g.drawRange.start,g.drawRange.count);
          const names=Object.keys(g.attributes).sort();values.push(names.length);
          for(const name of names){const a=g.attributes[name];values.push(this.identity(a),a.count,a.itemSize,(a instanceof T.InterleavedBufferAttribute?a.data.version:a.version));}
        }
        const influences=o instanceof T.Mesh?o.morphTargetInfluences:undefined;
        values.push(influences?.length??0);if(influences)for(const v of influences)values.push(v);
        const sourceMaterials=Array.isArray(o.material)?o.material:[o.material];values.push(sourceMaterials.length);
        for(const m of sourceMaterials){
          values.push(m.id);
          if(o.onBeforeRender!==T.Object3D.prototype.onBeforeRender||o.onAfterRender!==T.Object3D.prototype.onAfterRender)this.customRenderMaterials.add(m);
          if(materials.has(m))continue;
          materials.add(m);
          if(m.transparent&&m.side===T.DoubleSide&&!m.forceSinglePass)this.doubleSidedVersions.push({material:m,index:values.length+1,version:m.version});
          values.push(m.id,m.version,+m.visible,m.opacity,+m.transparent,m.side,+m.depthWrite,+m.depthTest);
          if(m instanceof T.MeshStandardMaterial){values.push(m.emissiveIntensity,m.roughness,m.metalness,m.color.r,m.color.g,m.color.b,m.emissive.r,m.emissive.g,m.emissive.b,+m.wireframe);}
          // Stock standard/physical materials sample only their declared slots;
          // enumerate those instead of every property. Others keep the full scan.
          if((m.constructor===T.MeshStandardMaterial||m.constructor===T.MeshPhysicalMaterial)&&m.onBeforeCompile===T.Material.prototype.onBeforeCompile){
            const slots=m as unknown as Record<string,unknown>;
            for(const slot of STANDARD_TEXTURE_SLOTS){const texture=slots[slot];if(texture instanceof T.Texture)values.push(texture.id,texture.version);}
          }else for(const texture of Object.values(m))if(texture instanceof T.Texture)values.push(texture.id,texture.version);
        }
      }
      if(o instanceof T.Light){values.push(o.intensity,o.color.r,o.color.g,o.color.b);
        if(o instanceof T.DirectionalLight){matrix(o.target.matrixWorld);matrix(o.shadow.camera.projectionMatrix);values.push(o.shadow.bias,o.shadow.normalBias,o.shadow.radius,o.shadow.mapSize.x,o.shadow.mapSize.y);}
      }
      if(this.diagnose)ranges.push({start,end:values.length,name:o.name||`${o.type}/${o.id}`});
    });
    const structuralChange=!this.valid||revision!==this.revision||values.length!==this.previous.length;
    const difference=structuralChange?-1:values.findIndex((v,i)=>!Object.is(v,this.previous[i]));
    const changed=structuralChange||difference!==-1;
    if(this.diagnose)this.lastChange=!changed?null:!this.valid?{kind:'invalidated'}:revision!==this.revision?{kind:'controls revision'}:values.length!==this.previous.length?{kind:'presentation length'}:{kind:'numeric value',index:difference,before:this.previous[difference],after:values[difference],object:ranges.find(range=>range.start<=difference&&difference<range.end)?.name};
    this.revision=revision;this.valid=true;this.current=this.previous;this.previous=values;
    return changed;
  }
}
