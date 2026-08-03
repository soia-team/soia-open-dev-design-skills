#!/usr/bin/env python3
"""Open Design 桌面版 App 的只读诊断入口。

桌面版每次启动都会换端口，且 UI / daemon / 代理各占一个，靠人肉 lsof 逐个试很费事。
本脚本只做探测与诊断，不改客户数据、不重启 App、不打印任何凭据。

用法：
    python3 scripts/desktop_ctl.py detect      # 找出活着的 daemon API 端口
    python3 scripts/desktop_ctl.py projects    # 列项目（含 entryFile 是否配好）
    python3 scripts/desktop_ctl.py doctor      # 「看不到项目」时的一键体检
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

APP_SUPPORT = os.path.expanduser("~/Library/Application Support/Open Design")
DEFAULT_NAMESPACE = "release-stable"
TIMEOUT = 4


def data_dir(namespace: str = DEFAULT_NAMESPACE) -> str:
    return os.path.join(APP_SUPPORT, "namespaces", namespace, "data")


def listening_ports() -> list[int]:
    """桌面版进程当前监听的本地端口（去重、有序）。"""
    try:
        out = subprocess.run(
            ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    ports: list[int] = []
    for line in out.splitlines():
        if not re.match(r"^Open", line, re.I):
            continue
        match = re.search(r":(\d+)\s*\(LISTEN\)", line)
        if match:
            port = int(match.group(1))
            if port not in ports:
                ports.append(port)
    return ports


def probe(port: int) -> dict | None:
    """返回 /api/projects 的 JSON；不是 daemon API 就返回 None。"""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/projects", timeout=TIMEOUT
        ) as reply:
            body = reply.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError):
        return None
    if not body.lstrip().startswith(("{", "[")):
        return None  # Next.js UI 会返回 HTML
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) and "projects" in parsed else None


def detect() -> tuple[int | None, list[int]]:
    ports = listening_ports()
    for port in ports:
        if probe(port) is not None:
            return port, ports
    return None, ports


def orphan_dirs(namespace: str) -> list[str]:
    """磁盘上有目录、但库里没有记录的项目（daemon 建到一半崩溃的残骸）。"""
    projects_dir = os.path.join(data_dir(namespace), "projects")
    if not os.path.isdir(projects_dir):
        return []
    known: set[str] = set()
    port, _ = detect()
    if port is not None:
        payload = probe(port) or {}
        known = {str(item.get("id")) for item in payload.get("projects", [])}
    if not known:
        return []
    return sorted(
        name for name in os.listdir(projects_dir)
        if os.path.isdir(os.path.join(projects_dir, name)) and name not in known
    )


def cmd_detect(args: argparse.Namespace) -> int:
    port, ports = detect()
    print(json.dumps({
        "daemon_api_port": port,
        "listening_ports": ports,
        "data_dir": data_dir(args.namespace),
        "status": "ok" if port else "daemon-unreachable",
    }, ensure_ascii=False, indent=1))
    return 0 if port else 1


def cmd_projects(args: argparse.Namespace) -> int:
    port, _ = detect()
    if port is None:
        print(json.dumps({"status": "daemon-unreachable",
                          "hint": "重启 Open Design App；数据都在磁盘上，没有丢失"},
                         ensure_ascii=False, indent=1))
        return 1
    rows = []
    for item in (probe(port) or {}).get("projects", []):
        metadata = item.get("metadata") or {}
        rows.append({
            "id": item.get("id"),
            "name": item.get("name"),
            # entryFile 埋在 metadata 里；缺它则项目卡片没有预览
            "entryFile": metadata.get("entryFile"),
            "renders": bool(metadata.get("entryFile")),
        })
    print(json.dumps({"status": "ok", "port": port, "projects": rows},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    port, ports = detect()
    root = data_dir(args.namespace)
    findings: list[str] = []
    if port is None:
        findings.append(
            "daemon API 没有响应：UI 可能还活着，所以界面能开但项目列表空白。"
            "重启 Open Design App 即可，数据都在磁盘上。"
        )
    if not os.path.isdir(root):
        findings.append(f"数据目录不存在：{root}（namespace 是否写对？）")
    orphans = orphan_dirs(args.namespace) if port else []
    for name in orphans:
        path = os.path.join(root, "projects", name)
        empty = os.path.isdir(path) and not os.listdir(path)
        findings.append(
            f"孤儿项目目录 {name}（{'空目录，可删' if empty else '有内容，先人工确认再处理'}）"
        )
    missing_entry = []
    if port:
        for item in (probe(port) or {}).get("projects", []):
            if not (item.get("metadata") or {}).get("entryFile"):
                missing_entry.append(item.get("name"))
    for name in missing_entry:
        findings.append(f"项目「{name}」没有 metadata_json.entryFile，卡片不会有预览")
    print(json.dumps({
        "status": "ok" if port and not findings else "attention",
        "daemon_api_port": port,
        "listening_ports": ports,
        "data_dir": root,
        "logs_dir": os.path.join(APP_SUPPORT, "namespaces", args.namespace, "logs"),
        "findings": findings or ["未发现问题"],
    }, ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Open Design 桌面版只读诊断")
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("detect", help="找出活着的 daemon API 端口")
    subparsers.add_parser("projects", help="列项目并检查 entryFile")
    subparsers.add_parser("doctor", help="「看不到项目」体检")
    args = parser.parse_args()
    return {"detect": cmd_detect, "projects": cmd_projects, "doctor": cmd_doctor}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
