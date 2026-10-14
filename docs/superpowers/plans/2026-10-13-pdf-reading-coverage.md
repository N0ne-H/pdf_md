# PDF Reader 4.3 Implementation Plan

**Goal:** Quick / Standard / Deep 选择不同阅读范围，以实际 CLI 输出事件计算进度并披露未读与未查看证据。

**Architecture:** 新增 reading.py 复用 CacheStore 和已有 Chunk。解析缓存仍统一于用户目录；独立阅读记录写在任务工作区 .pdf_reader_readings 或显式 --record 文件，不修改 document.json 或缓存版本。CLI 成功输出后提交定位、完整返回、截断和渲染事件；查看是有来源的外部回执，不是 Core 自动确认。

**Tech Stack:** Python 3.11、pytest、现有 PyMuPDF4LLM Core、用户级 pdf-reader Skill。

**Spec:** 本聊天的 4.3 Reading Coverage 要求。

## Implementation and verification

- [x] 读取缓存元数据、目录与现有 CLI。新增元数据接口及模式计划；验证不返回 Markdown、三种范围不同、参考文献/附录和无提取文字页被披露。
- [x] 添加阅读会话、分批 next、status、遗漏说明与视觉回执。read/search/render 可带可选会话 ID；验证搜索不算完整阅读、截断不算完整、重复不重复计数、渲染不算查看、失败输出不提交记录。
- [x] 更新全局 Skill 模式选择与命令、保持固定缓存入口。验证新范围与外部图像查看后提交回执；Core 和 Skill 重新安装。
- [x] 对 Attention 和结构不同的 TRAE 手册运行三模式分批基准。实际计量 CLI JSON cl100k_base 文本 Token，保存每次调用/状态；独立代理检查总结质量及遗漏，图像实际查看后记录。
- [x] 全量 pytest、项目外安装与 Skill 验收、生成 4.3 报告。披露分类启发式、外部工具截断和视觉回执的信任边界。停在 4.3。

当前会话执行；不自动提交或进入 4.4。
