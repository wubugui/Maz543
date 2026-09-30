# MAZ-543A 云端开发接续

当前可接续资料已在本仓库；精确还原项目仍有 **16 项整体验收 OPEN**。迁移成功不等于产品验收通过。

- **先读 [CLOUD_HANDOFF.md](CLOUD_HANDOFF.md)**：当前唯一已采用模型、完整性清单、启动验证、30GB共用云盘的按需检出、原Hub执行边界和剩余工作。
- [GOAL.md](GOAL.md) 与 [原始验收表](testcar/docs/ACCEPTANCE.md)：保留原始要求，不降低标准。
- [DELIVERY_STATE.json](migration/cloud-handoff/DELIVERY_STATE.json)：本提交的资料交付范围。
- `testcar/`：React/Three交互工程；Node 22.13+，依赖按锁文件重装。
- `external/`：原始参考；`restoration/`：历史候选和最初Git源码树，LFS资产可按需下载。

使用 `GIT_LFS_SKIP_SMUDGE=1` 克隆，按交接说明先拉当前GLB、两份整车母版及参考；不要在30GB共用云盘上默认取全部历史。

原始母版与参考保留，本机不再新增开发。历史旧本机启动说明在下方保留原文，仅供历史记录；对话、个人配置和可重装Windows运行时未放入公开仓库，云端启动以CLOUD_HANDOFF为准。

---

# MAZ-543A workspace

项目目录是 [testcar](testcar/)。开发、构建和 Blender 脚本从该目录执行。

- 接手说明：[testcar/AGENT_START_HERE.md](testcar/AGENT_START_HERE.md)
- 完整目标与历史进度：[testcar/MIGRATION_HANDOFF.md](testcar/MIGRATION_HANDOFF.md)
- 原始对话及迁移补档：`conversation/`
- 随包运行环境和外部参考：`external/`
- 原迁移说明：[migration/READ_ME_FIRST.md](migration/READ_ME_FIRST.md)
- 本机恢复报告和修改前副本：`restoration/`

双击 `migration/START_LOCAL.cmd` 启动网页，访问 http://localhost:3000/ 。
Blender 操作全部通过 `http://denghong01:8765` Hub，原项目版本为 4.5.13；禁止运行本机 Blender。迁移快照中的旧本机启动说明已失效。

全部 16 项整车验收仍未完成；恢复成功及局部验证通过不代表整车完成。
