#!/usr/bin/env python3
"""
Skill Sync CLI - Download skills from anthropics/skills repository.

Usage:
    uv run skill_sync.py              # Interactive TUI mode
    uv run skill_sync.py --list       # List available skills
    uv run skill_sync.py pdf docx     # Sync specific skills
    uv run skill_sync.py --all        # Sync all skills
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "textual>=0.89", "python-dotenv>=1.0"]
# ///

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env file from script directory
load_dotenv(Path(__file__).parent / ".env")
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Label, ProgressBar, Static

REPO_OWNER = "anthropics"
REPO_NAME = "skills"
SKILLS_PATH = "skills"
GITHUB_API = "https://api.github.com"


@dataclass
class Skill:
    """Represents a skill from the repository."""

    name: str
    description: str = ""
    files: list[str] = field(default_factory=list)


@dataclass
class SyncStatus:
    """Status of a skill relative to local installation."""

    skill: Skill
    status: str  # "new", "update", "ok"
    local_sha: str | None = None
    remote_sha: str | None = None


class GitHubClient:
    """Client for GitHub API interactions."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client = httpx.Client(headers=headers, timeout=30.0)
        self._latest_commit: str | None = None

    def get_latest_commit(self) -> str:
        """Fetch the latest commit SHA for the main branch."""
        if self._latest_commit:
            return self._latest_commit
        url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/commits/main"
        response = self.client.get(url)
        response.raise_for_status()
        self._latest_commit = response.json()["sha"]
        return self._latest_commit

    def list_skills(self) -> list[Skill]:
        """Fetch list of available skills from the repository."""
        url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{SKILLS_PATH}"
        response = self.client.get(url)
        response.raise_for_status()

        skills = []
        for item in response.json():
            if item["type"] == "dir":
                skills.append(Skill(name=item["name"]))
        return sorted(skills, key=lambda s: s.name)

    def download_skill(self, skill_name: str, target_dir: Path) -> list[str]:
        """Download all files for a skill to the target directory."""
        files = []
        self._download_directory(f"{SKILLS_PATH}/{skill_name}", target_dir, files)
        return files

    def _download_directory(self, path: str, target_dir: Path, files: list[str]):
        """Recursively download a directory."""
        url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"
        response = self.client.get(url)
        response.raise_for_status()

        target_dir.mkdir(parents=True, exist_ok=True)

        for item in response.json():
            if item["type"] == "file":
                self._download_file(item, target_dir)
                files.append(item["name"])
            elif item["type"] == "dir":
                subdir = target_dir / item["name"]
                self._download_directory(item["path"], subdir, files)

    def _download_file(self, item: dict, target_dir: Path):
        """Download a single file."""
        import base64

        if item.get("content"):
            content = base64.b64decode(item["content"])
        else:
            # Fetch content if not included
            response = self.client.get(item["url"])
            response.raise_for_status()
            content = base64.b64decode(response.json()["content"])

        file_path = target_dir / item["name"]
        file_path.write_bytes(content)


class SkillManager:
    """Manages local skill installation and manifest tracking."""

    def __init__(self, skills_dir: Path, manifest_dir: Path | None = None):
        self.skills_dir = skills_dir
        # Manifest lives in parent directory (fulcrum-template root), not inside template/skills
        self.manifest_path = (manifest_dir or skills_dir.parent.parent) / ".skill-manifest.json"

    def get_manifest(self) -> dict:
        """Load the manifest file."""
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text())
        return {"skills": {}}

    def save_manifest(self, manifest: dict):
        """Save the manifest file."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    def get_sync_status(
        self, skills: list[Skill], remote_sha: str
    ) -> list[SyncStatus]:
        """Compare remote skills with local manifest."""
        manifest = self.get_manifest()
        local_skills = manifest.get("skills", {})

        statuses = []
        for skill in skills:
            local_info = local_skills.get(skill.name)
            if local_info is None:
                status = SyncStatus(
                    skill=skill,
                    status="new",
                    local_sha=None,
                    remote_sha=remote_sha[:7],
                )
            elif local_info.get("commit_sha", "")[:7] != remote_sha[:7]:
                status = SyncStatus(
                    skill=skill,
                    status="update",
                    local_sha=local_info.get("commit_sha", "")[:7] or None,
                    remote_sha=remote_sha[:7],
                )
            else:
                status = SyncStatus(
                    skill=skill,
                    status="ok",
                    local_sha=local_info.get("commit_sha", "")[:7],
                    remote_sha=remote_sha[:7],
                )
            statuses.append(status)
        return statuses

    def record_sync(self, skill_name: str, commit_sha: str, files: list[str]):
        """Record a skill sync in the manifest."""
        manifest = self.get_manifest()
        manifest["skills"][skill_name] = {
            "commit_sha": commit_sha,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "files": files,
        }
        self.save_manifest(manifest)


class SkillSyncApp(App):
    """Textual TUI for skill selection and sync."""

    CSS = """
    #header-info {
        background: $surface;
        padding: 1;
        margin-bottom: 1;
    }
    #status {
        height: 3;
        padding: 1;
        background: $surface;
    }
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("s", "sync", "Sync Selected", show=True),
        Binding("a", "select_all", "Select All", show=True),
        Binding("n", "select_new", "Select New/Updated", show=True),
        Binding("space", "toggle", "Toggle", show=True, priority=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        github: GitHubClient,
        manager: SkillManager,
        statuses: list[SyncStatus],
        remote_sha: str,
    ):
        super().__init__()
        self.github = github
        self.manager = manager
        self.statuses = statuses
        self.remote_sha = remote_sha
        self.selected: set[str] = set()
        self.synced_skills: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"[bold]Skill Sync[/bold] - {REPO_OWNER}/{REPO_NAME}\n"
            f"Latest commit: [cyan]{self.remote_sha[:7]}[/cyan]",
            id="header-info",
        )
        yield DataTable(id="skills-table")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_column("", key="check")
        table.add_column("Skill", key="skill")
        table.add_column("Status", key="status")
        table.add_column("Local", key="local")
        table.add_column("Remote", key="remote")

        for s in self.statuses:
            status_style = {
                "new": "[green]NEW[/green]",
                "update": "[yellow]UPDATE[/yellow]",
                "ok": "[dim]OK[/dim]",
            }.get(s.status, s.status)

            table.add_row(
                r"\[ ]",
                s.skill.name,
                status_style,
                s.local_sha or "-",
                s.remote_sha or "-",
                key=s.skill.name,
            )

    def action_toggle(self):
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            return
        row_key = list(table.rows.keys())[table.cursor_row]
        skill_name = row_key.value  # Get actual key value from RowKey object

        if skill_name in self.selected:
            self.selected.discard(skill_name)
            table.update_cell(skill_name, "check", r"\[ ]")
        else:
            self.selected.add(skill_name)
            table.update_cell(skill_name, "check", r"\[x]")

    def action_select_all(self):
        table = self.query_one(DataTable)
        for s in self.statuses:
            self.selected.add(s.skill.name)
            table.update_cell(s.skill.name, "check", r"\[x]")

    def action_select_new(self):
        table = self.query_one(DataTable)
        self.selected.clear()
        for s in self.statuses:
            if s.status in ("new", "update"):
                self.selected.add(s.skill.name)
                table.update_cell(s.skill.name, "check", r"\[x]")
            else:
                table.update_cell(s.skill.name, "check", r"\[ ]")

    def action_sync(self):
        if not self.selected:
            self.update_status("[yellow]No skills selected[/yellow]")
            return
        self.sync_selected()

    @work(thread=True)
    def sync_selected(self):
        """Sync selected skills in a background thread."""
        skills_to_sync = [s for s in self.statuses if s.skill.name in self.selected]
        total = len(skills_to_sync)

        for i, status in enumerate(skills_to_sync, 1):
            skill_name = status.skill.name
            self.call_from_thread(
                self.update_status,
                f"Syncing {skill_name}... ({i}/{total})",
            )

            try:
                target = self.manager.skills_dir / skill_name
                # Remove existing if updating
                if target.exists():
                    import shutil
                    shutil.rmtree(target)

                files = self.github.download_skill(skill_name, target)
                self.manager.record_sync(skill_name, self.remote_sha, files)
                self.synced_skills.append(skill_name)
            except Exception as e:
                self.call_from_thread(
                    self.update_status,
                    f"[red]Error syncing {skill_name}: {e}[/red]",
                )

        self.call_from_thread(
            self.update_status,
            f"[green]Done! Synced {len(self.synced_skills)} skill(s)[/green]",
        )
        self.call_from_thread(self.refresh_table)

    def update_status(self, message: str):
        self.query_one("#status", Static).update(message)

    def refresh_table(self):
        """Refresh table after sync."""
        table = self.query_one(DataTable)
        new_statuses = self.manager.get_sync_status(
            [s.skill for s in self.statuses], self.remote_sha
        )

        for s in new_statuses:
            status_style = {
                "new": "[green]NEW[/green]",
                "update": "[yellow]UPDATE[/yellow]",
                "ok": "[dim]OK[/dim]",
            }.get(s.status, s.status)

            table.update_cell(s.skill.name, "status", status_style)
            table.update_cell(s.skill.name, "local", s.local_sha or "-")

            # Uncheck synced items
            if s.skill.name in self.synced_skills:
                self.selected.discard(s.skill.name)
                table.update_cell(s.skill.name, "check", r"\[ ]")

        self.statuses = new_statuses


def list_skills_cli(github: GitHubClient, manager: SkillManager):
    """Non-interactive skill listing."""
    print(f"Fetching skills from {REPO_OWNER}/{REPO_NAME}...")
    remote_sha = github.get_latest_commit()
    skills = github.list_skills()
    statuses = manager.get_sync_status(skills, remote_sha)

    print(f"\nLatest commit: {remote_sha[:7]}")
    print(f"{'Skill':<25} {'Status':<10} {'Local':<10} {'Remote':<10}")
    print("-" * 55)

    for s in statuses:
        status = s.status.upper()
        local = s.local_sha or "-"
        remote = s.remote_sha or "-"
        print(f"{s.skill.name:<25} {status:<10} {local:<10} {remote:<10}")


def sync_skills_cli(
    github: GitHubClient, manager: SkillManager, skill_names: list[str]
):
    """Non-interactive skill sync."""
    remote_sha = github.get_latest_commit()
    print(f"Syncing to commit: {remote_sha[:7]}")

    for name in skill_names:
        print(f"  Syncing {name}...", end=" ", flush=True)
        try:
            target = manager.skills_dir / name
            if target.exists():
                import shutil
                shutil.rmtree(target)
            files = github.download_skill(name, target)
            manager.record_sync(name, remote_sha, files)
            print(f"done ({len(files)} files)")
        except Exception as e:
            print(f"error: {e}")

    print("\nDone!")


def handle_rate_limit(e: httpx.HTTPStatusError):
    """Handle GitHub rate limit errors with helpful message."""
    if e.response.status_code == 403 and "rate limit" in str(e).lower():
        reset_time = e.response.headers.get("X-RateLimit-Reset")
        msg = "GitHub API rate limit exceeded."
        if reset_time:
            from datetime import datetime
            reset_dt = datetime.fromtimestamp(int(reset_time))
            msg += f" Resets at {reset_dt.strftime('%H:%M:%S')}."
        msg += "\n\nTip: Set GITHUB_TOKEN env var for higher limits (5000/hr vs 60/hr)."
        print(f"Error: {msg}")
        sys.exit(1)
    raise e


def main():
    parser = argparse.ArgumentParser(
        description="Sync skills from anthropics/skills repository"
    )
    parser.add_argument("skills", nargs="*", help="Specific skills to sync")
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available skills"
    )
    parser.add_argument("--all", "-a", action="store_true", help="Sync all skills")
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path(__file__).parent / "template" / "skills",
        help="Target directory for skills",
    )

    args = parser.parse_args()

    github = GitHubClient()
    manager = SkillManager(args.target)

    try:
        if args.list:
            list_skills_cli(github, manager)
            return

        if args.all or args.skills:
            # Non-interactive mode
            if args.all:
                skills = github.list_skills()
                skill_names = [s.name for s in skills]
            else:
                skill_names = args.skills
            sync_skills_cli(github, manager, skill_names)
            return

        # Interactive TUI mode
        print("Fetching skill catalog...")
        remote_sha = github.get_latest_commit()
        skills = github.list_skills()
        statuses = manager.get_sync_status(skills, remote_sha)

        app = SkillSyncApp(github, manager, statuses, remote_sha)
        app.run()
    except httpx.HTTPStatusError as e:
        handle_rate_limit(e)


if __name__ == "__main__":
    main()
