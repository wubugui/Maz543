import * as T from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

export async function exportGLB(root:T.Group, originalMaterials:Map<string,T.Material>, animations:T.AnimationClip[]=[]) {
  const scene=new T.Scene();scene.name='MAZ543_REFERENCE';const copy=root.clone(true);scene.add(copy);
  const materials=new Map<T.Material,T.Material>();
  copy.traverse(o=>{
    if(!(o instanceof T.Mesh))return;
    const src=originalMaterials.get(o.name)||(o.material as T.Material);
    if(!materials.has(src)){const mat=(src as T.MeshStandardMaterial).clone();mat.clippingPlanes=null;mat.wireframe=false;if(mat.map instanceof T.DataTexture)mat.map=null;if(mat.bumpMap instanceof T.DataTexture)mat.bumpMap=null;if(mat.roughnessMap instanceof T.DataTexture)mat.roughnessMap=null;materials.set(src,mat);}
    o.material=materials.get(src)!;
  });
  try{return await new GLTFExporter().parseAsync(scene,{binary:true,onlyVisible:true,animations}) as ArrayBuffer;}
  finally{materials.forEach(mat=>mat.dispose());}
}
