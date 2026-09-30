/** Host services used by the complete vehicle runtime. A worker host will
 * provide the same sizes/events/UI commands around its OffscreenCanvas.
 * No model, material or kinematic implementation lives in the host adapter.
 */
export type SimulationConnection=Pick<Worker,'postMessage'|'terminate'|'onmessage'|'onerror'>;
export type ViewportEnvironment={
  window:Pick<Window,'devicePixelRatio'|'innerWidth'|'location'>;
  document:Pick<Document,'hidden'|'createElement'|'addEventListener'|'removeEventListener'>;
  ResizeObserver:typeof ResizeObserver;
  requestAnimationFrame:typeof requestAnimationFrame;
  cancelAnimationFrame:typeof cancelAnimationFrame;
  canvas?:HTMLCanvasElement|OffscreenCanvas;
  input?:HTMLElement;
  createSimulation?:()=>SimulationConnection;
  frameSource?:()=>string;
};
export function browserViewportEnvironment():ViewportEnvironment{
  return {window,document,ResizeObserver,requestAnimationFrame:requestAnimationFrame.bind(window),cancelAnimationFrame:cancelAnimationFrame.bind(window)};
}

/** Release only this already-unmounted viewport's context. dispose() releases
 * renderer bookkeeping, but does not itself destroy the WebGL context.
 * Idempotence is useful when a worker shutdown races a component cleanup.
 */
export function viewportRendererRelease(renderer:{dispose:()=>void;forceContextLoss:()=>void},removeCanvas:()=>void){
  let released=false;
  return ()=>{if(released)return;released=true;try{renderer.dispose();}finally{try{renderer.forceContextLoss();}finally{removeCanvas();}}};
}
