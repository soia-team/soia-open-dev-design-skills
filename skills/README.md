# SOIA Open Skills Catalog

> Generated from `skills/*/SKILL.md` and optional `agents/openai.yaml`.
> Do not edit by hand. Run `python3 scripts/generate_skill_catalog.py`.
> Discoverable by `npx skills add soia-team/soia-open-dev-design-skills -l`: 6 skills.

## Source Fields

- `SKILL.md` is the canonical cross-agent instruction file. Capabilities, dependencies, setup, workflow steps, logs, and completion summaries must live there.
- `agents/openai.yaml` is optional UI/catalog metadata for OpenAI/Codex-style surfaces and SOIA registry display: `display_name`, `short_description`, and `default_prompt`.
- Claude Code and generic skills.sh-compatible agents must be assumed to consume `SKILL.md`; do not put required workflow steps only in `agents/openai.yaml`.
- Legacy `metadata.json` files are not used to generate this catalog.

## Development

| Skill | Description | Default Prompt |
|---|---|---|
| [`soia-dev-archify-diagrams`](./soia-dev-archify-diagrams/) | Create architecture and workflow diagrams with Archify. | Use soia-dev-archify-diagrams to create or update technical diagrams with JSON IR, validated HTML, and README PNG previews. Ask for or infer the delivery directory, pass --output-dir explicitly for repository/proposal outputs, and use ~/Downloads/soia-dev-archify-diagrams/ only as the safe default. |
| [`soia-dev-design-draft-prd`](./soia-dev-design-draft-prd/) | 将一句话产品想法整理为可评审的互联网通用 PRD。 | 为 ExampleCorp 的示例产品起草 PRD：帮助新用户完成首次任务。 |
| [`soia-dev-design-explorer`](./soia-dev-design-explorer/) | Create and verify hi-fi prototypes, decks, animations, and design reviews | Use $soia-dev-design-explorer with soia-dev-open-design-ops checks, user-provided brand inputs, a classified output destination, and verifiable delivery evidence. |
| [`soia-dev-drawio-visio-diagrams`](./soia-dev-drawio-visio-diagrams/) | 读取 VSDX，转换、理解并升级为可编辑 draw.io 图表。 | Use $soia-dev-drawio-visio-diagrams to inspect this VSDX safely, convert it into an editable draw.io source, apply requested upgrades without overwriting the original, and validate exported artifacts. |
| [`soia-dev-officecli-ops`](./soia-dev-officecli-ops/) | 安全读取、修改并验证 Word、Excel 和 PowerPoint 文件。 | 检查这个 Office 文件，先给出问题和修改计划；我确认后在副本上修复并完成验证。 |
| [`soia-dev-open-design-ops`](./soia-dev-open-design-ops/) | Operate Open Design daemon, catalogs, design systems, exports, and session resume | Use $soia-dev-open-design-ops to check my Open Design environment, start the local daemon safely, query real catalogs, and run a source-backed export or resume workflow. |

## Registry Export

Generate v7 SOIA registry manifests from the same sources when needed:

```bash
python3 scripts/generate_skill_catalog.py --registry-out <soia-repo>/runtime/registry/skills
```
