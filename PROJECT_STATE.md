# PDF Reader 项目状态

<!-- PDFREADER-HANDOFF-BEGIN PH-20261014-431 -->

## 交接登记

- 编号：PH-20261014-431
- 更新时间：2026-10-14（Asia/Shanghai）
- 源任务：01a1346b-eaff-7390-8f4a-ab75e2779057
- 目录：`D:\大学学习\大二上\codex`，在原目录接续，保留现有成果。
- 用户授权：保存交接并创建新对话，为开始 4.3.1 做准备。
- 接手任务：01a138a6-1710-7661-8c83-00193059192f（local）。
- 状态：已接手。源任务已转交修改权；4.3.1 Codex 核查与上下文开销优化已实现、安装并验证，等待用户验收。

## 当前目标与边界

4.3 全文阅读与总结覆盖率已实现、测试并交付；用户尚未明确声明验收通过。用户随后明确授权 **4.3.1**：先在当前 Codex 环境核查 TRAE 对比报告中的 Deep 输出/计数差异，再继续上下文开销优化。核查未复现 Core 跳块；仅优化 CLI 响应与阅读指引，不修改批次选择。4.3.1 已实现、安装及验证，等待验收。不进入 4.4，不针对 TRAE 开发兼容功能，不引入 MinerU，也不实施报告的 OCR/表格重建建议。

持续限制：不引入付费 API、大模型、MCP、向量数据库；不重新实现解析、不修改已验证 BM25（除非明确缺陷）；保持缓存兼容及跨项目 Skill。后续 Core 修改须重新安装原 Conda 环境并验证全局 Skill。不要改系统通用 pdf Skill。

## 已完成与证据

- 4.3.1 报告：`docs/2026-10-14-pdf-reader-4.3.1-context-overhead.md`；计划：`docs/superpowers/plans/2026-10-14-pdf-reader-4.3.1-context-overhead.md`。
- Codex 修改前 Deep 核查：10 批47块，原始 stdout、工具完整展示/模型可见正文与状态新增ID逐批一致；证据 `output/reading-4.3.1/codex-audit/`。受控外层截断确有显示与记录差异，gap撤销并重读有效；Core 20字符截断保持0块已读。未复现报告所称跳块Bug，不修改 reading.py。
- 4.3.1 新增可选 `--compact`（reading-start/next/status），保留完整正文与状态语义；`--details --compact` 保留全部诊断，仅压缩空白。Skill按需查询结构和候选，不常规重复目录。
- 两文档三模式同范围对比：CLI响应Token减少26.05%–34.44%，正文、事件和详细覆盖一致。最终证据 `output/reading-4.3.1/benchmark-c2bbda2a/metrics.json`；此范围含outline、不含ingest，不等同4.3总量，更不代表实际计费。
- 4.3.1全量 **43 passed in 61.63s**：`output/reading-4.3.1/pytest-release.txt`。已重装原Conda Core及同步全局Skill/reference，哈希一致，pip check通过，项目外固定入口可读取旧记录。
- 4.2.1 Skill 发现与自动触发、4.2.2 运行可靠性：用户已验收；4.2.2 原 27 项 pytest 通过。
- 4.3 新增 Quick/Standard/Deep 内容计划、只含元数据的 chunks、独立阅读日志、分批恢复、块/页/章节状态、遗漏及外部视觉回执；具体问题保留 search。
- 4.3 最终全量 **39 passed in 131.77s**：`output/reading-4.3/pytest-release.txt`。代码已非 editable 重装，全局 Skill 已同步，源码/安装 reading.py 和 Skill/reference 哈希一致；pip check 无冲突。
- 权威阶段报告：`docs/2026-10-14-pdf-reader-4.3-reading-coverage.md`。实现计划：`docs/superpowers/plans/2026-10-13-pdf-reading-coverage.md`。
- 最终两文档三模式基准：`output/reading-4.3/benchmark-498ef271/metrics.json`，同目录各案例 calls、batch、reading、status JSON。复现脚本 `output/reading-4.3/benchmark.py`。旧基准目录不是最终结果。
- Attention 自动计划 Quick/Standard/Deep 读取 10/31/47 块（总54）；实际 Skill 总结补读后 12/35/47。实际视觉回执1/6/15（总15候选）。手册三模式计划10/75/84块（总88）；实际手册 Quick11块，未查看图片。手册 Standard/Deep 仅范围/统计测试，没有独立回答质量验收。
- 实际阅读/回答证据：`output/reading-4.3/agent-{quick,standard,deep}.json` 和相应 `*-summary.md`，另 `agent-manual-quick.json`/`agent-manual-quick-summary.md`；中途未读附录证据 `agent-deep-mid-status.json`。
- 项目内及 `D:\TRAE10.11` 验证固定入口和复用用户缓存；项目外导入 site-packages。
- 源对话已结束业务修改；没有仍需推进的已知测试/安装进程。旧独立代理任务已完成，不要自动重跑或接管它们。

## 文件与运行环境

保存时分支：`main`；HEAD：`0e748170970b4b56fd53323046cf3a682f6a4fdb`。

4.3 成果已包含在提交 `0e748170970b4b56fd53323046cf3a682f6a4fdb`（4.3全文阅读与总结覆盖率）：`src/pdf_reader/reading.py`（新增）、`cli.py`、`__init__.py`；`tests/test_reading.py`（新增12项）；`skills/pdf-reader/SKILL.md`、`skills/pdf-reader/references/reading.md`；阶段报告与计划。未修改 BM25、parser、cache 格式、render 核心与固定启动脚本。交接另新增本文件，当前仅本文件未跟踪。实际分支/HEAD 在接手时用 git 只读核对；不自动提交、推送或丢弃改动。

本机路径（不能假设跨机器可用）：

- Python：`D:\env\conda\2024\envs\pdf-md-v1\python.exe`
- 全局 Skill：`C:\Users\26214\.agents\skills\pdf-reader\SKILL.md`
- 全部 Skill CLI 命令固定入口：`C:\Users\26214\.agents\skills\pdf-reader\scripts\reader.py`
- PDF 缓存：`C:\Users\26214\.cache\pdf-reader`，启动脚本拒绝覆盖缓存目录。
- 阅读记录：任务内 `.pdf_reader_readings` 或显式 --record；这是任务日志，不是另一个解析缓存。

## 有效决定与已知限制

- 普通总结默认 Standard，快速概览 Quick，完整/深入阅读 Deep。模式改变实际范围，不仅改变回答长度。计划为标题/结构启发式，用户问题需要时补读。
- 搜索命中≠全文阅读；CLI完整返回≠模型理解；外层截断要登记 reading-gap。渲染≠图片已查看。视觉回执为 external_tool_receipt_not_machine_authenticated，需真实工具轨迹支持。
- plan_complete≠complete_text_delivery。Deep 默认排除参考文献/目录，仍披露缺口。候选图表不是全部重要对象语义清单；15/15回执不是全部公式或整份PDF视觉核验。
- Token 数据为离线 cl100k_base 的CLI响应，不是计费；Attention Quick/Standard/Deep总JSON为7,673/14,249/18,702，全文Markdown10,967；手册15,096/35,252/38,511，全文17,339。Standard/Deep 总JSON可能更贵，不能宣称普遍省Token。
- 同一阅读日志一个写入者；空提取页按未知缺口披露，不自动断言空白或解析失败。
- 4.3 尚未重新做完整自动触发概率评估；显式 `$pdf-reader` 仍为可复现方式。

## 接续步骤

1. 用户已要求真实Codex端到端最终验收，当前8/12独立任务完成，最终报告尚未生成。三个case遇执行升级返回`Rejected("rejected by user")`，保存拒绝轨迹，不重试或绕过；需重新授权后完成。手册Deep Compact尚未启动。准确接续点见`output/reading-4.3.1-e2e/CONTINUE.md`。不自行展开4.4。
2. 当前未提交修改为cli.py、test_reading.py、项目Skill/reference及4.3.1报告/计划；output证据被Git忽略，保留原目录，不自动清理或提交。
3. TRAE报告缺少原始调用轨迹；运行环境/执行流程只是差异的可能来源，不宣称已定位TRAE根因。外层截断仍需登记gap，逐批真正展示正文后再继续。

<!-- PDFREADER-HANDOFF-END PH-20261014-431 -->

<!-- PDFREADER-HANDOFF-BEGIN PH-20261015-432 -->

## 面向4.3.2的当前交接（2026-10-15）

- 交接编号：PH-20261015-432；源任务：01a138a6-1710-7661-8c83-00193059192f。
- 工作目录：`D:\大学学习\大二上\codex`。用户随后明确要求`$project-handoff 创建新对话4.3.2`，授权保存、同一项目原目录新建并打开接手对话、核对后接续；未指定模型，不覆盖默认值。不把4.3.2标签当作具体功能实现授权。
- 接手任务编号：01a13fde-a2c9-74e3-af01-41a3aadab0f7（local，同一项目原目录）。状态：已接手；接手只读核验已通过，目录/HEAD/9项状态/三个断点/原8项251文件哈希一致。已收到源任务登记完成及修改权移交指令，接手已更新本状态；下一步确认4.3.2具体范围或是否先续完4.3.1剩余三项。源任务此后只观察，不再推进业务或改交接正文。
- 当前分支`main`，HEAD `41800b68ff55749d262b29beb475853b5ad1a0d0`，提交标题`4.3.1`。上方PH-20261014-431的`0e74817`和未提交说明属于旧快照，不能作为当前提交状态。此提交变化不是本轮验收执行的提交操作。
- 4.3.1实现已提交，既有43项pytest通过；本轮不修改Core/Skill/检索算法、不安装、不改权限配置、不引入MinerU。本轮并未重新执行43项pytest。保护文件哈希与验收起点一致。

### 4.3.1最终验收当前状态

共12项独立子代理任务，之前8项完整结果保留，未重跑（251个文件哈希核对零变化）。Attention Deep Compact的47块正文和11页实际查看均保留，剩余10回执及最终status已通过正常审批由父任务续交，现为9项流程完成。其余三项原代理因usage_limit_exceeded停止，不能标为通过：手册Standard Compact40/75块、下块c000046；手册Deep JSON35/84块、下块c000040；手册Deep Compact45/84块、下块c000050。三项均尚未执行原页查看或回执。精确快照见`handoff-runtime.json`。

- 当前无仍运行子代理，已核对collaboration状态；旧三代理为`/root/manual_standard_compact`、`/root/manual_deep_json`、`/root/manual_deep_compact`，原始task_complete用量限制错误已核实。正常审批收拢源会话残留进程，见`handoff-process-cleanup.json`。新对话不可假定能接管旧TTY session_id；恢复时先核对自己的实际可见正文与日志，必要时显示已存stdout补回上下文，不重新执行原8项。
- 主证据：`output/reading-4.3.1-e2e/`，每case的`calls.json`、原始stdout、`reading.json`、`views.json`、`tool-trace.json`、`run-summary.json`和`answer.md`。
- 统计脚本：`analyze.py`；最终报告生成器为`write_final_report.py`，必须在12项结束及原PDF质量核对后生成`output/reading-4.3.1-e2e/4.3.1-e2e-final-report.md`及`docs/4.3.1-e2e-final-report.md`。旧`final_report.py`是未执行的早期草稿，不用于当前结论。
- 计量新发现：本地Codex的`token_usage_record.thread_token_usage`可提供各子任务后端累计Token，`audit_rollouts.py`仅导出本实验12线程的用量/模型配置，见`observed-model-usage.json`。去重response usage之和与线程累计一致。不是CLI估计或账单，不包含父任务全部协调；图片/隐藏协议拆账与纯格式因果量仍未知。原八项summary中的null保留，不回写它们。
- Attention Deep Compact曾因并行render漏记一次proxy stdout；已从原始CommandExecution `exec-7c4fb5b1-10ff-4baa-a8f8-5c8841ae2dce`找回完整产出，单独保存`recovered-calls.json`。原calls不改、不重跑；当时是否完整模型可见仍不能认证。额外render/失败回执/恢复运输偏离保留，不当Core缺陷。
- 固定交互验收脚本`session.py`正常审批后仅接收case限定的CLI命令；正文每批实际消费后再推进。曾有换行转义/TTY恢复停顿，仅修验收驱动输入，不改Core或权限。原8项文件哈希起点见`completed-eight-before.json`，最终仍须核对。
- 当前附属report-app已有原始报告ID，保留同一artifact；本轮localhost预览连接失败/超时，UI复核尚未完成，不冒称验证。Markdown为用户要求的主要交付。

### 4.3.2边界与接续第一步

4.3.2具体功能范围尚未由用户定义。本次版本标签不能当作已授权实施更精简Markdown、修改Core或引入解析器。源任务原授权是先完成4.3.1最终报告，完成后停止等用户确认；用户尚未确认本轮最终验收通过。

接手先只读核对本目录、此编号、当前HEAD、CONTINUE.md最新段、handoff-runtime.json及关键证据；最终报告目前未生成，不可伪称存在。核实无源任务仍写入，再核对9/12状态与三项断点、说明4.3.2范围尚未定义，询问用户具体目标。若用户继续原4.3.1验收授权，则仅续未完成3项，完成原PDF质量核对和复算后生成最终报告、停止等确认。不得只凭“已提交4.3.1”推断端到端验收通过。源任务转交修改权后只观察，不再业务写入。

### 4.3.2用户定义的范围与本地交付（2026-10-15）

用户已在接手任务明确授权“阅读内容选择优化（Task-Aware Reading Optimization）”的实现、本地测试、原Conda/全局Skill更新及中文报告。此新指令替代上文交接时“范围未定义、只读、不修改Core/Skill、不安装”的临时边界；不补跑4.3.1剩余三项、不启动新的真实Agent对照、不引入MinerU/OCR/新模型/MCP/向量库/付费API、不改解析缓存和BM25、不自动提交推送，完成后停止，不进入4.4。

- 实现：Quick改为相关章节代表，覆盖方法而非全局前10块；Standard补主要方法/实验实质内容并排除重复页眉；Focused保持search/read，局部推导不触发全文；Deep保留旧默认，新增互斥的`--pages FIRST LAST`、`--section PATH`、`--scope body|all`。Compact、事件覆盖、断点、截断和gap保留，旧日志不改计划。
- 修改：`src/pdf_reader/reading.py`、`cli.py`，`tests/test_reading.py`，项目Skill及reading reference；没有修改检索/解析/缓存/渲染核心。
- 报告：`docs/2026-10-15-pdf-reader-4.3.2-task-aware-reading.md`；计划：`docs/superpowers/plans/2026-10-15-pdf-reader-4.3.2-task-aware-reading.md`。本地证据、脚本及原始stdout在`output/reading-4.3.2/`，按原规则被Git忽略，保留原目录。
- 起点43项回归通过；新增18项。阅读相关34项通过；收尾前曾61项通过，最终完整回归为60 passed、1 failed（57.96s），不能称最终全绿。失败为未修改的并发渲染测试：render.py:42读取PNG时PermissionError，单独重跑1 passed但完整运行再次失败，根因未完全定位；保留`pytest-release.txt`、`pytest-concurrent-render-failure.txt`、`pytest-render-check.txt`，不扩展修改渲染或权限。无新的真实Agent调用或原页人工质量验收，文字契约检查不等于模型路由验证。
- 两文档同流程Compact的离线cl100k_base对比：Attention Quick 4448→6035 Token（结构锚点4/14→14/14，第3–5页0→7块），Standard 8915→10269（13/14→14/14）；手册Quick 7994→8340（8/9→9/9），Standard19522→19389（9/9不变、少9个纯格式块）。默认Deep的47/84块及正文不变。锚点命中不是全细节覆盖、理解或视觉核验；计量不含outline/ingest/图片/模型账单，与旧报告范围不同。
- 原Conda本地非editable安装、全局Skill/reference同步及项目外固定入口检查见`installation-verification.json`；旧日志可用、固定缓存不被覆盖、pip check无冲突。4.3.1原8项251文件重新核对零变化，两份PDF缓存哈希未变。
- 版本保全：4.3.1仍在`main/41800b68ff55749d262b29beb475853b5ad1a0d0`；本轮代码/文档未提交。`output/reading-4.3.2/baseline/`保存起点源码、安装版本、全局Skill及工作区补丁。4.3.1端到端仍9/12，最终报告不存在，不标验收通过。
- 当前阶段：4.3.2本地实现交付，存在1项既有并发渲染回归失败，等待用户确认；不展开下一阶段。限制和已知质量问题见报告第8节。

### 4.3.2.1 Windows PNG并发缓存修复（2026-10-15）

用户已授权在本任务定位并修复并发PNG缓存异常，仅本地Python/pytest，不启动Agent、不改阅读策略/BM25/Compact/解析缓存/Skill路由，不自动提交或推送，完成后停止。当前4.3.2已由用户保存到`main/bf6e561e1360b9ccc5772516a5a9a09bd41d285a`，本轮仅在其上保留未提交的修复及文档。

- 根因证据：初始目标测试首次失败（4.88s）；重复replace会替换已发布胜出文件。只改不覆盖rename后10轮仍2次缓存读失败；真实DELETE访问句柄确定性复现普通CRT读缺少FILE_SHARE_DELETE时的共享冲突，独占锁测试仍报错。
- 修复仅在`src/pdf_reader/render.py`：Windows不覆盖rename发布完整临时PNG；缓存读用只读CreateFileW并共享读/写/删除，句柄交标准流关闭。无新依赖、无重试或等待，不改ACL/安全设置，其他平台仍用原replace/read_bytes路径。`tests/test_runtime.py`新增7项回归，保留原目标测试并适配发布故障注入点。
- 最终验证：运行专项15 passed（6.36s）；真实四进程并发专项重复10轮全部通过，40个子进程、每轮一个有效PNG、无临时残留；完整pytest **68 passed in 59.80s**，无失败或跳过。中间rename-only的失败日志也保留，不掩盖。
- 已本地重装原Conda Core，无依赖下载。安装/项目Core哈希一致，项目外全局固定入口渲染与缓存命中、旧阅读记录只读兼容、pip check通过。保护哈希证明本阶段阅读/检索/解析/缓存/Compact/Skill未变；原4.3.1八项251文件哈希不变。
- 报告：`docs/2026-10-15-pdf-reader-4.3.2.1-windows-png-cache.md`；计划：`docs/superpowers/plans/2026-10-15-pdf-reader-4.3.2.1-windows-png-cache.md`；证据与起点快照：`output/reading-4.3.2.1/`。4.3.2历史失败记录不回写，当前状态以上述4.3.2.1结果为准。
- 边界：验证支持本机所测并发场景，不保证外部独占锁、ACL变更、强制终止或磁盘/网络文件系统异常；这些仍应报错。原有失败且清理也被拒绝时保留原始错误的处理未改，异常退出可能留下待处理临时文件；正常完成的并发验证无残留。4.3.1端到端仍9/12，无最终验收报告，未补跑。
- 本阶段已交付并停止，等待用户确认，不进入4.4。

<!-- PDFREADER-HANDOFF-END PH-20261015-432 -->
