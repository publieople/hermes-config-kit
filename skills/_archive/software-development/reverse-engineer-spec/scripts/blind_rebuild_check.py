"""Blind-rebuild verification harness — reverse-engineer-spec skill.

Use this as the template when step 9 of the skill calls for an objective
check that the spec is rebuild-ready. Copy to a scratch dir, fill in the
spec-derived expectations, and run. Pass = the spec was sufficient for the
chosen surface area; failure pinpoints the gap.

A spec is rebuild-ready iff a fresh agent can implement the documented
contracts without ever opening the source. The check below proves that
for whatever surface area you target.

Tested against `rich/console.py` on 2026-07-19: 7/7 pass.
"""

from typing import Any, Callable


# ---------- 1. Pick a small surface area to rebuild --------------------------
# Choose ONE of: a function, a class, a context manager, a Protocol. The point
# is to prove the spec, not to rebuild the whole module.
#
# Examples (from real stress-test against rich/console.py):
#   - ConsoleOptions.copy() + update(width=10)
#   - Console.render(object()) -> NotRenderableError
#   - Console.export_text() without record=True -> AssertionError byte-exact

# ---------- 2. Re-implement from spec ONLY -----------------------------------
# Re-read specs/<module>.spec.md and implement. DO NOT open the source.


def my_console_rebuild() -> Any:
    """Build the surface area. Implementation goes here."""
    raise NotImplementedError("Fill me from the spec")


# ---------- 3. Self-check covering 4 categories ------------------------------
# 1. byte-exact literal (error message / output prefix)
# 2. Protocol dispatch site
# 3. thread/lock/invariant if applicable
# 4. exception type raised


def run_checks() -> None:
    """Run all contract checks. Pass = spec is sufficient for this surface."""
    # --- Byte-exact literal ---
    try:
        my_console_rebuild().export_text()  # without record=True
    except AssertionError as ex:
        assert (
            str(ex)
            == "To export console contents set record=True in the constructor or instance"
        ), f"byte-exact assertion message mismatch: {ex!r}"

    # --- Protocol dispatch site ---
    # ... exercise the dispatch and assert outcome ...

    # --- Invariant ---
    # ... assert thread-local / lock / buffer index ...

    # --- Exception type ---
    # ... trigger the error path and assert exact class ...

    print("rebuild-check: N/N contract checks passed.")


if __name__ == "__main__":
    run_checks()