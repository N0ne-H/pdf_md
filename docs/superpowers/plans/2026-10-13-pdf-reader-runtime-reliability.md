# PDF Reader 4.2.2 Implementation Plan

**Goal:** 在不同工作目录统一使用用户缓存，可靠处理页面渲染失败，并让公式回答明确区分已查看与未核验。

**Architecture:** 全局 Skill 增加一个固定缓存路径的轻量启动脚本，复用安装的 CLI。只在 render.py 改善 PNG 写入和失败处理；BM25、解析、缓存格式与 CLI 参数保持原样。

**Tech Stack:** Python 3.11、PyMuPDF、PowerShell、pytest、Codex 全局 Skill。

**Spec:** 本聊天中用户的 4.2.2 要求及 docs/2026-10-13-pdf-reader-4.2.1-skill-discovery.md。

## Steps

- [x] 复现安装版 render-page 第 5 页写入失败，检查渲染子目录 ACL 与文件，比较当前沙箱和获准执行结果。验证：记录命令、退出码及错误，不把权限限制推断为文件占用。
- [x] 为渲染写入错误添加回归：模拟底层 PNG 文件保存拒绝，CLI 应给出可理解的错误；验证失败时临时文件清理及重复/并发渲染。必要时改为 Python 写 PNG 字节及唯一临时文件，原子替换最终文件，保留原错误。
- [x] 创建 Skill 启动脚本 scripts/reader.py，传入固定用户缓存，拒绝重复 --cache-dir。更新 SKILL.md 的启动方式、权限处理及精确公式必须实际查看/披露未核验的规则。验证：两个 cwd 下 ingest 命中同一缓存，覆盖显式覆盖路径被拒绝。
- [x] 校验并安装用户级 Skill 和更新的非 editable Core。验证：安装路径指向 site-packages，全量 pytest 与 pip check。
- [x] 在两个新会话验证统一启动和精确公式图片查看；另测无法查看时的披露。保存工具轨迹与修复报告。停止在 4.2.2，不进入 4.3。

采用当前会话执行，用户已授权实施；不自动提交或进入下一阶段。
