# Hub 状态写入故障只读排障结果

## 结论与边界

**不是全部 Hub 任务状态都无法写入；目前只观察到一个 Blender 任务目录发生 WinError 5。尚不能确认临时锁已解除，所以没有重试。**

- 主机 `denghong01`，服务 `Inference Hub`，正常入口 `http://denghong01:8765`，当前服务 PID `42948`。没有证据表明这是一个特定名称的 Windows Service，不能虚构服务名。
- 故障任务 `6e95834d-f419-495b-9e5b-9e6b9b561d87` 仍为 `failed`；`execution.state=finished`、`reason=runner_error`、`resource_held=0`、`attempt_count=1`、`retry_count=0`、`next_retry=0`，不在可见活动队列。API 表明其运行器执行已结束；没有擅自操作历史 PID。
- 任务实际 stdout/stderr 两路日志 GET 均 HTTP 200，长度均为 0；`result.files=[]`、`exit_code=null`。不能宣称候选脚本已运行完成。
- 最近 100 个 Blender 任务：88 succeeded、11 failed、1 cancelled；只有本任务错误字段含 WinError 5。此前 MAZ543 只读空间审计与探照灯任务已成功。**故障后没有新的 Blender 任务**，因此此前成功不能证明当前运行器状态文件写入已恢复。
- 最近全局任务中，有两项 H3 在故障完成时间之后成功结束：`cf33d279-53b4-4424-82e5-6ddafaeb0a2f`、`70dd115e-519f-4bb9-8055-9b90da4de75b`。队列另有一项 H3 running、一项 queued，Blender CPU 0/2。这里只读观察，未操作其他任务。
- `/health`、`/health/blender` 起初分别 ok/ready，4.5.13 可用。任务历史与公开诊断导出一度耗时较长；一次 `/health/live` 15秒内0字节超时。请求最终返回后，后续 `/health/live` 返回 alive/PID42948。暂时 API 无响应与状态文件拒绝访问的因果关系未确定。
- `/api/diagnostics` 实际返回 ZIP，尽管 OpenAPI 标成 JSON。本次客户端先按文本读取，文件不可作为可靠 ZIP 证据；未使用其内容得出结论，也未为补取导出重复调用耗时接口。上面的结论全部来自独立任务、队列、健康和日志接口。

只读证据保存在 `work/hub-permission-diagnosis-20260930/`：故障任务详情、health、blender、queue、read-1.json（100个 Blender）、read-2.json（50个全局任务）、read-3/4.json（实际零字节日志）。公开接口没有文件占用句柄、锁持有者或任务目录当前原子写入测试的只读查询能力。

## 最小具体用户动作

请在 **denghong01** 主机上，由 **启动/维护 InferenceHub :8765 的账户所有者** 检查下列文件的占用句柄与 Hub 运行器错误日志，确认是否是独占句柄或持续服务写入故障，以及是否已解除：

`F:\InferenceHub\data\blender\6e95834d-f419-495b-9e5b-9e6b9b561d87\ab315ce4-29d2-4d0b-82b8-6efceb0688ba\state.json`

失败操作为同目录 `state-tia8lmo_.new` 原子替换该文件。当前服务 PID42948；任务记录中的历史 runner PID40328、Blender PID61448 仅用于识别记录，不能凭这些旧 PID 终止进程。请反馈锁持有者/服务日志结论和“原子状态写入故障已解除”的明确结果。无需改 ACL、服务账户、安全设置、删状态文件、改路径、停止其他任务；本代理没有执行上述动作。

在允许 API 范围内无法只读确定瞬时文件锁已解除。满足用户指定的恢复条件前停止 Hub 依赖建模；旧任务和候选完整保留，不进行无意义循环或试错重试。恢复证据确认后，正常 `/retry` 路径至多安全重试一次相同阶段，保存幂等键及旧任务关系，继续真实原生与多视角检查。

## 不依赖 Hub 的尺寸核对

当前原生玻璃两侧高度均 0.4861498 m，前壳高度 1.4900001 m，比例 32.6275%。既有 museum-front 照片审计目标约47–49%属于投影图像比例，并非厂家尺寸。若暂保持当前玻璃上沿2.5212908 m，算出的初步下沿约1.7912–1.8210 m，仅作下一轮曲线轮廓拟合范围；不能直接当精确 CAD 尺寸或通过标准。冷却参考笔记也明确膨胀水箱、安装坐标和完整管路为拟合，盖板必须同时核查机械与驾驶室空间，不能用外壳遮住安装问题。

正式两份母版和网页 GLB 本轮未改。完整目标 ACTIVE，16项仍 OPEN。上一轮报告和截图已在原 Slack 线程，不重复发送旧附件。
