#!/usr/bin/env python3
"""
Sync skill-creator from anthropics/skills repository into the main directory.

Usage:
    uv run sync_skill_creator.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "python-dotenv>=1.0"]
# ///

import base64
import os
import shutil
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from script directory
load_dotenv(Path(__file__).parent / ".env")

REPO_OWNER = "anthropics"
REPO_NAME = "skills"
SKILL_MAKER_PATH = "skills/skill-creator"
GITHUB_API = "https://api.github.com"


class GitHubClient:
    """Client for GitHub API interactions."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client = httpx.Client(headers=headers, timeout=30.0)

    def get_latest_commit(self) -> str:
        """Fetch the latest commit SHA for the main branch."""
        url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/commits/main"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()["sha"]

    def download_directory(self, path: str, target_dir: Path) -> list[str]:
        """Recursively download a directory."""
        files = []
        self._download_directory(path, target_dir, files)
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
                files.append(str(target_dir / item["name"]))
            elif item["type"] == "dir":
                subdir = target_dir / item["name"]
                self._download_directory(item["path"], subdir, files)

    def _download_file(self, item: dict, target_dir: Path):
        """Download a single file."""
        if item.get("content"):
            content = base64.b64decode(item["content"])
        else:
            response = self.client.get(item["url"])
            response.raise_for_status()
            content = base64.b64decode(response.json()["content"])

        file_path = target_dir / item["name"]
        file_path.write_bytes(content)


def main():
    script_dir = Path(__file__).parent
    target_dir = script_dir / "skill-creator"  # Sync to fulcrum-template directory

    github = GitHubClient()

    print(f"Fetching latest commit from {REPO_OWNER}/{REPO_NAME}...")
    commit_sha = github.get_latest_commit()
    print(f"Latest commit: {commit_sha[:7]}")

    # Remove existing directory if present
    if target_dir.exists():
        print(f"Removing existing {target_dir}...")
        shutil.rmtree(target_dir)

    print(f"Downloading {SKILL_MAKER_PATH} to {target_dir}...")
    files = github.download_directory(SKILL_MAKER_PATH, target_dir)
    print(f"Done! Downloaded {len(files)} files.")


if __name__ == "__main__":
    main()
