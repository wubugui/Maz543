// Regression against the actual shipped file. No synthetic mesh, asset write,
// native source recovery, or re-encoding of decoded (already lossy) positions.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseArgs} from 'node:util';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {loadDoorPrecisionDecoder, inspectPackedDoorPositionPrecision} from './cab-door-position-precision.mjs';
const {values} = parseArgs({options: {repo: {type: 'string'}, out: {type: 'string'}}});
const repo = path.resolve(values.repo), out = path.resolve(values.out);
await fs.mkdir(out, {recursive: true});
const asset = path.join(repo, 'testcar/public/models/review/maz543a-cab-va180-v1.glb');
const bytes = await fs.readFile(asset), sha = b => createHash('sha256').update(b).digest('hex');
assert.equal(sha(bytes), 'fde04e480978d065f5d071ff04669d6b4adfef54e0204513e3be8ccd47ea7d1e');
assert.equal(bytes.length, 24743400);
const length = bytes.readUInt32LE(12), input = {bytes, j: JSON.parse(bytes.subarray(20, 20 + length)), start: 28 + length};
const snapshot = JSON.stringify(input.j);
const draco = await loadDoorPrecisionDecoder(path.join(repo, 'testcar/public/draco'));
const report = inspectPackedDoorPositionPrecision(input, input, {}, draco);
assert.equal(report.status, 'FAIL_DOOR_POSITION_GRID_BUDGET');
assert.equal(report.checked.length, 20); assert.equal(report.failedNodes.length, 12);
await fs.writeFile(path.join(out, 'shipped-grid-report.json'), JSON.stringify(report, null, 2) + '\n');
const cases = [];
function rejects(name, make, pattern) {
  const candidate = {...input, j: structuredClone(input.j)};
  make(candidate);
  assert.throws(() => inspectPackedDoorPositionPrecision(input, candidate, {}, draco), pattern);
  cases.push({name, rejected: true});
}
rejects('missing-known-door', x => { x.j.nodes.find(n => n.name === 'cab_pivot_002').name += '_missing'; }, /Incomplete/);
rejects('changed-door-scope', x => { x.j.nodes.find(n => n.name === 'cab_pivot_002').children.pop(); }, /scope/);
rejects('scaled-door-chain', x => { x.j.nodes.find(n => n.name === 'cab_pivot_002').scale = [2, 1, 1]; }, /Scaled door/);
rejects('unknown-door-matrix', x => { x.j.nodes.find(n => n.name === 'cab_pivot_002').matrix = []; }, /TRS/);
const claimedReplacement = inspectPackedDoorPositionPrecision(input, input,
  {changedMeshes: report.checked.map(r => r.node)}, draco);
assert.equal(claimedReplacement.status, 'FAIL_DOOR_POSITION_GRID_BUDGET');
assert.ok(claimedReplacement.checked.every(r => r.selected === 'native-candidate'));
cases.push({name: 'claiming-old-streams-are-new-does-not-repair-precision', rejected: true});

// Execute the proposed packer from an isolated code directory. A preload blocks
// every model write even if this regression discovers that the guard is broken.
const shadow = path.join(out, 'packer-replay');
await fs.mkdir(path.join(shadow, 'scripts'), {recursive: true});
await fs.mkdir(path.join(shadow, 'public'), {recursive: true});
await fs.symlink(path.join(repo, 'testcar/public/draco'), path.join(shadow, 'public/draco'));
for (const name of ['preserve-unmodified-body-streams.mjs', 'cab-door-position-precision.mjs'])
  await fs.copyFile(new URL(name, import.meta.url), path.join(shadow, 'scripts', name));
await fs.copyFile(path.join(repo, 'testcar/scripts/scoped-body-transforms.mjs'), path.join(shadow, 'scripts/scoped-body-transforms.mjs'));
const preloader = path.join(shadow, 'reject-asset-writes.mjs');
await fs.writeFile(preloader, "import fs from 'node:fs/promises';\nconst original = fs.writeFile;\nfs.writeFile = async function(file, ...args) { if (!String(file).endsWith('wrapper.cjs')) throw new Error('FORBIDDEN_ASSET_WRITE_ATTEMPT'); return original.call(this, file, ...args); };\n");
const config = path.join(shadow, 'config.json'), output = path.join(shadow, 'FORBIDDEN.glb');
await fs.writeFile(config, JSON.stringify({source: asset, candidate: asset, output, report: path.join(shadow, 'FORBIDDEN-report.json'), changedMeshes: []}) + '\n');
const run = spawnSync(process.execPath, ['--import', preloader, path.join(shadow, 'scripts/preserve-unmodified-body-streams.mjs'), config],
  {encoding: 'utf8', timeout: 30000});
await fs.writeFile(path.join(out, 'packer-rejection.log'), run.stdout + run.stderr);
assert.equal(run.status, 1); assert.match(run.stderr, /Refusing to pack under-budget door POSITION streams/);
assert.doesNotMatch(run.stderr, /FORBIDDEN_ASSET_WRITE_ATTEMPT/);
assert.equal(await fs.stat(output).then(() => true, () => false), false);
assert.equal(JSON.stringify(input.j), snapshot); assert.equal(sha(await fs.readFile(asset)), sha(bytes));
const summary = {status: 'PASS_ACTUAL_ASSET_REJECTION_AND_PACKER_WRITE_PREVENTION', assetSHA256: sha(bytes),
  checkedPrimitives: 20, rejectedPrimitives: 12, cases, executedPackerExitCode: run.status,
  assetWriteAttempted: false, inputAssetAndDescriptorsUnchanged: true,
  limits: 'The shipped asset intentionally FAILS precision. This test proves refusal, not native export correctness or a repaired asset.'};
await fs.writeFile(path.join(out, 'guard-regression.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary));
