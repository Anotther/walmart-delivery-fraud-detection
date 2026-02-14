from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.audit_dashboard_theme import BLOCKING_RULES, DEFAULT_TARGETS, run_audit, scan_file


def test_scan_file_detects_white_plot_bg(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text("fig.update_layout(plot_bgcolor='white')\n", encoding="utf-8")

    findings = scan_file(sample, BLOCKING_RULES)
    assert findings
    assert findings[0].rule_name == "plotly-white-plot-bg"


def test_repository_passes_theme_audit_strict():
    repo_root = Path(__file__).resolve().parents[2]
    findings = run_audit(repo_root=repo_root, targets=DEFAULT_TARGETS, strict=True)
    assert findings == []
