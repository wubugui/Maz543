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
  track(root:T.Object3D){
    if(this.closed){const late=new RenderResources();late.track(root);late.dispose();return;}
    root.traverse(o=>{
      if(!(o instanceof T.Mesh||o instanceof T.Line||o instanceof T.Points))return;
      this.geometries.add(o.geometry);
      for(const mat of Array.isArray(o.material)?o.material:[o.material]){
        this.materials.add(mat);
        for(const value of Object.values(mat))if(value instanceof T.Texture)this.textures.add(value);
      }
    });
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
  }
}
