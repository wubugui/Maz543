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
