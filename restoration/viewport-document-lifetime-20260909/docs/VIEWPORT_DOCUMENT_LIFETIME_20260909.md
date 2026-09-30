# 文档离开时的完整查看器释放

完整 goal ACTIVE，16 项整车门槛 OPEN。上一阶段的巨大占用没有完全归因；本轮定位并修复确定存在的文档退出清理缺口，保留全部模型和机械状态精度。动态整车帧率仍未解决。

## 原始现场

开发参数 `lifecycle-audit=1` 启用有界 96 条事件记录、显式快照按钮和本应用专用 sessionStorage 日志，没有定时采样、unload 监听、强制 GC 或浏览器设置修改。记录 pagehide/pageshow 的 persisted、可见性、组件/线程清理、完整装配、导航类型及旧式 JS 堆读数。日志中的 `page` 是审计实例 ID，热更新也会生成新实例，不能直接当作独立浏览器文档数量。

普通完整车辆装配 8868 实例后，切换到完整 Worker。旧页实际报告 `pagehide.persisted=false`，只有 pagehide 和 visibilitychange，没有 viewer-effect-cleanup。因此本次不能归因于 BFCache；React 组件清理确实没有覆盖这次完整文档离开。主线程初次旧式 JS 堆读数为 1,710,593,306 bytes，但它不是纯几何、可达对象或图形驱动内存的精确计量。

## 修复与状态边界

`lib/viewportDocumentLifetime.ts` 为当前查看器绑定 pagehide：persisted=false 时调用既有完整释放函数，与之后的 React cleanup 共用一次性保护；persisted=true 时不释放，保留浏览器冻结的原机械状态。没有靠卸载监听禁用历史缓存，也没有在返回时暗中重置机械计算。该绑定用于普通主线程与实验 Worker；普通入口无需诊断参数即可得到释放修复。

主线程既有释放包含模型/资产几何与材质、贴图、解码器、机械线程、后处理、阴影、事件、观察器和本查看器 WebGL 上下文。Worker 使用既有客户端停止、消息端口、线程与回执流程。本轮没有改变求解器、机械状态转换、建模或渲染参数。

[Chrome 生命周期说明](https://developer.chrome.com/docs/web-platform/page-lifecycle-api) 区分 pagehide 的 persisted 分支。本修复只依据实际事件决定释放，不把一次观察扩大为所有历史行为。Chrome 的[内存诊断说明](https://developer.chrome.com/docs/devtools/memory-problems)区分系统占用、JS 堆和可达对象；当前快照没有完成这些口径的隔离，因此不宣称已测得真实泄漏大小。

## 实际验证

修复后的完整主线程离开记录为 pagehide(false) → viewport-owner-release(document-exit) → viewer-effect-cleanup(main) → main-viewport-disposed → audit-listeners-dispose。主 disposer 在该现场约 185–186 ms 内返回，下一页重新装配完整 8868 实例、静止缓存、240 Hz 与零积压。

修复后的 Worker 硬导航记录为 pagehide(false) → owner release → effect cleanup(worker) → render-client-stop → audit listeners dispose。此前同页热更新获得过 render-worker-disposed-ack 和 terminated；**硬导航没有取得该回执**，两种证据不混用。完整 Worker 的发布生命周期门槛仍 OPEN。

实际 EventTarget 单元验证 persisted=true 不动原状态、false 触发释放、React/文档双重清理仅一次、抛错也移除监听；既有实际客户端同步/异步失败清理用例通过，TypeScript 和生产构建通过。11 个机械/导出文件、16735 字符姿态块与显示质量配置仍与适用不可变归档相同。

## 剩余工作

后续混合页面快照仍出现约 2.48–2.58 GB 的旧式堆读数，未强制 GC、未隔离主/Worker VM、未测得图形驱动内存释放，不能用它证明修复无效或证明全部增长消失。真实 persisted=true 的返回恢复尚未观察，只完成控制事件验证。继续核查持续资源占用和动态显示负载；不能把成功退出/重载等同于完整产品仿真或流畅度验收。

原始记录、总结、测试和构建日志分别在 `outputs/viewport-lifecycle-audit/` 与 `work/viewport-lifecycle-audit/`；普通预览在取证后恢复。恢复后实际右舱前门由 0° 到 99°，随后回到静止缓存，完整实例与 240 Hz/零积压保持；已保存并查看截图，初始视图较小，不能替代所有结构和运动的完整视觉验收。
