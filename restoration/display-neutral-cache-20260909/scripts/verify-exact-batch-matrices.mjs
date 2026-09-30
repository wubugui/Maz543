import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {registerHooks} from 'node:module';
import * as T from 'three';
registerHooks({resolve(s,c,next){try{return next(s,c);}catch(e){if(s.startsWith('.')&&!/\.[a-z]+$/i.test(s))return next(s+'.ts',c);throw e;}}});
const {DisplayBatches}=await import('../lib/displayBatches.ts');
const root=new T.Group(),material=new T.MeshStandardMaterial({roughness:.413}),a=new T.Mesh(new T.BoxGeometry(.31,.37,.42),material),b=new T.Mesh(new T.SphereGeometry(.17,8,6),material);
a.position.set(.234567891,.762834529,-.163514337);a.rotation.set(.174625391,.81762354,-.1835412);a.scale.set(.1732,.4831,.2432);
b.position.set(-1.20384917,.12938,2.1738491);b.rotation.set(-.421783,.27182934,.039172835);b.scale.set(1.47,.49,.73);
root.position.set(.283719237,1.723846192,2.384761973);root.add(a,b);root.updateMatrixWorld(true);
for(const mesh of [a,b]){mesh.castShadow=true;mesh.receiveShadow=true;}
const callback=material.onBeforeCompile,presentation=new DisplayBatches(root,{exactMatrices:true}),scene=new T.Scene();scene.add(root,presentation.root);presentation.sync();
assert.equal(presentation.stats.instances,2);assert.equal(material.onBeforeCompile,callback,'source shader is untouched');
const batch=presentation.root.children[0],texture=batch._matricesTexture,base=texture.image.width*(texture.image.height/3)*4;
const originalVertices=a.geometry.attributes.position.array.slice();let checks=0;
for(const camera of [new T.PerspectiveCamera(35,1.3,.05,120),new T.OrthographicCamera(-10,10,9,-9,.5,40)]){
 camera.position.set(-7.183,13.237,7.149);camera.lookAt(.38,.73,-.29);camera.updateMatrixWorld(true);
 batch.onBeforeRender({},scene,camera,batch.geometry,batch.material,null);
 for(const [instance,mesh] of [a,b].entries()){
  const modelView=new T.Matrix4().multiplyMatrices(camera.matrixWorldInverse,mesh.matrixWorld),normal=new T.Matrix3().getNormalMatrix(modelView),data=texture.image.data;
  assert.deepEqual(data.slice(base+instance*16,base+(instance+1)*16),new Float32Array(modelView.elements),'exact stock model-view upload');
  const actualNormal=new Float32Array([0,1,2,4,5,6,8,9,10].map(offset=>data[base*2+instance*16+offset]));assert.deepEqual(actualNormal,new Float32Array(normal.elements),'exact stock normal upload');
  assert.deepEqual(data.slice(instance*16,(instance+1)*16),new Float32Array(mesh.matrixWorld.elements),'stock world tile remains readable by BatchedMesh');checks++;
 }
}
material.color.setRGB(.183,.284,.573);material.roughness=.137;presentation.sync();assert.deepEqual(batch.material.color,material.color);assert.equal(batch.material.roughness,material.roughness);
assert.deepEqual(a.geometry.attributes.position.array,originalVertices);assert.equal(batch.customDepthMaterial.depthPacking,new T.MeshDepthMaterial().depthPacking);
const shader={vertexShader:T.ShaderLib.standard.vertexShader,fragmentShader:T.ShaderLib.standard.fragmentShader,uniforms:{}};batch.material.onBeforeCompile(shader,{});assert.ok(shader.vertexShader.includes('mazModelView * vec4( transformed, 1.0 )'));assert.ok(shader.vertexShader.includes('mazNormal * objectNormal'));
assert.equal(presentation.auditGeometry().mismatches,0);presentation.dispose();assert.equal(a.layers.mask,1);assert.equal(a.material,material);
const report={passed:true,cameras:2,objects:2,matrixSetsChecked:checks,worldViewNormalFloat32BitEquality:true,sourceGeometryAndMaterialPreserved:true,materialUpdatesPreserved:true,limits:'Exact stock CPU-upload values and geometry copies only. Shader compilation, raster order, culling, pixels and performance need actual browser validation.'};
await fs.mkdir('outputs/exact-batch',{recursive:true});await fs.writeFile('outputs/exact-batch/matrix-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
