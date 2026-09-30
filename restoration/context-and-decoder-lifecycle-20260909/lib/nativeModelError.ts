/** Three's Draco worker rejects with {type,id,error}, not an Error instance.
 * Keep the concrete decoder reason instead of turning it into [object Object]. */
export function nativeModelError(error:unknown):string{
  if(error instanceof Error)return `${error.name}: ${error.message}`;
  if(error&&typeof error==='object'&&'error' in error&&typeof error.error==='string')return error.error;
  if(error&&typeof error==='object'&&'message' in error&&typeof error.message==='string')return error.message;
  try{return typeof error==='object'?JSON.stringify(error):String(error);}catch{return String(error);}
}
