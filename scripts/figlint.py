"""Axis-label lint. Every visible axis with data must have x and y labels (heatmap/bar ticks count as data)."""
import sys


def lint(fig, name):
    bad = []
    for ax in fig.axes:
        if ax.get_label() == "<colorbar>":
            continue
        if not ax.axison or not ax.get_visible():
            continue
        if not (ax.lines or ax.collections or ax.patches or ax.images):
            continue
        if not ax.get_xlabel().strip():
            bad.append("x")
        if not ax.get_ylabel().strip():
            bad.append("y")
    if bad:
        sys.exit(f"FIGLINT FAIL {name}: missing axis label(s) {bad}. Add set_xlabel/set_ylabel with units.")
