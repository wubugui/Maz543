import * as T from 'three';

/** Conservative display invalidation for this viewer. Compares the complete
 * visible presentation at full JS numeric precision: no position epsilon,
 * rounding, frozen physics or reduced tessellation. Invisible mechanisms keep
 * solving independently. Unknown custom rendering should call invalidate().
 */
export class DisplayFrameCache{
  private previous:number[]=[];
  private current:number[]=[];
  private revision:unknown;
  private valid=false;
  private ids=new WeakMap<object,number>();
  private nextId=1;
  private identity(o:object){let id=this.ids.get(o);if(id===undefined){id=this.nextId++;this.ids.set(o,id);}return id;}
  invalidate(){this.valid=false;}
  needsRender(scene:T.Scene,camera:T.Camera,revision:unknown){
    scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);
    const values=this.current;values.length=0;
    const matrix=(m:T.Matrix4)=>{for(const v of m.elements)values.push(v);};
    matrix(camera.matrixWorld);matrix(camera.projectionMatrix);values.push(camera.layers.mask);
    scene.traverseVisible(o=>{
      values.push(o.id,o.layers.mask,o.renderOrder,+o.castShadow,+o.receiveShadow);matrix(o.matrixWorld);
      if(o instanceof T.Mesh||o instanceof T.Line||o instanceof T.Points){
        const g=o.geometry;values.push(g.id,g.index?this.identity(g.index):0,g.index?.version??-1,g.drawRange.start,g.drawRange.count);
        for(const name of Object.keys(g.attributes).sort()){const a=g.attributes[name];values.push(this.identity(a),a.count,a.itemSize,(a instanceof T.InterleavedBufferAttribute?a.data.version:a.version));}
        if(o instanceof T.Mesh&&o.morphTargetInfluences)for(const v of o.morphTargetInfluences)values.push(v);
        for(const m of Array.isArray(o.material)?o.material:[o.material]){
          values.push(m.id,m.version,+m.visible,m.opacity,+m.transparent,m.side,+m.depthWrite,+m.depthTest);
          if(m instanceof T.MeshStandardMaterial){values.push(m.emissiveIntensity,m.roughness,m.metalness,m.color.r,m.color.g,m.color.b,m.emissive.r,m.emissive.g,m.emissive.b,+m.wireframe);}
          for(const texture of Object.values(m))if(texture instanceof T.Texture)values.push(texture.id,texture.version);
        }
      }
      if(o instanceof T.Light){values.push(o.intensity,o.color.r,o.color.g,o.color.b);
        if(o instanceof T.DirectionalLight){matrix(o.target.matrixWorld);matrix(o.shadow.camera.projectionMatrix);values.push(o.shadow.bias,o.shadow.normalBias,o.shadow.radius,o.shadow.mapSize.x,o.shadow.mapSize.y);}
      }
    });
    const changed=!this.valid||revision!==this.revision||values.length!==this.previous.length||values.some((v,i)=>!Object.is(v,this.previous[i]));
    this.revision=revision;this.valid=true;this.current=this.previous;this.previous=values;
    return changed;
  }
}
