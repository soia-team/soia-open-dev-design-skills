# SOIA Design & Document Skills

[中文](README.md) · English

Turn requirements into something you can look at: PRDs, prototypes, architecture diagrams, Office files — all editable, not screenshots.

## What this is

`soia-open-dev-design-skills` covers the design and document pipeline from requirement to deliverable:

```text
One-line idea
    ↓
PRD (scope, user stories, acceptance criteria)
    ↓
Prototype / diagram (Open Design hi-fi · Archify architecture · draw.io flows)
    ↓
Office artifacts (DOCX / XLSX / PPTX, editable and validated)
```

Every diagram is an **editable source file** (JSON, drawio, OpenXML), not a one-off screenshot — you can revise it, reuse it, and keep it under version control.

### When to use it

- "Turn this idea into a PRD we can review."
- "Draw an architecture diagram for this system."
- "Convert my pile of Visio files into editable draw.io diagrams."
- "Build a hi-fi prototype so I can see it."
- "Edit this spreadsheet without breaking the formatting."

### What it does not do

- No visual brand design. Palettes, logos, and brand guidelines are out of scope.
- Not a replacement for a designer. Output is a reviewable draft and editable source, not a final visual.
- Never edits original Office files in place. It copies first, then modifies, then validates OpenXML.
- No social-media formatting or publishing — see [soia-open-media-content-skills](https://github.com/soia-team/soia-open-media-content-skills).

## Where to start

| Your task | Use | Done when |
|---|---|---|
| Write an idea up as a PRD | `soia-dev-design-draft-prd` | Scope, user stories, acceptance criteria present |
| Draw architecture or sequence diagrams | `soia-dev-archify-diagrams` | Maintainable JSON plus PNG preview |
| Convert Visio to editable diagrams | `soia-dev-drawio-visio-diagrams` | drawio source is re-editable |
| Build a hi-fi prototype | `soia-dev-design-explorer` | HTML prototype with design review notes |
| Edit Word/Excel/PowerPoint | `soia-dev-officecli-ops` | Copy-then-modify, OpenXML validation passes |

Skills marked 🟡 need external tooling such as Open Design or Archify; each checks and reports what is missing before running.

## Skill catalog

> **Ready to use**: ✅ works right after install · 🟡 needs an API key or a third-party login first

| Skill | Responsibility | Ready to use |
|---|---|---|
| `soia-dev-archify-diagrams` | Generate maintainable architecture, data-flow, and process diagrams with Archify and PNG previews. | 🟡 |
| `soia-dev-design-draft-prd` | Draft general-purpose PRDs, product requirement documents, and user stories from a one-line idea. | ✅ |
| `soia-dev-design-explorer` | Explore high-fidelity HTML prototypes, design variants, slides, and animation with Open Design. | 🟡 |
| `soia-dev-drawio-visio-diagrams` | Safely convert, inventory, and upgrade Visio VSDX files into editable draw.io diagrams. | ✅ |
| `soia-dev-officecli-ops` | Safely read, copy-edit, and validate DOCX, XLSX, and PPTX files with OfficeCLI. | ✅ |
| `soia-dev-open-design-ops` | Manage Open Design environments, project onboarding, resource queries, exports, and session recovery. | 🟡 |

## Trigger phrases

Once installed, just speak naturally — the agent routes to a skill by these phrases (the full trigger list lives in each skill's `SKILL.md` `description`).

> Trigger phrases are listed in the language the skill actually matches on. Most are Chinese because that is what these skills were written to recognize; describing the same intent in English works too — the agent matches on meaning, not on the literal string.

| You say | Skill |
|---|---|
| `用 Archify 画` / `Archify 架构图` / `Archify 时序图` | `soia-dev-archify-diagrams` |
| `VSDX 转 draw.io` / `Visio 图表升级` / `draw.io 图表盘点` | `soia-dev-drawio-visio-diagrams` |
| `OfficeCLI` / `OpenXML 验证` / `Office 文件原子修改` | `soia-dev-officecli-ops` |
| `检查 Open Design` / `接入 DESIGN.md` / `恢复设计会话` | `soia-dev-open-design-ops` |

## Install

Installing the whole domain plugin is recommended — it brings every skill in this repo:

```bash
claude plugin marketplace add soia-team/soia-open-skills
```

```bash
claude plugin install soia-dev-design@soia
```

For Codex:

```bash
codex plugin marketplace add soia-team/soia-open-skills
codex plugin add soia-dev-design@soia
```

For a single skill you can use the npx route. Note the skill lands in the shared
source `~/.agents/skills`; if the plugin is installed too, the same skill shows up
twice and the two copies drift apart — pick one:

```bash
npx skills add soia-team/soia-open-dev-design-skills -g -a '*' -s <skill-name> -y
```

## Validate & contribute

After changing a skill, run before committing:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/generate_skill_catalog.py --check
python3 scripts/audit_skills.py --strict
```

Contribution flow, the skill contract, and release steps are in the portal's
[CONTRIBUTING.md](https://github.com/soia-team/soia-open-skills/blob/main/CONTRIBUTING.md).

## Ecosystem

Specifications, the full ecosystem catalog, and install guides live in [soia-team/soia-open-skills](https://github.com/soia-team/soia-open-skills).
The full maintenance workflow is in [CONTRIBUTING.md](https://github.com/soia-team/soia-open-skills/blob/main/CONTRIBUTING.md).

## License

MIT License — see [LICENSE](./LICENSE).
