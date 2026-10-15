# SPDX-License-Identifier: MPL-2.0
"""Conservative portable path rules for an UNAPPROVED OHA manifest proposal.

Research only. Never use string checks as a substitute for descriptor-relative
extraction and filesystem race protection.
"""

from __future__ import annotations

import re
import unicodedata

MAX_CANDIDATE_PATH_BYTES = 4096
MAX_CANDIDATE_COMPONENT_BYTES = 255
MAX_CANDIDATE_DEPTH = 64
MAX_CANDIDATE_ENTRIES = 1_000_000
FORBIDDEN_WINDOWS_CHARS = set('<>:"\\|?*')
DEVICE = re.compile(r"^(?:con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])$")


class CandidatePathError(ValueError):
    pass


def validate_candidate_path(path: str, *, max_bytes: int = MAX_CANDIDATE_PATH_BYTES,
                            max_depth: int = MAX_CANDIDATE_DEPTH) -> str:
    """Reject unsafe or non-portable relative names without normalizing away bytes."""
    if not isinstance(path, str) or not path:
        raise CandidatePathError("empty or non-Unicode relative path")
    if max_bytes < 1 or max_depth < 1:
        raise ValueError("invalid path resource budget")
    try:
        raw = path.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise CandidatePathError("undecodable Unicode surrogate") from exc
    if len(raw) > max_bytes:
        raise CandidatePathError("path byte budget")
    if unicodedata.normalize("NFC", path) != path:
        raise CandidatePathError("non-NFC path; cannot silently normalize")
    if path.startswith("/") or "\\" in path:
        raise CandidatePathError("absolute or backslash path")
    parts = path.split("/")
    if len(parts) > max_depth:
        raise CandidatePathError("path depth budget")
    for part in parts:
        if part in ("", ".", ".."):
            raise CandidatePathError("empty/current/parent path component")
        if len(part.encode("utf-8")) > MAX_CANDIDATE_COMPONENT_BYTES:
            raise CandidatePathError("component byte budget")
        if part.endswith((" ", ".")):
            raise CandidatePathError("Windows trailing dot/space")
        if any(ch in FORBIDDEN_WINDOWS_CHARS or
               unicodedata.category(ch) == "Cc" for ch in part):
            raise CandidatePathError("Windows-reserved or control character")
        if DEVICE.fullmatch(part.split(".", 1)[0].casefold()):
            raise CandidatePathError("Windows reserved device name")
    return path


def validate_candidate_tree(entries: list[tuple[str, str]], *,
                            max_entries: int = MAX_CANDIDATE_ENTRIES) -> dict[str, int]:
    """Reject collisions in a *candidate* file/dir manifest, with no filesystem writes.

    Casefold is intentionally conservative, not an exact model of any target
    filesystem's Unicode rules. Runtime extraction still needs per-volume checks.
    """
    if max_entries < 0:
        raise ValueError("invalid entry budget")
    if len(entries) > max_entries:
        raise CandidatePathError("manifest entry count budget")
    names: dict[str, tuple[str, str]] = {}
    prefix_names: dict[str, str] = {}
    for item in entries:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise CandidatePathError("malformed candidate entry")
        path, kind = item
        validate_candidate_path(path)
        if kind not in ("file", "dir"):
            raise CandidatePathError("unsupported candidate entry type")
        key = path.casefold()
        if key in names:
            raise CandidatePathError("duplicate or case-colliding path")
        names[key] = (path, kind)
        parts = path.split("/")
        for depth in range(1, len(parts) + 1):
            visible = "/".join(parts[:depth])
            folded = visible.casefold()
            prior = prefix_names.setdefault(folded, visible)
            if prior != visible:
                raise CandidatePathError("case-colliding directory component")
    for key, (path, _) in names.items():
        parts = key.split("/")
        for depth in range(1, len(parts)):
            parent = "/".join(parts[:depth])
            if parent in names and names[parent][1] != "dir":
                raise CandidatePathError("file cannot be an ancestor directory")
    return {"entries": len(entries), "file_entries": sum(k == "file" for _, k in names.values()),
            "directory_entries": sum(k == "dir" for _, k in names.values())}
