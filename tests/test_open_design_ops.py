#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "soia-dev-open-design-ops" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_env  # noqa: E402
import daemon_ctl  # noqa: E402
import desktop_ctl  # noqa: E402
import list_skills  # noqa: E402


def load_run_with_env():
    name = "open_design_ops_run_with_env"
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / "run_with_env.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load run_with_env.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


run_with_env = load_run_with_env()


class CheckEnvTests(unittest.TestCase):
    def test_missing_node_fails_closed(self) -> None:
        def which(name: str) -> str | None:
            return None if name == "node" else "/tool/pnpm"

        with mock.patch.dict(os.environ, {"OPEN_DESIGN_HOME": "/checkout"}, clear=True), mock.patch.object(
            check_env, "load_private_env"
        ), mock.patch.object(check_env.shutil, "which", side_effect=which), mock.patch.object(
            check_env, "executable_version", return_value="10.33.2"
        ), mock.patch.object(check_env.os.path, "isdir", return_value=True), mock.patch.object(
            check_env.os.path, "isfile", return_value=True
        ):
            result = check_env.check_environment()

        self.assertEqual(result["status"], "error")
        self.assertIn("node", result["missing"])
        self.assertFalse(result["checks"]["node"]["found"])

    def test_missing_open_design_home_fails_closed(self) -> None:
        def which(name: str) -> str:
            return f"/tool/{name}"

        def version(executable: str) -> str:
            return "v24.1.0" if executable.endswith("node") else "10.33.2"

        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
            check_env, "load_private_env"
        ), mock.patch.object(check_env.shutil, "which", side_effect=which), mock.patch.object(
            check_env, "executable_version", side_effect=version
        ), mock.patch.object(check_env.os.path, "isdir", return_value=False):
            result = check_env.check_environment()

        self.assertEqual(result["status"], "error")
        self.assertIn("OPEN_DESIGN_HOME", result["missing"])
        self.assertFalse(result["checks"]["open_design_home"]["configured"])


class FakeResponse:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class DaemonHealthTests(unittest.TestCase):
    def test_health_reachable_skills_response(self) -> None:
        response = FakeResponse({"skills": [{"name": "one"}, {"name": "two"}]})
        with mock.patch.object(daemon_ctl.urllib.request, "urlopen", return_value=response) as urlopen:
            result = daemon_ctl.health_request("http://127.0.0.1:7456")

        self.assertTrue(result["reachable"])
        self.assertEqual(result["skills_count"], 2)
        urlopen.assert_called_once()

    def test_health_unreachable(self) -> None:
        with mock.patch.object(
            daemon_ctl.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            result = daemon_ctl.health_request("http://127.0.0.1:7456")

        self.assertFalse(result["reachable"])
        self.assertEqual(result["error"], "URLError")


class ListSkillsTests(unittest.TestCase):
    def test_parse_sample_payload_and_category_filter(self) -> None:
        fixture = {
            "skills": [
                {
                    "id": "pptx-generator",
                    "name": "pptx-generator",
                    "description": "Create editable decks.",
                    "mode": "deck",
                    "category": "slides",
                },
                {
                    "id": "web-clone",
                    "description": "Clone a web design.",
                    "mode": "prototype",
                    "category": "web-artifacts",
                },
            ]
        }

        parsed = list_skills.parse_skill_payload(fixture, category="slides")

        self.assertEqual(
            parsed,
            [
                {
                    "name": "pptx-generator",
                    "description": "Create editable decks.",
                    "od": {"mode": "deck"},
                    "category": "slides",
                }
            ],
        )


class RunWithEnvAllowlistTests(unittest.TestCase):
    def test_rejects_arbitrary_commands_before_loading_config(self) -> None:
        for command in (
            ["env"],
            ["/bin/sh", "-c", "pnpm tools-dev status"],
            ["pnpm", "exec", "arbitrary-tool"],
            ["pnpm", "dlx", "arbitrary-package"],
            ["node", "arbitrary.js"],
        ):
            with self.subTest(command=command), mock.patch.object(
                run_with_env, "load_private_env"
            ) as load, mock.patch.object(run_with_env.subprocess, "run") as run:
                stderr = StringIO()
                with redirect_stderr(stderr):
                    return_code = run_with_env.main(command)

                self.assertEqual(return_code, 2)
                load.assert_not_called()
                run.assert_not_called()
                self.assertIn("allowlist", stderr.getvalue())

    def test_accepts_documented_commands(self) -> None:
        accepted = (
            ["pnpm", "install"],
            ["pnpm", "tools-dev", "status"],
            ["pnpm", "--filter", "@open-design/daemon", "build"],
            ["corepack", "enable"],
            ["corepack", "pnpm", "--version"],
        )
        for command in accepted:
            with self.subTest(command=command):
                self.assertTrue(run_with_env.is_allowed_command(command))


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _make_payload(versions_root: Path, version: str) -> None:
    """Create a minimal but structurally valid launcher payload directory
    (only the one file resolve_launcher_payload() actually checks for)."""
    _touch(
        versions_root
        / version
        / "payload"
        / "Open Design.app"
        / "Contents"
        / "Resources"
        / "app"
        / "prebundled"
        / "daemon"
        / "daemon-cli.mjs"
    )


class DesktopCtlLauncherPayloadTests(unittest.TestCase):
    """0.18.1 实测(2026-08-07)：launcher 把可执行文件放进版本化的
    versions/<version>/payload/ 目录，版本号随自动升级变化。这组测试锁定
    resolve_launcher_payload() 的三级回退顺序，防止日后有人把路径改回写死。
    """

    def _ns_dir(self, app_support: Path) -> Path:
        return app_support / "launcher" / "channels" / "stable" / "namespaces" / "release-stable"

    def test_prefers_runtime_json_active_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            ns_dir = self._ns_dir(app_support)
            versions_root = ns_dir / "versions"
            # 磁盘上留了一个更高版本号的目录，但 runtime.json 说 0.18.1 才是
            # 当前生效版本——必须信 runtime.json，不能自己按目录名排序猜。
            _make_payload(versions_root, "0.18.0")
            _make_payload(versions_root, "0.18.1")
            _make_payload(versions_root, "9.9.9")
            (ns_dir / "runtime.json").parent.mkdir(parents=True, exist_ok=True)
            (ns_dir / "runtime.json").write_text(
                json.dumps({"active": {"version": "0.18.1"}}), encoding="utf-8"
            )
            (ns_dir / "install.json").write_text(
                json.dumps({"launchPath": "/Applications/Open Design.app"}), encoding="utf-8"
            )

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                result = desktop_ctl.resolve_launcher_payload()

        self.assertEqual(result["version"], "0.18.1")
        self.assertEqual(result["source"], "runtime_json")
        self.assertTrue(result["daemon_cli"].endswith("versions/0.18.1/payload/Open Design.app"
                         "/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs"))
        self.assertEqual(result["launch_path"], "/Applications/Open Design.app")

    def test_falls_back_to_highest_valid_version_when_runtime_json_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            ns_dir = self._ns_dir(app_support)
            versions_root = ns_dir / "versions"
            _make_payload(versions_root, "0.18.0")
            _make_payload(versions_root, "0.18.1")
            # 一个残缺目录（比如更新到一半）：目录存在但没有 daemon-cli.mjs，
            # 必须被跳过，不能被语义版本排序选中。
            (versions_root / "0.19.0" / "payload").mkdir(parents=True)

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                result = desktop_ctl.resolve_launcher_payload()

        self.assertEqual(result["version"], "0.18.1")
        self.assertEqual(result["source"], "versions_scan")

    def test_falls_back_to_fixed_path_when_launcher_dir_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(desktop_ctl, "APP_SUPPORT", tmp):
                result = desktop_ctl.resolve_launcher_payload()

        self.assertIsNone(result["version"])
        self.assertEqual(result["source"], "fallback_fixed_path")
        self.assertEqual(result["app_bundle"], desktop_ctl.FALLBACK_APP_BUNDLE)
        self.assertEqual(result["launch_path"], desktop_ctl.FALLBACK_APP_BUNDLE)


class DesktopCtlWorkspaceIdentityTests(unittest.TestCase):
    """0.18.1 实测(2026-08-07)：已绑定 workspace 的项目要求
    x-od-workspace-id / x-od-workspace-member-id header，这两个值本机
    只能从 app.sqlite 读到。这组测试用最小 schema 的临时 sqlite 锁定
    resolve_workspace_identity() 的取值与回退优先级。"""

    def test_member_id_from_workspace_projects_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            data_dir = app_support / "namespaces" / "release-stable" / "data"
            data_dir.mkdir(parents=True)
            db_path = data_dir / "app.sqlite"
            con = sqlite3.connect(str(db_path))
            con.execute(
                "CREATE TABLE workspace_projects (project_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT, updated_by_workspace_member_id TEXT)"
            )
            con.execute(
                "CREATE TABLE workspace_resources (resource_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT)"
            )
            con.execute(
                "INSERT INTO workspace_projects VALUES ('p1', 'ws1', 'member1', NULL)"
            )
            con.commit()
            con.close()

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                identity = desktop_ctl.resolve_workspace_identity()

        self.assertEqual(identity["workspace_id"], "ws1")
        self.assertEqual(identity["workspace_member_id"], "member1")
        self.assertEqual(identity["source"], "workspace_projects")
        self.assertFalse(identity["ambiguous"])
        self.assertIsNone(identity["error"])

    def test_falls_back_to_workspace_resources_when_unattributed(self) -> None:
        # 实测本机真实场景：桌面版历史项目的 created_by_workspace_member_id
        # 是 NULL（"unattributed"，daemon 仍接受），这时退回同一 workspace 下
        # 其它资源（如已装的设计系统）记录的建立者。
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            data_dir = app_support / "namespaces" / "release-stable" / "data"
            data_dir.mkdir(parents=True)
            db_path = data_dir / "app.sqlite"
            con = sqlite3.connect(str(db_path))
            con.execute(
                "CREATE TABLE workspace_projects (project_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT, updated_by_workspace_member_id TEXT)"
            )
            con.execute(
                "CREATE TABLE workspace_resources (resource_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT)"
            )
            con.execute("INSERT INTO workspace_projects VALUES ('p1', 'ws1', NULL, NULL)")
            con.execute(
                "INSERT INTO workspace_resources VALUES ('design_system:x', 'ws1', 'member-from-resources')"
            )
            con.commit()
            con.close()

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                identity = desktop_ctl.resolve_workspace_identity()

        self.assertEqual(identity["workspace_id"], "ws1")
        self.assertEqual(identity["workspace_member_id"], "member-from-resources")
        self.assertEqual(identity["source"], "workspace_resources")

    def test_no_bound_projects_reports_soft_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            data_dir = app_support / "namespaces" / "release-stable" / "data"
            data_dir.mkdir(parents=True)
            db_path = data_dir / "app.sqlite"
            con = sqlite3.connect(str(db_path))
            con.execute(
                "CREATE TABLE workspace_projects (project_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT, updated_by_workspace_member_id TEXT)"
            )
            con.execute(
                "CREATE TABLE workspace_resources (resource_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT)"
            )
            con.commit()
            con.close()

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                identity = desktop_ctl.resolve_workspace_identity()

        self.assertIsNone(identity["workspace_id"])
        self.assertEqual(identity["error"], "no_bound_projects")

    def test_missing_sqlite_reports_soft_error_not_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(desktop_ctl, "APP_SUPPORT", tmp):
                identity = desktop_ctl.resolve_workspace_identity()

        self.assertEqual(identity["error"], "app_sqlite_not_found")
        self.assertEqual(desktop_ctl.workspace_headers(identity), {})

    def test_ambiguous_when_multiple_workspaces_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app_support = Path(tmp)
            data_dir = app_support / "namespaces" / "release-stable" / "data"
            data_dir.mkdir(parents=True)
            db_path = data_dir / "app.sqlite"
            con = sqlite3.connect(str(db_path))
            con.execute(
                "CREATE TABLE workspace_projects (project_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT, updated_by_workspace_member_id TEXT)"
            )
            con.execute(
                "CREATE TABLE workspace_resources (resource_id TEXT, workspace_id TEXT,"
                " created_by_workspace_member_id TEXT)"
            )
            con.execute("INSERT INTO workspace_projects VALUES ('p1', 'ws1', 'm1', NULL)")
            con.execute("INSERT INTO workspace_projects VALUES ('p2', 'ws2', 'm2', NULL)")
            con.commit()
            con.close()

            with mock.patch.object(desktop_ctl, "APP_SUPPORT", str(app_support)):
                identity = desktop_ctl.resolve_workspace_identity()

        self.assertTrue(identity["ambiguous"])


class DesktopCtlHealthProbeTests(unittest.TestCase):
    """0.18.1 实测(2026-08-07)：daemon 存活判据从"/api/projects 返回
    {'projects':[...]}"改成"/api/health 返回 {'ok':true,...}"——前者在
    workspace 为空时也会返回合法但具误导性的空数组。"""

    def test_health_ok_json_is_recognized(self) -> None:
        response = FakeResponse({"ok": True, "version": "0.18.1"})
        with mock.patch.object(desktop_ctl.urllib.request, "urlopen", return_value=response):
            result = desktop_ctl.probe_health(57303)
        self.assertEqual(result, {"ok": True, "version": "0.18.1"})

    def test_html_ui_port_is_rejected(self) -> None:
        class HtmlResponse(FakeResponse):
            def read(self) -> bytes:  # type: ignore[override]
                return b"<!DOCTYPE html><html></html>"

        with mock.patch.object(
            desktop_ctl.urllib.request, "urlopen", return_value=HtmlResponse({})
        ):
            result = desktop_ctl.probe_health(57312)
        self.assertIsNone(result)

    def test_connection_error_is_rejected(self) -> None:
        with mock.patch.object(
            desktop_ctl.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            result = desktop_ctl.probe_health(9)
        self.assertIsNone(result)

    def test_empty_projects_no_longer_treated_as_daemon_liveness(self) -> None:
        # probe() 仍然可用（兼容旧调用方），但 detect() 不应再拿它判活。
        response = FakeResponse({"projects": []})
        with mock.patch.object(desktop_ctl.urllib.request, "urlopen", return_value=response):
            data = desktop_ctl.probe(57303)
        self.assertEqual(data, {"projects": []})


if __name__ == "__main__":
    unittest.main()
