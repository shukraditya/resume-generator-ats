"""Utilities for parsing and applying unified git diffs."""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DiffHunk:
    """Represents a single hunk in a unified diff."""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]


@dataclass
class DiffFile:
    """Represents a file diff in unified format."""
    old_file: str
    new_file: str
    hunks: List[DiffHunk]


def parse_unified_diff(diff_text: str) -> Optional[DiffFile]:
    """
    Parse a unified diff into structured components.

    Args:
        diff_text: The unified diff string

    Returns:
        DiffFile object or None if parsing fails
    """
    lines = diff_text.strip().split('\n')
    if len(lines) < 2:
        return None

    # Parse --- and +++ lines
    old_file = None
    new_file = None
    hunk_start_idx = 0

    for i, line in enumerate(lines):
        if line.startswith('---'):
            old_file = line[4:].strip()
            # Remove any timestamp after filename
            old_file = old_file.split('\t')[0].strip()
        elif line.startswith('+++'):
            new_file = line[4:].strip()
            new_file = new_file.split('\t')[0].strip()
            hunk_start_idx = i + 1
            break

    if not old_file or not new_file:
        return None

    # Parse hunks
    hunks = []
    current_hunk = None
    current_lines = []

    for i in range(hunk_start_idx, len(lines)):
        line = lines[i]

        # Check for hunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            if current_hunk:
                current_hunk.lines = current_lines
                hunks.append(current_hunk)
                current_lines = []

            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

            current_hunk = DiffHunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                lines=[]
            )
        elif current_hunk is not None:
            current_lines.append(line)

    if current_hunk:
        current_hunk.lines = current_lines
        hunks.append(current_hunk)

    return DiffFile(old_file=old_file, new_file=new_file, hunks=hunks)


def apply_unified_diff(original_content: str, diff_text: str) -> Tuple[bool, str, Optional[str]]:
    """
    Apply a unified diff to original content.

    Args:
        original_content: The original file content
        diff_text: The unified diff to apply

    Returns:
        Tuple of (success, result_content, error_message)
    """
    try:
        diff = parse_unified_diff(diff_text)
        if not diff:
            return False, original_content, "Failed to parse diff"

        lines = original_content.split('\n')
        result_lines = []
        current_line = 0

        for hunk in diff.hunks:
            # Add lines before this hunk
            hunk_old_start = hunk.old_start
            # Convert from 1-indexed to 0-indexed
            start_idx = hunk_old_start - 1

            # Add unchanged lines before this hunk
            while current_line < start_idx and current_line < len(lines):
                result_lines.append(lines[current_line])
                current_line += 1

            # Apply hunk lines
            for line in hunk.lines:
                if line.startswith(' '):
                    # Context line - should match original
                    result_lines.append(line[1:])
                    current_line += 1
                elif line.startswith('-'):
                    # Removed line - skip it
                    expected = line[1:]
                    if current_line < len(lines) and lines[current_line] == expected:
                        current_line += 1
                    # If it doesn't match, we still skip (fuzzy matching)
                elif line.startswith('+'):
                    # Added line - include it
                    result_lines.append(line[1:])
                elif line.startswith('\\'):
                    # "\ No newline at end of file" - ignore
                    pass

        # Add remaining lines after last hunk
        while current_line < len(lines):
            result_lines.append(lines[current_line])
            current_line += 1

        return True, '\n'.join(result_lines), None

    except Exception as e:
        return False, original_content, str(e)


def create_unified_diff(old_content: str, new_content: str, old_filename: str = "a/resume.tex",
                         new_filename: str = "b/resume.tex", context: int = 3) -> str:
    """
    Create a unified diff between two strings.

    Args:
        old_content: Original content
        new_content: New content
        old_filename: Filename for old file
        new_filename: Filename for new file
        context: Number of context lines

    Returns:
        Unified diff string
    """
    import difflib

    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=old_filename,
        tofile=new_filename,
        lineterm='',
        n=context
    )

    return '\n'.join(diff)


def find_line_number(content: str, search_text: str, start_from: int = 0) -> Optional[int]:
    """
    Find the line number of a search text in content.

    Args:
        content: The content to search
        search_text: Text to find
        start_from: Line number to start from (0-indexed)

    Returns:
        Line number (0-indexed) or None if not found
    """
    lines = content.split('\n')
    for i in range(start_from, len(lines)):
        if search_text in lines[i]:
            return i
    return None


def apply_suggestions_sequential(latex_content: str, suggestions: List) -> Tuple[str, List[bool]]:
    """
    Apply multiple suggestions sequentially.

    Args:
        latex_content: Original LaTeX content
        suggestions: List of LaTeXSuggestion objects

    Returns:
        Tuple of (final_content, list_of_success_status)
    """
    current_content = latex_content
    results = []

    for suggestion in suggestions:
        success, new_content, error = apply_unified_diff(current_content, suggestion.diff)
        if success:
            current_content = new_content
        results.append(success)

    return current_content, results
