/// <reference types="vite/client" />
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './style.css';

declare const __NATIVE_STATIC_ASSET__: {
  url: string;
  bytes: number;
  sha256: string;
  source: string;
};

const asset = __NATIVE_STATIC_ASSET__;
const viewport = document.querySelector<HTMLDivElement>('#viewport')!;
const loading = document.querySelector<HTMLDivElement>('#loading')!;
const loadTitle = document.querySelector<HTMLElement>('#load-title')!;
const loadMessage = document.querySelector<HTMLElement>('#load-message')!;
const renderStatus = document.querySelector<HTMLElement>('#render-status')!;
const buttons = [
  ...document.querySelectorAll<HTMLButtonElement>('button[data-view]'),
];
const saveView = document.querySelector<HTMLButtonElement>('#save-view')!;
const views = {
  overview: new THREE.Vector3(-1.4, 0.72, 1),
  front: new THREE.Vector3(-1, 0, 0),
  side: new THREE.Vector3(0, 0, 1),
  rear: new THREE.Vector3(1, 0, 0),
};
type View = keyof typeof views;

document.querySelector<HTMLElement>('#asset-identity')!.textContent =
  `${asset.bytes.toLocaleString('en-US')} bytes · SHA-256 ${asset.sha256} · ${asset.source}`;

function fail(error: unknown) {
  viewport.dataset.state = 'error';
  loading.hidden = false;
  loading.dataset.error = 'true';
  loadTitle.textContent = '真实模型尚未显示';
  loadMessage.textContent =
    error instanceof Error ? error.message : String(error);
  renderStatus.textContent = '静态 frame 0 · 加载或显示失败 · 未验收';
  buttons.forEach((button) => {
    button.disabled = true;
  });
  saveView.disabled = true;
}

async function main() {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1;
  viewport.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#aebbb7');
  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.enabled = false;
  const abort = new AbortController();
  let disposed = false;
  let ready = false;
  let frame = 0;
  const loaded: { model?: THREE.Group } = {};
  const bounds = new THREE.Box3();
  const center = new THREE.Vector3();
  let radius = 1;

  // Observation lights only; no replacement geometry or material overrides.
  scene.add(new THREE.HemisphereLight(0xffffff, 0xb2b5ae, 2));
  for (const [position, intensity] of [
    [new THREE.Vector3(-8, 12, 8), 3],
    [new THREE.Vector3(7, 6, -8), 2],
    [new THREE.Vector3(0, -6, 3), 0.7],
  ] as const) {
    const light = new THREE.DirectionalLight(0xffffff, intensity);
    light.position.copy(position);
    scene.add(light);
  }

  function stopWithError(error: unknown) {
    ready = false;
    controls.enabled = false;
    cancelAnimationFrame(frame);
    frame = 0;
    if (!disposed) fail(error);
  }
  function render() {
    frame = 0;
    if (!disposed && loaded.model) {
      try {
        renderer.render(scene, camera);
      } catch (error) {
        stopWithError(error);
      }
    }
  }
  function requestRender() {
    if (!disposed && ready && !frame) frame = requestAnimationFrame(render);
  }
  function frameCamera(view: View) {
    // The bounding sphere fits every view, including a narrow viewport. Only
    // the camera and controls target move; the exported root is never changed.
    const halfVertical = THREE.MathUtils.degToRad(camera.fov / 2);
    const halfHorizontal = Math.atan(Math.tan(halfVertical) * camera.aspect);
    const distance =
      (radius / Math.sin(Math.min(halfVertical, halfHorizontal))) * 1.12;
    camera.position
      .copy(center)
      .addScaledVector(views[view].clone().normalize(), distance);
    camera.near = Math.max(0.001, radius / 10000);
    camera.far = Math.max(100, radius * 100);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.minDistance = radius * 0.03;
    controls.maxDistance = radius * 30;
    controls.update();
    buttons.forEach((button) =>
      button.setAttribute('aria-pressed', String(button.dataset.view === view)),
    );
    viewport.dataset.view = view;
    requestRender();
  }
  function resize() {
    const width = Math.max(1, viewport.clientWidth);
    const height = Math.max(1, viewport.clientHeight);
    const scale = Math.min(1, 1280 / width, 800 / height);
    renderer.setSize(
      Math.round(width * scale),
      Math.round(height * scale),
      false,
    );
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    requestRender();
  }
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(viewport);
  resize();
  controls.addEventListener('change', requestRender);
  controls.addEventListener('start', () => {
    buttons.forEach((button) => button.setAttribute('aria-pressed', 'false'));
    viewport.dataset.view = 'orbit';
  });
  buttons.forEach((button) =>
    button.addEventListener('click', () =>
      frameCamera(button.dataset.view as View),
    ),
  );
  saveView.addEventListener('click', () => {
    if (!ready || disposed) return;
    const snapshotView = viewport.dataset.view ?? 'orbit';
    const snapshotTime = Date.now();
    try {
      renderer.render(scene, camera);
    } catch (error) {
      stopWithError(error);
      return;
    }
    try {
      // Copy immediately after a fresh real render. Add a separate caption band
      // without painting over, resizing, or altering any rendered model pixels.
      const snapshot = document.createElement('canvas');
      snapshot.width = renderer.domElement.width;
      snapshot.height = renderer.domElement.height + 64;
      const context = snapshot.getContext('2d');
      if (!context) throw new Error('浏览器无法创建 PNG 画布。');
      context.drawImage(renderer.domElement, 0, 64);
      context.fillStyle = '#172225';
      context.fillRect(0, 0, snapshot.width, 64);
      context.fillStyle = '#f0c389';
      context.font = '16px sans-serif';
      context.fillText('MAZ-543A · 待核对诊断候选', 16, 25);
      context.fillStyle = '#dae3dc';
      context.font = '12px sans-serif';
      context.fillText(
        'normal + joint FAIL · 2299 issues · all 16 gates OPEN · frame 0',
        16,
        47,
      );
      snapshot.toBlob((blob) => {
        if (!blob) {
          renderStatus.textContent = 'PNG 保存失败，请重试；诊断状态仍未验收。';
          return;
        }
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `maz543a-diagnostic-${snapshotView}-${snapshotTime}.png`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
      }, 'image/png');
    } catch (error) {
      renderStatus.textContent = `PNG 保存失败：${error instanceof Error ? error.message : String(error)}`;
    }
  });
  renderer.domElement.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    stopWithError(
      new Error('WebGL 上下文已中断，请刷新页面重新加载真实模型。'),
    );
  });

  function disposeModel(root: THREE.Group) {
    const geometries = new Set<THREE.BufferGeometry>();
    const materials = new Set<THREE.Material>();
    const textures = new Set<THREE.Texture>();
    root.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) return;
      geometries.add(object.geometry);
      for (const material of Array.isArray(object.material)
        ? object.material
        : [object.material]) {
        materials.add(material);
        for (const value of Object.values(material))
          if (value instanceof THREE.Texture) textures.add(value);
      }
    });
    textures.forEach((texture) => texture.dispose());
    materials.forEach((material) => material.dispose());
    geometries.forEach((geometry) => geometry.dispose());
  }
  function dispose() {
    disposed = true;
    abort.abort();
    cancelAnimationFrame(frame);
    resizeObserver.disconnect();
    controls.dispose();
    if (loaded.model) disposeModel(loaded.model);
    renderer.dispose();
  }
  window.addEventListener('pagehide', (event) => {
    if (!event.persisted) dispose();
  });
  if (import.meta.hot) import.meta.hot.dispose(dispose);

  try {
    loadTitle.textContent = '下载并校验完整模型';
    const response = await fetch(asset.url, {
      cache: 'no-store',
      signal: abort.signal,
    });
    if (!response.ok) {
      document.querySelector<HTMLElement>('#recovery')!.hidden = false;
      throw new Error(await response.text());
    }
    const bytes = await response.arrayBuffer();
    if (disposed) return;
    if (bytes.byteLength !== asset.bytes)
      throw new Error('下载长度与已发布 manifest 不符，已停止加载。');
    if (!crypto.subtle)
      throw new Error(
        '浏览器需要 localhost 或 HTTPS 安全上下文进行完整 SHA-256 校验。',
      );
    loadMessage.textContent = '正在核对全部字节的 SHA-256';
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    const sha256 = [...new Uint8Array(digest)]
      .map((value) => value.toString(16).padStart(2, '0'))
      .join('');
    if (sha256 !== asset.sha256)
      throw new Error('下载文件 SHA-256 与已发布 manifest 不符，已停止加载。');
    if (disposed) return;
    loadTitle.textContent = '校验完成，解析真实模型';
    loadMessage.textContent = 'GLTFLoader 正在读取全部节点、网格和原导出材质';
    // Parsing begins only after the full browser-side digest matches. No decoder,
    // legacy vehicle assembly, animation mixer, or pose writer is involved.
    const gltf = await new GLTFLoader().parseAsync(bytes, '');
    if (disposed) {
      disposeModel(gltf.scene);
      return;
    }
    const model = gltf.scene;
    loaded.model = model;
    scene.add(model);
    model.updateWorldMatrix(true, true);
    bounds.setFromObject(model);
    if (
      bounds.isEmpty() ||
      !Number.isFinite(bounds.getSize(new THREE.Vector3()).length())
    ) {
      throw new Error('真实模型没有可用的有限包围范围，已停止显示。');
    }
    const sphere = bounds.getBoundingSphere(new THREE.Sphere());
    center.copy(sphere.center);
    radius = Math.max(sphere.radius, 0.001);
    const requestedView = new URLSearchParams(location.search).get('view');
    const firstView =
      requestedView && Object.hasOwn(views, requestedView)
        ? (requestedView as View)
        : 'overview';
    frameCamera(firstView);
    loadTitle.textContent = '准备第一帧';
    loadMessage.textContent = '保留原始姿态，正在提交真实模型渲染';
    await new Promise<void>((resolve) =>
      requestAnimationFrame(() => resolve()),
    );
    if (disposed) return;
    renderer.render(scene, camera);
    if (renderer.getContext().isContextLost())
      throw new Error('第一帧渲染时 WebGL 上下文中断，请刷新重试。');
    ready = true;
    controls.enabled = true;
    buttons.forEach((button) => {
      button.disabled = false;
    });
    saveView.disabled = false;
    loading.hidden = true;
    viewport.dataset.state = 'ready';
    viewport.dataset.sha256 = sha256;
    document.querySelector<HTMLElement>('#asset-facts')!.textContent =
      `实际 GLTFLoader 已解析：${gltf.parser.json.nodes?.length ?? 0} 个原始 glTF 节点 / ${gltf.parser.json.meshes?.length ?? 0} 个原始 mesh 定义 / ${gltf.parser.json.materials?.length ?? 0} 份材质；第一帧 render 已完成。画布最多 1280 × 800，像素比 1，按需重绘。`;
    renderStatus.textContent =
      '静态 frame 0 · SHA-256 完整核对 · 真实 GLTFLoader 已解析 / 第一帧已绘制 · 待核对';
  } catch (error) {
    stopWithError(error);
  }
}

main().catch(fail);
