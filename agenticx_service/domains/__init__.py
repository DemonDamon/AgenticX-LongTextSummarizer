"""Pluggable summarization domains.

Author: Damon Li
"""

from agenticx_service.domains.base import DomainPlugin, DomainRegistry, RuleEngine
from agenticx_service.domains.email.plugin import EmailDomainPlugin
from agenticx_service.domains.news.plugin import NewsDomainPlugin


def build_domain_registry(config) -> DomainRegistry:
    """Construct the default domain plugin registry from config."""
    return DomainRegistry(
        [EmailDomainPlugin(), NewsDomainPlugin()],
        default_domain=config.domains.default,
    )


__all__ = [
    "DomainPlugin",
    "DomainRegistry",
    "RuleEngine",
    "EmailDomainPlugin",
    "NewsDomainPlugin",
    "build_domain_registry",
]
