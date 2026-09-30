# 迁移依赖审计（2026-09-06）

## 结论

对 `outputs` 中全部 18 个 `.blend` / `.blend1` 文件执行了便携 Blender 4.5.13 后台只读打开与原生依赖扫描，全部成功；未保存、导出或修改模型。没有发现当前不存在的未打包依赖。

原生未打包外链仅涉及以下位置，必须随迁移携带：

- `D:/maz543-references/factory-543a-profile.jpg`
- `D:/maz543-references/maz543a-5.jpg`
- `D:/maz543-references/museum-front-oblique.jpg`
- `D:/maz543-references/museum-front.jpg`
- 项目自己的 `outputs/D12A525A_Engine_Master.blend`、`MAZ543A_Cardan_Master.blend`、`MAZ543A_Cooling_Master.blend`、`MAZ543A_Starting_Master.blend`、`MAZ543A_Suspension_Master.blend`。

全部位置在本机存在。没有外部链接 Library datablock，没有发现外部物理缓存路径；发现的字体均为 Blender 内置 Bfont。其余图片作为 packed image 已在母版内打包，下面 JSON 保留每张图片的原路径和打包状态。某些 packed 图片的原路径即使变动，也不等于其图像数据丢失。

## 源码、Git 和运行时

- 项目完整递归枚举未发现 Windows reparse point、符号链接或 junction。`.git` 是实际目录，只有 `D:/testcar` 一个 main worktree；未发现 submodule、Git LFS 文件或外部 object alternates。HEAD 为 `4b89e61c2c99fe01fa251df1e5de3e3fc54ccfbd`。大量修改及新增文件未提交，必须复制整个工作目录，包括隐藏和 ignored 文件；仅复制 Git 提交远远不够。
- `scripts/blender-model.py`、`blender-d12.py`、`blender-suspension.py`、`blender-starting.py`、`prepare-cam-profiles.py`、`update-d12-cams.py` 使用 `D:/maz543-references`。这是已识别的外部素材根目录，需整个携带。
- `scripts/repair-starting-action-slots.py` 硬编码 `D:/testcar`，历史 `work/check-action-slots.py`、`inspect-starting-materials.py`、`inspect-native-gears.py`、`debug-cardan-splines.py` 也有该根路径。其余主脚本多数由 `__file__` 自动求项目根目录。
- 浏览器模型的 Draco 解码器使用 `/draco/`，三个 JS/WASM 文件都在 `public/draco`，没有必须依赖在线 CDN 的模型解码器。页面中的网上资料链接需要联网查看；参考文档是否已下载由迁移主清单核对。
- Node 项目声明 `node >= 22.13.0`；`node_modules`、锁文件、构建产物 `.next/.vinext/dist` 与 `.wrangler` 应完整保留。便携 Node 的整个目录以及 npm 自身 `node_modules` 均需要携带，不能只复制 `node.exe`。
- Blender 自带 Python/NumPy，位于项目 `work/tools/blender-4.5.13-windows-x64`。几何预处理脚本使用单独 Python 3.12 和 `work/pythonlibs/shapely` 2.1.2；后者为 cp312 二进制，不能直接换用 Blender 自带不同 ABI 的 Python。
- 被使用的外部 Python 3.12 根目录为 `C:/Users/wubugui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python`，Pillow、NumPy、pdfplumber 在其内部。未发现该 Python 的 `.pth` 指向额外外部代码目录。整个 Codex `dependencies` 目录打包可涵盖 Python、Poppler、Git、PowerShell 等；启动时应把迁移后的对应目录加入进程 PATH。
- 历史辅助脚本 `work/read-pump-catalog.py` 导入 `bs4`，而本次检查的 Python 3.12 和 `work/pythonlibs` 内均没有该包。这是当前环境已有的辅助脚本依赖缺口，并非打包导致的丢失；它不在主建模/浏览器路径上。如未来需要重新运行此抓取辅助脚本，须准备 beautifulsoup4 及其依赖。本次未安装任何包。

## 换路径后的恢复

1. 最少改动方式是恢复到 `D:/testcar` 与 `D:/maz543-references`。如果新电脑使用不同目录，不要直接运行仍含旧绝对路径的历史脚本。
2. 将上述源码中的旧根路径指向迁移后的目录；主建模脚本的素材根应使用实际 `maz543-references` 位置。新机器可用 Blender 的 Find Missing Files 指向恢复后的素材目录，检查后另存迁移副本。此次审计保持原始母版不变。
3. 如母版中保留的 `outputs` 路径在搬迁后失效，指向恢复后的同名母版；外部参考图和构建脚本路径要同时处理，不能只让网页能加载。
4. Windows x64 运行依赖已准备为文件备份，但操作系统、显卡驱动、浏览器安装和账户登录不能由项目文件替代。Blender GPU 设置、浏览器 WebGL 能力与性能需要在新机器实际确认。不要把老电脑的驱动目录直接覆盖到新电脑。
5. 本审计只验证依赖可定位与文件读取，不代表模型结构、动画、真实性或产品验收已通过。完整源文件内容、大小和 SHA256 由迁移主程序另行核验。

## 原生依赖逐文件记录

```json
{
  "timestamp": "2026-09-06T12:22:39.470959+08:00",
  "scope": "Read-only Blender 4.5.13 scan of all current outputs/*.blend and *.blend1. Models not saved or exported.",
  "files": [
    {
      "file": "D12A525A_Engine_Master.blend",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "02-kmz-complete-after.webp",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\engine\\02-kmz-complete-after.webp",
          "exists": true
        },
        {
          "name": "05-family-camshafts.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\05-family-camshafts.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-cam-caption.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-cam-caption.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-fig7-gear-scheme.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-fig7-gear-scheme.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-fig9-cam-assembly.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-fig9-cam-assembly.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-valve-phases.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-valve-phases.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-valve-text.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-valve-text.jpg",
          "exists": true
        },
        {
          "name": "D12-page-33.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\work\\reference-docs\\D12-page-33.png",
          "exists": true
        },
        {
          "name": "D12-page-38.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\work\\reference-docs\\D12-page-38.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "D12A525A_Engine_Master.blend1",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "02-kmz-complete-after.webp",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\engine\\02-kmz-complete-after.webp",
          "exists": true
        },
        {
          "name": "05-family-camshafts.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\05-family-camshafts.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-cam-caption.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-cam-caption.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-fig7-gear-scheme.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-fig7-gear-scheme.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-fig9-cam-assembly.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-fig9-cam-assembly.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-valve-phases.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-valve-phases.jpg",
          "exists": true
        },
        {
          "name": "1973-maz-valve-text.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\maz543-references\\engine\\timing\\1973-maz-valve-text.jpg",
          "exists": true
        },
        {
          "name": "D12-page-33.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\work\\reference-docs\\D12-page-33.png",
          "exists": true
        },
        {
          "name": "D12-page-38.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\work\\reference-docs\\D12-page-38.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_CabFit_Study.blend",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_CabFit_Study.blend1",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_Cardan_Master.blend",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "543-cardan-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-cardan-exploded.png",
          "exists": true
        },
        {
          "name": "MAZ1973-0575.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0575.jpg",
          "exists": true
        },
        {
          "name": "MCB-408-dimensions.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MCB-408-dimensions.png",
          "exists": true
        },
        {
          "name": "MCB-grooved-cross-definition.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MCB-grooved-cross-definition.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Cardan_Master.blend1",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "543-cardan-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-cardan-exploded.png",
          "exists": true
        },
        {
          "name": "MAZ1973-0575.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0575.jpg",
          "exists": true
        },
        {
          "name": "MCB-408-dimensions.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MCB-408-dimensions.png",
          "exists": true
        },
        {
          "name": "MCB-grooved-cross-definition.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MCB-grooved-cross-definition.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Cooling_Installation_Audit.blend",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cardan_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A-museum-front.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ543A-museum-front.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_Cooling_Installation_Audit.blend1",
      "external_paths": [
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cardan_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "543-1308509-lower-photo.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-1308509-lower-photo.png",
          "exists": true
        },
        {
          "name": "543-cardan-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-cardan-exploded.png",
          "exists": true
        },
        {
          "name": "543-fan-install.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-fan-install.png",
          "exists": true
        },
        {
          "name": "543-lower-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-lower-exploded.png",
          "exists": true
        },
        {
          "name": "543-oil-pump-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-oil-pump-exploded.png",
          "exists": true
        },
        {
          "name": "543-upper-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-upper-exploded.png",
          "exists": true
        },
        {
          "name": "COOL_lower_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "MAZ1973-0534.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0534.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0575.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0575.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0582.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0582.jpg",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_Cooling_Master.blend",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "543-1308509-lower-photo.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-1308509-lower-photo.png",
          "exists": true
        },
        {
          "name": "543-cardan-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-cardan-exploded.png",
          "exists": true
        },
        {
          "name": "543-fan-install.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-fan-install.png",
          "exists": true
        },
        {
          "name": "543-lower-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-lower-exploded.png",
          "exists": true
        },
        {
          "name": "543-oil-pump-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-oil-pump-exploded.png",
          "exists": true
        },
        {
          "name": "543-upper-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-upper-exploded.png",
          "exists": true
        },
        {
          "name": "COOL_lower_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "MAZ1973-0534.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0534.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0575.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0575.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0582.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0582.jpg",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Cooling_Master.blend1",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "543-1308509-lower-photo.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-1308509-lower-photo.png",
          "exists": true
        },
        {
          "name": "543-cardan-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-cardan-exploded.png",
          "exists": true
        },
        {
          "name": "543-fan-install.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-fan-install.png",
          "exists": true
        },
        {
          "name": "543-lower-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-lower-exploded.png",
          "exists": true
        },
        {
          "name": "543-oil-pump-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-oil-pump-exploded.png",
          "exists": true
        },
        {
          "name": "543-upper-exploded.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\543-upper-exploded.png",
          "exists": true
        },
        {
          "name": "COOL_lower_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "MAZ1973-0534.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0534.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0575.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0575.jpg",
          "exists": true
        },
        {
          "name": "MAZ1973-0582.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ1973-0582.jpg",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Master.blend",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A-museum-front.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ543A-museum-front.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_Master.blend1",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A-museum-front.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ543A-museum-front.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [
        {
          "name": "Bfont Regular",
          "path": "<builtin>",
          "packed": false
        }
      ],
      "caches": []
    },
    {
      "file": "MAZ543A_Starting_Master.blend",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "07-c5-2s-starter.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\07-c5-2s-starter.jpg",
          "exists": true
        },
        {
          "name": "08-mzn2-mn1-prelubrication.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\08-mzn2-mn1-prelubrication.jpg",
          "exists": true
        },
        {
          "name": "1973-c5-drive-fig122.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\1973-c5-drive-fig122.jpg",
          "exists": true
        },
        {
          "name": "1973-mzn2-fig24.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\1973-mzn2-fig24.jpg",
          "exists": true
        },
        {
          "name": "1977-c5-installation-p338-339.webp",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\source-text\\1977-c5-installation-p338-339.webp",
          "exists": true
        },
        {
          "name": "c5-2s-full-section-native.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\c5-2s-full-section-native.png",
          "exists": true
        },
        {
          "name": "candidate-mn1-6020.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\candidate-mn1-6020.jpg",
          "exists": true
        },
        {
          "name": "candidate-mn1-6022.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\candidate-mn1-6022.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Starting_Master.blend1",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "07-c5-2s-starter.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\07-c5-2s-starter.jpg",
          "exists": true
        },
        {
          "name": "08-mzn2-mn1-prelubrication.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\08-mzn2-mn1-prelubrication.jpg",
          "exists": true
        },
        {
          "name": "1973-c5-drive-fig122.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\1973-c5-drive-fig122.jpg",
          "exists": true
        },
        {
          "name": "1973-mzn2-fig24.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\1973-mzn2-fig24.jpg",
          "exists": true
        },
        {
          "name": "1977-c5-installation-p338-339.webp",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\source-text\\1977-c5-installation-p338-339.webp",
          "exists": true
        },
        {
          "name": "c5-2s-full-section-native.png",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\c5-2s-full-section-native.png",
          "exists": true
        },
        {
          "name": "candidate-mn1-6020.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\candidate-mn1-6020.jpg",
          "exists": true
        },
        {
          "name": "candidate-mn1-6022.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\starting\\motor-internals\\candidate-mn1-6022.jpg",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Suspension_Master.blend",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "1973-fig90-suspension.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\1973-fig90-suspension.jpg",
          "exists": true
        },
        {
          "name": "1973-fig91-damper.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\1973-fig91-damper.jpg",
          "exists": true
        },
        {
          "name": "maz-543_scud_b_tel_035_of_192.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\candidates\\maz-543_scud_b_tel_035_of_192.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Suspension_Master.blend1",
      "external_paths": [],
      "libraries": [],
      "images": [
        {
          "name": "1973-fig90-suspension.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\1973-fig90-suspension.jpg",
          "exists": true
        },
        {
          "name": "1973-fig91-damper.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\1973-fig91-damper.jpg",
          "exists": true
        },
        {
          "name": "maz-543_scud_b_tel_035_of_192.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\suspension\\candidates\\maz-543_scud_b_tel_035_of_192.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Textured.blend",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A-museum-front.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ543A-museum-front.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A_BaseColor",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_BaseColor.png",
          "exists": true
        },
        {
          "name": "MAZ543A_Normal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_Normal.png",
          "exists": true
        },
        {
          "name": "MAZ543A_ORM",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_ORM.png",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    },
    {
      "file": "MAZ543A_Textured.blend1",
      "external_paths": [
        {
          "path": "D:\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "path": "D:\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\D12A525A_Engine_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Cooling_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Starting_Master.blend",
          "exists": true
        },
        {
          "path": "D:\\testcar\\outputs\\MAZ543A_Suspension_Master.blend",
          "exists": true
        }
      ],
      "libraries": [],
      "images": [
        {
          "name": "COOL_lower_cast_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_lower_cast_roughness.002",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_normal.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "COOL_upper_cast_roughness.001",
          "source": "FILE",
          "packed": true,
          "path": "",
          "exists": false
        },
        {
          "name": "factory-543a-profile.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\factory-543a-profile.jpg",
          "exists": true
        },
        {
          "name": "maz543a-5.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\maz543a-5.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A-museum-front.jpg",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\work\\reference-docs\\MAZ543A-museum-front.jpg",
          "exists": true
        },
        {
          "name": "MAZ543A_BaseColor",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_BaseColor.png",
          "exists": true
        },
        {
          "name": "MAZ543A_Normal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_Normal.png",
          "exists": true
        },
        {
          "name": "MAZ543A_ORM",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\public\\models\\textures\\MAZ543A_ORM.png",
          "exists": true
        },
        {
          "name": "MN1_20mm_woven_insulation_normal.002",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\MN1_insulation_normal.png",
          "exists": true
        },
        {
          "name": "museum-front-oblique.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front-oblique.jpg",
          "exists": true
        },
        {
          "name": "museum-front.jpg",
          "source": "FILE",
          "packed": false,
          "path": "D:\\testcar\\outputs\\..\\..\\maz543-references\\museum-front.jpg",
          "exists": true
        },
        {
          "name": "S543_CastNormal",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastNormal.png",
          "exists": true
        },
        {
          "name": "S543_CastRoughness",
          "source": "FILE",
          "packed": true,
          "path": "D:\\testcar\\outputs\\S543_CastRoughness.png",
          "exists": true
        }
      ],
      "fonts": [],
      "caches": []
    }
  ]
}
```
