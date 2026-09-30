/** React effect cleanup does not run when a document is discarded by a full
 * navigation. Release this viewport on non-persisted pagehide as well.
 * Persisted pages retain the existing frozen mechanical state for restoration.
 * No unload listener or browser cache policy is installed. */
export function bindViewportDocumentLifetime(target:Pick<Window,'addEventListener'|'removeEventListener'>,dispose:()=>void,record?:(event:string,details?:Record<string,unknown>)=>void){
  let released=false;
  const release=(reason:string)=>{
    if(released)return;released=true;target.removeEventListener('pagehide',onPageHide);
    record?.('viewport-owner-release',{reason});
    dispose();
  };
  const onPageHide=(event:PageTransitionEvent)=>{if(!event.persisted)release('document-exit');};
  target.addEventListener('pagehide',onPageHide);
  return ()=>release('component-cleanup');
}
