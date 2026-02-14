from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import src.dashboard.components as dashboard_components


def test_kpi_card_escapes_dynamic_fields_by_default(monkeypatch):
    captured: dict[str, str] = {}

    def fake_markdown(html: str, unsafe_allow_html: bool = False):  # noqa: ARG001
        captured["html"] = html

    monkeypatch.setattr(dashboard_components.st, "markdown", fake_markdown)

    dashboard_components.kpi_card(
        title="<b>Risk</b>",
        value="<script>alert('x')</script>",
        delta='<img src=x onerror="alert(1)">',
        tooltip='test "quote"',
    )

    html = captured["html"]
    assert "<script>" not in html
    assert "&lt;script&gt;alert(" in html
    assert "&lt;b&gt;Risk&lt;/b&gt;" in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html


def test_kpi_card_allows_html_value_when_enabled(monkeypatch):
    captured: dict[str, str] = {}

    def fake_markdown(html: str, unsafe_allow_html: bool = False):  # noqa: ARG001
        captured["html"] = html

    monkeypatch.setattr(dashboard_components.st, "markdown", fake_markdown)

    dashboard_components.kpi_card(
        title="KPI",
        value="<strong>42</strong>",
        allow_html_value=True,
    )

    assert "<strong>42</strong>" in captured["html"]


def test_insight_card_escapes_content_by_default(monkeypatch):
    captured: dict[str, str] = {}

    def fake_markdown(html: str, unsafe_allow_html: bool = False):  # noqa: ARG001
        captured["html"] = html

    monkeypatch.setattr(dashboard_components.st, "markdown", fake_markdown)

    dashboard_components.insight_card(
        title="Insight",
        content="<script>alert('x')</script>",
        icon="Signal",
        compact=True,
    )

    html = captured["html"]
    assert "<script>" not in html
    assert "&lt;script&gt;alert('x')&lt;/script&gt;" in html


def test_insight_card_keeps_html_when_explicitly_allowed(monkeypatch):
    captured: dict[str, str] = {}

    def fake_markdown(html: str, unsafe_allow_html: bool = False):  # noqa: ARG001
        captured["html"] = html

    monkeypatch.setattr(dashboard_components.st, "markdown", fake_markdown)

    dashboard_components.insight_card(
        title="Insight",
        content="Line A<br>Line B",
        icon="Signal",
        allow_html=True,
    )

    assert "Line A<br>Line B" in captured["html"]
