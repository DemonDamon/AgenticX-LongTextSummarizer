"""User feedback → preference memory → prompt injection.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from agenticx_service.config import AppConfig


class PersonalizationStore:
    """Persist user summarization preferences and build injection blocks."""

    def __init__(self, config: AppConfig, *, store_dir: Path | None = None) -> None:
        self.config = config
        base = store_dir or Path.home() / ".agenticx" / "workspace" / "summarizer_prefs"
        self.store_dir = base
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, list[str]] = {}

    def _key(self, user_id: str, domain: str) -> str:
        return f"{user_id}:{domain}"

    def _path(self, user_id: str, domain: str) -> Path:
        safe = self._key(user_id, domain).replace(":", "_")
        return self.store_dir / f"{safe}.json"

    async def record_feedback(self, user_id: str, domain: str, instruction: str) -> None:
        instruction = instruction.strip()
        if not instruction:
            return
        key = self._key(user_id, domain)
        prefs = self._memory.setdefault(key, [])
        if instruction not in prefs:
            prefs.append(instruction)
        path = self._path(user_id, domain)
        payload = json.dumps(prefs, ensure_ascii=False, indent=2)
        await asyncio.to_thread(path.write_text, payload, encoding="utf-8")
        await self._index_workspace(path)

    async def _index_workspace(self, path: Path) -> None:
        try:
            from agenticx.memory.workspace_memory import WorkspaceMemoryStore

            store = WorkspaceMemoryStore()
            await store.index_file(path)
        except Exception:  # noqa: BLE001
            pass

    def _load_prefs(self, user_id: str, domain: str) -> list[str]:
        key = self._key(user_id, domain)
        if key in self._memory:
            return self._memory[key]
        path = self._path(user_id, domain)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self._memory[key] = list(data)
            return self._memory[key]
        return []

    async def build_injection(self, user_id: str | None, domain: str) -> str:
        if not user_id:
            return ""
        prefs = self._load_prefs(user_id, domain)
        if not prefs:
            try:
                from agenticx.memory.workspace_memory import WorkspaceMemoryStore

                store = WorkspaceMemoryStore()
                hits = await store.search(
                    f"summarizer_pref {user_id} {domain}",
                    limit=3,
                    mode="hybrid",
                )
                for hit in hits:
                    text = str(hit.get("text") or hit.get("content") or "")
                    if text and text not in prefs:
                        prefs.append(text[:200])
            except Exception:  # noqa: BLE001
                pass
        if not prefs:
            return ""
        lines = "\n".join(f"- {p}" for p in prefs[:5])
        block = (
            "# 用户个性化要求\n"
            "在不违反上述核心摘要要求的前提下，请额外遵循：\n"
            f"{lines}"
        )
        max_chars = self.config.agentic.personalization_max_chars
        return block[:max_chars]
