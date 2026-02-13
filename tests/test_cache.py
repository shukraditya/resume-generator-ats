"""Tests for the caching module."""

import pytest
import time
from src.cache import (
    get_cache_key,
    get_cached_pdf,
    get_cached_latex,
    get_cached_ats,
    cache_result,
    get_cache_status,
    clear_cache,
    get_cache_stats,
    ATS_CACHE_TTL,
)


class TestCacheKey:
    """Test cache key generation."""

    def test_same_content_same_key(self):
        """Identical content should produce identical keys."""
        text1 = "# Resume\n\nName: John"
        text2 = "# Resume\n\nName: John"
        assert get_cache_key(text1) == get_cache_key(text2)

    def test_different_content_different_key(self):
        """Different content should produce different keys."""
        text1 = "# Resume\n\nName: John"
        text2 = "# Resume\n\nName: Jane"
        assert get_cache_key(text1) != get_cache_key(text2)

    def test_normalization_whitespace(self):
        """Leading/trailing whitespace should be normalized."""
        text1 = "  # Resume\n\nName: John  "
        text2 = "# Resume\n\nName: John"
        assert get_cache_key(text1) == get_cache_key(text2)

    def test_normalization_case(self):
        """Case should be normalized (lowercased)."""
        text1 = "# RESUME\n\nName: JOHN"
        text2 = "# resume\n\nname: john"
        assert get_cache_key(text1) == get_cache_key(text2)

    def test_normalization_line_endings(self):
        """Line endings should be normalized."""
        text1 = "# Resume\r\n\r\nName: John"
        text2 = "# Resume\n\nName: John"
        assert get_cache_key(text1) == get_cache_key(text2)

    def test_key_length(self):
        """Key should be 16 characters (hex)."""
        key = get_cache_key("test content")
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)


class TestCacheStorage:
    """Test cache storage and retrieval."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_cache_pdf(self):
        """PDF bytes can be cached and retrieved."""
        key = "test_key_123"
        pdf_bytes = b"%PDF-1.4 fake pdf content"

        cache_result(key, pdf=pdf_bytes)

        assert get_cached_pdf(key) == pdf_bytes

    def test_cache_latex(self):
        """LaTeX content can be cached and retrieved."""
        key = "test_key_123"
        latex = "\\documentclass{article}"

        cache_result(key, latex=latex)

        assert get_cached_latex(key) == latex

    def test_cache_ats(self):
        """ATS report can be cached and retrieved."""
        key = "test_key_123"
        ats_report = {"score": 85, "keywords": ["python"]}

        cache_result(key, ats=ats_report)

        assert get_cached_ats(key) == ats_report

    def test_cache_all_together(self):
        """All types can be cached together."""
        key = "test_key_123"
        pdf = b"pdf bytes"
        latex = "latex content"
        ats = {"score": 90}

        cache_result(key, pdf=pdf, latex=latex, ats=ats)

        assert get_cached_pdf(key) == pdf
        assert get_cached_latex(key) == latex
        assert get_cached_ats(key) == ats

    def test_cache_miss_returns_none(self):
        """Cache miss should return None."""
        assert get_cached_pdf("nonexistent") is None
        assert get_cached_latex("nonexistent") is None
        assert get_cached_ats("nonexistent") is None

    def test_cache_update(self):
        """Cache can be updated with new values."""
        key = "test_key_123"

        cache_result(key, pdf=b"original")
        assert get_cached_pdf(key) == b"original"

        cache_result(key, pdf=b"updated")
        assert get_cached_pdf(key) == b"updated"


class TestCacheExpiration:
    """Test ATS cache expiration."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_ats_expires_after_ttl(self, monkeypatch):
        """ATS cache should expire after TTL."""
        key = "test_key_123"
        ats = {"score": 85}

        # Mock time to control expiration
        current_time = time.time()
        monkeypatch.setattr(time, "time", lambda: current_time)

        cache_result(key, ats=ats)
        assert get_cached_ats(key) == ats

        # Advance time past TTL
        monkeypatch.setattr(time, "time", lambda: current_time + ATS_CACHE_TTL + 1)
        assert get_cached_ats(key) is None

    def test_pdf_does_not_expire(self, monkeypatch):
        """PDF cache should not expire."""
        key = "test_key_123"
        pdf = b"pdf content"

        current_time = time.time()
        monkeypatch.setattr(time, "time", lambda: current_time)

        cache_result(key, pdf=pdf)

        # Advance time far into future
        monkeypatch.setattr(time, "time", lambda: current_time + ATS_CACHE_TTL * 1000)
        assert get_cached_pdf(key) == pdf

    def test_latex_does_not_expire(self, monkeypatch):
        """LaTeX cache should not expire."""
        key = "test_key_123"
        latex = "latex content"

        current_time = time.time()
        monkeypatch.setattr(time, "time", lambda: current_time)

        cache_result(key, latex=latex)

        # Advance time far into future
        monkeypatch.setattr(time, "time", lambda: current_time + ATS_CACHE_TTL * 1000)
        assert get_cached_latex(key) == latex


class TestCacheStatus:
    """Test cache status reporting."""

    def setup_method(self):
        clear_cache()

    def test_status_no_cache(self):
        """Status for non-existent key."""
        status = get_cache_status("nonexistent")
        assert status == {"exists": False}

    def test_status_with_pdf_only(self):
        """Status when only PDF cached."""
        key = "test_key_123"
        cache_result(key, pdf=b"pdf")

        status = get_cache_status(key)
        assert status["exists"] is True
        assert status["has_pdf"] is True
        assert status["has_latex"] is False
        assert status["has_ats"] is False

    def test_status_with_all(self):
        """Status when all types cached."""
        key = "test_key_123"
        cache_result(key, pdf=b"pdf", latex="latex", ats={"score": 85})

        status = get_cache_status(key)
        assert status["exists"] is True
        assert status["has_pdf"] is True
        assert status["has_latex"] is True
        assert status["has_ats"] is True
        assert status["ats_expired"] is False


class TestCacheStats:
    """Test cache statistics."""

    def setup_method(self):
        clear_cache()

    def test_empty_stats(self):
        """Stats for empty cache."""
        stats = get_cache_stats()
        assert stats == {
            "total_entries": 0,
            "with_pdf": 0,
            "with_latex": 0,
            "with_valid_ats": 0,
        }

    def test_stats_with_entries(self):
        """Stats with multiple entries."""
        cache_result("key1", pdf=b"pdf")
        cache_result("key2", latex="latex")
        cache_result("key3", ats={"score": 85})

        stats = get_cache_stats()
        assert stats["total_entries"] == 3
        assert stats["with_pdf"] == 1
        assert stats["with_latex"] == 1
        assert stats["with_valid_ats"] == 1

    def test_clear_cache(self):
        """Clear cache removes all entries."""
        cache_result("key1", pdf=b"pdf")
        cache_result("key2", latex="latex")

        assert get_cache_stats()["total_entries"] == 2

        clear_cache()

        assert get_cache_stats()["total_entries"] == 0
