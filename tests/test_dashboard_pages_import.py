"""
Test suite: import-level validation for all Streamlit dashboard pages.

Each page module is imported in isolation inside a subprocess so that:
  - Streamlit's global state does not bleed between tests.
  - st.set_page_config() (which must be the first Streamlit call) can fire
    once per process without raising a duplicate-call error.
  - Heavy side-effects executed at module scope (data loading, etc.) are
    contained.

The parent process only checks the exit-code and stderr of each subprocess
and records success / failure accordingly.
"""

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
PAGES_DIR = PROJECT_ROOT / "dashboard" / "pages"

PAGE_FILES = [
    "1_Overview.py",
    "2_Monitor.py",
    "3_Drivers.py",
    "4_Customers.py",
    "5_Geographic.py",
    "6_Product_Analysis.py",
    "7_Methodology.py",
    "8_Patterns.py",
    "9_Model_Performance.py",
]

# ---------------------------------------------------------------------------
# Helper: run a single import inside a fresh interpreter
# ---------------------------------------------------------------------------

IMPORT_SNIPPET = """
import sys, importlib.util, traceback
sys.path.insert(0, {project_root!r})

# Minimal Streamlit stub so that st.set_page_config() and other top-level
# calls do not blow up outside a running Streamlit server.
#
# Strategy: use a MagicMock as the module object directly so that *any*
# attribute access (including st.page_link, st.sidebar, etc.) automatically
# returns another MagicMock without needing an explicit allowlist.
# cache_data and cache_resource are overridden to act as pass-through
# decorators so that @st.cache_data-decorated functions remain callable.
import unittest.mock

_permissive = unittest.mock.MagicMock()

# Make cache_data / cache_resource behave as pass-through decorators
def _passthrough_decorator(*args, **kwargs):
    if args and callable(args[0]):
        return args[0]
    def _wrap(fn):
        return fn
    return _wrap

_permissive.cache_data = _passthrough_decorator
_permissive.cache_resource = _passthrough_decorator
_permissive.session_state = {{}}
# context-manager support for "with st.sidebar:" and "with st.spinner():"
_permissive.__enter__ = lambda s, *a: s
_permissive.__exit__ = lambda s, *a: False

sys.modules["streamlit"] = _permissive
sys.modules["streamlit.components"] = _permissive
sys.modules["streamlit.components.v1"] = _permissive

page_path = {page_path!r}

try:
    spec = importlib.util.spec_from_file_location("_page_under_test", page_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("OK")
    sys.exit(0)
except Exception:
    traceback.print_exc()
    sys.exit(1)
"""


def _test_page(page_filename: str) -> tuple[bool, str]:
    """
    Spawn a subprocess that imports the given page file.

    Returns
    -------
    (success: bool, detail: str)
    """
    page_path = str(PAGES_DIR / page_filename)
    snippet = IMPORT_SNIPPET.format(
        project_root=str(PROJECT_ROOT),
        page_path=page_path,
    )

    result = subprocess.run(
        [sys.executable, "-c", snippet],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode == 0:
        return True, "Import successful"

    # Combine stdout + stderr for the error report
    detail = (result.stderr or "") + (result.stdout or "")
    return False, detail.strip()


# ---------------------------------------------------------------------------
# pytest tests (one per page)
# ---------------------------------------------------------------------------

import pytest


@pytest.mark.parametrize("page_filename", PAGE_FILES)
def test_page_imports_without_error(page_filename: str) -> None:
    """
    Verify that importing the page module does not raise any exception.

    A Streamlit stub replaces the real ``streamlit`` package so that
    UI calls at module scope (set_page_config, load_css, render_sidebar,
    etc.) are no-ops.  Any genuine ImportError, NameError, or other
    exception inside the page or one of its src.* dependencies will
    propagate and fail this test.
    """
    success, detail = _test_page(page_filename)
    assert success, (
        f"\n{'=' * 60}\n"
        f"Page '{page_filename}' failed to import.\n"
        f"{'=' * 60}\n"
        f"{detail}\n"
    )


# ---------------------------------------------------------------------------
# Standalone runner (python tests/test_dashboard_pages_import.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Dashboard Page Import Tests")
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Pages dir    : {PAGES_DIR}")
    print("=" * 70)

    results: list[tuple[str, bool, str]] = []

    for filename in PAGE_FILES:
        print(f"\nTesting: {filename} ...", end=" ", flush=True)
        success, detail = _test_page(filename)
        status = "PASS" if success else "FAIL"
        print(status)
        if not success:
            print(f"  Error detail:\n{detail}")
        results.append((filename, success, detail))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    for filename, ok, _ in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}]  {filename}")

    print(f"\nTotal: {len(results)}  |  Passed: {passed}  |  Failed: {failed}")
    print("=" * 70)

    if failed:
        sys.exit(1)
