#!/usr/bin/env python3
"""Project quality gate for the current development stage."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_DIRS = ["tools", "scripts", "docs", "references", "backend"]
TEXT_SUFFIXES = {".md", ".py", ".txt", ".example", ".gitignore"}
FORBIDDEN_FILES = {
    ".env",
    "backend/.env",
    "frontend/.env",
}
FORBIDDEN_TEXT = [
    "sk-" + "c70bf55508eb43b4918dfe994d0b8f8f",
]
FORBIDDEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{24,}"),
    re.compile(r"AKID[A-Za-z0-9]{12,}"),
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_files() -> list[Path]:
    files: list[Path] = []
    for dirname in CHECK_DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                files.append(path)
    for path in [ROOT / "README.md", ROOT / ".gitignore"]:
        if path.exists():
            files.append(path)
    return files


def check_forbidden_files(errors: list[str]) -> None:
    for forbidden in FORBIDDEN_FILES:
        if (ROOT / forbidden).exists():
            errors.append(f"Forbidden local secret file exists: {forbidden}")


def check_utf8_and_secrets(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix not in TEXT_SUFFIXES and path.name not in {".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"Not UTF-8: {rel(path)} ({exc})")
            continue
        for secret in FORBIDDEN_TEXT:
            if secret in text:
                errors.append(f"Forbidden secret text found in {rel(path)}")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                errors.append(f"Forbidden secret-like pattern found in {rel(path)}")


def check_python_syntax(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix != ".py":
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"Python syntax error in {rel(path)}: {exc}")


def main() -> int:
    errors: list[str] = []
    files = iter_files()
    check_forbidden_files(errors)
    check_utf8_and_secrets(files, errors)
    check_python_syntax(files, errors)

    if errors:
        print("Quality check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Quality check passed. Checked {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
