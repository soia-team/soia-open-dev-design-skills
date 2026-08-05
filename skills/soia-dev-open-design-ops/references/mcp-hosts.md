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
| pi | `~/.pi/agent/settings.json` | `pi --help` / `pi list` | ➖ **不支持 MCP**，见下 |
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

#### pi：不支持 MCP（2026-08-05 实测 v0.83.0）

之前误标为「格式未验证」。实际是**它没有 MCP 这个概念**，三条证据：

- `pi --help` 的子命令只有 `install / remove / uninstall / update / list / config / auth`，**没有 `mcp`**
- `~/.pi/agent/settings.json` 顶层键只有 `defaultProvider` / `defaultModel` /
  `lastChangelogVersion` / `theme` / `defaultThinkingLevel`，**没有任何 MCP 字段**
- 它的扩展机制是 `pi install npm:@foo/bar` / `git:` / `https:` / `./local` 的
  **package**，不是 MCP server

所以 pi 归类为**不适用**，与 qwen 同类，`install_od_mcp.py` 不应把它列为待安装目标。
若 pi 后续加入 MCP 支持，重新实测再改这一条。

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
