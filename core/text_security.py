"""
Shared validation for public plain-text and search input (XSS hardening, control bytes).
Django’s ORM parameterizes queries (SQLi-safe); this layer blocks obvious script/HTML
fragments in text fields and limits search length.
"""
import re
from typing import Any

from django.core.exceptions import ValidationError

# Blocks common reflected/stored XSS vectors in *plain* text (not for trusted rich HTML)
_DANGEROUS_PLAINTEXT = re.compile(
    r'<\s*script|</\s*script|<\s*iframe|<\s*object|<\s*embed|'
    r'<\s*svg\b[^>]*\bon\w+|<\s*img\b[^>]*\bon\w+|'
    r'javascript\s*:|vbscript\s*:|data\s*:\s*text/html|'
    r'on\w+\s*=|expression\s*\(|<\s*meta\b',
    re.IGNORECASE | re.DOTALL,
)

def _raise_if_bytes(value: Any, message: str) -> str:
    s = str(value) if value is not None else ''
    if not s:
        return s
    if '\x00' in s:
        raise ValidationError(message, code='invalid_characters')
    for c in s:
        if ord(c) < 32 and c not in '\n\r\t':
            raise ValidationError(message, code='invalid_characters')
    return s


def validate_plain_text(
    value: str,
    *,
    field_name: str = 'This field',
) -> str:
    """Validate name, message, etc.: no nulls/control chars, no script-like fragments."""
    s = _raise_if_bytes(
        value,
        'This field contains invalid control characters. Please use normal text only.',
    )
    s = s.strip()
    if not s:
        return s
    if _DANGEROUS_PLAINTEXT.search(s):
        raise ValidationError(
            '%(name)s may not include HTML, scripts, or disallowed code. Please use plain text only.',
            code='unsafe_content',
            params={'name': field_name},
        )
    return s


def validate_search_query(value: str) -> str:
    """
    Shorter search string: length cap, no control characters, no obvious XSS probes.
    Does not use aggressive SQL word blocking to avoid false positives in Nepali/English.
    """
    s = (value or '').strip()
    if not s:
        return ''
    if len(s) > 200:
        raise ValidationError(
            'Search text is too long. Use at most 200 characters.',
            code='search_too_long',
        )
    s = _raise_if_bytes(
        s,
        'Search contains invalid characters. Remove unusual symbols and try again.',
    )
    if _DANGEROUS_PLAINTEXT.search(s):
        raise ValidationError(
            'That search is not valid. Do not use HTML, scripts, or code in the search box.',
            code='unsafe_search',
        )
    return s
