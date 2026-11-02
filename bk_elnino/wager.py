"""Contract statistic, decision threshold and operating characteristics.

M = mean over the target window of 100 * [log y_t(actual) - log yhat_t(no-effect path)],
re-based to the base year: with a one-year window, per-capita growth from the base year to
the end year minus baseline growth over the same years. The question asks whether growth
beats the cutoff, so it resolves No (the outcome Bilal-Kaenzig predict) when M <= c and
Yes when M > c. Sensitivity = P(No | paper right); false positive = P(No | no effect).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


def window_mean(D: np.ndarray, years, window: tuple[int, int]) -> np.ndarray:
    years = np.asarray(list(years))
    sel = (years >= window[0]) & (years <= window[1])
    if sel.sum() != window[1] - window[0] + 1:
        raise ValueError("window not fully inside the simulated years")
    return np.atleast_2d(D)[:, sel].mean(axis=1)


@dataclass
class OperatingCharacteristics:
    threshold: float                 # c, in percent log deviation (resolves No if M <= c)
    threshold_pct_level: float       # 100*(exp(c/100)-1)
    sensitivity: float               # P_H1(M <= c)  (true-positive rate)
    false_positive: float            # P_H0(M <= c)  (Type I error)
    specificity: float
    false_negative: float            # Type II error
    youden_j: float
    overlap: float                   # overlapping coefficient of the two densities
    mean_h0: float
    mean_h1: float
    sd_h0: float
    sd_h1: float
    auc: float

    def as_dict(self):
        return asdict(self)


def overlap_coefficient(a: np.ndarray, b: np.ndarray, bins: int = 400) -> float:
    lo, hi = min(a.min(), b.min()), max(a.max(), b.max())
    edges = np.linspace(lo, hi, bins + 1)
    pa, _ = np.histogram(a, edges, density=True)
    pb, _ = np.histogram(b, edges, density=True)
    return float(np.minimum(pa, pb).sum() * (edges[1] - edges[0]))


def auc(m0: np.ndarray, m1: np.ndarray) -> float:
    """P(M_H1 < M_H0): probability a random H1 outcome is lower than a random H0 outcome."""
    allv = np.concatenate([m1, m0])
    ranks = allv.argsort().argsort() + 1.0
    r1 = ranks[: len(m1)].sum()
    n1, n0 = len(m1), len(m0)
    u = r1 - n1 * (n1 + 1) / 2
    return float(1 - u / (n1 * n0))


def evaluate(m0: np.ndarray, m1: np.ndarray, c: float) -> OperatingCharacteristics:
    sens = float((m1 <= c).mean())
    fpr = float((m0 <= c).mean())
    return OperatingCharacteristics(
        float(c), float(100 * (np.exp(c / 100) - 1)), sens, fpr, 1 - fpr, 1 - sens, sens - fpr,
        overlap_coefficient(m0, m1), float(m0.mean()), float(m1.mean()), float(m0.std()),
        float(m1.std()), auc(m0, m1))


def youden_threshold(m0: np.ndarray, m1: np.ndarray, tol: float = 0.0025) -> OperatingCharacteristics:
    """c maximising J(c) = P_H1(M<=c) - P_H0(M<=c).

    J is flat near its optimum and the empirical argmax jitters with Monte Carlo noise,
    so c is the median of all candidates whose J is within ``tol`` of the maximum
    (tol ~ one Monte Carlo s.e. of J at 50,000 paths). Deterministic given the seed.
    """
    cand = np.quantile(np.concatenate([m0, m1]), np.linspace(0.001, 0.999, 20001))
    s0, s1 = np.sort(m0), np.sort(m1)
    F0 = np.searchsorted(s0, cand, side="right") / len(s0)
    F1 = np.searchsorted(s1, cand, side="right") / len(s1)
    J = F1 - F0
    near = np.flatnonzero(J >= J.max() - tol)
    c = float(np.median(cand[near]))
    return evaluate(m0, m1, c)


def loss_threshold(m0: np.ndarray, m1: np.ndarray, prior_h1: float = 0.5, cost_fp: float = 1.0,
                   cost_fn: float = 1.0) -> OperatingCharacteristics:
    """c minimising expected loss (1-p) cost_fp P_H0(M<=c) + p cost_fn P_H1(M>c)."""
    cand = np.quantile(np.concatenate([m0, m1]), np.linspace(0, 1, 20001))
    s0, s1 = np.sort(m0), np.sort(m1)
    F0 = np.searchsorted(s0, cand, side="right") / len(s0)
    F1 = np.searchsorted(s1, cand, side="right") / len(s1)
    loss = (1 - prior_h1) * cost_fp * F0 + prior_h1 * cost_fn * (1 - F1)
    return evaluate(m0, m1, float(cand[np.argmin(loss)]))
