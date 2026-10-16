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

### 4.4 跨文档可靠性与Token效率评估（2026-10-16）

用户明确授权本阶段只测试和报告，不修改Python Core、全局Skill、阅读算法、BM25或缓存格式，不运行独立Agent/真实模型问答/自评分，不接入新解析器或服务，报告后停止等待确认。基线为`main/886844923762c63c91116911e9a76ef3003c8b9d`（4.3.2.1）；本轮开始工作区干净，Core/Skill保护哈希18项最终不变，安装Core及全局Skill仍匹配。

- 输入：Attention15页、TRAE手册32页；新增GAN综述13页（SHA `3f3bc956793f9b9fc88fc891a51dd5c1cbf348fe6f4b58c9f4b845b5d4939cd3`）、CTM44页（SHA `671fd295f6362b3910d5def7e78d5eb08f8a99d3866c4808f79a26c685dec171`）。新文档正常ingest首轮缓存未命中、热缓存命中；GAN10.78s/56块/23997全文MD Token，CTM32.16s/177块/36436 Token。原两文档缓存复用，未重复解析。
- 独立基准：先原PDF文字与11张实际原页查看，冻结每篇8题共16锚点，再运行search；之后补看CTM第33页表4，共12页。路径、范围及实际查看说明在views-ledger.json。未把渲染路径当查看，也未给本地阅读模式伪造视觉回执。
- Focused：固定search Top5加完整read所有5命中，含过量读取，不是Agent策略评估。完整素材包Top1为GAN5/8、CTM2/8；Top5为GAN8/8、CTM6/8，合计14/16。C1/C3缺失块存在于缓存，金标准指导补3次read恢复，不能回写成原检索成功。公式图片仍需实际视觉核验，素材包命中不是回答准确率。
- 模式：GAN Quick仅c000035一个不完整表格块，概览失败；Standard44块完整CLI25011 Token，高于全文MD23997。CTM Quick16块有主要角色但漏明确局限和部分跨页/结果内容；Standard37块完整CLI11828。两篇指定Deep（GAN页9–11的13块；CTM第3节10块）与本地all（56/177全块）均验证计划/原文/真实stdout/日志一致。所有Token为离线cl100k_base，Core的estimated_*未当作实测。不存在模型阅读全文或计费结论。
- 原页质量：GAN9个标题抽查7个正确，2.1.2/2.1.3嵌在正文未成为标题；双栏伪页眉/副标题祖先影响选块，表1跨块断在单元格中。GAN表3/4目标数值及列头经原页核对正确；CTM表4四行/缺失标记正确。公式多为PNG可恢复，风险提示依赖窄查询词，缺提示不等于可靠。无不可恢复的目标正文/数值缺失被这16锚点证实，不推广到全篇。
- 回归：现有完整pytest **68 passed in 108.97s**，含Windows并发PNG目标；与其他本地评估同时运行，不和上轮时长直接作性能比较。旧两文档4个固定锚点均Top1，全部Quick/Standard/默认Deep计划ID与4.3.2基准一致（Attention16/40/47，手册11/66/84）；Attention Quick核心方法原页3–5仍7块。原页缓存稳定、无临时残留，原八项251文件哈希未变。未补跑4.3.1三项或12-Agent矩阵；4.3.1仍9/12、最终报告不存在。
- 报告：`docs/2026-10-16-pdf-reader-4.4-evaluation.md`；计划：`docs/superpowers/plans/2026-10-16-pdf-reader-4.4-evaluation.md`；全部脚本、冻结锚点、190条任务调用原始日志、模式记录、指标、查看证据和校验在`output/reading-4.4/`（Git忽略，保留原目录）。未自动提交/推送或重装。
- 结论：评估工作已完成，**当前版本未达到4.4完整质量验收标准**，阻塞为GAN Quick跨文档分组/选择失败；源码与元数据可复现，不能归BM25。报告只提出最小选块/跨块/响应开销建议，未实施。暂不建议立即进入5.0更换解析栈，先等用户确认是否授权小修及复测。本阶段停止等待用户确认。

<!-- PDFREADER-HANDOFF-END PH-20261015-432 -->

<!-- PDFREADER-HANDOFF-BEGIN PH-20261016-441 -->
## 面向4.4.1的交接（2026-10-16）

- 交接编号：PH-20261016-441；源任务：01a13fde-a2c9-74e3-af01-41a3aadab0f7。
- 用户明确调用project-handoff要求“创建新对话4.4.1”，授权保存、同一项目原目录创建并打开、只读核对后接续。工作目录：`D:\大学学习\大二上\codex`；项目ID：d829174b-622a-45fc-8b60-7ad4a1e8bf92，local。未指定模型，不覆盖默认设置。
- 接手任务编号：01a14497-480f-7590-bb23-536007bf1b2c（local，同一项目原目录）；交接状态：已接手。用户已验收4.4.1/4.4.2/4.4.3并授权v4.4稳定收尾及本地Git保存；完整基线84项通过。当前只做发布文档和版本保存，不启动5.0；无后台任务待接管。
- 当前分支main；稳定收尾前HEAD `5758e532fd615e491efee4887cf4fbf4358ab693`（4.4.3），三轮实现已在历史中。稳定发布提交以本地`v4.4^{commit}`定位，本轮授权创建发布收尾提交及注释标签，不推送。交接初始84aaf15和各阶段旧HEAD/未提交说明为历史快照。

### 权威成果与真实结论

以下为4.4历史评估快照：评估已完成，原版本未达到4.4完整质量验收标准。用户已于2026-10-17授权4.4.1修复，见本区末尾新进度；不能将4.4失败快照当作修复后结果。4.4报告：`docs/2026-10-16-pdf-reader-4.4-evaluation.md`；完整本地原始证据：`output/reading-4.4/`，该目录被Git忽略，仅本机原目录保留，不清理。报告中的原页事实、冻结anchors.json、views-ledger.json、focused-assessment.json、mode-assessment.json和summary.json可核对具体结论。

- 4份PDF实际名称、SHA、页数及结构见报告和inventory.json/documents.json。新增GAN综述13页56块，全文MD23997 Token；CTM44页177块，全文MD36436 Token。原Attention15页和TRAE32页只做少量回归。
- 基于原PDF先冻结16锚点，再检索；实际查看12张代表原页，未把图片路径当查看。Focused完整素材包Top1为7/16，Top5为14/16。CTM两题缺块存在缓存，金标准指导补读不算原Top5成功；不等同模型回答准确率。
- 阻塞P1：GAN Quick仅选c000035一个不完整表格块，缺概览。共享英文副标题祖先使Quick按[:2]章节分组坍缩，Standard的Methods匹配祖先使其选全44个正文块；非BM25根因。最小建议是纠正共享包装标题下真实章节分组并做角色覆盖回归，但尚未获授权实施。
- GAN Standard完整CLI25011 Token超过全文MD23997；CTM Quick16块漏明确局限等，Standard37块完整CLI11828。管理输出开销、跨块表格/公式视觉风险和提示查询词依赖为其他问题，详报告。不同模式范围不同，不把较少Token宣称同任务等价收益。
- 指定Deep与all本地覆盖一致：GAN页9–11的13块、CTM第3节10块；all分别56/177块。计划/成功stdout/原文/记录一致；本地CLI交付不是模型阅读全文。全部Token离线cl100k_base，不是计费结果。
- 完整pytest：`output/reading-4.4/pytest-release.txt`，68 passed in 108.97s，含Windows并发PNG回归。final-validation.json记录190条任务调用stderr全空、原PDF和保护文件未变、实际查看12页。4.4未修改Core/Skill/算法/缓存，18项保护哈希不变，安装版本仍匹配，不需重装。
- 旧Attention/TRAE四个锚点均Top1，Quick/Standard/默认Deep计划与4.3.2一致，Attention Quick仍覆盖3–5页核心方法7块；原页缓存稳定无临时残留，原4.3.1八项251文件哈希未变。

### 保留的边界与历史状态

保持Python Core + 全局Skill，原Conda为`D:\env\conda\2024\envs\pdf-md-v1\python.exe`；固定入口`C:\Users\26214\.agents\skills\pdf-reader\scripts\reader.py`；固定缓存`C:\Users\26214\.cache\pdf-reader`。保留Compact、页码/风险提示、断点/截断/gap、4.3.2.1 PNG修复。不引入MinerU/OCR/向量库/MCP/付费API或新模型，不做无关重构，不自动提交/推送，不擅自进入5.0。4.4仅测试报告的授权不等于新修复授权。

4.3.2.1通过Windows非覆盖发布+共享读写删除句柄解决已复现竞争，无重试；十轮四进程通过，外部独占锁/ACL/强制终止等风险仍不能保证。详其独立报告。4.3.1历史E2E仍9/12，最终报告不存在，三个手册流程40/75、35/84、45/84，不能标为已验收。用户已明确不补跑剩余大规模Agent测试；不重启12任务矩阵、真实模型问答或自评分。

### 接续第一步和修改权

接手核验、修改权移交和4.4.1范围确认均已完成。用户明确要求只修复Quick策略，检查CTM，四文档本地回归/Token对比、完整pytest、原Conda安装验证，完成后停止；不进入4.4.2/5.0，不改解析/BM25/分块/缓存/Compact/PNG，不运行多Agent或全文模型深读。

### 4.4.1实际进度（2026-10-17）

- 仅改Core的`src/pdf_reader/reading.py`，基于正文公共路径归一化、正文代表优先、块内显式概览/局限标记、无清晰章节时分散回退、同节跨页明显英文断句一层补读。没有文档标题/固定ID硬编码，未修改Skill或其固定入口。
- 旧源码加载新测试红灯6 failed/37 passed；修复后阅读专项43 passed；全量77 passed in 59.89s（原68项+9项）。原Conda按`--no-deps --no-build-isolation --force-reinstall .`非editable安装完成，源码/安装全部Core及项目/全局Skill一致，pip check通过；项目外四文档全局Quick计划、首批阅读和status正常。
- GAN Quick 1→10/56块，正文1234→4724 Token，完整CLI3082→7285；已选问题/方法/实验设置/比较/结论代表。CTM16→19/177块，正文3431→3873、CLI7442→7947；新增c000030/c000044连续前文及c000046明确局限。Attention16→18，原核心证据全保留并补两块前文；TRAE11块ID不变、九章保留。四文档Standard/默认Deep计划ID不变。
- 冻结16锚点和原必要块组不变：GAN完整素材包0→2/8，CTM2→4/8，非Quick强制验收指标，不是模型问答准确率。585项保护条目只允许reading.py变化；原4.4证据/PDF/缓存及其他Core/Skill不变。
- 报告：`docs/2026-10-17-pdf-reader-4.4.1-overview-reliability.md`；计划：`docs/superpowers/plans/2026-10-17-pdf-reader-4.4.1-quick-overview.md`；原始证据`output/reading-4.4.1/`（最终baseline-final/after-final、comparison.json、pytest-release.txt、install-validation.json）。首次默认pytest临时目录权限错误及早期评估脚本未成功的目录保留，不作为最终结果。
- 剩余：GAN表格原有切分/总结续文、Standard过量选块；CTM仍有损失枚举、方法/实验深入素材未选；英文断句补读非通用语义保证，公式/表格需Focused补读和实际原页查看。未修解析栈，未补4.3.1矩阵，无提交推送。当前HEAD仍84aaf15，业务修改未提交；本阶段停止等待用户确认。
### 4.4.2实际进度（2026-10-17）

- 用户随后明确授权Focused跨块证据补全与Token优化，取代上阶段“不进入4.4.2”的暂停边界；本阶段完成后停止，不进入4.4.3/5.0。当前基线main/`6ae871c59a602cf8b66451c54a60a12f0e92210f`（4.4.1已由现有仓库状态包含），上方84aaf15及未提交说明为4.4.1历史快照，不是当前HEAD。
- 分析先行：C1原Top5缺c000016/c000018，C3缺c000022；正文存在缓存。实际比较拆分查询、图注、同节/相邻元数据；C1定向查询加两次read新增1478 CLI Token，C3最终查询加read新增983。没有修改Core或增加接口，没有章节过滤CLI。
- 仅生产修改项目Skill的SKILL.md及references/reading.md：短预览按需增大、有选择完整read、缺口驱动定向/相邻补读、Codex判断充分性；区分解析缓存、历史交付与当前可用原文。上下文失效可显式重读，真实截断登记gap；复用不伪造交付事件。不创建Focused模式计划，不永久禁止已读块。
- 复用冻结16锚点/原查询/必要块组。人工审阅固定调用的离线模拟全部16必要块组齐全：GAN八题独立CLI19525、共享18681、G8前失效19525（原48734）；CTM三种模拟均13709（原19515仅6/8，原金标准补读后20578为8/8）。不是真实模型上下文节省或自动策略成功率。共享本身仅GAN少一次c000044重读，省718正文/844 CLI Token；主要降幅来自选择读取与短预览。
- 16原查询完整hits一致，旧Attention/TRAE四锚点仍Top1，四文档12组Quick/Standard/Deep计划与4.4.1一致。1317保护条目仅预期两份Skill变化；Core/旧证据/PDF/缓存/冻结锚点不变。
- 新增2测试（流程契约与现有记录复用/重读/gap/独立记录行为），先红灯1 failed/2 passed，Focused子集3 passed；完整pytest **79 passed in 66.76s**。没有Agent矩阵或真实模型语义评分。实际重新查看CTM第4/5页与GAN第9页；未把其他锚点视为本轮全部视觉验证。
- 已备份并同步两份全局Skill；Core未变化，不重复安装。安装Core与源码、全局Skill/reference/launcher与项目逐字一致；项目外10次Focused search/read通过，pip check无冲突。
- 报告：`docs/2026-10-17-pdf-reader-4.4.2-focused-evidence-token.md`；计划：`docs/superpowers/plans/2026-10-17-pdf-reader-4.4.2-focused-evidence.md`；证据：`output/reading-4.4.2/`，最终action-manifest-final.json/workflow-final/workflow-results-final.json；旧中间结果保留。
- 局限：固定样本人工选择有已知金标准优势，未测未知问题模型自主执行效果；Core不能证明模型仍记得原文；无章节过滤；公式/复杂表格仍须必要原页查看；16素材包齐全不等于问答准确或全部视觉核验。未改4.4.1 Quick、BM25、解析/分块、Compact、缓存或PNG；未提交推送，未补旧4.3.1任务。本阶段停止等待用户确认。
### 4.4.3实际进度（2026-10-17）

- 用户已明确验收4.4.2，授权Standard/Deep管理输出优化，取代上阶段暂停于4.4.3的边界；不改阅读策略、不删正文、不改变原JSON/Compact、不进入5.0。
- 先建立四场景同绝对记录路径、同5块/6000字符、同调用数且均含最终status的JSON/Compact基线。发现CTM局部Method的Compact status仍带59条未完全覆盖章节（绝大多范围外），每批重复record/document/mode；由测量决定新增可选`--lean`，而非修改旧Compact。
- Core仅改`src/pdf_reader/cli.py`，新增互斥--lean响应投影；next保留所有Compact chunk字段，省顶层重复管理信息；status保留计划/全局计数、活动gap原ID/页/原因、未恢复截断、未知空提取页、计划内视觉计数与外部声明信任。`--details --lean`返回原完整审计schema。ReadingTracker、事件/coverage保存、schema1、选块/BM25/Focused/解析/PNG/缓存均不变。Skill两份指引推荐Standard/Deep Lean、Quick Compact。
- 统一路径Compact→Lean：GAN Standard正文19829不变，总25022→24020（4.00%），管理5193→4191；CTM Method Deep正文1943不变，总5450→2815（48.35%），管理3507→872；Attention Standard总10569→9544；TRAE Standard总19869→17205。调用数依次11/4/10/16，未省status，不是账单或不同任务等价比较。
- 82次旧JSON/Compact响应逐字一致；Lean全部正文/ID/原页/章节/截断/风险、事件流和完整coverage一致（仅独立reading_id不同）。四文档12组计划不变；16冻结Focused hits和16代表read一致、旧四检索Top1保留；旧/新日志只读恢复正常。1888保护条目仅cli.py和两份Skill预期变化，全部旧评估/PDF/缓存不变。
- 5新增Lean案例先红灯，阅读专项50 passed；完整pytest **84 passed in 61.24s**，含默认Deep/all、截断/gap、补读、flush失败及Windows PNG并发。原Conda按既有非editable/no-deps/no-build-isolation方式重装，备份并同步全局Skill；安装所有Core及Skill/reference/launcher逐字匹配，项目外固定入口23次调用通过，pip check无冲突。
- 报告`docs/2026-10-17-pdf-reader-4.4.3-management-overhead.md`；计划`docs/superpowers/plans/2026-10-17-pdf-reader-4.4.3-management-output.md`；证据`output/reading-4.4.3/`（before/after分阶段metrics、comparison.json、pytest-release.txt、global-validation.json等）。原证据不清理，安装build已归档到本轮install-build。
- 仍有完整长章节路径、JSON包装和按需完整审计开销；持久化coverage计算/日志体积未优化。公式/表格/语义可靠性仍需原有核验。建议用户验收本轮后正式结束4.4，不为固定Token比例扩大范围。当前停止等待确认，无提交推送、无Agent矩阵、无旧4.3.1补测、不自动进入5.0。
### v4.4稳定版本收尾（2026-10-17）

- 用户已验收4.4.1/4.4.2/4.4.3，授权文档整理与本地稳定提交、v4.4标签，明确不推送、不开发新功能或进入5.0。开始时main/5758e53、工作区干净、无v4.4同名标签。
- 仅更新README、发布报告及本状态；Core/Skill/测试/包元数据不变。README涵盖架构、四种阅读方式、Compact/Lean、视觉核验、缓存/日志/上下文区别、恢复和全部已知限制。v4.4是Git标签，分发包仍0.1.0。
- 复用84 passed in 61.24s及4.4.3安装证据；本轮12次帮助/Focused/Quick/Standard/Deep固定入口轻量调用通过，安装全部Core和全局Skill/reference/launcher与项目一致，pip check无冲突。未重跑大矩阵，4.3.1仍9/12。
- 发布报告：`docs/2026-10-17-pdf-reader-v4.4-release.md`；轻量原始证据：`output/release-v4.4/validation.json`。暂存与本地保存仅限上述三份文档；不提交论文、缓存、日志、大型输出或新增个人环境信息。
- 本地发布提交与标签以Git实际引用为准，可用`git log -1 v4.4`和`git rev-parse 'v4.4^{commit}'`核对。Git保存代码/Skill/测试/文档；原始PDF和本地证据继续在本机保留，不由标签携带。未来开发可从该标签新建分支，恢复原日志需保留相应本地缓存。
- 本轮结束后停止，后续5.0仅列候选方向，未经新授权不执行。
<!-- PDFREADER-HANDOFF-END PH-20261016-441 -->


