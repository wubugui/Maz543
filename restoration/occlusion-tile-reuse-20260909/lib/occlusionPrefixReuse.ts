import * as T from 'three';
import {ConservativeRasterBounds,rasterTiles} from './conservativeRasterBounds';

type Proof={prefix:number;signature:number;zero:boolean};
type Entry={proof?:Proof;pending?:{query:WebGLQuery;prefix:number;signature:number};observed?:{prefix:number;signature:number;frame:number}};
type Pass={ordinal:number;prefix:number;clear:boolean;key?:string;viewport?:number[];tiles?:number[];blocked?:boolean};

/** DEV experiment: reuse an original draw's zero-sample proof only when its
 * complete preceding depth-write sequence and its own depth inputs are exactly
 * the same. No hashes, approximate bounds, delayed visibility or geometry edits.
 * Motion invalidates that prefix; original drawing is the fallback.
 * This first implementation deliberately uses the whole depth prefix. */
export class OcclusionPrefixReuse{
  lastReport:Record<string,unknown>|undefined;
  private readonly gl:WebGL2RenderingContext;
  private entries=new Map<string,Entry>();
  private signatures=new Map<string,{values:unknown[];token:number}>();
  private prefixes=new Map<string,number>();
  private nextSignature=1;private nextPrefix=1;private frame=0;
  private targetIds=new WeakMap<object,number>();private nextTarget=1;
  private readonly spatial:boolean;private bounds=new ConservativeRasterBounds();
  constructor(privateRenderer:T.WebGLRenderer,options:{spatial?:boolean}={}){this.gl=privateRenderer.getContext() as WebGL2RenderingContext;this.spatial=!!options.spatial;}
  invalidate(){
    for(const entry of this.entries.values())if(entry.pending)this.gl.deleteQuery(entry.pending.query);
    this.entries.clear();this.signatures.clear();this.prefixes.clear();this.nextSignature=1;this.nextPrefix=1;
  }
  private targetId(target:object|null){if(!target)return 0;let id=this.targetIds.get(target);if(!id)this.targetIds.set(target,id=this.nextTarget++);return id;}
  private signature(key:string,values:unknown[]){
    const previous=this.signatures.get(key);
    if(previous&&values.length===previous.values.length&&values.every((value,i)=>Object.is(value,previous.values[i])))return previous.token;
    const token=this.nextSignature++;this.signatures.set(key,{values,token});return token;
  }
  private append(prefix:number,signature:number){
    const key=`${prefix}/${signature}`;let value=this.prefixes.get(key);
    if(value===undefined)this.prefixes.set(key,value=this.nextPrefix++);return value;
  }
  render(renderer:T.WebGLRenderer,scene:T.Scene,camera:T.Camera,draw:()=>void){
    const gl=this.gl;
    const report={kind:this.spatial?'spatial-depth-prefix-occlusion':'exact-depth-prefix-occlusion',queried:0,skipped:0,savedTriangles:0,reusedPositive:0,waitingForStablePrefix:0,pending:0,unsupported:0,passes:0,queryError:0,
      spatialBounds:0,fullViewportBounds:0,tileTouches:0,spatialBudgetFallback:0,
      prefixNodes:0,proofEntries:0,epochReset:false,
      firstChangedDepthDraws:[] as {pass:string;object:string;material:string}[],
      firstChangedFullViewportDraws:[] as {pass:string;object:string;morphPositions:number}[],
      limits:this.spatial?'Development-only ordered per-tile depth dependencies using outward influence bounds, original query coverage/MSAA. No shadow culling, moving-target inference or steady-state FPS claim.':'Development-only exact ordered-depth-prefix proofs, original query coverage/MSAA. No shadow culling, moving-target inference, spatial bounds or steady-state FPS claim.'};
    this.lastReport=report;
    // Bound historical proof storage. Exhaustion only restores original draws;
    // it never drops geometry or treats missing results as invisible.
    if(++this.frame%16===0||this.prefixes.size>100000||this.entries.size>10000){this.invalidate();report.epochReset=true;}
    if(gl.isContextLost()||renderer.capabilities.logarithmicDepthBuffer||renderer.capabilities.reversedDepthBuffer||renderer.clippingPlanes.length||scene.onBeforeRender!==T.Object3D.prototype.onBeforeRender||scene.onAfterRender!==T.Object3D.prototype.onAfterRender){this.invalidate();draw();return {...report,unsupported:1};}
    for(const entry of this.entries.values())if(entry.pending&&gl.getQueryParameter(entry.pending.query,gl.QUERY_RESULT_AVAILABLE)){
      const pending=entry.pending;entry.proof={prefix:pending.prefix,signature:pending.signature,zero:!gl.getQueryParameter(pending.query,gl.QUERY_RESULT)};
      gl.deleteQuery(pending.query);entry.pending=undefined;
    }
    const passes=new Map<T.WebGLRenderTarget|null,Pass>();
    const originalClear=renderer.clear,originalDraw=renderer.renderBufferDirect;
    const owner=this;
    renderer.clear=function(...args){
      const target=renderer.getRenderTarget();const prior=passes.get(target);
      const result=originalClear.apply(renderer,args);
      if(args[1]!==false)passes.set(target,{ordinal:(prior?.ordinal??0)+1,prefix:0,
        clear:!!gl.getParameter(gl.DEPTH_WRITEMASK)&&gl.getParameter(gl.DEPTH_CLEAR_VALUE)===1&&!gl.isEnabled(gl.SCISSOR_TEST)&&!gl.isEnabled(gl.SAMPLE_COVERAGE)&&!gl.isEnabled(gl.RASTERIZER_DISCARD)});
      return result;
    };
    renderer.renderBufferDirect=function(...args){
      const [passCamera,passScene,geometry,material,object,group]=args;
      if(passCamera!==camera||passScene!==scene)return originalDraw.apply(renderer,args);
      const target=renderer.getRenderTarget(),pass=passes.get(target);
      if(!pass?.clear)return originalDraw.apply(renderer,args);
      if(pass.blocked){report.unsupported++;return originalDraw.apply(renderer,args);}
      if(!pass.key){
        pass.viewport=Array.from(gl.getParameter(gl.VIEWPORT) as Int32Array);
        if(owner.spatial)pass.tiles=rasterTiles(null,pass.viewport).map(()=>0);
        pass.key=[owner.targetId(target),pass.ordinal,target?.width??gl.drawingBufferWidth,target?.height??gl.drawingBufferHeight,
          gl.getParameter(gl.SAMPLES),gl.getParameter(gl.DEPTH_BITS),...pass.viewport,
          owner.targetId(target?.depthTexture??null),target?.depthTexture?.version??0,target?.depthTexture?.type??0].join('/');report.passes++;
      }
      if(!material.depthWrite){
        if(object.onBeforeRender!==T.Object3D.prototype.onBeforeRender||object.onAfterRender!==T.Object3D.prototype.onAfterRender||material.onBeforeRender!==T.Material.prototype.onBeforeRender){
          const token=owner.nextSignature++;pass.prefix=owner.append(pass.prefix,token);
          if(pass.tiles)pass.blocked=true;
        }
        return originalDraw.apply(renderer,args);
      }
      const mesh=object as T.Mesh,m=material as T.MeshStandardMaterial;
      const materialPrototype=Object.getPrototypeOf(material);
      const standard=materialPrototype===T.MeshStandardMaterial.prototype||materialPrototype===T.MeshPhysicalMaterial.prototype||materialPrototype===T.MeshNormalMaterial.prototype;
      const definitions=Object.entries(m.defines??{});
      const stockDefines=definitions.every(([key,value])=>(key==='STANDARD'||key==='PHYSICAL')&&value==='');
      const finite=!!geometry.boundingSphere&&Number.isFinite(geometry.boundingSphere.radius)&&geometry.boundingSphere.center.toArray().every(Number.isFinite)&&object.matrixWorld.elements.every(Number.isFinite)&&object.modelViewMatrix.elements.every(Number.isFinite)&&camera.projectionMatrix.elements.every(Number.isFinite)&&(mesh.morphTargetInfluences??[]).every(Number.isFinite);
      const known=finite&&Object.getPrototypeOf(object)===T.Mesh.prototype&&standard&&stockDefines&&material.depthTest&&material.depthFunc===T.LessEqualDepth&&!material.stencilWrite&&!material.alphaHash&&!material.alphaToCoverage&&!material.alphaTest&&!m.displacementMap&&!m.wireframe&&!material.clippingPlanes?.length&&
        object.onBeforeRender===T.Object3D.prototype.onBeforeRender&&object.onAfterRender===T.Object3D.prototype.onAfterRender&&material.onBeforeRender===T.Material.prototype.onBeforeRender&&material.onBeforeCompile===T.Material.prototype.onBeforeCompile;
      const rowKey=`${pass.key}/${object.id}/${(material as T.Material&{id:number}).id}/${material.side}/${group?.start??-1}/${group?.count??-1}/${group?.materialIndex??-1}`;
      let signature:number,changed=false;
      if(known){
        const values:unknown[]=[geometry,material,material.side,material.precision,...definitions.flat(),material.depthFunc,material.polygonOffset,material.polygonOffsetFactor,material.polygonOffsetUnits,
          geometry.drawRange.start,geometry.drawRange.count,geometry.morphTargetsRelative,camera.coordinateSystem,camera.reversedDepth,...object.matrixWorld.elements,...object.modelViewMatrix.elements,...camera.projectionMatrix.elements,...(mesh.morphTargetInfluences??[])];
        const attribute=(a:T.BufferAttribute|T.InterleavedBufferAttribute|null)=>{
          if(!a){values.push(null);return;}values.push(a,a.array,a.array.buffer,a.count,a.itemSize,a.normalized);
          if(a instanceof T.InterleavedBufferAttribute)values.push(a.data,a.data.version,a.data.stride,a.offset);else values.push(a.version,a.gpuType);
        };
        attribute(geometry.index);
        for(const name of Object.keys(geometry.attributes).sort()){values.push(name);attribute(geometry.attributes[name]);}
        for(const name of Object.keys(geometry.morphAttributes).sort()){
          const attributes=geometry.morphAttributes[name as keyof typeof geometry.morphAttributes]??[];values.push(name,attributes.length);for(const item of attributes)attribute(item);
        }
        const previous=owner.signatures.get(rowKey);
        signature=owner.signature(rowKey,values);
        changed=!!previous&&previous.token!==signature;
        if(previous&&previous.token!==signature&&!report.firstChangedDepthDraws.some(change=>change.pass===pass.key))report.firstChangedDepthDraws.push({pass:pass.key,object:object.name,material:material.name});
      }else{signature=owner.nextSignature++;report.unsupported++;}
      // One unknown depth writer makes the rest of a spatial pass unprovable.
      // Stop building tile histories immediately, especially in section mode.
      if(owner.spatial&&!known){pass.blocked=true;return originalDraw.apply(renderer,args);}
      let prefix=pass.prefix;
      if(pass.tiles&&pass.viewport){
        const rect=known&&renderer.capabilities.precision==='highp'&&(!material.precision||material.precision==='highp')?owner.bounds.get(geometry,object.modelViewMatrix,camera.projectionMatrix,pass.viewport,mesh.morphTargetInfluences):null;
        if(rect)report.spatialBounds++;else report.fullViewportBounds++;
        if(!rect&&changed&&!report.firstChangedFullViewportDraws.some(change=>change.pass===pass.key))report.firstChangedFullViewportDraws.push({pass:pass.key,object:object.name,morphPositions:geometry.morphAttributes.position?.length??0});
        const tiles=rasterTiles(rect,pass.viewport);
        if(report.tileTouches+tiles.length>250000||owner.prefixes.size>150000){report.spatialBudgetFallback++;pass.blocked=true;return originalDraw.apply(renderer,args);}
        report.tileTouches+=tiles.length;
        prefix=owner.signature(rowKey+'/tile-prefix',tiles.flatMap(tile=>[tile,pass.tiles![tile]]));
        for(const tile of tiles)pass.tiles[tile]=owner.append(pass.tiles[tile],signature);
      }else pass.prefix=owner.append(prefix,signature);
      // Unknown shader/depth behavior is an unstable prefix contribution. It
      // cannot authorize culling itself or any following dependent draw.
      const candidate=known&&!material.transparent&&!(material as T.MeshPhysicalMaterial).transmission;
      if(!candidate)return originalDraw.apply(renderer,args);
      let entry=owner.entries.get(rowKey);if(!entry)owner.entries.set(rowKey,entry={});
      const observed=entry.observed;
      const stable=observed?.frame===owner.frame-1&&observed.prefix===prefix&&observed.signature===signature;
      entry.observed={frame:owner.frame,prefix,signature};
      const proof=entry.proof;
      if(proof?.prefix===prefix&&proof.signature===signature){
        if(proof.zero){
          const count=geometry.index?.count??geometry.attributes.position.count;
          const start=Math.max(geometry.drawRange.start,group?.start??0),end=Math.min(count,geometry.drawRange.start+geometry.drawRange.count,group?group.start+group.count:Infinity);
          report.skipped++;report.savedTriangles+=Math.max(0,Math.floor((end-start)/3));return;
        }
        report.reusedPositive++;return originalDraw.apply(renderer,args);
      }
      // A prefix changing every frame cannot yield a reusable exact proof.
      // Wait for two identical observations before paying for a GPU query.
      if(!stable){report.waitingForStablePrefix++;return originalDraw.apply(renderer,args);}
      if(entry.pending||owner.entries.size>10000||gl.getQuery(gl.ANY_SAMPLES_PASSED,gl.CURRENT_QUERY)||gl.getQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,gl.CURRENT_QUERY))return originalDraw.apply(renderer,args);
      const query=gl.createQuery();if(!query)return originalDraw.apply(renderer,args);
      entry.pending={query,prefix,signature};report.queried++;
      gl.beginQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE,query);
      try{return originalDraw.apply(renderer,args);}finally{gl.endQuery(gl.ANY_SAMPLES_PASSED_CONSERVATIVE);}
    };
    try{draw();report.queryError=gl.getError();if(report.queryError)this.invalidate();}
    catch(error){this.invalidate();throw error;}
    finally{renderer.clear=originalClear;renderer.renderBufferDirect=originalDraw;}
    report.pending=[...this.entries.values()].filter(entry=>entry.pending).length;report.prefixNodes=this.prefixes.size;report.proofEntries=this.entries.size;return report;
  }
  dispose(){this.invalidate();this.bounds.clear();}
}
