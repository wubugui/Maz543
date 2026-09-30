import * as T from 'three';

const patched=new WeakSet<T.Material>();
const functions=/* glsl */`
#ifdef USE_BATCHING
mat4 mazBatchMatrix( const in float index, const in int tile ) {
  ivec2 dimensions = textureSize( batchingTexture, 0 );
  int j = int( index ) * 4;
  int x = j % dimensions.x;
  int y = j / dimensions.x + tile * ( dimensions.y / 3 );
  return mat4(
    texelFetch( batchingTexture, ivec2( x, y ), 0 ),
    texelFetch( batchingTexture, ivec2( x + 1, y ), 0 ),
    texelFetch( batchingTexture, ivec2( x + 2, y ), 0 ),
    texelFetch( batchingTexture, ivec2( x + 3, y ), 0 ) );
}
#endif
`;
const batching=/* glsl */`
#ifdef USE_BATCHING
float mazBatchIndex = getIndirectIndex( gl_DrawID );
mat4 batchingMatrix = getBatchingMatrix( mazBatchIndex );
mat4 mazModelView = mazBatchMatrix( mazBatchIndex, 1 );
mat3 mazNormal = mat3( mazBatchMatrix( mazBatchIndex, 2 ) );
#endif
`;
const project=/* glsl */`
#ifdef USE_BATCHING
vec4 mvPosition = mazModelView * vec4( transformed, 1.0 );
gl_Position = projectionMatrix * mvPosition;
#else
${T.ShaderChunk.project_vertex}
#endif
`;
const normal=/* glsl */`
#ifdef USE_BATCHING
vec3 transformedNormal = mazNormal * objectNormal;
#ifdef FLIP_SIDED
transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
vec3 transformedTangent = ( mazModelView * vec4( objectTangent, 0.0 ) ).xyz;
#ifdef FLIP_SIDED
transformedTangent = - transformedTangent;
#endif
#endif
#else
${T.ShaderChunk.defaultnormal_vertex}
#endif
`;
const world=/* glsl */`
#ifdef USE_BATCHING
#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined( USE_SHADOWMAP ) || defined( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
vec4 worldPosition = batchingMatrix * vec4( transformed, 1.0 );
#endif
#else
${T.ShaderChunk.worldpos_vertex}
#endif
`;

/** Instance-local shader adapter, pinned to Three r183 chunks. Ordinary meshes
 * keep the stock branch; no global ShaderChunk or source material is modified. */
export function applyExactBatchShader(material:T.Material){
  if(patched.has(material))return;patched.add(material);
  const previous=material.onBeforeCompile,previousKey=material.customProgramCacheKey;
  material.onBeforeCompile=function(shader,renderer){
    previous.call(this,shader,renderer);
    for(const [name,replacement] of Object.entries({batching_pars_vertex:T.ShaderChunk.batching_pars_vertex+functions,batching_vertex:batching,project_vertex:project,defaultnormal_vertex:normal,worldpos_vertex:world})){
      shader.vertexShader=shader.vertexShader.replace(`#include <${name}>`,replacement);
    }
  };
  material.customProgramCacheKey=function(){return previousKey.call(this)+'|maz-exact-batch-matrices-r183';};material.needsUpdate=true;
}

type Source={instance:number;mesh:T.Mesh;active:boolean};
type MatrixStorage={_matricesTexture:T.DataTexture};
/** Keep the original world-matrix tile at its stock offsets for BatchedMesh
 * bounds/sorting. Additional tiles hold the CPU-computed stock per-draw
 * modelView and normal uniforms, including for the light/normal passes. */
export function attachExactBatchMatrices(batch:T.BatchedMesh,sources:Source[]){
  const storage=batch as unknown as MatrixStorage,original=storage._matricesTexture;
  const {width,height}=original.image,baseFloats=width*height*4;
  const data=new Float32Array(baseFloats*3);data.set(original.image.data as Float32Array);
  const texture=new T.DataTexture(data,width,height*3,T.RGBAFormat,T.FloatType);texture.needsUpdate=true;
  storage._matricesTexture=texture;original.dispose();
  const view=new T.Matrix4(),normal=new T.Matrix3(),normal4=new T.Matrix4();
  const before=batch.onBeforeRender;
  batch.onBeforeRender=function(renderer,scene,camera,geometry,material,group){
    if(storage._matricesTexture!==texture)throw new Error('Exact batch matrix storage was resized');
    before.call(this,renderer,scene,camera,geometry,material,group);
    for(const source of sources){if(!source.active)continue;
      view.multiplyMatrices(camera.matrixWorldInverse,source.mesh.matrixWorld);view.toArray(data,baseFloats+source.instance*16);
      normal.getNormalMatrix(view);const n=normal.elements;
      normal4.set(n[0],n[3],n[6],0,n[1],n[4],n[7],0,n[2],n[5],n[8],0,0,0,0,1);normal4.toArray(data,baseFloats*2+source.instance*16);
    }
    texture.needsUpdate=true;
  };
  const depth=new T.MeshDepthMaterial();applyExactBatchShader(depth);batch.customDepthMaterial=depth;
  return {extraBytes:baseFloats*2*4,dispose(){batch.onBeforeRender=before;depth.dispose();batch.customDepthMaterial=undefined;}};
}
