import * as T from 'three';

/** Owns resources of GLTFs loaded by one viewer instance. Material.dispose()
 * does not dispose its textures. Late async loads must also release resources
 * after that viewer has unmounted (including development hot replacement).
 */
export class RenderResources{
  private geometries=new Set<T.BufferGeometry>();
  private materials=new Set<T.Material>();
  private textures=new Set<T.Texture>();
  private closed=false;
  private readonly geometryLabels?:Map<T.BufferGeometry,Set<string>>;
  constructor(geometryLabels?:Map<T.BufferGeometry,Set<string>>){this.geometryLabels=geometryLabels;}
  track(root:T.Object3D){
    if(this.closed){const late=new RenderResources();late.track(root);late.dispose();return;}
    root.traverse(o=>{
      if(!(o instanceof T.Mesh||o instanceof T.Line||o instanceof T.Points))return;
      this.geometries.add(o.geometry);
      if(this.geometryLabels){let labels=this.geometryLabels.get(o.geometry);if(!labels)this.geometryLabels.set(o.geometry,labels=new Set());labels.add(o.name);}
      for(const mat of Array.isArray(o.material)?o.material:[o.material]){
        this.materials.add(mat);
        for(const value of Object.values(mat))if(value instanceof T.Texture)this.textures.add(value);
      }
    });
  }
  /** Read-only census of owned versus still-referenced resources, including
   * hidden assemblies. Counts underlying buffers once, not each typed view.
   * Does not infer GPU/driver allocation from JS resource counts. */
  inventory(root:T.Object3D){
    const live=new RenderResources();live.track(root);
    const buffers=(geometries:Iterable<T.BufferGeometry>)=>{
      const result=new Set<ArrayBufferLike>();
      for(const geometry of geometries){
        const attributes=[...Object.values(geometry.attributes),...Object.values(geometry.morphAttributes).flat(),...(geometry.index?[geometry.index]:[])];
        for(const attribute of attributes)result.add(attribute.array.buffer);
      }
      return result;
    };
    const sum=(values:Iterable<ArrayBufferLike>)=>[...values].reduce((n,buffer)=>n+buffer.byteLength,0);
    const owned=buffers(this.geometries),referenced=buffers(live.geometries);
    const orphans=[...this.geometries].filter(geometry=>!live.geometries.has(geometry));
    return {owned:{geometries:this.geometries.size,materials:this.materials.size,textures:this.textures.size,geometryBuffers:owned.size,geometryBufferBytes:sum(owned)},
      referenced:{geometries:live.geometries.size,materials:live.materials.size,textures:live.textures.size,geometryBuffers:referenced.size,geometryBufferBytes:sum(referenced)},
      orphaned:{geometries:orphans.length,materials:[...this.materials].filter(m=>!live.materials.has(m)).length,textures:[...this.textures].filter(t=>!live.textures.has(t)).length,
        exclusiveGeometryBufferBytes:sum([...owned].filter(buffer=>!referenced.has(buffer))),
        geometry:orphans.map(geometry=>({labels:[...(this.geometryLabels?.get(geometry)??[])],bufferBytes:sum(buffers([geometry]))}))},
      limits:'Underlying JS geometry buffers only, including index, interleaved attributes and morph targets. Shared backing buffers count once and are exclusive only if absent from every retained geometry. Includes hidden objects; excludes driver/GPU allocations, parser caches, textures, simulation and temporary allocations.'};
  }
  /** Call only after native assembly is complete. Keep every geometry used by
   * the assembled root, including invisible internal/alternate assemblies.
   * Replaced source geometry has no remaining viewport consumer. Materials and
   * textures stay owned because export/style maps can reference them directly. */
  releaseReplacedGeometry(root:T.Object3D){
    if(this.closed)return 0;
    const retained=new Set<T.BufferGeometry>();
    root.traverse(object=>{if(object instanceof T.Mesh||object instanceof T.Line||object instanceof T.Points)retained.add(object.geometry);});
    let released=0;
    for(const geometry of this.geometries)if(!retained.has(geometry)){
      geometry.dispose();this.geometries.delete(geometry);this.geometryLabels?.delete(geometry);released++;
    }
    return released;
  }
  dispose(){
    if(this.closed)return;this.closed=true;
    this.geometries.forEach(g=>g.dispose());this.materials.forEach(m=>m.dispose());
    const images=new Set<ImageBitmap>();
    this.textures.forEach(texture=>{
      const candidates=Array.isArray(texture.image)?texture.image:[texture.image];
      if(typeof ImageBitmap!=='undefined')for(const image of candidates)if(image instanceof ImageBitmap)images.add(image);
      texture.dispose();
    });
    images.forEach(image=>image.close());
    this.geometries.clear();this.materials.clear();this.textures.clear();
    this.geometryLabels?.clear();
  }
}
