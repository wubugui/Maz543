import * as T from 'three';
import {DirectionalShadowCache} from './directionalShadowCache';
import {renderWithOneShadowUpdate} from './compositedShadows';

/** Development-only experiment. The authoritative scene is never repartitioned.
 * A static subset is rechecked at full JS precision on every rendered pose.
 * Stock shadow rendering creates both subsets; a same-format, single-sample
 * depth blit seeds the combined map before the stock dynamic depth draws.
 * No opaque/color/AO/transmission draw is skipped or reordered. */
export class PartitionedShadowCache {
  private guard=new DirectionalShadowCache();
  private staticGuard=new DirectionalShadowCache();
  private history=new WeakMap<T.Mesh,number[]>();
  private staticMap:T.WebGLRenderTarget|null=null;
  private sourceMap:T.WebGLRenderTarget|null=null;
  private sourceDepth:T.DepthTexture|null=null;
  private readonly sourceDisposed=()=>this.invalidate();
  private initialized=false;
  invalidate(){this.staticGuard.invalidate();this.initialized=false;}
  render(scene:T.Scene,camera:T.Camera,light:T.DirectionalLight,renderer:T.WebGLRenderer,draw:()=>void){
    const eligible=this.guard.assess(scene,camera,light,renderer);
    if(renderer.clippingPlanes.length){eligible.eligible=false;eligible.reasons.push('global clipping');}
    const map=light.shadow.map;
    const report={kind:'partitioned-shadow-depth',eligible:eligible.eligible,reasons:eligible.reasons,
      staticCasters:0,dynamicCasters:0,staticRefreshed:false,staticDraws:0,dynamicDraws:0,depthCopies:0,
      extraBytes:this.staticMap?this.staticMap.width*this.staticMap.height*8:0,limits:'Development experiment; all original color/normal/transmission draws remain. No stable FPS claim.'};
    if(!eligible.eligible||!(map instanceof T.WebGLRenderTarget)||!map.depthTexture||map.samples!==0||map.depthTexture.format!==T.DepthFormat||map.depthTexture.type!==T.UnsignedIntType){
      this.invalidate();renderWithOneShadowUpdate(renderer,draw);return report;
    }
    const stationary=new Set<T.Mesh>();
    scene.traverseVisible(object=>{
      if(!(object instanceof T.Mesh)||!object.castShadow||!object.layers.test(camera.layers))return;
      if(!(Array.isArray(object.material)?object.material:[object.material]).some(material=>material.visible))return;
      const pose=[...object.matrixWorld.elements,...(object.morphTargetInfluences??[])];
      const previous=this.history.get(object);
      if(previous&&previous.length===pose.length&&pose.every((v,i)=>Object.is(v,previous[i])))stationary.add(object);
      this.history.set(object,pose);
    });
    report.staticCasters=stationary.size;report.dynamicCasters=eligible.casters-stationary.size;
    if(this.sourceMap!==map||this.sourceDepth!==map.depthTexture||this.staticMap?.width!==map.width||this.staticMap?.height!==map.height){
      this.sourceMap?.removeEventListener('dispose',this.sourceDisposed);this.sourceDepth?.removeEventListener('dispose',this.sourceDisposed);
      this.staticGuard.dispose();this.staticMap?.depthTexture?.dispose();this.staticMap?.dispose();
      this.staticMap=map.clone();this.sourceMap=map;this.sourceDepth=map.depthTexture;
      map.addEventListener('dispose',this.sourceDisposed);map.depthTexture.addEventListener('dispose',this.sourceDisposed);
      this.initialized=false;
    }
    const staticMap=this.staticMap!;
    report.extraBytes=map.width*map.height*8;
    const shadow=light.shadow,shadowMap=renderer.shadowMap;
    const originalShadowRender=shadowMap.render,originalDraw=renderer.renderBufferDirect,originalClear=renderer.clear;
    const originalTarget=renderer.getRenderTarget(),originalFace=renderer.getActiveCubeFace(),originalLevel=renderer.getActiveMipmapLevel();
    const originalAuto=shadowMap.autoUpdate;
    let handled=false,phase:'static'|'dynamic'|null=null;
    shadowMap.autoUpdate=false;shadowMap.needsUpdate=true;
    try{
      renderer.renderBufferDirect=function(...args){
        if(phase&&args[0]===shadow.camera&&args[1]===null){
          const isStatic=stationary.has(args[4] as T.Mesh);
          if((phase==='static')!==isStatic)return;
          if(phase==='static')report.staticDraws++;else report.dynamicDraws++;
        }
        return originalDraw.apply(renderer,args);
      };
      renderer.clear=function(...args){
        const result=originalClear.apply(renderer,args);
        if(phase==='dynamic'&&renderer.getRenderTarget()===map&&args[1]!==false){
          renderer.copyTextureToTexture(staticMap.depthTexture!,map.depthTexture!);
          // Three's depth-copy implementation unbinds READ and DRAW FBOs.
          // Restore through its public state-aware API before any source draw.
          renderer.setRenderTarget(map);report.depthCopies++;
        }
        return result;
      };
      const owner=this;
      shadowMap.render=function(lights,renderScene,renderCamera){
        if(handled||renderScene!==scene||renderCamera!==camera)return originalShadowRender.call(shadowMap,lights,renderScene,renderCamera);
        handled=true;
        shadow.map=staticMap;
        try{
          const assessment=owner.staticGuard.assess(scene,camera,light,renderer,mesh=>stationary.has(mesh));
          if(!assessment.eligible)throw new Error('Static subset lost full-scene shadow eligibility');
          if(!owner.initialized||assessment.refresh){
            phase='static';shadowMap.needsUpdate=true;shadow.needsUpdate=true;
            originalShadowRender.call(shadowMap,lights,renderScene,renderCamera);
            owner.initialized=true;report.staticRefreshed=true;
          }
        }finally{shadow.map=map;}
        phase='dynamic';shadowMap.needsUpdate=true;shadow.needsUpdate=true;
        originalShadowRender.call(shadowMap,lights,renderScene,renderCamera);
        phase=null;
        if(report.depthCopies!==1)throw new Error('Expected exactly one same-format directional depth copy');
      };
      draw();
      if(!handled)this.invalidate();
      else this.staticGuard.commit(staticMap); // Accept stock DoubleSide versions only after the complete color draw.
    }catch(error){this.invalidate();shadowMap.needsUpdate=true;shadow.needsUpdate=true;renderer.setRenderTarget(originalTarget,originalFace,originalLevel);throw error;}
    finally{
      renderer.renderBufferDirect=originalDraw;renderer.clear=originalClear;shadowMap.render=originalShadowRender;
      shadowMap.autoUpdate=originalAuto;shadow.map=map;
    }
    return report;
  }
  dispose(){
    this.sourceMap?.removeEventListener('dispose',this.sourceDisposed);this.sourceDepth?.removeEventListener('dispose',this.sourceDisposed);
    this.staticGuard.dispose();this.guard.dispose();this.staticMap?.depthTexture?.dispose();this.staticMap?.dispose();
    this.staticMap=null;this.sourceMap=null;this.sourceDepth=null;this.history=new WeakMap();this.initialized=false;
  }
}
