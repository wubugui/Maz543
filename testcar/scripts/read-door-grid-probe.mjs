// Binary Draco stdin only: no model buffer is persisted or encoded as text.
import {parseArgs} from 'node:util';
import {loadDoorPrecisionDecoder, readDoorPositionGrid, requiredDoorPositionBits} from './cab-door-position-precision.mjs';
const {values} = parseArgs({options: {'decoder-dir': {type: 'string'}, 'position-id': {type: 'string'}, range: {type: 'string'}}});
if (values.range !== undefined) {
  console.log(JSON.stringify({requiredBits: requiredDoorPositionBits(Number(values.range))}));
} else {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  const draco = await loadDoorPrecisionDecoder(values['decoder-dir']);
  console.log(JSON.stringify(readDoorPositionGrid(draco, Buffer.concat(chunks), Number(values['position-id']))));
}
