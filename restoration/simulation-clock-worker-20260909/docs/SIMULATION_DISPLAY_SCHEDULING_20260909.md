# 独立机械调度与显示分离

完整 goal ACTIVE，全部 16 项整车验收 OPEN。用户要求保留全部建模和机械精度，优先解决预览不可用的问题。本阶段继承 [CAD 显示优化](PERFORMANCE_CAD_DISPLAY_20260908.md)，不是整车性能最终验收。

## 实施

原来 RAF 每次最多推进 0.05 秒；当绘制约 0.5 FPS 时，机械时间也会被拖得很慢。现在 MechanicalTimeline 在独立 Worker 内以 240 Hz 调用原有 `advance`，正常动力计算保持 240 Hz，悬架内部保持 480 Hz。所有物理函数和参数没有改写，几何资产没有变动。

迟到回调保留待推进时间，以固定步长补齐；单次回调预算限制计算数量，不放大步长、不丢弃积欠时间。控制操作在下一个固定步边界生效，重置使用 generation 排除旧消息。页面隐藏时暂停墙钟计时，恢复后不补算隐藏期间。既有慢动作、发动机暂停和悬架暂停控制仍传入原求解器。

Worker 在每次完成新的求解 tick 后发布当前准确状态，没有另设更低的动画更新频率；绘制线程取最新状态计算原有全部零件位姿。若一轮补算多个 tick，仍逐步求解，只发布补算后的状态。显示本身依然受实际渲染速度限制。

线程启动失败时明确报告并回退到原有逐帧路径，状态条保留错误原因；不能把回退误报为独立计算。状态条增加模拟时间及独立计算频率/待推进时间，供用户核对实际运行。

## 验证

- `scripts/verify-mechanical-timeline.mjs`：不同回调延迟及预算下，1,440 tick 的完整状态严格一致；480 tick 与直接逐次调用原有求解器严格一致。验证隐藏暂停、下一个步边界输入、重置消息隔离，及 9.75 秒积欠最终补足至 2,400 tick。
- 使用真实 Node Worker 运行同一个浏览器 Worker 模块。主线程阻塞 1.2 秒后再留 0.15 秒接收消息，机械时间推进约 1.35 秒，待推进时间为 0。确切本次数字见 `outputs/simulation-worker-evidence/timeline-tests.json`。该测试不能单独证明浏览器集成。
- 浏览器首次接入失败：`new Worker(new URL(..., import.meta.url))` 在当前开发转换中产生 `file:///lib/mechanics.worker.ts?worker_file&type=module`，同源检查拒绝。采用 [Vite 官方专用 Worker 导入](https://vite.dev/guide/features#web-workers) 的 `?worker` 入口后，实际返回同源 `/lib/mechanics.worker.ts?worker_file&type=module`。响应保存在 development-worker-entry.txt。
- 浏览器实测已显示“独立机械计算 240 Hz · 待推进 0.000 s”。实际点击 START 后进入自行运转约 549 RPM、主油路 11.73 kgf/cm²；即使绘制只有约 0.5 FPS，模拟时间仍继续推进。证据为 worker-idle-ax.txt、worker-started-ax.txt、worker-running.png。
- 实际点击 STOP 后观察到惯性转动约 540 RPM，之后发动机已停止 0 RPM。传动侧仍有约 −2.9 RPM 的残余滑差，不能强行冻结该计算来获得缓存命中。之后点击既有“暂停并检查”，其控件变为“继续机构运动”。该手动检查暂停不是修改默认物理行为。
- TypeScript 检查通过，生产构建完成；日志为 work/simulation-worker-types.log、work/simulation-worker-build.log。生产包生成独立 mechanics.worker JS 文件。生产服务器未另开端口，不能把构建通过等同于生产环境实际运行通过。

## 边界和后续

本次解决的是机械时间受绘制拖累的问题，不是 GPU 帧率。IAB 仍报告 Microsoft Basic Render Driver；整车/复杂机构绘制仍慢，部分 UI 检查会超时。不得降低细分、删零件、放大物理步长或冻结残余运动来宣称完成。

继续处理图形主线程阻塞、保守遮挡与显示提交优化。此前合批候选仍仅供开发诊断，因画面差异、额外内存和实测收益不足，没有默认启用。chrome://gpu 被浏览器 URL 安全策略拒绝的边界仍有效，不得绕过。完整变矩器、机械内构、参数标定、安装闭合及全车写实验证继续按原 goal 推进。
