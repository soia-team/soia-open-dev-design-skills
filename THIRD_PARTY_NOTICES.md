# THIRD_PARTY_NOTICES

> Last updated: 2026-07-22
> License values are metadata snapshots. Recheck the upstream source before reuse.

## Runtime tools and third-party skills

| Upstream | License snapshot | Used by | Relationship |
|---|---|---|---|
| [nexu-io/open-design](https://github.com/nexu-io/open-design) | Apache-2.0 | `soia-dev-open-design-ops`, `soia-dev-design-explorer` | External design engine invoked at runtime. |
| [tt-a1i/archify](https://github.com/tt-a1i/archify) | MIT | `soia-dev-archify-diagrams` | External architecture diagram renderer invoked at runtime. |
| [jgraph/drawio-desktop](https://github.com/jgraph/drawio-desktop) | Apache-2.0 | `soia-dev-drawio-visio-diagrams` | Official desktop CLI used for VSDX import, draw.io conversion, and rendering. |
| `huashu-design` — [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) | MIT | `soia-dev-design-explorer` | External hard dependency installed separately; third-party skill files are not modified. |

## Workflow and capability references (no code copied)

| Upstream | License snapshot | Used by | Relationship |
|---|---|---|---|
| [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | MIT | `soia-dev-drawio-visio-diagrams` | Reference for editable `.drawio` source, CLI rendering, and verification workflow. |
| [lgazo/drawio-mcp-server](https://github.com/lgazo/drawio-mcp-server) | MIT | `soia-dev-drawio-visio-diagrams` | Optional element-level editing capability reference; no code is copied. |

## Maintenance

- Record new upstream links, install commands, or API endpoints here when a skill adds them.
- Recheck upstream licenses before reuse or redistribution.
