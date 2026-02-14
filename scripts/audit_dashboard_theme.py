#!/usr/bin/env python3
"""Static audit rules for dashboard light/dark theme consistency."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_TARGETS = [
    "dashboard/app.py",
    "dashboard/pages/*.py",
    "src/dashboard/components.py",
    "src/dashboard/theme.py",
    "dashboard/styles/main.css",
]


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class Finding:
    file_path: Path
    line_no: int
    rule_name: str
    message: str
    line_text: str


BLOCKING_RULES: Sequence[Rule] = (
    Rule(
        name="plotly-white-plot-bg",
        pattern=re.compile(r"plot_bgcolor\s*=\s*['\"]white['\"]", re.IGNORECASE),
        message="Use theme token (COLORS['plot_bg']) or apply_plotly_theme(), not literal white.",
    ),
    Rule(
        name="plotly-white-paper-bg",
        pattern=re.compile(r"paper_bgcolor\s*=\s*['\"]white['\"]", re.IGNORECASE),
        message="Use theme token (COLORS['paper_bg']) or apply_plotly_theme(), not literal white.",
    ),
    Rule(
        name="plotly-font-inter-hardcoded",
        pattern=re.compile(r"font_family\s*=\s*['\"]Inter['\"]", re.IGNORECASE),
        message="Use theme token (COLORS['font_family']) or apply_plotly_theme(), not literal Inter.",
    ),
)


def iter_target_files(repo_root: Path, targets: Sequence[str]) -> List[Path]:
    files: List[Path] = []
    for target in targets:
        if any(char in target for char in "*?[]"):
            files.extend(sorted(repo_root.glob(target)))
        else:
            candidate = repo_root / target
            if candidate.exists():
                files.append(candidate)
    return sorted({file.resolve() for file in files if file.is_file()})


def scan_file(path: Path, rules: Sequence[Rule]) -> List[Finding]:
    findings: List[Finding] = []
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")

    for idx, line in enumerate(content.splitlines(), start=1):
        for rule in rules:
            if rule.pattern.search(line):
                findings.append(
                    Finding(
                        file_path=path,
                        line_no=idx,
                        rule_name=rule.name,
                        message=rule.message,
                        line_text=line.strip(),
                    )
                )
    return findings


def run_audit(repo_root: Path, targets: Sequence[str], strict: bool = False) -> List[Finding]:
    _ = strict  # Reserved flag for future rule expansion.
    files = iter_target_files(repo_root, targets)
    findings: List[Finding] = []
    for file_path in files:
        findings.extend(scan_file(file_path, BLOCKING_RULES))
    return findings


def format_findings(findings: Iterable[Finding], repo_root: Path) -> str:
    lines = []
    for finding in findings:
        rel_path = finding.file_path.relative_to(repo_root)
        lines.append(
            f"- {rel_path}:{finding.line_no} [{finding.rule_name}] {finding.message}\n"
            f"  {finding.line_text}"
        )
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit dashboard theme hardcoding rules")
    parser.add_argument("--strict", action="store_true", help="Run strict policy (reserved for compatibility)")
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Optional additional target pattern relative to repo root",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path(__file__).resolve().parent.parent

    targets = list(DEFAULT_TARGETS)
    if args.target:
        targets.extend(args.target)

    findings = run_audit(repo_root=repo_root, targets=targets, strict=args.strict)
    if findings:
        print("Dashboard theme audit failed. Blocking findings:\n")
        print(format_findings(findings, repo_root))
        return 1

    mode_label = "strict" if args.strict else "standard"
    print(f"Dashboard theme audit passed ({mode_label}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
