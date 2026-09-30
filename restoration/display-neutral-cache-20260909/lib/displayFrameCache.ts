import * as T from 'three';

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
  invalidate(){this.valid=false;}
  needsRender(scene:T.Scene,camera:T.Camera,revision:unknown){
    scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
    const values=this.current;values.length=0;
    this.doubleSidedVersions.length=0;
    this.customRenderMaterials.clear();
    const ranges:{start:number;end:number;name:string}[]=[];
    const matrix=(m:T.Matrix4)=>{for(const v of m.elements)values.push(v);};
    matrix(camera.matrixWorld);matrix(camera.projectionMatrix);values.push(camera.layers.mask);
    if(this.diagnose)ranges.push({start:0,end:values.length,name:'camera'});
    scene.traverseVisible(o=>{
      const start=values.length;
      values.push(o.id,o.layers.mask,o.renderOrder,+o.castShadow,+o.receiveShadow);matrix(o.matrixWorld);
      if(o instanceof T.Mesh||o instanceof T.Line||o instanceof T.Points){
        const g=o.geometry;values.push(g.id,g.index?this.identity(g.index):0,g.index?.version??-1,g.drawRange.start,g.drawRange.count);
        for(const name of Object.keys(g.attributes).sort()){const a=g.attributes[name];values.push(this.identity(a),a.count,a.itemSize,(a instanceof T.InterleavedBufferAttribute?a.data.version:a.version));}
        if(o instanceof T.Mesh&&o.morphTargetInfluences)for(const v of o.morphTargetInfluences)values.push(v);
        for(const m of Array.isArray(o.material)?o.material:[o.material]){
          if(o.onBeforeRender!==T.Object3D.prototype.onBeforeRender||o.onAfterRender!==T.Object3D.prototype.onAfterRender)this.customRenderMaterials.add(m);
          if(m.transparent&&m.side===T.DoubleSide&&!m.forceSinglePass)this.doubleSidedVersions.push({material:m,index:values.length+1,version:m.version});
          values.push(m.id,m.version,+m.visible,m.opacity,+m.transparent,m.side,+m.depthWrite,+m.depthTest);
          if(m instanceof T.MeshStandardMaterial){values.push(m.emissiveIntensity,m.roughness,m.metalness,m.color.r,m.color.g,m.color.b,m.emissive.r,m.emissive.g,m.emissive.b,+m.wireframe);}
          for(const texture of Object.values(m))if(texture instanceof T.Texture)values.push(texture.id,texture.version);
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
