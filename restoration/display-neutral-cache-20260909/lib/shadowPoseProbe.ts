import * as T from 'three';

/** Diagnostic only: compare pose matrices with the Float32 values submitted by
 * Three's stock directional-depth shader. It neither edits poses nor caches
 * shadows. Other shadow inputs still require separate validation. */
export class ShadowPoseProbe{
  private previous=new Map<number,{world:number[];depth:Float32Array;morph:Float32Array}>();
  private modelView=new T.Matrix4();
  inspect(scene:T.Scene,light:T.DirectionalLight,camera:T.Camera){
    let meshes=0,newMeshes=0,worldChanges=0,depthChanges=0,morphChanges=0;
    const changedExamples:string[]=[];
    scene.traverseVisible(object=>{
      if(!(object instanceof T.Mesh)||!object.castShadow||!object.layers.test(camera.layers))return;
      meshes++;
      this.modelView.multiplyMatrices(light.shadow.camera.matrixWorldInverse,object.matrixWorld);
      const world=object.matrixWorld.elements.slice(),depth=new Float32Array(this.modelView.elements);
      const influences=object.morphTargetInfluences??[],base=object.geometry.morphTargetsRelative?1:1-influences.reduce((sum,value)=>sum+value,0);
      const morph=new Float32Array([base,...influences]);
      const previous=this.previous.get(object.id);
      const different=(a:ArrayLike<number>,b:ArrayLike<number>)=>a.length!==b.length||Array.from(a).some((value,i)=>!Object.is(value,b[i]));
      if(!previous)newMeshes++;
      else{
        if(different(world,previous.world))worldChanges++;
        if(different(depth,previous.depth)){depthChanges++;if(changedExamples.length<6)changedExamples.push(object.name);}
        if(different(morph,previous.morph))morphChanges++;
      }
      this.previous.set(object.id,{world,depth,morph});
    });
    return {visibleShadowMeshes:meshes,newMeshes,worldMatrixChanges:worldChanges,depthUniformMatrixChanges:depthChanges,morphUniformChanges:morphChanges,changedExamples,
      limits:'Pose-only diagnostic against the last rendered light camera. Includes all visible cast-shadow meshes before shadow frustum culling. Not a complete shadow-cache eligibility test.'};
  }
}
