"""Prompt resolution seam for layered prompt lifecycle.

Author: Damon Li
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from agenticx_service.domains.base import DomainRegistry
from agenticx_service.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)


@runtime_checkable
class PromptResolver(Protocol):
    async def resolve(self, domain: str, stage: str, ctx: dict[str, Any]) -> str:
        ...


class StaticPromptResolver:
    """Resolve prompts from static templates via domain plugin prompt ids."""

    def __init__(
        self,
        registry: DomainRegistry,
        prompts: PromptRegistry,
    ) -> None:
        self.registry = registry
        self.prompts = prompts

    async def resolve(self, domain: str, stage: str, ctx: dict[str, Any]) -> str:
        plugin = self.registry.get(domain)
        prompt_ids = plugin.prompt_ids()
        template_id = prompt_ids.get(stage) or prompt_ids.get("single")
        if not template_id:
            ctx["_resolver_fallback"] = True
            template_id = prompt_ids.get("single", "v4")
            logger.warning("No prompt id for domain=%s stage=%s, fallback=%s", domain, stage, template_id)
        return self.prompts.format(template_id, **ctx)


class LayeredPromptResolver:
    """Stack static → frozen → skill → personalization layers (Phase E)."""

    def __init__(
        self,
        static: StaticPromptResolver,
        *,
        frozen_store: Any | None = None,
        skill_provider: Any | None = None,
        personalization: Any | None = None,
    ) -> None:
        self.static = static
        self.frozen_store = frozen_store
        self.skill_provider = skill_provider
        self.personalization = personalization

    async def resolve(self, domain: str, stage: str, ctx: dict[str, Any]) -> str:
        layers: list[str] = []
        trace_layers: list[str] = []

        base = await self._resolve_static(domain, stage, ctx)
        layers.append(base)
        trace_layers.append("static")

        if self.frozen_store is not None:
            frozen = self.frozen_store.get(domain, stage)
            if frozen:
                layers = [frozen]
                trace_layers.append("frozen")

        if self.skill_provider is not None:
            hint = ctx.get("scenario_hint", "")
            skill_prompt = self.skill_provider.resolve(domain, stage, hint)
            if skill_prompt:
                layers = [skill_prompt]
                trace_layers.append("skill")

        if self.personalization is not None:
            user_id = ctx.get("user_id")
            extra = await self.personalization.build_injection(user_id, domain)
            if extra:
                layers.append(extra)
                trace_layers.append("personalization")

        ctx.setdefault("_prompt_layers", trace_layers)
        return "\n\n".join(part for part in layers if part)

    async def _resolve_static(self, domain: str, stage: str, ctx: dict[str, Any]) -> str:
        try:
            return await self.static.resolve(domain, stage, ctx)
        except Exception:  # noqa: BLE001
            logger.exception("Static prompt resolve failed domain=%s stage=%s", domain, stage)
            return self.static.prompts.format("v4", user_raw_text_input=ctx.get("user_raw_text_input", ""))
