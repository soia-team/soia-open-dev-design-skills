# MCP 各宿主的配置形态与实测矩阵

> 主文件「环境与 daemon → 4. MCP 路线」的展开：配置形态、逐家实测结果、派 run 的硬约束。

#### 配置形态

不走网络端口，而是用 Electron Helper 以 Node 模式跑打包内的 `daemon-cli.mjs mcp`：

```json
"open-design": {
  "command": "/Applications/Open Design.app/Contents/Frameworks/Open Design Helper.app/Contents/MacOS/Open Design Helper",
  "args": ["/Applications/Open Design.app/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs", "mcp"],
  "env": {
    "OD_DATA_DIR": "<APP_SUPPORT>/namespaces/<namespace>/data",
    "OD_SIDECAR_IPC_PATH": "/tmp/open-design/ipc/<namespace>/daemon.sock",
    "ELECTRON_RUN_AS_NODE": "1"
  }
}
```

`OD_SIDECAR_IPC_PATH` 正是「`od://` scheme 只在 MCP sidecar 上下文里可用」的原因。
`namespace` 要从 `detect_route.py` 的输出取，不要写死 `release-stable`。

**装 MCP 不能靠客户端 UI。** Claude 桌面版的 Add custom connector 只接受
`Remote MCP server URL`，本地 stdio server 加不进去；那个 Connectors 菜单列的是
托管型连接器，本地 server 不会出现在里面。只能写配置文件或用 `claude mcp add`。
用 `install_od_mcp.py` 处理各家格式差异。

#### 实测矩阵（2026-08-05）

**只写实际跑过的，未验证的一律标未验证。** 证据强度分三级：
配置被解析 < 连接握手成功 < 工具调用返回真实数据。

| Agent | 配置落点与键名 | 验证命令 | 结果 |
| --- | --- | --- | --- |
| Claude Code | `~/.claude.json` → `mcpServers` | `claude mcp list` | ✅ **工具调用**（本会话全程在用） |
| codex | `~/.codex/config.toml` → `[mcp_servers.x]` + `[.env]` | `codex mcp list` / `get` / `exec` | ✅ **工具调用**：`mcp: open-design/list_projects started → (completed)`，返回 5 个项目 id |
| opencode | `~/.config/opencode/opencode.json` → **`mcp`**（非 `mcpServers`） | `opencode mcp list` | ✅ **连接握手**：状态 `connected`；未取得工具调用输出 |
| cursor | `~/.cursor/mcp.json` → `mcpServers` | 未验证 | ⬜ 格式已核对（与 Claude 同构），**未装未测** |
| WorkBuddy | **UI 配置**（插件 → MCP → Add），非配置文件 | 客户端界面 | ⬜ 参数已核对，**脚本不适用**——见下 |
| pi | `~/.pi/agent/mcp.json`（装 `pi-mcp-adapter` 后）→ `mcpServers` | `pi -p "调用 open-design MCP 的 list_projects..." --mode text` | ✅ **工具调用**：返回 5 个真实项目 id，见下 |
| qwen | `settings.json` 无 MCP 键 | — | ➖ 不适用（`shells/init-mcp.sh` 是改 Claude 配置的工具，非自身 MCP） |

两条来自实测的要点：

- **opencode 的 `env` 走 `/usr/bin/env` 前缀注入**（它的条目结构是 argv 数组 + `type`/`enabled`，
  未见 env 字段）。这个方案已验证可连：`opencode mcp list` 显示 `✓ connected`，
  且同列表中 `pencil` 显示 `✗ failed ENOENT`，证明该状态是真实探测而非静态回显。
- **codex 的 `Status: enabled` 只是配置状态，不代表连得上。** 要确证必须让它真跑一次：

  ```bash
  codex exec --skip-git-repo-check "调用 open-design MCP 的 list_projects，原样列出项目 id"
  ```

  输出里出现 `mcp: open-design/list_projects (completed)` 才算数。

回退：脚本写入前会备份成 `<配置文件>.bak-od`，或用各家自带命令移除
（如 `codex mcp remove open-design`）。

#### pi：核心不带 MCP，装 `pi-mcp-adapter` 扩展后可用（2026-08-05 实测 v0.83.0）

**pi 核心本身没有 MCP 概念**，这条结论没变：`pi --help` 的子命令只有
`install / remove / uninstall / update / list / config / auth`，没有 `mcp`；
默认的 `~/.pi/agent/settings.json` 也没有任何 MCP 字段。

但它的扩展机制（`pi install npm:@foo/bar`）里有个现成的第三方包能补上这一层：

```bash
pi install npm:pi-mcp-adapter
```

装完后 `settings.json.packages` 里多一条 `"npm:pi-mcp-adapter"`，`pi` 启动时会加载它，
并新建 `~/.pi/agent/mcp.json` 作为 pi 自己的 MCP 注册表，结构是：

```json
{ "mcpServers": {}, "imports": [] }
```

`mcpServers` 这一层和 claude-code/cursor 同构（`mcpServers.<name> = {command, args, env}`），
可以直接复用本文档开头那段配置形态原样写进去。

**不要用 `pi-mcp-adapter init` 的 imports 模式。** 这条命令会扫描本机 cursor / claude-code /
claude-desktop / codex / opencode 五个宿主，把它们**全部**已配置的 MCP server 借过来写进
`imports` 字段，而不是只借 open-design 这一条。实测踩过的坑：

- codex 里 `[mcp_servers.computer-use]` 本来就是 `enabled = false`（codex 自己都没启用），
  且 `command` 是相对路径 `./Codex Computer Use.app/...` + `cwd = "."`——codex 启动时会把
  cwd 切到 `~/.codex/computer-use/` 才能解析。import 机制照抄了 command 和 cwd，**既不尊重
  `enabled=false` 开关，也没保留 codex 的 cwd 上下文**，在 pi 里必然 `spawn ... ENOENT`。
- cursor 和 opencode 都定义了名为 `pencil` 的 server 但路径完全不同（分别指向
  `~/.qoder/extensions/...` 和 `~/.pencil/mcp/...`），**同名冲突**，import 合并后用到坏的那个。
- cursor 的 `claude-mem`（一个 node 脚本）通过 import 起了但连接被对方关闭，
  没有单独验证是脚本本身的问题还是缺上下文。

正确做法是清空 `imports`，只在 `mcpServers` 里直接定义 open-design，和 codex/opencode 那两条
路线保持同一种模式（各家独立配置各自需要的 server，不整体互相借用）：

```json
{
  "mcpServers": {
    "open-design": {
      "command": "/Applications/Open Design.app/Contents/Frameworks/Open Design Helper.app/Contents/MacOS/Open Design Helper",
      "args": ["/Applications/Open Design.app/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs", "mcp"],
      "env": {
        "OD_DATA_DIR": "<APP_SUPPORT>/namespaces/<namespace>/data",
        "OD_SIDECAR_IPC_PATH": "/tmp/open-design/ipc/<namespace>/daemon.sock",
        "ELECTRON_RUN_AS_NODE": "1"
      }
    }
  },
  "imports": []
}
```

验证用非交互模式（`--print`/`-p`），不用进 TUI：

```bash
pi -p "调用 open-design MCP 的 list_projects 工具，只输出它返回的原始项目列表" --mode text
```

实测输出是 5 个真实项目 id/name（与 codex 那条验证拿到的一致），达到矩阵里最高一级证据
（工具调用返回真实数据），不是配置解析或握手成功这两级。

#### WorkBuddy：UI 配置，脚本不适用

WorkBuddy 在客户端里配 MCP（插件 → MCP → Add），**没有可写的配置文件落点**，
所以 `install_od_mcp.py` 对它只打印不写。界面要填的字段与对应值：

| 界面字段 | 填什么 | 能不能写死 |
| --- | --- | --- |
| 启动命令 | `…/Open Design Helper.app/Contents/MacOS/Open Design Helper` | 可以（App 安装路径固定） |
| 参数 1 | `…/app/prebundled/daemon/daemon-cli.mjs` | 可以 |
| 参数 2 | `mcp` | 可以 |
| `ELECTRON_RUN_AS_NODE` | `1` | **必填固定值**。缺了它 Helper 会以 GUI 模式启动，MCP 起不来 |
| `OD_DATA_DIR` | `<APP_SUPPORT>/namespaces/<namespace>/data` | **不能写死**，`namespace` 随安装变 |
| `OD_SIDECAR_IPC_PATH` | `/tmp/open-design/ipc/<namespace>/daemon.sock` | **不能写死**，同上 |
| 环境变量传递 | 留空 | — |
| **工作目录** | **留空** | OD MCP 通过 IPC socket 连 daemon，不依赖 cwd。实测佐证：codex 的 `cwd: -`、opencode 未设 cwd，两者均连通且 codex 完成了工具调用 |

两个 `<namespace>` 用 `detect_route.py --json` 的 `routes.mcp.evidence.ipc_sockets`
取，不要照抄本文里的 `release-stable`。

查当前装了没（Claude Code）：

```bash
claude mcp list
```

#### 派 run 的契约

```
start_run(project, prompt)  → 立刻返回 runId，OD 自己 spawn agent 去做
get_run(runId)              → queued|running|succeeded|failed|canceled
```

三条实测教训：

1. **prompt 里必须内联 `tokens.css` 全文。** run 内的 agent 读
   `design-systems/<id>/` 会拿到 404，它看不到挂载的设计系统文件。只在 prompt 里
   写「请遵守 Warm Editorial」是不够的——agent 只能靠猜或反推。可行的替代是让它
   参考项目里一个已经正确应用了该系统的页面。
2. **`toolBundle.mcpServers` 默认是空的**，run 内的 agent 只有 Bash/Read/Write，
   没有任何 MCP 工具。要给它加，得在 OD 界面「集成 → 外部 MCP 服务器」配置
   （落在 `.od/mcp-config.json`）。这个方向和上面那个 MCP 是**反的**：那里 OD 是
   客户端，这里 OD 是服务端，别混。
3. **实时进度不在 API 里，在磁盘上。** `get_run` 只给状态，看不到 agent 在干什么。
   要「打印」就 tail 事件流：

   ```bash
   tail -f "<data>/runs/<runId>/events.jsonl"
   ```

   事件形如 `{"id","event","data","timestamp"}`；`event` 为 `pipeline_stage_started`
   / `pipeline_stage_completed` / `agent`（`data.type` 再分 `tool_use` / `tool_result`
   / `text`）/ `diagnostic` / `error`。这是四种官方入口都没提供的能力。

一次 run 通常 5–30 分钟。**文件 mtime 长时间不变是 agent 在思考，不是卡死**，
不要因此 `cancel_run`，更不要改用 `write_file` 自己把设计写了——那样就绕过了
OD 的生成管线，产出质量和「派给 OD」不是一回事。
