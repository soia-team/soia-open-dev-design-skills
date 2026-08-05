#!/usr/bin/env python3
"""判定本机该走哪条 Open Design 接入路线。

存在的理由：同一台机器上「CLI 源码 checkout」「桌面版 App」「MCP」是三条彼此
独立的路线，装了哪条完全看客户怎么安装。上层技能如果不先判定就直接跑
`check_env.py`（那是 CLI 路线的检查），在只装了桌面版的机器上必然拿到
`status=error`，从而误判成「环境坏了」而停下——实际上桌面版 + MCP 都是好的。

本脚本只探测、不修改：不启停 daemon、不改任何 agent 配置、不打印凭据。

用法：
    python3 scripts/detect_route.py            # 人读摘要
    python3 scripts/detect_route.py --json     # 机读，供上层技能分流

退出码：
    0  至少一条路线可用
    1  三条都不可用（此时 suggestions 给出修复方向）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_env  # noqa: E402
import desktop_ctl  # noqa: E402

APP_BUNDLE = "/Applications/Open Design.app"
HELPER = (
    f"{APP_BUNDLE}/Contents/Frameworks/Open Design Helper.app"
    "/Contents/MacOS/Open Design Helper"
)
DAEMON_CLI = f"{APP_BUNDLE}/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs"
IPC_ROOT = "/tmp/open-design/ipc"

# 各家 agent 的 MCP 落点。**键名与条目结构逐个实测过，不要按 Claude 的格式套**：
#   json-claude   mcpServers.<name> = {command: str, args: [...], env: {...}}
#   json-opencode mcp.<name>        = {command: [argv...], type: "local", enabled: bool}
#                 —— command 是 argv 数组而非字符串，且未见 env 字段
#   toml-codex    [mcp_servers.<name>] command/args + [mcp_servers.<name>.env]
#   unknown       结构没验证过，只报告、不自动写
#
# pi (v0.83.0) 无 mcp 子命令、settings.json 无 MCP 字段，扩展机制是 package 而非
# MCP server，故同样不列为目标。qwen 的 ~/.qwen/settings.json 里没有任何 MCP 键；~/.qwen/shells/init-mcp.sh 是个
# 改 ~/.claude/settings.json 的管理脚本，不是 qwen 自己的 MCP 配置，故不列为目标。
AGENT_CONFIGS: tuple[tuple[str, str, str, str], ...] = (
    ("claude-code", "~/.claude.json", "json-claude", "mcpServers"),
    ("codex", "~/.codex/config.toml", "toml-codex", "mcp_servers"),
    ("cursor", "~/.cursor/mcp.json", "json-claude", "mcpServers"),
    ("opencode", "~/.config/opencode/opencode.json", "json-opencode", "mcp"),
    ("workbuddy", "~/.workbuddy", "unknown", ""),
)


def probe_cli() -> dict[str, Any]:
    """CLI / 源码 checkout 路线：要 checkout + Node 24 + pnpm 10.33 + 7456 端口。"""
    env = check_env.check_environment()
    blockers = list(env.get("missing") or [])
    daemon_up = desktop_ctl.probe(7456) is not None
    if not daemon_up:
        blockers.append("daemon_7456_unreachable")
    return {
        "available": env.get("status") == "ok" and daemon_up,
        "evidence": {
            "check_env_status": env.get("status"),
            "daemon_7456": daemon_up,
        },
        "blockers": blockers,
    }


def probe_desktop() -> dict[str, Any]:
    """桌面版路线：App 装了、数据目录在、daemon API 端口活着。"""
    port, ports = desktop_ctl.detect()
    namespaces: list[str] = []
    ns_root = os.path.join(desktop_ctl.APP_SUPPORT, "namespaces")
    if os.path.isdir(ns_root):
        namespaces = sorted(
            n for n in os.listdir(ns_root) if os.path.isdir(os.path.join(ns_root, n))
        )
    return {
        "available": bool(port),
        "evidence": {
            "app_bundle": os.path.isdir(APP_BUNDLE),
            "api_port": port,
            "listening_ports": ports,
            "namespaces": namespaces,
        },
        # 端口每次启动都变，别把它写进任何配置或文档
        "blockers": [] if port else ["no_live_daemon_api_port"],
    }


def _json_has_open_design(path: str, mcp_key: str) -> bool | None:
    """在 JSON 配置的 MCP 段里精确查 open-design；解析失败返回 None。

    mcp_key 因 agent 而异（Claude/Cursor 是 mcpServers，opencode 是 mcp），
    传错键名会把「未配」误判成「已配」或反之。
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    found = False

    def walk(node: Any) -> None:
        nonlocal found
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            # 只认该 agent 自己的 MCP 注册表，别处出现同名字符串一律不算
            if key == mcp_key and isinstance(value, dict):
                if any("open-design" in name for name in value):
                    found = True
            walk(value)

    walk(data)
    return found


def _toml_has_open_design(path: str) -> bool | None:
    """TOML 只认 [mcp_servers.<name>] 段；解析失败或无 tomllib 返回 None。"""
    try:
        import tomllib
    except ModuleNotFoundError:
        return None
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, ValueError):
        return None
    servers = data.get("mcp_servers")
    if not isinstance(servers, dict):
        return False
    return any("open-design" in name for name in servers)


def probe_mcp() -> dict[str, Any]:
    """MCP 路线：sidecar 可执行文件在不在，哪些 agent 已经配了 open-design。

    注意两点：
    1. 本脚本探测的是「配置里装没装」。当前这个 agent 手里到底有没有
       mcp__open-design__* 工具，只有它自己知道——脚本无法代答。
    2. 判定必须按格式解析到 MCP 注册表那一段。裸用子串匹配会被骗：codex 的
       config.toml 里有 [projects."…/upstream/open-design"]，那是项目路径，
       不是 MCP 配置，子串匹配会误报「已配」。
    """
    sockets: list[str] = []
    if os.path.isdir(IPC_ROOT):
        for ns in sorted(os.listdir(IPC_ROOT)):
            sock = os.path.join(IPC_ROOT, ns, "daemon.sock")
            if os.path.exists(sock):
                sockets.append(sock)

    agents: dict[str, dict[str, Any]] = {}
    for name, raw_path, fmt, mcp_key in AGENT_CONFIGS:
        path = os.path.expanduser(raw_path)
        exists = os.path.exists(path)
        configured: bool | None = False
        if exists and os.path.isfile(path):
            if fmt.startswith("json"):
                configured = _json_has_open_design(path, mcp_key)
            elif fmt.startswith("toml"):
                configured = _toml_has_open_design(path)
            else:
                configured = None  # 格式没验过，不猜
        elif exists:
            configured = None  # 是目录，落点未知
        agents[name] = {
            "config": raw_path,
            "format": fmt,
            "mcp_key": mcp_key,
            "installed": exists,
            # None = 无法判定，不要当成「未配」去覆盖客户配置
            "has_open_design": configured,
        }

    launchable = os.path.exists(HELPER) and os.path.exists(DAEMON_CLI)
    return {
        "available": launchable,
        "evidence": {
            "helper": os.path.exists(HELPER),
            "daemon_cli": os.path.exists(DAEMON_CLI),
            "ipc_sockets": sockets,
            "agents": agents,
        },
        "blockers": [] if launchable else ["mcp_sidecar_binary_missing"],
    }


def decide() -> dict[str, Any]:
    routes = {"cli": probe_cli(), "desktop": probe_desktop(), "mcp": probe_mcp()}

    # 优先级来自实测：MCP 能派 run 且能读写项目文件，桌面版 HTTP API 次之，
    # CLI 在打包安装的机器上基本用不上（od 不进 PATH）。
    if routes["mcp"]["available"] and routes["desktop"]["available"]:
        route = "desktop-mcp"
    elif routes["desktop"]["available"]:
        route = "desktop"
    elif routes["cli"]["available"]:
        route = "cli"
    else:
        route = "none"

    suggestions: list[str] = []
    if route == "none":
        if not routes["desktop"]["evidence"]["app_bundle"]:
            suggestions.append("装 Open Design 桌面版，或准备 CLI 源码 checkout。")
        else:
            suggestions.append("桌面版已装但 daemon API 不可达：重启 App 即可，数据都在磁盘上。")
    if route in ("desktop", "desktop-mcp"):
        suggestions.append("不要跑 check_env.py / daemon_ctl.py，那是 CLI 路线的检查。")
    agents = routes["mcp"]["evidence"]["agents"]
    missing = [n for n, i in agents.items() if i["installed"] and i["has_open_design"] is False]
    unknown = [n for n, i in agents.items() if i["installed"] and i["has_open_design"] is None]
    if missing:
        suggestions.append(
            "这些 agent 装了但没配 open-design MCP："
            + "、".join(missing)
            + "；用 install_od_mcp.py 补。"
        )
    if unknown:
        suggestions.append(
            "这些 agent 的配置格式还没验证过，装之前必须先打开看："
            + "、".join(unknown)
            + "；不要照 Claude Code 的 JSON 格式硬套。"
        )
    return {"route": route, "routes": routes, "suggestions": suggestions}


def render(result: dict[str, Any]) -> str:
    lines = [f"route = {result['route']}", ""]
    for name, info in result["routes"].items():
        mark = "✓" if info["available"] else "✗"
        lines.append(f"{mark} {name}")
        for key, value in info["evidence"].items():
            if key == "agents":
                for agent, meta in value.items():
                    if not meta["installed"]:
                        continue
                    flag = {True: "已配", False: "未配", None: "格式未验"}[
                        meta["has_open_design"]
                    ]
                    lines.append(f"      {agent:<12} {flag:<6}{meta['config']}")
            else:
                lines.append(f"      {key}: {value}")
        if info["blockers"]:
            lines.append(f"      blockers: {', '.join(info['blockers'])}")
    if result["suggestions"]:
        lines.append("")
        for item in result["suggestions"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="判定 Open Design 接入路线")
    parser.add_argument("--json", action="store_true", help="输出 JSON 供上层技能分流")
    args = parser.parse_args()

    result = decide()
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 0 if result["route"] != "none" else 1


if __name__ == "__main__":
    raise SystemExit(main())
