"""PII masking utilities and FunctionTool wrapper.

Author: Damon Li
"""

from __future__ import annotations

import re

from agenticx.tools import tool

_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
_PHONE_PATTERN = re.compile(r"\b(?:\+?86)?1[3-9]\d{9}\b")
_ID_CARD_PATTERN = re.compile(r"\b\d{17}[\dXx]\b|\b\d{15}\b")
_URL_PATTERN = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)
_SIGNATURE_PATTERN = re.compile(r"--[\s\S]*$")


def _mask_with_regex(content: str) -> str:
    replacements: dict[str, str] = {}
    for pattern in (
        _EMAIL_PATTERN,
        _PHONE_PATTERN,
        _ID_CARD_PATTERN,
        _URL_PATTERN,
    ):
        replacements.update({match.group(): "***" for match in pattern.finditer(content)})

    content = _SIGNATURE_PATTERN.sub("-- ***", content)
    for original, masked in replacements.items():
        content = content.replace(original, masked)
    return content


def _mask_with_jionlp(content: str) -> str:
    from jionlp import (  # type: ignore[import-untyped]
        recognize_location,
        remove_email,
        remove_id_card,
        remove_phone_number,
        remove_url,
    )

    for location in recognize_location(content):
        content = content.replace(location, "***")

    content = remove_email(content).replace("[EMAIL]", "***")
    content = remove_phone_number(content).replace("[PHONE]", "***")
    content = remove_id_card(content).replace("[ID]", "***")
    content = remove_url(content).replace("[URL]", "***")
    return _SIGNATURE_PATTERN.sub("-- ***", content)


def mask_pii(content: str, preprocessor: str = "regex") -> str:
    """Mask common PII patterns in email or news text."""
    if preprocessor == "jionlp":
        try:
            return _mask_with_jionlp(content)
        except ImportError:
            return _mask_with_regex(content)
    return _mask_with_regex(content)


@tool()
def desensitize_text(content: str) -> str:
    """Mask PII (email, phone, id-card, url, signature) in raw text."""
    return mask_pii(content)
