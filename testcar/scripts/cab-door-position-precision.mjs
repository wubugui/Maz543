// Static door-stream packaging precondition, not native transport or Float32 motion proof.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

export const DOOR_POSITION_POLICY = Object.freeze({
  id: 'cab-door-position-grid-20um-v1',
  comparisonBudgetM: 20e-6,
  // Full local POSITION grid step is limited to half the adopted comparison.
  // This is a precondition, NOT a complete world-space/Float32 error budget.
  maximumGridStepM: 10e-6,
  maxQuantizationBits: 30,
});
const PIVOTS = ['cab_pivot_002', 'cab_pivot_003', 'cab_pivot_006', 'cab_pivot_007'];
const hash = b => createHash('sha256').update(b).digest('hex');

export function requiredDoorPositionBits(rangeM) {
  assert.ok(Number.isFinite(rangeM) && rangeM > 0, 'Invalid native/Draco range');
  for (let bits = 1; bits <= DOOR_POSITION_POLICY.maxQuantizationBits; bits++) {
    if (rangeM / (2 ** bits - 1) <= DOOR_POSITION_POLICY.maximumGridStepM) return bits;
  }
  throw new Error('Door range exceeds the supported POSITION quantization budget');
}

export async function loadDoorPrecisionDecoder(directory = new URL('../public/draco/', import.meta.url)) {
  const dir = directory instanceof URL ? directory : pathToFileURL(path.resolve(directory) + path.sep);
  const wrapper = await fs.readFile(new URL('draco_wasm_wrapper.js', dir));
  const wasm = await fs.readFile(new URL('draco_decoder.wasm', dir));
  assert.equal(hash(wrapper), '8bb2952d2ba7d67e1414f8df819410cb0434a666be53f671fff75f68843d76f6', 'Review changed Draco wrapper before using this guard');
  assert.equal(hash(wasm), 'a680d927bed9cb864ddbd63521868891af2bfbe755092761b4837487618df8ac', 'Review changed Draco decoder before using this guard');
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'maz-door-decoder-'));
  try {
    const filename = path.join(temporary, 'wrapper.cjs');
    await fs.writeFile(filename, wrapper);
    return await createRequire(import.meta.url)(filename)({wasmBinary: wasm});
  } finally {
    await fs.rm(temporary, {recursive: true, force: true});
  }
}

export function readDoorPositionGrid(draco, bytes, positionId) {
  const decoder = new draco.Decoder(), mesh = new draco.Mesh();
  const buffer = new draco.DecoderBuffer(), quant = new draco.AttributeQuantizationTransform();
  let status;
  try {
    buffer.Init(bytes, bytes.length);
    decoder.SkipAttributeTransform(draco.POSITION);
    status = decoder.DecodeBufferToMesh(buffer, mesh);
    assert.ok(status.ok(), status.error_msg());
    const attribute = decoder.GetAttributeByUniqueId(mesh, positionId);
    assert.ok(attribute && attribute.ptr && attribute.num_components() === 3, 'Invalid POSITION binding');
    assert.equal(attribute.attribute_type(), draco.POSITION, 'POSITION points to another attribute');
    assert.ok(quant.InitFromAttribute(attribute), 'Unquantized/unknown POSITION requires a separately reviewed lossless path');
    const bits = quant.quantization_bits(), rangeM = quant.range();
    assert.ok(Number.isInteger(bits) && bits >= 1 && bits <= DOOR_POSITION_POLICY.maxQuantizationBits, 'Unsupported POSITION bits');
    const minimum = [0, 1, 2].map(i => quant.min_value(i));
    assert.ok(minimum.every(Number.isFinite), 'Nonfinite POSITION grid origin');
    const requiredBits = requiredDoorPositionBits(rangeM), gridStepM = rangeM / (2 ** bits - 1);
    return {bits, rangeM, minimum, requiredBits, gridStepM, gridAccepted: bits >= requiredBits,
      points: mesh.num_points(), triangles: mesh.num_faces(), streamSHA256: hash(bytes)};
  } finally {
    for (const object of [status, quant, buffer, mesh, decoder]) if (object) draco.destroy(object);
  }
}

function indexAndParents(gltf) {
  const names = new Map(), parents = new Map();
  gltf.nodes.forEach((node, i) => {
    assert.ok(!names.has(node.name), `Duplicate node name: ${node.name}`);
    names.set(node.name, i);
    for (const child of node.children ?? []) {
      assert.ok(!parents.has(child), 'Multiple node parents');
      parents.set(child, i);
    }
  });
  return {names, parents};
}

function requireRigidChain(gltf, parents, index) {
  const seen = new Set();
  while (index !== undefined) {
    assert.ok(!seen.has(index), 'Cyclic node ancestry'); seen.add(index);
    const node = gltf.nodes[index]; assert.ok(node, 'Missing node');
    assert.ok(!node.matrix, 'Door precision policy needs a reviewed TRS chain');
    const translation = node.translation ?? [0, 0, 0];
    assert.ok(translation.length === 3 && translation.every(Number.isFinite), 'Invalid translation');
    assert.equal(node.skin, undefined, 'Skinned doors need separate precision review');
    assert.equal(node.weights, undefined, 'Morph weights need separate precision review');
    assert.ok(!(gltf.animations ?? []).some(a => (a.channels ?? []).some(c => c.target?.node === index)),
      'Animated door ancestry needs separate precision review');
    assert.deepEqual(node.scale ?? [1, 1, 1], [1, 1, 1], 'Scaled door precision requires a world-space budget');
    const q = node.rotation ?? [0, 0, 0, 1];
    assert.ok(q.length === 4 && q.every(Number.isFinite) && Math.abs(q.reduce((s, v) => s + v * v, 0) - 1) < 1e-12, 'Non-unit rotation');
    index = parents.get(index);
  }
}

// Inspect the exact stream that the packer will retain. Never infer precision
// from the new export's settings or POSITION accessor min/max (pre-encode data).
export function inspectPackedDoorPositionPrecision(before, candidate, config, draco) {
  const oldIndex = indexAndParents(before.j), newIndex = indexAndParents(candidate.j);
  const present = PIVOTS.filter(name => newIndex.names.has(name));
  if (!present.length && !PIVOTS.some(name => oldIndex.names.has(name)))
    return {status: 'NOT_APPLICABLE_NO_KNOWN_CAB_DOORS', checked: []};
  assert.equal(present.length, 4, 'Incomplete known cab-door hierarchy');
  const changed = new Set(config?.changedMeshes ?? []), added = new Set(config?.newMeshes ?? []);
  const checked = [];
  for (let door = 0; door < PIVOTS.length; door++) {
    const pivotName = PIVOTS[door], pivot = candidate.j.nodes[newIndex.names.get(pivotName)];
    const prefix = `BL_Door_${door < 2 ? -1 : 1}_${door % 2}`;
    const expected = [`${prefix}_handle`, `${prefix}_lock`, `${prefix}_window`,
      `BL_Merged_${pivotName}_OD_green_aged_enamel`, `BL_Merged_${pivotName}_Rubber_window_seals`].sort();
    const children = (pivot.children ?? []).map(i => candidate.j.nodes[i]);
    assert.deepEqual(children.map(n => n.name).sort(), expected, 'Unreviewed door mesh scope');
    for (const node of children) {
      assert.ok(!node.children?.length, 'Unexpected nested door mesh');
      requireRigidChain(candidate.j, newIndex.parents, newIndex.names.get(node.name));
      const useNative = changed.has(node.name) || added.has(node.name);
      const input = useNative ? candidate : before;
      const inputIndex = useNative ? newIndex : oldIndex;
      const sourceNode = input.j.nodes[inputIndex.names.get(node.name)];
      assert.ok(sourceNode && sourceNode.mesh !== undefined, `Missing selected door stream: ${node.name}`);
      const primitives = input.j.meshes[sourceNode.mesh].primitives;
      assert.equal(primitives.length, 1, 'Unreviewed door primitive scope');
      const p = primitives[0], ext = p.extensions?.KHR_draco_mesh_compression;
      assert.ok(ext && Number.isInteger(ext.attributes?.POSITION), 'Missing Draco POSITION');
      assert.ok(p.mode === undefined || p.mode === 4, 'Door is not a triangle primitive');
      assert.ok(!p.targets?.length, 'Morphing doors need separate precision review');
      const view = input.j.bufferViews[ext.bufferView];
      assert.equal(view.buffer, 0); assert.ok(Number.isInteger(view.byteLength) && view.byteLength > 0);
      const start = input.start + (view.byteOffset ?? 0), end = start + view.byteLength;
      assert.ok(start >= input.start && end <= input.bytes.length, 'Invalid door buffer range');
      const grid = readDoorPositionGrid(draco, input.bytes.subarray(start, end), ext.attributes.POSITION);
      checked.push({node: node.name, selected: useNative ? 'native-candidate' : 'retained-baseline', ...grid});
    }
  }
  const failed = checked.filter(row => !row.gridAccepted);
  return {status: failed.length ? 'FAIL_DOOR_POSITION_GRID_BUDGET' : 'PASS_GRID_PRECONDITION_ONLY',
    policy: DOOR_POSITION_POLICY, checked, failedNodes: failed.map(row => row.node),
    limits: 'Grid precondition only. Native corner/topology/attribute transport, Float32 error, materials, UVs, full asset and browser acceptance still require independent checks.'};
}

export async function assertPackedDoorPositionPrecision(before, candidate, config) {
  if (![...before.j.nodes, ...candidate.j.nodes].some(n => PIVOTS.includes(n.name))) return null;
  const draco = await loadDoorPrecisionDecoder();
  const report = inspectPackedDoorPositionPrecision(before, candidate, config, draco);
  assert.equal(report.status, 'PASS_GRID_PRECONDITION_ONLY',
    `Refusing to pack under-budget door POSITION streams: ${report.failedNodes?.join(', ')}. Re-export the exact native Textured source and verify transport; a pivot correction cannot repair quantization.`);
  return report;
}
