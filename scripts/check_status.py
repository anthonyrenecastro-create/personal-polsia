#!/usr/bin/env python3
"""Deterministic status checks for Personal Polsia companies.

No secrets, no writes. Prints JSON to stdout.
GitHub CI checks use the workspace github-push helper when available;
if that fails, the field says why instead of guessing.
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HOME = Path.home()
PROJECTS = HOME / "workspace" / "projects"


def http_status(url: str, timeout: int = 45) -> dict:
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "personal-polsia-check/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"url": url, "status": r.status}
    except Exception as e:  # noqa: BLE001 - report, don't crash the cycle
        return {"url": url, "status": None, "error": str(e)[:200]}


def git_local(path: Path) -> dict:
    if not (path / ".git").exists():
        return {"path": str(path), "git": False}
    def run(*args):
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=15).stdout.strip()
    try:
        branch = run("rev-parse", "--abbrev-ref", "HEAD")
        head = run("log", "--oneline", "-1")
        dirty = run("status", "--short")
        return {"path": str(path), "git": True, "branch": branch, "head": head, "dirty_lines": len([l for l in dirty.splitlines() if l])}
    except Exception as e:  # noqa: BLE001
        return {"path": str(path), "git": True, "error": str(e)[:200]}


def github_ci(repo: str) -> dict:
    helper = HOME / "workspace" / "skills" / "github-push" / "bin" / "gh_api.py"
    if not helper.exists():
        return {"repo": repo, "ci": "helper-missing"}
    try:
        out = subprocess.run(
            [sys.executable, str(helper), "GET", f"/repos/anthonyrenecastro-create/{repo}/actions/runs?per_page=3"],
            capture_output=True, text=True, timeout=45, cwd=str(helper.parent.parent),
        )
        data = json.loads(out.stdout)
        runs = [
            {"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion"),
             "branch": r["head_branch"], "created_at": r["created_at"], "url": r["html_url"]}
            for r in data.get("workflow_runs", [])
        ]
        return {"repo": repo, "runs": runs}
    except Exception as e:  # noqa: BLE001
        return {"repo": repo, "ci_error": str(e)[:200]}


def main() -> None:
    result = {
        "companies": {
            "quadra-mind-sight": {
                "live": http_status("https://quadra-mind-sight.onrender.com/"),
                "local": git_local(PROJECTS / "quadra-mind-sight"),
                "github": github_ci("quadra-mind-sight"),
            },
            "alchemy-factory": {
                "local": git_local(PROJECTS / "alchemy-factory"),
                "github": github_ci("alchemy-factory"),
            },
            "newsletter-autopilot": {
                "local": git_local(PROJECTS / "newsletter-autopilot"),
                "github": github_ci("newsletter-autopilot"),
                "local_path_exists": (PROJECTS / "newsletter-autopilot").exists(),
            },
        }
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
