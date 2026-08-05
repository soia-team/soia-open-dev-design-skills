---
name: soia-dev-open-design-ops
description: 提供供上层设计流程调用的 Open Design 原子操作与运行保障。触发：「检查 Open Design」「接入 DESIGN.md」「恢复设计会话」
version: 1.4.0
created_at: 2026-07-20 14:16:00
updated_at: 2026-08-05 12:10:00
created_by: gpt-5.6-sol
updated_by: claude-opus-5
---

# soia-dev-open-design-ops — Open Design 原子操作层

只执行可验证的 Open Design 原子操作，不替客户做视觉方向、叙事或模板取舍。上层设计流程可把本技能作为 daemon、目录、设计系统与导出能力的底座。

## 客户可读说明

### 这个技能可以做什么

| 客户想要 | 技能会做 | 客户能看到 |
|---|---|---|
| 检查或启动 Open Design | 先判定装的是哪条路线（CLI / 桌面版 / MCP），再按路线检查 | `route` 判定、缺失项、日志位置与修复命令 |
| 给别的 agent 装 OD MCP | 按各家真实格式生成配置（键名与结构逐个实测过），默认只预览 | 每家的 diff、备份路径、验证命令 |
| 把设计同步回代码仓 | 归档 OD 产物进 `docs/design/`，并对比稿与实现的令牌漂移 | 文件清单、逐条漂移、裸色值与红线上下文 |
| 接入设计系统 | 区分正式三件套与 `DESIGN.md`-only 兼容路径，再用上游 CLI/App 接入 | 设计系统 id、来源、验证结果 |
| 查询能力目录 | 分开查询 functional skills 与 rendering templates | 名称、说明、`od.mode`/category 清单 |
| 渲染和导出 | 按上游稳定入口驱动 App/CLI，导出 HTML、PDF、PPTX 或 MP4 | 产物路径、格式语义、可打开性检查 |
| 继续已有设计会话 | 复用 daemon 保存的原生 session handle | 同一会话的 follow-up 结果或明确降级原因 |

### 客户如何使用

其他可识别说法包括「查询设计目录」「导出设计产物」；要求设计探索或评审时由上层 `soia-dev-design-explorer` 编排，本技能只执行原子操作。

1. 说明目标：环境检查、daemon、设计系统、目录查询、渲染/导出或继续会话。
2. 提供 Open Design checkout 路径；设计系统接入时再提供项目路径或 `DESIGN.md`。
3. 导出时提供 project id、项目内源文件、目标格式与输出路径；PPTX 还要说明“像素保真”还是“可编辑”。
4. Agent 先运行只读检查，再执行最小原子命令；覆盖文件、删除系统或写远端前必须单独确认。
5. 执行后检查真实 API 响应或产物，不以命令退出码代替验收。

### 依赖与安装

安装本技能：

```bash
claude plugin marketplace add soia-team/soia-open-skills
```

```bash
claude plugin install soia-dev-design@soia
```

只要这一个技能时，可用 npx 路线。注意技能会落进共享真源 `~/.agents/skills`；若同时装了插件，同一技能会出现两份索引且各自漂移，建议二选一：

```bash
npx skills add soia-team/soia-open-dev-design-skills -g -a '*' -s soia-dev-open-design-ops -y
```

#### Open Design 本体：先探测，再询问，最后才安装

**不要一上来就 clone 或 install。** 多数客户机器上 Open Design 已经在了（桌面版 App
或既有 checkout），此时一行安装命令都不该跑。按下面的顺序判断，命中即停：

1. **一条命令判定全部三条路线**（桌面版 / CLI checkout / MCP）：

   ```bash
   python3 scripts/detect_route.py
   ```

   `route` 不是 `none` 就说明已经装好了，**到此为止，一行安装命令都不要跑**。
   `desktop` / `desktop-mcp` 不需要 checkout、不需要 Node/pnpm，直接走
   「环境与 daemon」的第 3、4 小节。

2. **`route=none` 时**再看细分证据：`routes.cli.blockers` 说明 CLI 路线缺什么，
   `routes.desktop.evidence.app_bundle` 说明 App 装没装。

3. **确实两者都没有** → **先问客户，拿到明确同意再装**，并让客户自己选路线：
   桌面版 App（无需 Node/pnpm，日常使用推荐）还是源码 checkout（要参与 upstream 开发时才需要）。
   客户没答复之前，停止需要 daemon 的 workflow 并说明缺什么，不要替客户决定。

只有在客户明确选择源码路线后，才使用下面的命令。上游前置为 Node.js 24.x、pnpm 10.33.x
与 Corepack（按 upstream `QUICKSTART.md`）：

```bash
git clone https://github.com/nexu-io/open-design.git <open-design-root>
cd <open-design-root>
corepack enable
corepack pnpm --version   # upstream 当前 pin 10.33.2
pnpm install
```

本技能不安装或内嵌 Open Design，也不把 Open Design 当作另一个 agent skill。
Node/pnpm/checkout 任一缺失时，停止需要 daemon 的 workflow，并返回补齐命令——
**返回命令供客户执行，不代客户执行**。

### 私有配置

复制 `assets/config.example.yml` 到：

```text
~/.config/soia-skills/soia-dev-open-design-ops/config.yml
SOIA_DEV_OPEN_DESIGN_OPS_CONFIG_FILE=<custom-config-path>
```

至少配置 `OPEN_DESIGN_HOME`。daemon 默认绑定 loopback，端口默认 `7456`；可用 `OPEN_DESIGN_DAEMON_PORT`、`OPEN_DESIGN_WEB_PORT`、`OPEN_DESIGN_DAEMON_URL` 覆盖。项目自己的 `DESIGN.md` 路径可放 `OPEN_DESIGN_PROJECT_DESIGN_MD`。本机 checkout 与项目路径只进私有 config 或进程环境，不写进公开正文、仓库或日志。

### 私密信息与中间数据

- **凭据**：本技能不持有任何凭据。Open Design 的登录态由 App 自己管理；
  `OPEN_DESIGN_HOME`、项目路径等本机信息只进私有 `config.yml` 或进程环境，
  不写入 `SKILL.md`、日志、回执或提交。
- **端口与 socket 路径**：桌面版端口每次启动都变，`OD_SIDECAR_IPC_PATH` 含
  namespace。两者都**只在运行时探测**，不缓存、不写死进任何文件。
- **中间数据**：`detect_route.py` / `desktop_ctl.py` / `od_sync.py --check` 全部
  只读，不落盘。`install_od_mcp.py` 与 `od_sync.py --archive` 会写盘，写前展示 diff
  或文件清单，并把被覆盖的原文件备份为 `<file>.bak-od`。
- **归档产物**：`od_sync.py --archive` 只写客户明确指定的 `<repo>/docs/design/`，
  跳过 `.artifact.json` 等 OD 内部元数据；不触碰 Open Design 的数据目录。
- 落盘位置遵循本仓 `DATA_STORAGE_SPEC.md`。

### 日志与完成回执

daemon 后台日志与 PID 状态写入用户 state 目录；可用 `OPEN_DESIGN_STATE_DIR` 改位置。不得打印 config 内容或 env 值。最低回执：

```markdown
完成：<本次原子操作及结果>。

日志摘要：
- environment/daemon: <ok、missing 或 unreachable>
- processed: <系统/技能/模板/产物数量>
- created/updated: <产物或状态类别>
- skipped/failed: <数量与原因>

文件变化：<产物路径或“未改动项目文件”>
验证：<API、文件存在、页数/时长/打开检查>
问题与下一步：<缺依赖、需客户确认或“无”>
```

## 定位与边界

- 只做安装引导、daemon、目录、设计系统接入、渲染/导出和 resume 等原子操作。
- 不决定设计方向、版式、品牌语言、deck 叙事或视觉评审；这些属于 slides、visual、`soia-dev-design-explorer` 等上层流程。
- functional skill 是 agent 工作中的能力；design template 是渲染形态。不得把两类目录合并成一个列表。
- 不臆造 headless API。上游没有稳定脚本入口时，明确写“由 agent 按文档驱动 upstream App/CLI”。
- 凭据、provider 登录态和本机路径只进 provider 自有存储、私有 config 或进程环境。

## 环境与 daemon

> **入口判断先做一次，且必须先做**：本机可能装了三条彼此独立的路线——CLI 源码
> checkout、桌面版 App、MCP。装了哪条完全取决于客户怎么安装。
>
> ```bash
> python3 scripts/detect_route.py          # 人读
> python3 scripts/detect_route.py --json   # 机读，供上层分流
> ```
>
> 输出 `route` 为 `cli` / `desktop` / `desktop-mcp` / `none`，据此选择本节的对应小节：
>
> | route | 用哪节 | 不要做什么 |
> | --- | --- | --- |
> | `cli` | 1–2 | — |
> | `desktop` | 3 | **不要跑 `check_env.py` / `daemon_ctl.py`** |
> | `desktop-mcp` | 3 + 4 | 同上；优先走 4，能力最全 |
> | `none` | 按 `suggestions` 修复 | 不要硬跑任何一节 |
>
> **这一步不能省。** 只装了桌面版的机器上跑 `check_env.py` 必然返回
> `status=error`（缺 `node_24` / `pnpm_10_33` / `daemon_7456_unreachable`），
> 那是「没装 CLI 路线」的正确结论，**不是环境坏了**。把它当故障会让整条流程
> 停在一个根本不需要的前置上。

### 1. 检测环境（CLI / 源码 checkout 路线）

从本 skill 目录运行：

```bash
python3 scripts/check_env.py
```

脚本离线检查 `node`、`pnpm`、`OPEN_DESIGN_HOME` 与关键仓库文件，输出 `status`、`missing`、`checks` 和 `suggestions` JSON。Node 不是 24.x、pnpm 不是 10.33.x 时返回不兼容状态，不自动升级。

### 2. 启停与健康检查

```bash
python3 scripts/daemon_ctl.py start
python3 scripts/daemon_ctl.py status
python3 scripts/daemon_ctl.py health
python3 scripts/daemon_ctl.py stop
```

`start` 使用 upstream Quickstart 的 `pnpm tools-dev run web` 控制面，显式传 `--daemon-port`，并以 detached/nohup-style 后台进程记录 PID 与日志。不要使用已移除的 `pnpm dev`、`pnpm daemon` 或 `pnpm start` aliases。健康检查以 `GET /api/skills` 返回 `skills` 数组为准；`/api/health` 只说明进程级存活，不证明技能目录可用。

默认 URL 是 `http://127.0.0.1:7456`。只允许 loopback URL；需要远端部署、反向代理或 `0.0.0.0` 时，本技能停止并要求客户按 upstream 安全配置处理，不替客户公开本机 daemon。

### 3. 桌面版 App（与 CLI daemon 是两套，别混用）

客户装了 `/Applications/Open Design.app` 时，上面的 CLI daemon 路线基本不适用：

- **数据目录不同**：桌面版在 `~/Library/Application Support/Open Design/namespaces/<namespace>/data/`
  （`namespace` 通常是 `release-stable`），CLI 在仓库的 `.od/`。**两边互相看不见对方的项目**。
- **`od` CLI 在打包版里不进 PATH**。官方文档写 `od status`、`curl od://app/...`，但打包安装后：
  - `/usr/bin/od` 是 macOS 自带的**八进制转储工具**，直接敲 `od status` 会调错程序、报一堆无关错误；
  - `curl` 不认识 `od://` 这个 Electron 自定义 scheme，`curl -s od://app/api/health` 返回空；
  - 实测 `--daemon-url od://app` 在命令行下也解析失败（即使显式给了 `OD_SIDECAR_IPC_PATH`），
    该 scheme 目前只在 MCP sidecar 上下文里可用。

  打包版的 `od` 等价调用（实测可用）：

  ```bash
  HELPER="/Applications/Open Design.app/Contents/Frameworks/Open Design Helper.app/Contents/MacOS/Open Design Helper"
  CLI="/Applications/Open Design.app/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs"
  od(){ ELECTRON_RUN_AS_NODE=1 "$HELPER" "$CLI" "$@"; }
  ```

  **它默认打 `http://127.0.0.1:7456`（CLI daemon 的端口），对桌面版无效**，
  所以每条命令都要显式带 `--daemon-url http://127.0.0.1:<探测到的端口>`。

- **端口每次启动都变，且没有默认值**。不要写死 7456，也不要缓存上次探到的端口：

  ```bash
  lsof -nP -iTCP -sTCP:LISTEN | grep -i '^Open' | awk '{print $9}' | sed 's/.*://'
  ```

  逐个探测哪个是 daemon API（返回 `{"projects":[...]}`）；其余端口是 Next.js UI 和代理，会返回 HTML。
  这件事已脚本化，优先用它，不要每次手敲：

  ```bash
  python3 scripts/desktop_ctl.py detect      # 活着的 daemon API 端口
  python3 scripts/desktop_ctl.py projects    # 列项目，并标出谁缺 entryFile
  python3 scripts/desktop_ctl.py doctor      # 「看不到项目」一键体检
  ```

  `desktop_ctl.py` 是**只读诊断**：不改客户数据、不重启 App、不打印凭据；
  daemon 不可达时以非零退出码和明确 hint 收场，不假装正常。
- **桌面版启动会接管并停掉 CLI daemon**，所以两者不能同时用。

打包版 `od` 的等价调用、项目元数据（`entryFile` 与 `.artifact.json`）、「看不到项目」的诊断、删除本地插件要清的三处——见 [references/desktop-app.md](references/desktop-app.md)。

### 4. MCP 路线（能力最全，派 run 的唯一通路）

桌面版把自己暴露成一个 MCP server。**这是唯一能「派活给 Open Design 让它自己
生成、同时让客户在界面里全程看到」的通路**——HTTP API 只能读写文件，派不了 run。

```
start_run(project, prompt)  → 立刻返回 runId，OD 自己 spawn agent 去做
get_run(runId)              → queued|running|succeeded|failed|canceled
```

**三条硬约束，不遵守就白跑**：prompt 必须内联 `tokens.css` 全文（run 内 agent 读
`design-systems/` 是 404）；`toolBundle.mcpServers` 默认为空；实时进度只在磁盘的
`<data>/runs/<runId>/events.jsonl` 里，`get_run` 看不到。

配置形态、逐家 agent 的实测矩阵、WorkBuddy 的 UI 字段、以及上述约束的完整说明——见
[references/mcp-hosts.md](references/mcp-hosts.md)。

### 5. 把设计同步回客户代码仓

桌面版的数据目录随时可能因重装、换机或 daemon 故障而看不到，**任何要长期留存的
设计资产都必须有一份在客户自己的 git 仓库里**。更要紧的是：设计稿与生产实现会
各自漂移而没人发现——稿里 10px、实现里 13px，两边单看都不像错。

```bash
# 归档：OD 的 pages/ specs/ index.html → <repo>/docs/design/（默认预览）
python3 scripts/od_sync.py --project <id> --repo <repo-root> --archive
python3 scripts/od_sync.py --project <id> --repo <repo-root> --archive --apply

# 核对：稿 vs 实现的 :root 令牌漂移、:root 外裸色值、可选红线
python3 scripts/od_sync.py --project <id> --repo <repo-root> --check \
  --design pages/<page>.html --impl <path-in-repo> [--redlines <file>]
```

`--check` 有漂移即非零退出，可挂进 CI。

**红线扫描必须剥离注释，且只报上下文不下结论。** 写得好的代码库会在注释里写明
纪律（「绝不做完成率排名」「不显示倒计时」），不剥离注释就会把**遵守的证据**
当成违规报出来——实测某单文件应用 5 类命中里 4 类是注释；剥离后剩 2 类，其中
一类还是视频文件名。所以扫描器输出上下文供人工判定，不直接判违规。

### 6. 一个产品只开一个设计项目

不要每做一个页面就新建一个 Open Design 项目——散成一堆之后，客户改任何一页都要先想「这是哪个项目」。

推荐结构（一个项目，文件名与线上路由一一对应）：

```
<project>/
├── index.html            入口：全路由对照表，标明哪些有稿、哪些待设计
├── pages/<route>.html    每个线上路由一个页面稿
└── specs/*.md            分层设计规范（基础体系 + 各页专项）
```

新页面通过在**同一个项目**里跑 run 生成，产出落进 `pages/`，再到 `index.html` 里把它从
「待设计」挪到「已有设计稿」。旧的一次性项目在确认资产已并入后删除，别留着让客户困惑。

命令行直接在既有项目里跑 run（不经 MCP，daemon 重启后立刻可用）：

```bash
od run start --project <projectId> --agent codex \
  --message "$(cat brief.md)" --json --daemon-url "$DAEMON_URL"
od run watch <runId> --daemon-url "$DAEMON_URL"   # ND-JSON 事件流
od run info  <runId> --daemon-url "$DAEMON_URL"
```

不带 `--plugin` 时 daemon 会自行挑选（例如 `example-web-prototype`）；
需要特定模板就显式传 `--plugin <id>`（`od` 无 plugin list 子命令，用
`GET /api/plugins` 取 id）。生成通常要 5–30 分钟，轮询 `run info`，
不要因为文件 mtime 不动就取消。

**同一项目里做第二个页面，必须先开新会话**：`run start` 不带 `--conversation`
会复用项目的默认会话。上一轮的任务还在上下文里，agent 会把新 brief 当成
「继续上一轮」，回一句「当前没有新的改动请求」就正常退出——
status=succeeded、exit=0、`artifactCount: 0`、无 agentMessage，**一个文件都不写**。
先建新会话再跑：

```bash
curl -s -X POST "$DAEMON_URL/api/projects/<projectId>/conversations" \
  -H 'content-type: application/json' -d '{}'      # 返回 conversation.id
od run start --project <projectId> --conversation <newId> --agent codex \
  --message "$(cat brief.md)" --json --daemon-url "$DAEMON_URL"
```

排查时看 `<data>/runs/<runId>/events.jsonl`：agent 的文字输出在 `data.type=="text"` 的事件里。

**run 活不过 daemon 重启**：桌面版 daemon 掉线或重启后，进行中的 run 会连同记录一起消失
（`run info` 返回 `NOT_FOUND`），且不留产物。所以长 run 期间不要重启 App；
真的重启了就重新 `run start`，不要花时间找回原来那个 runId。

## 设计系统管理与项目接入

### Design System Project 三件套

新建或维护正式 Open Design Design System Project 时，以 upstream `_schema` 为源，最低契约为：

```text
<design-system-slug>/
├── manifest.json
├── DESIGN.md
└── tokens.css
```

- `manifest.json` 使用 `od-design-system-project/v1`，folder slug 与 manifest id 一致。
- `DESIGN.md` 是给 agent 的 canonical design prose；`tokens.css` 是 canonical compiled semantic tokens。
- 新系统不得把 `DESIGN.md`-only 当 authoring target。rich package 的可选文件与 token 约束以 upstream `docs/design-systems.md`、`design-systems/_schema/AGENTS.md` 和 TypeScript schema 为准。

### 包一致性校验

**内置包会自相矛盾，不能只读 `DESIGN.md` 就动手。** 冲突时的裁决优先级：

```
tokens.css  >  components.html  >  DESIGN.md / USAGE.md
```

实测证据（`warm-editorial` 的五处冲突）、内置包在磁盘上的位置、挂载与校验命令——见
[references/design-systems.md](references/design-systems.md)。

### 用户项目的 `DESIGN.md`-only 兼容接入

现有项目可先把设计规则放在 `<user-project>/DESIGN.md`。daemon 对已注册的 legacy/user-installed 目录保留 `DESIGN.md`-only discovery，但这是兼容 fallback。项目接入优先走 CLI/App 的 local import，让 daemon 扫描并建立可编辑设计系统：

```bash
node <open-design-root>/apps/daemon/dist/cli.js design-systems import-local <user-project> --name "<project-name>" --json
node <open-design-root>/apps/daemon/dist/cli.js design-systems list --json
```

首次实例可把某个真实产品项目的 `<product-project>/DESIGN.md` 配到私有 `OPEN_DESIGN_PROJECT_DESIGN_MD`，再以 `<product-project>` 执行 `import-local`；不要复制或写死维护者路径。若 `dist/cli.js` 不存在，先在 checkout 中运行 `pnpm --filter @open-design/daemon build`。

常用管理命令以 `od design-systems help` 的实际输出为准；v0.13.0 已有 list/show/rename/download/import-local/import-github/import-shadcn。rename、delete、覆盖导入或 token rebuild 影响持久状态，先展示目标与现状再确认。

## 目录查询

### Functional skills

```bash
python3 scripts/list_skills.py
python3 scripts/list_skills.py --category slides
```

脚本调用 daemon `GET /api/skills`，输出 `name`、`description`、`od.mode` 与 category；`--category` 是对 API 返回结果做本地精确过滤，因为该路由本身没有 server-side category query。

### Rendering templates

渲染模板由 `GET /api/design-templates` 与 checkout 的 `design-templates/` 提供，不属于 `/api/skills`。需要模板时用 App 的 New Project “Start from” rail 或直接查询该 API；不要用 `list_skills.py` 假装覆盖模板目录。

Deck 先在三类入口中选一类，再交给上层流程做设计决定：

- `simple-deck`：design-system 驱动、单文件、约束明确的水平 deck；
- `guizang-ppt`：电子杂志/WebGL 系，包含 Monocle、WIRED、Kinfolk、Domus、Lab 五个方向；
- `html-ppt`：HTML PPT Studio 系，提供 full-deck、theme、layout、animation 与 presenter runtime 目录。

## 渲染与导出

### 提交渲染任务

1. 在 App 选择 runtime、design template 与 design system，提交 prompt；filesystem-capable runtime 写 canonical project files，text-only/BYOK runtime 返回完整 `<artifact>`。
2. 从 App 打开项目并验证预览；或让 daemon-spawned agent 使用注入的 `OD_BIN`、`OD_DAEMON_URL`、`OD_PROJECT_ID`、`OD_PROJECT_DIR`。
3. 不直接 POST 未文档化的 chat/run payload。自动化优先使用已构建的 `od` CLI；App-only 交互由 agent 按 upstream 文档驱动。

### HTML

HTML 是 project 中的 canonical artifact。用 App Download → HTML，或读取/复制项目内源文件。v0.13.0 的 `od export` 没有 `--format html`，不得伪造该格式；项目文件 API/route 仅在确有 project id 与路径时使用。

### PDF 与 PPTX

构建 daemon CLI 后，可用 upstream v0.13.0 的稳定命令：

```bash
node <open-design-root>/apps/daemon/dist/cli.js export <project-file.html> \
  --project <project-id> --format pdf --out <output.pdf>
node <open-design-root>/apps/daemon/dist/cli.js export <deck.html> \
  --project <project-id> --format pptx --out <output.pptx>
```

内置 PPTX 是一页一张截图，适合像素保真交付，不是可编辑 shape/text deck。可编辑 PPTX 推荐链：

1. 以 HTML deck 为视觉真相源；
2. 调 functional skill `pptx-generator` 生成可编辑 `.pptx`；
3. 调 `pptx-html-fidelity-audit` 比较 HTML/PPTX，修 footer overflow、裁切、字体/italic 与节奏漂移；
4. 打开最终 PPTX，核对页数、画幅、关键文本与无越界。

### MP4

MP4 使用 HyperFrames HTML 渲染器，不冒充通用视频导出：

```bash
node <open-design-root>/apps/daemon/dist/cli.js media generate \
  --surface video --model hyperframes-html \
  --project <project-id> --composition-dir <project-relative-composition-dir> \
  --output <output.mp4>
```

composition 目录必须包含 upstream 要求的 `hyperframes.json`/`meta.json`/`index.html`。daemon 实际驱动 `npx hyperframes render`；任务排队后按 CLI 返回的 task id 使用 `od media wait`，最后验证文件存在、MIME、时长与可播放性。

## 会话 resume（v0.13.0）

Native resume 由 daemon 自动完成，不是用户手工 `od resume`：

1. 重新打开原 project 与原 conversation，不新建会话；
2. 发送 follow-up turn；
3. daemon 对支持的 runtime 复用已捕获的 native session id，使 Codex、OpenCode、Pi 与 Open Design Cloud 等 v0.13.0 支持项跨 turn 延续；
4. 检查 run 结果与 touched files，确认不是 cold start。

如果 session handle 过期、runtime 不支持或 CLI 拒绝 resume，明确报告是“resume unavailable/expired”，再由客户决定是否以历史消息重建上下文；不得把重建冒充原生 resume。daemon 重启后仍以实际 conversation/run metadata 为证据。

## 私有配置命令包装器

需要显式加载 config 执行受控 upstream 命令时：

```bash
python3 scripts/run_with_env.py -- pnpm tools-dev status
python3 scripts/run_with_env.py -- pnpm --filter @open-design/daemon build
```

包装器只允许 Corepack/pnpm 的已知 Open Design 生命周期与 build/install/version 形态；拒绝 shell、`env`、`printenv`、任意 executable 和 pnpm exec/dlx。不得用 `set -x`，不得打印 env 值。

## 安全守则

1. daemon 是本机特权服务，默认只绑定 `127.0.0.1`；不得为了方便暴露公网端口。
2. 不打印 config、env、provider 凭据或 daemon 注入的 token；日志只说明存在/缺失。
3. stop 只处理本技能记录的 PID；PID 不匹配或状态不明时停止并报告，不猜进程。
4. import、rename、delete、download overwrite、export overwrite 前查看目标现状；删除和覆盖必须获得当前请求的明确授权。
5. 不修改 `OPEN_DESIGN_HOME` 里的 upstream 源码来“接通”项目；本技能只读查询或按官方 CLI/App 操作。

## 验收

- 环境：`check_env.py` 返回 `status=ok`，无 missing。
- daemon：`daemon_ctl.py health` 验证 `/api/skills` 返回数组。
- 目录：skills 与 templates 分开取数；category 过滤结果全部匹配。
- 设计系统：三件套齐全，或明确标为 `DESIGN.md`-only compatibility；import 后能 list/show。
- 导出：目标文件存在、非空、格式可打开；PDF/PPTX 核页数，MP4 核时长和可播放。
- resume：同一 project/conversation 的 follow-up 有 native resume 证据；无证据时不得声称成功。
