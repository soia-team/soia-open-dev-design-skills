# SOIA 设计与文档技能库

[English](README.en.md) · 中文

把需求变成能看的东西：PRD、原型、架构图、Office 文档——都可编辑，不是截图。

## 这是什么

`soia-open-dev-design-skills` 覆盖从需求到可交付产物的设计与文档产线：

```text
一句话想法
    ↓
PRD（范围、用户故事、验收标准）
    ↓
原型 / 架构图（Open Design 高保真 · Archify 架构 · draw.io 流程）
    ↓
Office 产物（DOCX / XLSX / PPTX，可编辑且经校验）
```

所有图表产物都是**可编辑源文件**（JSON、drawio、OpenXML），不是一次性截图——后续能改、能复用、能进版本库。

### 适合什么场景

- 「把这个想法整理成一份能评审的 PRD。」
- 「画一张这个系统的架构图。」
- 「我这堆 Visio 文件，转成 draw.io 能编辑的。」
- 「做一版高保真原型，我要看效果。」
- 「改一下这个 Excel，别改坏格式。」

### 不负责什么

- 不做视觉品牌设计。配色、Logo、品牌规范不在本仓。
- 不替代设计师。产出是可评审的草稿与可编辑源文件，不是最终视觉稿。
- 不直接改原始 Office 文件。先复制再改，并做 OpenXML 校验，避免破坏原件。
- 不做新媒体排版发布，那在 [soia-open-media-content-skills](https://github.com/soia-team/soia-open-media-content-skills)。

## 从哪里开始

| 你要做的 | 用这个 | 完成标准 |
|---|---|---|
| 把想法写成 PRD | `soia-dev-design-draft-prd` | 范围、用户故事、验收标准齐全 |
| 画架构图或时序图 | `soia-dev-archify-diagrams` | 可维护 JSON + PNG 预览 |
| Visio 转可编辑图表 | `soia-dev-drawio-visio-diagrams` | drawio 源文件可二次编辑 |
| 做高保真原型 | `soia-dev-design-explorer` | HTML 原型与设计评审记录 |
| 改 Word/Excel/PPT | `soia-dev-officecli-ops` | 复制后修改并通过 OpenXML 校验 |

带 🟡 的技能需要先装 Open Design 或 Archify 等外部工具，技能会在执行前检查并告诉你缺什么。

## 技能清单

> **开箱可用**：✅ 装完即可使用 · 🟡 还需申请 API key 或完成第三方登录

| 技能 | 一句话职责 | 开箱可用 |
|---|---|---|
| `soia-dev-archify-diagrams` | 用 Archify 将架构、数据流和流程说明生成可维护 JSON 图表及 PNG 预览。 | 🟡 |
| `soia-dev-design-draft-prd` | 起草互联网通用 PRD、产品需求文档与用户故事。 | ✅ |
| `soia-dev-design-explorer` | 基于 Open Design 做高保真原型、设计变体与评审。 | 🟡 |
| `soia-dev-drawio-visio-diagrams` | 将 Visio VSDX 安全转换、盘点和受控升级为可编辑 draw.io 图表。 | ✅ |
| `soia-dev-officecli-ops` | 以 OfficeCLI 安全读取、复制后修改并验证 DOCX、XLSX、PPTX。 | ✅ |
| `soia-dev-open-design-ops` | 提供供上层设计流程调用的 Open Design 原子操作与运行保障。 | 🟡 |

## 安装

推荐装整个领域插件，一次装好本仓全部技能：

```bash
claude plugin marketplace add soia-team/soia-open-skills
```

```bash
claude plugin install soia-dev-design@soia
```

Codex 用户：

```bash
codex plugin marketplace add soia-team/soia-open-skills
codex plugin add soia-dev-design@soia
```

只要单个技能时可用 npx 路线。注意技能会落进共享真源 `~/.agents/skills`；
若同时装了插件，同一技能会出现两份索引且各自漂移，建议二选一：

```bash
npx skills add soia-team/soia-open-dev-design-skills -g -a '*' -s <技能名> -y
```

## 生态导航

规范真源、全生态技能目录与安装指南见 [soia-team/soia-open-skills](https://github.com/soia-team/soia-open-skills)。
维护本仓技能的完整流程见 [CONTRIBUTING.md](https://github.com/soia-team/soia-open-skills/blob/main/CONTRIBUTING.md)。

## License

MIT License — see [LICENSE](./LICENSE).
