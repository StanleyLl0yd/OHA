"""Reject high-risk GitHub Actions workflow configurations without third-party YAML dependencies."""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PINNED_ACTION = re.compile(r"^(?:[\w.-]+/)+[\w.-]+@[0-9a-f]{40}$")
PINNED_IMAGE = re.compile(r"\S+@sha256:[0-9a-f]{64}$")


def verify() -> list[str]:
    errors: list[str] = []
    workflows = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    if not workflows:
        return ["No CI workflows found"]
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*pull_request_target\s*:", text):
            errors.append(f"{path.name}: pull_request_target is prohibited")
        if re.search(r"(?m)^\s*permissions\s*:\s*(?:write-all|read-all)\s*$", text):
            errors.append(f"{path.name}: broad permissions declaration")
        if not re.search(r"(?m)^permissions:\s*\{\s*\}\s*$", text):
            errors.append(f"{path.name}: top-level permissions must be {{}}")
        for number, line in enumerate(text.splitlines(), 1):
            action = re.match(r"\s*-?\s*uses:\s*([^\s#]+)", line)
            if action and not action.group(1).startswith("./") and not PINNED_ACTION.fullmatch(action.group(1)):
                errors.append(f"{path.name}:{number}: action must be pinned by 40-char SHA")
            image = re.match(r"\s*image:\s*([^\s#]+)", line)
            if image and not PINNED_IMAGE.fullmatch(image.group(1)):
                errors.append(f"{path.name}:{number}: container image must be pinned by digest")
    return errors


if __name__ == "__main__":
    found = verify()
    if found:
        raise SystemExit("\n".join(found))
    print("CI supply-chain policy PASS")
