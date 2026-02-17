"""Pydantic/dataclass models for resume toolchain."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class LaTeXSuggestion:
    """A single ATS improvement suggestion for LaTeX."""
    id: str
    description: str
    target_section: str
    priority: int
    diff: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "target_section": self.target_section,
            "priority": self.priority,
            "diff": self.diff,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LaTeXSuggestion":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            target_section=data["target_section"],
            priority=data["priority"],
            diff=data["diff"],
            reason=data["reason"]
        )


@dataclass
class LaTeXImprovementResponse:
    """Response from ATS improvement endpoint."""
    suggestions: List[LaTeXSuggestion]
    overall_score: int
    target_score: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestions": [s.to_dict() for s in self.suggestions],
            "overall_score": self.overall_score,
            "target_score": self.target_score
        }


@dataclass
class DiffApplicationResult:
    """Result of applying a diff to LaTeX content."""
    success: bool
    updated_latex: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "updated_latex": self.updated_latex,
            "error": self.error
        }
