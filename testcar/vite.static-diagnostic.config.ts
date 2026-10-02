import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { defineConfig, type Plugin, type UserConfig } from 'vite';

const project = fileURLToPath(new URL('.', import.meta.url));
const manifestPath = new URL(
  './outputs/cloud-native-static-suspension-20261002/manifest.json',
  import.meta.url,
);
const assetPath = new URL(
  './work/native-static-preview/native-static.glb',
  import.meta.url,
);
const endpoint = '/__native-static/model.glb';

export default defineConfig(async (): Promise<UserConfig> => {
  const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
  if (
    manifest.schema !== 'MAZ_NATIVE_GLB_BINARY_PARTS_V1' ||
    manifest.native_filename !== 'native-static.glb' ||
    !Number.isSafeInteger(manifest.bytes) ||
    manifest.bytes <= 0 ||
    !/^[a-f0-9]{64}$/.test(manifest.sha256)
  ) {
    throw new Error('Invalid canonical native-static manifest');
  }

  const assetPlugin: Plugin = {
    name: 'native-static-diagnostic-asset',
    // This endpoint exists only in this independent development server.
    // There is no public GLB copy, fallback model, or production route.
    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        if (request.url?.split('?')[0] !== endpoint) return next();
        response.setHeader('Cache-Control', 'no-store');
        if (request.method !== 'GET' && request.method !== 'HEAD') {
          response.writeHead(405, { Allow: 'GET, HEAD' });
          response.end();
          return;
        }
        try {
          // Hash and send the same bytes, so a later file change cannot slip
          // between validation and a separate streaming read.
          const bytes = await readFile(assetPath);
          if (
            bytes.length !== manifest.bytes ||
            createHash('sha256').update(bytes).digest('hex') !== manifest.sha256
          ) {
            response.writeHead(409, {
              'Content-Type': 'text/plain; charset=utf-8',
            });
            response.end('诊断资产长度或 SHA-256 不符；请核对本地恢复文件。');
            return;
          }
          response.writeHead(200, {
            'Content-Type': 'model/gltf-binary',
            'Content-Length': bytes.length,
            'X-Content-SHA256': manifest.sha256,
          });
          response.end(request.method === 'HEAD' ? undefined : bytes);
        } catch (error) {
          const missing = (error as NodeJS.ErrnoException).code === 'ENOENT';
          response.writeHead(missing ? 503 : 500, {
            'Content-Type': 'text/plain; charset=utf-8',
          });
          response.end(
            missing
              ? '诊断资产尚未恢复。请在 testcar 运行 npm run prepare:static-diagnostic，再刷新本页。'
              : '诊断资产读取失败，请检查本地开发服务日志。',
          );
          if (!missing) server.config.logger.error(String(error));
        }
      });
    },
  };

  return {
    root: project,
    publicDir: false,
    plugins: [assetPlugin],
    define: {
      __NATIVE_STATIC_ASSET__: JSON.stringify({
        url: endpoint,
        bytes: manifest.bytes,
        sha256: manifest.sha256,
        source: 'outputs/cloud-native-static-suspension-20261002/manifest.json',
      }),
    },
    build: {
      outDir: 'dist/static-diagnostic-check',
      rolldownOptions: {
        input: fileURLToPath(
          new URL('./diagnostics/native-static/index.html', import.meta.url),
        ),
      },
    },
  };
});
