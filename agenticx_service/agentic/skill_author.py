"""Agent-authored skills for uncovered summarization scenarios.

Author: Damon Li
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agenticx_service.config import AppConfig


class SkillPromptProvider:
    """Resolve prompts from agent-authored SKILL.md files."""

    def __init__(self, config: AppConfig, *, skills_root: Path | None = None) -> None:
        self.config = config
        if skills_root:
            self.skills_root = skills_root
        elif config.agentic.skills_dir:
            self.skills_root = Path(config.agentic.skills_dir).expanduser()
        else:
            self.skills_root = Path.home() / ".agenticx" / "skills" / "summarizer"

    def resolve(self, domain: str, stage: str, scenario_hint: str) -> str | None:
        if not self.skills_root.exists():
            return None
        hint = (scenario_hint or "").lower()
        for skill_dir in sorted(self.skills_root.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            meta, body = self._parse_skill(skill_md.read_text(encoding="utf-8"))
            activates = str(meta.get("activates_on", "")).lower()
            skill_domain = str(meta.get("domain", domain)).lower()
            if skill_domain != domain.lower():
                continue
            if hint and hint not in activates and activates not in hint:
                if not meta.get("always_on"):
                    continue
            prompt_key = f"prompt_{stage}"
            match = re.search(rf"^{prompt_key}:\s*\|\s*\n((?:  .+\n)+)", body, re.MULTILINE)
            if match:
                return self._dedent_block(match.group(1))
            if stage == "single" and "prompt:" in body:
                match2 = re.search(r"^prompt:\s*\|\s*\n((?:  .+\n)+)", body, re.MULTILINE)
                if match2:
                    return self._dedent_block(match2.group(1))
        return None

    @staticmethod
    def _parse_skill(text: str) -> tuple[dict[str, Any], str]:
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                return meta, parts[2]
        return {}, text

    @staticmethod
    def _dedent_block(block: str) -> str:
        lines = block.splitlines()
        if not lines:
            return ""
        indent = len(lines[0]) - len(lines[0].lstrip())
        return "\n".join(line[indent:] if len(line) >= indent else line for line in lines).strip()


class SkillAuthor:
    """Draft and persist skills after guard scanning."""

    def __init__(self, config: AppConfig, provider: SkillPromptProvider | None = None) -> None:
        self.config = config
        self.provider = provider or SkillPromptProvider(config)

    def author_skill(
        self,
        name: str,
        domain: str,
        stage: str,
        prompt_template: str,
        *,
        description: str = "",
        activates_on: str = "",
    ) -> tuple[bool, str]:
        if not self.config.agentic.skill_authoring:
            return False, "skill_authoring disabled"
        safe_name = re.sub(r"[^\w\-/]", "-", name).strip("-") or "custom-scenario"
        skill_dir = self.provider.skills_root / safe_name.replace("/", "_")
        skill_dir.mkdir(parents=True, exist_ok=True)
        content = (
            "---\n"
            f"name: {safe_name}\n"
            f"description: {description or 'Agent-authored summarizer skill'}\n"
            f"domain: {domain}\n"
            f"activates_on: {activates_on}\n"
            "---\n\n"
            f"prompt_{stage}: |\n"
            + "\n".join(f"  {line}" for line in prompt_template.splitlines())
            + "\n"
        )
        try:
            from agenticx.skills.guard import scan_skill_markdown_text, should_allow

            result = scan_skill_markdown_text(content, source="agent-created")
            allowed, reason = should_allow(result, source="agent-created")
            if not allowed:
                return False, reason
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        return True, str(skill_dir)
