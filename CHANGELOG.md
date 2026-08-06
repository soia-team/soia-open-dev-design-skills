# Changelog

本文件由 soia-meta-skill-release 在每次正式发版时自动更新，与 GitHub Release 同源；
更早的版本演进见 git 提交历史与 GitHub Releases。

## v1.8.0 — 2026-08-06

Open Design 三路线判定与 MCP 宿主实测矩阵(pi 经 pi-mcp-adapter 实测可用)、open-design-ops 渐进式重构

## 新增
- feat(open-design-ops): 路线判定、MCP 接入与设计↔代码双向契约 (#44)
- feat(open-design-ops): 补桌面版 App 运维与只读诊断脚本 (#35)

## 修复
- fix(open-design-ops): 纠正 pi 的 MCP 支持结论，实测装 pi-mcp-adapter 后工具调用可用
- fix(open-design-ops): 安装改为渐进式——先探测，再询问，最后才装 (#39)

## 维护
- chore(release): feat 在列,版本列车提为 next-minor
- docs(open-design-ops): pi 实测为不支持 MCP，从安装目标移除 (#51)
- chore(skills): config.example.yml 归位到 assets/ (#50)
- chore(skills): 补上安装章节改动遗漏的版本 bump (#49)
- docs(skills): 安装章节补齐三个一等宿主 (#48)
- refactor(open-design-ops): 按渐进式原则拆分，补齐结构与配置要求，升 1.4.0 (#47)
- docs(open-design-ops): 补 WorkBuddy 的 MCP 配置形态与参数约束 (#46)
- docs(open-design-ops): 补 MCP 安装实测矩阵，升 1.3.0 (#45)
- docs(agents): branch off main; releases fast-forward dev onto main (#43)
- docs(open-design-ops): 补技能版本号与本地插件删除方法 (#42)
- chore(release): switch dev train to patch level (#40)
- chore(release): open next train after v1.7.0 (#38)
- release: finalize v1.7.0 (drop -SNAPSHOT) (#36)
- docs(changelog): seed with current release baseline (#34)
- docs(agents): dev-branch integration workflow (#33)
- chore(release): open dev branch — audit on dev, version train 1.7.0-SNAPSHOT

## v1.7.0 — 2026-08-03

补 Open Design 桌面版 App 运维：端口漂移、entryFile 埋点、只读诊断脚本

## 新增
- feat(open-design-ops): 补桌面版 App 运维与只读诊断脚本 (#35)

## 维护
- docs(changelog): seed with current release baseline (#34)
- docs(agents): dev-branch integration workflow (#33)
- chore(release): open dev branch — audit on dev, version train 1.7.0-SNAPSHOT

## v1.6.0 — 2026-08-01

架构图、流程图与设计文档工作流。
