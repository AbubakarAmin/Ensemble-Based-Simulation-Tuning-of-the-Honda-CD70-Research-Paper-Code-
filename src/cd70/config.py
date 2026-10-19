"""Load the YAML config files and map unit-interval samples to input dictionaries. LOCKED FILE for the agent."""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def priors() -> dict:
    return _load("priors.yaml")


def calibration() -> dict:
    return _load("calibration.yaml")


def scenarios() -> dict:
    return _load("scenarios.yaml")


def optimiser() -> dict:
    return _load("optimiser.yaml")


def validation() -> dict:
    return _load("validation.yaml")


def seeds() -> dict:
    return _load("seeds.yaml")


def uncertain_names() -> list:
    return [d["name"] for d in priors()["uncertain"]]


def design_names() -> list:
    return [d["name"] for d in priors()["design"]]


def nominal_unc() -> dict:
    return {d["name"]: float(d["nominal"]) for d in priors()["uncertain"]}


def baseline_design() -> dict:
    return {d["name"]: float(d["baseline"]) for d in priors()["design"]}


def unit_to_unc(u: np.ndarray) -> list:
    """u: (n, 32) in [0,1]. Returns a list of n dicts of uncertain inputs."""
    spec = priors()["uncertain"]
    u = np.atleast_2d(u)
    assert u.shape[1] == len(spec), (u.shape, len(spec))
    out = []
    for row in u:
        d = {}
        for x, s in zip(row, spec):
            if s["dist"] == "uniform":
                v = s["low"] + x * (s["high"] - s["low"])
            elif s["dist"] == "loguniform":
                v = math.exp(math.log(s["low"]) + x * (math.log(s["high"]) - math.log(s["low"])))
            elif s["dist"] == "discrete":
                vals = s["values"]
                v = vals[min(int(x * len(vals)), len(vals) - 1)]
            else:
                raise ValueError(s["dist"])
            d[s["name"]] = float(v)
        out.append(d)
    return out


def unit_to_design(u: np.ndarray, names: list | None = None) -> list:
    """u: (n, len(names)) in [0,1]. Variables not in `names` stay at baseline. Integer variables are rounded."""
    spec = {d["name"]: d for d in priors()["design"]}
    names = names or design_names()
    u = np.atleast_2d(u)
    base = baseline_design()
    out = []
    for row in u:
        d = dict(base)
        for x, n in zip(row, names):
            s = spec[n]
            v = s["low"] + float(x) * (s["high"] - s["low"])
            d[n] = float(round(v)) if s["integer"] else float(v)
        out.append(d)
    return out


def design_bounds(names: list | None = None) -> tuple:
    spec = {d["name"]: d for d in priors()["design"]}
    names = names or design_names()
    return (np.array([spec[n]["low"] for n in names], float), np.array([spec[n]["high"] for n in names], float))


def hardware_class(cls: str) -> list:
    return list(priors()["hardware_classes"][cls])
