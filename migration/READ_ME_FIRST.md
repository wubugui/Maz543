# MAZ-543 项目完整迁移快照

本包用于从损坏电脑搬走当前项目。模型仍在开发中；打包完成不代表模型已经达到最终验收标准。

## 新电脑使用

1. 把 `MAZ543_COMPLETE_20260906.zip` 与同名 `.sha256`、`VERIFIED.json` 一起复制走。先检查 SHA-256，再完整解压。建议预留至少 15 GB 空间，并使用支持 ZIP64、长路径的解压工具。不要只解压源码目录。
2. 解压后应有 `testcar/`、`external/`、`conversation/`、`migration/` 四个目录。直接双击 `migration/START_LOCAL.cmd`，浏览器打开 `http://localhost:3000/`。启动脚本仅对自身进程设置环境，使用随包 Node，不需先运行 npm install。
3. Blender 位于 `testcar/work/tools/blender-4.5.13-windows-x64/blender.exe`。先打开 `testcar/outputs/MAZ543A_Master.blend` 查看完整母版；冷却/发动机/悬挂/起动机/Cardan 母版也都保留在 outputs。
4. 继续建模前先读 `testcar/MIGRATION_HANDOFF.md`、`testcar/NEXT_AGENT_PROMPT.md`、`testcar/docs/ACCEPTANCE.md`。当前 cooling 浏览器 GLB 尚未包含最后的原生弹簧改动，不能把网页当作最新母版。
5. 最省事的原生重建布局是把解压的 `testcar` 放回 `D:\testcar`，把 `external/maz543-references` 复制到 `D:\maz543-references`。`RESTORE_REFERENCES.ps1` 提供不覆盖已有目录的复制操作。若新电脑没有 D 盘，可在新路径浏览网页，但重建脚本中的历史绝对路径和 Blender 图片外链需要按依赖审计重定向。

## 包含范围

- 项目全部文件，包括 `.git`、未提交/未跟踪文件、被忽略的 `outputs`、`work`、`node_modules`、所有 `.blend/.blend1`、GLB、贴图、脚本、下载资料、验证报告、日志与构建缓存。
- `D:\maz543-references` 全目录、D 盘根目录早期 MAZ 参考文件、此任务实际引用的浏览器临时下载照片及任务可视化目录。
- 当前系统 Node.js 全目录、Codex 工作依赖完整目录（Python 3.12、Node、Git、PowerShell、Poppler 等）及历史使用的 Python 3.10 完整目录。
- `conversation/raw/` 主线程与全部相关子任务原始 JSONL，包含用户输入、工具调用/输出、上下文压缩事件；另有可读 Markdown、逐条任务历史 SQLite 导出、目标和线程元数据。
- `MANIFEST.json` 每个文件的源路径、大小、SHA-256；`COVERAGE.json` 收集范围；外部 `VERIFIED.json` 是生成后完整读回验证结果。

本包不依赖 Git 提交来恢复文件。不要用 git reset/clean 覆盖当前工作树。

## 对话边界和继续工作

`conversation/history-index.json` 给出每份原始记录的精确捕获字节数、首末时间、记录数和 SHA-256。主记录从 2026-09-05 首次请求开始；已保存的完整历史不会因上下文压缩而只剩摘要。打包/校验期间在捕获时点之后新产生的进度消息及最终交付消息不属于该历史快照。

将 `testcar` 作为新电脑工作目录，给新助手发送 `NEXT_AGENT_PROMPT.md` 中的内容即可继续读取本地证据。原始 JSONL/SQLite 是可检查的档案；这里没有声称 Codex 会自动把它们恢复成侧栏中的同一个任务。目标保持暂停，未标记完成。

## 环境边界

随包二进制针对 Windows x64。新电脑仍需要兼容的 Windows、图形驱动和浏览器；这些属于机器环境。线上账号登录、云端网站权限和本机全局账号凭据不是此项目数据，本包没有复制它们。已有网页与模型的外部参考资料不需要依赖账号登录即可读取。

Python 使用 `external/codex-dependencies/python/python.exe`，不要依赖旧电脑 PATH；Shapely 位于 `testcar/work/pythonlibs`。包中还保留原 Python 3.10 环境用于旧工具复查。历史辅助脚本 `work/read-pump-catalog.py` 缺少 bs4 是原环境已有缺口，未以“已安装”冒充解决。

Python 3.10 的 `easy-install.pth` 还指向本机另一项目 `E:\aiproj\zy`。MAZ 项目脚本未发现使用该项目；它不属于本迁移范围。Python 3.10 安装目录按原样保留，并不代表那个无关项目已随之携带；新电脑的主建模预处理请使用随包 Python 3.12。

唯一从项目根递归打包时排除的目录是本迁移输出目录本身，避免 ZIP 把自己无限嵌套。它的恢复说明、捕获记录和清单通过单独 archive 前缀收录。完整路径映射见 COVERAGE.json。
