import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {bindViewportDocumentLifetime} from '../lib/viewportDocumentLifetime.ts';

class Host extends EventTarget{
 listeners=0;
 addEventListener(...args){this.listeners++;super.addEventListener(...args);}
 removeEventListener(...args){this.listeners--;super.removeEventListener(...args);}
 hide(persisted){const event=new Event('pagehide');Object.defineProperty(event,'persisted',{value:persisted});this.dispatchEvent(event);}
}
const retained=new Host(),events=[];let releases=0;
const cleanup=bindViewportDocumentLifetime(retained,()=>releases++,(event,details)=>events.push({event,details}));
retained.hide(true);retained.hide(true);assert.equal(releases,0,'Persisted page retains exact existing state');assert.equal(retained.listeners,1);
retained.hide(false);assert.equal(releases,1);assert.equal(retained.listeners,0);assert.equal(events[0].details.reason,'document-exit');
cleanup();retained.hide(false);assert.equal(releases,1,'Document exit and later React cleanup release once');
const ordinary=new Host();let ordinaryReleases=0;const ordinaryCleanup=bindViewportDocumentLifetime(ordinary,()=>ordinaryReleases++);
ordinaryCleanup();ordinaryCleanup();ordinary.hide(false);assert.equal(ordinaryReleases,1);assert.equal(ordinary.listeners,0);
const failure=new Host();let failedCalls=0;const failedCleanup=bindViewportDocumentLifetime(failure,()=>{failedCalls++;throw new Error('dispose fixture');});
assert.throws(failedCleanup,/dispose fixture/);failedCleanup();assert.equal(failedCalls,1);assert.equal(failure.listeners,0,'Listener removed even if underlying release fails');
const report={passed:true,persistedStateUntouched:true,documentExitReleases:true,componentCleanupReleases:true,releasesOnce:true,listenersRemovedOnFailure:true,
 limits:'Actual lifetime owner with real EventTarget and controlled persisted flags. Browser release callbacks, driver memory and history restoration require separate observation.'};
await fs.writeFile('outputs/viewport-lifecycle-audit/document-lifetime-tests.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
