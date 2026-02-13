"""Shared caching module for PDF generation and ATS analysis results."""

import hashlib
import time
from typing import Optional


# In-memory cache: hash -> {pdf_bytes, latex_content, ats_report, timestamp}
_cache: dict[str, dict] = {}

# TTL in seconds (1 hour for ATS analysis)
ATS_CACHE_TTL = 3600
# No TTL for PDF (deterministic generation)


def get_cache_key(resume_text: str) -> str:
    """
    Generate cache key from resume text.
    Uses SHA256 hash of normalized text (first 16 chars).
    """
    normalized = resume_text.strip().lower().replace('\r\n', '\n')
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _is_expired(timestamp: float, ttl: Optional[int] = None) -> bool:
    """Check if cached entry has expired."""
    if ttl is None:
        return False  # No expiration
    return time.time() - timestamp > ttl


def get_cached_pdf(key: str) -> Optional[bytes]:
    """Get cached PDF bytes if available and not expired."""
    if key not in _cache:
        return None
    entry = _cache[key]
    # PDF has no TTL (deterministic)
    return entry.get('pdf')


def get_cached_latex(key: str) -> Optional[str]:
    """Get cached LaTeX content if available."""
    if key not in _cache:
        return None
    entry = _cache[key]
    return entry.get('latex')


def get_cached_ats(key: str) -> Optional[dict]:
    """Get cached ATS report if available and not expired (1 hour TTL)."""
    if key not in _cache:
        return None
    entry = _cache[key]
    if _is_expired(entry.get('timestamp', 0), ATS_CACHE_TTL):
        # Clear ATS portion only, keep PDF
        entry['ats'] = None
        return None
    return entry.get('ats')


def cache_result(
    key: str,
    pdf: Optional[bytes] = None,
    latex: Optional[str] = None,
    ats: Optional[dict] = None
) -> None:
    """
    Cache generation results.

    Args:
        key: Cache key from get_cache_key()
        pdf: Generated PDF bytes
        latex: LaTeX source content
        ats: ATS analysis report dict
    """
    if key not in _cache:
        _cache[key] = {'timestamp': time.time()}

    if pdf is not None:
        _cache[key]['pdf'] = pdf
    if latex is not None:
        _cache[key]['latex'] = latex
    if ats is not None:
        _cache[key]['ats'] = ats
        _cache[key]['timestamp'] = time.time()


def get_cache_status(key: str) -> dict:
    """Get cache status for debugging/monitoring."""
    if key not in _cache:
        return {'exists': False}

    entry = _cache[key]
    now = time.time()
    ats_expired = _is_expired(entry.get('timestamp', 0), ATS_CACHE_TTL)

    return {
        'exists': True,
        'has_pdf': 'pdf' in entry,
        'has_latex': 'latex' in entry,
        'has_ats': 'ats' in entry and not ats_expired,
        'ats_expired': ats_expired,
        'age_seconds': int(now - entry.get('timestamp', now))
    }


def clear_cache() -> None:
    """Clear all cached entries."""
    _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    now = time.time()
    total = len(_cache)
    has_pdf = sum(1 for e in _cache.values() if 'pdf' in e)
    has_latex = sum(1 for e in _cache.values() if 'latex' in e)
    has_ats = sum(1 for e in _cache.values() if 'ats' in e and not _is_expired(e.get('timestamp', 0), ATS_CACHE_TTL))

    return {
        'total_entries': total,
        'with_pdf': has_pdf,
        'with_latex': has_latex,
        'with_valid_ats': has_ats
    }
