"""
MarketMate - tools/safety.py
Phase 8: Language Quality Checker and Cached Fallback

Nothing here does database access, so there is no circular-import risk
with market_tools.py.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

FALLBACK_PATH = Path(__file__).resolve().parent.parent / "data" / "fallback_result.json"

# Common Roman-Urdu marker words (heuristic to detect if text is actually Roman Urdu)
_ROMAN_URDU_MARKERS = [
    "hai", "hain", "ka", "ki", "ke", "aur", "yeh", "ap", "aap",
    "liye", "karo", "karna", "mein", "se", "ko", "ne", "sath",
    "abhi", "jaldi", "khaas", "behtar", "sab", "bas", "lekin",
    "phir", "bhi", "jo", "toh", "kya", "hoga", "karen",
]

_DOUBLE_SPACE_RE = re.compile(r"  +")
_REPEATED_PUNCT_RE = re.compile(r"([!?.،,])\1{2,}")
_ALL_CAPS_RE = re.compile(r"\b[A-Z]{5,}\b")


def check_language_quality(content: str, language: str = "English") -> list[str]:
    """
    Scan content for obvious formatting / quality problems.

    Returns a list of human-readable issue descriptions.
    An empty list means no issues were detected.
    """
    issues: list[str] = []
    stripped = content.strip()

    if not stripped or len(stripped) < 15:
        issues.append(f"{language}: Content is too short or empty.")
        return issues

    if _DOUBLE_SPACE_RE.search(content):
        issues.append(f"{language}: Contains double spaces.")

    if _REPEATED_PUNCT_RE.search(content):
        issues.append(
            f"{language}: Contains repeated punctuation marks "
            "(e.g. '!!!', '???', '،،،')."
        )

    caps_words = _ALL_CAPS_RE.findall(content)
    if len(caps_words) > 3:
        sample = ", ".join(caps_words[:4])
        issues.append(
            f"{language}: Excessive ALL-CAPS words detected ({sample}…). "
            "Consider using sentence case for readability."
        )

    # Roman-Urdu specific check: verify text actually contains Urdu vocabulary
    if language.lower() in ("roman urdu", "urdu", "roman_urdu"):
        found = sum(
            1
            for w in _ROMAN_URDU_MARKERS
            if re.search(r"\b" + w + r"\b", content, re.IGNORECASE)
        )
        if found < 2:
            issues.append(
                "Roman Urdu: Content may not be in Roman Urdu "
                "(too few common Urdu words detected). "
                "Please verify the copywriter produced Roman Urdu text."
            )

    return issues


def review_campaign_content(result_text: str) -> dict[str, list[str]]:
    """
    Scan the full campaign result text for language quality issues.

    Tries best-effort section detection for English / Roman Urdu / WhatsApp
    sections. Falls back to a general whole-text check if sections cannot
    be found.

    Returns {section_label: [issues]}.  Empty dict = no issues found.
    """
    if not result_text or not result_text.strip():
        return {"General": ["Campaign result is empty."]}

    report: dict[str, list[str]] = {}

    # Try to locate each section by scanning for heading keywords
    section_specs = [
        ("English Copy", ["english"], "English"),
        ("Roman Urdu Copy", ["roman urdu", "urdu copy", "urdu:"], "Roman Urdu"),
        ("WhatsApp Copy", ["whatsapp"], "English"),
    ]

    for section_label, keywords, lang in section_specs:
        for kw in keywords:
            idx = result_text.lower().find(kw)
            if idx != -1:
                # Grab up to 600 chars after the keyword as a representative snippet
                snippet = result_text[idx : idx + 600].strip()
                issues = check_language_quality(snippet, lang)
                if issues:
                    report[section_label] = issues
                break

    # If no sections were detected, do a general check on the full text
    if not report:
        general = check_language_quality(result_text, "Campaign Output")
        if general:
            report["General"] = general

    return report


# ---------------------------------------------------------------------------
# Cached Fallback
# ---------------------------------------------------------------------------

def save_fallback(result_text: str) -> None:
    """
    Persist a known-good campaign result to ``data/fallback_result.json``.

    Called automatically by crew.main() after every successful run.
    Safe to call with an empty / None result - silently skips in that case.
    """
    if not result_text or not str(result_text).strip():
        return
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at": date.today().isoformat(),
        "result": str(result_text),
    }
    FALLBACK_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_fallback() -> dict | None:
    """
    Load the cached fallback result from ``data/fallback_result.json``.

    Returns ``{"saved_at": "YYYY-MM-DD", "result": "..."}``
    or ``None`` if the file is missing or corrupt.
    """
    if not FALLBACK_PATH.exists():
        return None
    try:
        data = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "result" in data:
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return None
