"""Versioned frozen prompt store.

Author: Damon Li
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class FrozenPromptStore:
    """Load frozen prompts from prompts/frozen/<domain>/<stage>@<ver>.txt."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.manifest_path = self.root / "manifest.yaml"
        self._manifest: dict[str, Any] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self.manifest_path.exists():
            with self.manifest_path.open(encoding="utf-8") as handle:
                self._manifest = yaml.safe_load(handle) or {}
        else:
            self._manifest = {"entries": {}}

    def _save_manifest(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self._manifest, handle, allow_unicode=True)

    def get(self, domain: str, stage: str) -> str | None:
        key = f"{domain}.{stage}"
        entry = (self._manifest.get("entries") or {}).get(key)
        if not entry:
            return None
        version = entry.get("version")
        if not version:
            return None
        path = self.root / domain / f"{stage}@{version}.txt"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip()

    def freeze(
        self,
        domain: str,
        stage: str,
        template: str,
        meta: dict[str, Any] | None = None,
    ) -> str:
        existing = (self._manifest.get("entries") or {}).get(f"{domain}.{stage}", {})
        current_ver = existing.get("version", "v0")
        match = re.match(r"v(\d+)", str(current_ver))
        next_num = int(match.group(1)) + 1 if match else 1
        version = f"v{next_num}"
        target_dir = self.root / domain
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{stage}@{version}.txt"
        path.write_text(template.strip() + "\n", encoding="utf-8")
        key = f"{domain}.{stage}"
        entries = self._manifest.setdefault("entries", {})
        entries[key] = {
            "version": version,
            "path": str(path.relative_to(self.root)),
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "meta": meta or {},
        }
        self._save_manifest()
        return version
