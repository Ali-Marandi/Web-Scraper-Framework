"""Anomaly Detection Module for Web Scraping Applications.

Provides statistical, change-point, drift, pattern, and scraping-specific
anomaly detection using only the standard library and NumPy.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_float_array(values: Sequence) -> NDArray[np.float64]:
    """Convert a sequence to a 1-D NumPy float64 array."""
    arr = np.array(values, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError("Input must be a 1-D sequence")
    return arr


def _norm_inv(p: float) -> float:
    """Rational approximation to the inverse normal CDF (Abramowitz & Stegun 26.2.23)."""
    if p <= 0.0: return float("-inf")
    if p >= 1.0: return float("inf")
    if p == 0.5: return 0.0
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low = 0.02425
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)
    if p <= 1.0 - p_low:
        q, r = p - 0.5, (p - 0.5) ** 2
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1.0)
    q = math.sqrt(-2.0 * math.log(1.0 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1.0)


def _log_beta(a: float, b: float) -> float:
    """Log of the Beta function B(a, b)."""
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _beta_cf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    TINY = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d, h = 1.0, 1.0, 1.0 / max(abs(1.0 - qab * x / qap), TINY)
    h = 1.0 / (1.0 - qab * x / qap) if abs(1.0 - qab * x / qap) >= TINY else 1.0 / TINY
    for m in range(1, 201):
        m2 = 2 * m
        # Even step
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = max(TINY, 1.0 + aa * d); c = max(TINY, 1.0 + aa / c)
        d = 1.0 / d; h *= d * c
        # Odd step
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = max(TINY, 1.0 + aa * d); c = max(TINY, 1.0 + aa / c)
        d = 1.0 / d; delta = d * c; h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return h


def _reg_inc_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - _log_beta(a, b))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_cf(a, b, x) / a
    return 1.0 - front * _beta_cf(b, a, 1.0 - x) / b


def _student_t_crit(alpha: float, df: int) -> float:
    """Approximate absolute t critical value via Newton-Raphson (|error| < 1e-8)."""
    if df < 1: return float("inf")
    p = 1.0 - alpha / 2.0

    def cdf(t: float) -> float:
        x = t * t / (t * t + df)
        return float(_reg_inc_beta(df / 2.0, 0.5, x)) / 2.0 + (0.5 if t > 0 else 0.0)

    def pdf(t: float) -> float:
        coeff = math.gamma((df + 1) / 2.0) / (math.sqrt(df * math.pi) * math.gamma(df / 2.0))
        return coeff * (1.0 + t * t / df) ** (-(df + 1) / 2.0)

    z = _norm_inv(p)
    t = z + (z**3 + z) / (4*df) + (5*z**5 + 16*z**3 + 3*z) / (96*df*df)
    for _ in range(60):
        f, fp = cdf(t) - p, pdf(t)
        if fp < 1e-15: break
        t -= f / fp
        if abs(f) < 1e-12: break
    return abs(t)


def _ks_cdf(stat: float, n1: int, n2: int) -> float:
    """Asymptotic KS CDF (Kolmogorov distribution, Marsaglia et al. 2003)."""
    neff = math.sqrt(float(n1 * n2) / float(n1 + n2))
    if (neff + 0.12 + 0.11 / neff) * stat >= 4.0:
        return 1.0
    total = 0.0
    for k in range(1, 200):
        try:
            term = (-1.0)**(k-1) * math.exp(-2.0 * k*k * stat*stat * neff*neff)
        except OverflowError:
            term = 0.0
        total += term
        if abs(term) < 1e-15: break
    return max(0.0, min(1.0, 1.0 - 2.0 * total))


def _kl_divergence(p: NDArray[np.float64], q: NDArray[np.float64]) -> float:
    """KL(p || q) with Laplace smoothing."""
    eps = 1e-10
    p_s, q_s = p + eps, q + eps
    p_s, q_s = p_s / p_s.sum(), q_s / q_s.sum()
    return float(np.sum(p_s * np.log(p_s / q_s)))


# ===========================================================================
# 1. StatisticalAnomalyDetector
# ===========================================================================

class StatisticalAnomalyDetector:
    """Classical statistical methods for outlier detection.

    Each method returns flagged points with index, value, and diagnostic score.
    """

    def zscore_detect(self, values: Sequence[float], threshold: float = 3.0) -> List[Tuple[int, float, float]]:
        """Flag outliers via Pearson z-score. Returns [(index, value, z_score), ...]."""
        arr = _as_float_array(values)
        mu, sigma = float(np.mean(arr)), float(np.std(arr, ddof=1))
        if sigma == 0: return []
        return [(i, float(v), float((v - mu) / sigma))
                for i, v in enumerate(arr) if abs((v - mu) / sigma) >= threshold]

    def iqr_detect(self, values: Sequence[float], k: float = 1.5) -> List[Tuple[int, float, bool]]:
        """Flag outliers via Tukey IQR fences. Returns [(index, value, True), ...]."""
        arr = _as_float_array(values)
        q1, q3 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
        iqr = q3 - q1
        if iqr == 0: return []
        lo, hi = q1 - k * iqr, q3 + k * iqr
        return [(i, float(v), True) for i, v in enumerate(arr) if v < lo or v > hi]

    def modified_zscore_detect(self, values: Sequence[float], threshold: float = 3.5) -> List[Tuple[int, float, float]]:
        """Flag outliers via MAD-based modified z-score. Returns [(index, value, mz_score), ...]."""
        arr = _as_float_array(values)
        med = float(np.median(arr))
        mad = max(float(np.median(np.abs(arr - med))), 1e-12)
        factor = 0.6745 / mad
        return [(i, float(v), float(factor * (v - med)))
                for i, v in enumerate(arr) if abs(factor * (v - med)) >= threshold]

    def grubbs_test(self, values: Sequence[float], alpha: float = 0.05) -> List[int]:
        """Iterative Grubbs' test. Returns sorted original indices of outliers."""
        arr = _as_float_array(values)
        if len(arr) < 3: return []
        outliers: List[int] = []
        idx_map = list(range(len(arr)))
        remaining = arr.copy()
        while len(remaining) >= 3:
            m = len(remaining)
            mu, sigma = float(np.mean(remaining)), float(np.std(remaining, ddof=1))
            if sigma == 0: break
            dev = np.abs(remaining - mu)
            pos = int(np.argmax(dev))
            g = float(dev[pos]) / sigma
            t = _student_t_crit(alpha / m, m - 2)
            g_crit = ((m - 1) / math.sqrt(m)) * math.sqrt(t**2 / (m - 2 + t**2))
            if g > g_crit:
                outliers.append(idx_map[pos])
                idx_map.pop(pos)
                remaining = np.delete(remaining, pos)
            else:
                break
        return sorted(outliers)

    def detect_percentile(self, values: Sequence[float], lower: float = 5.0, upper: float = 95.0) -> List[Tuple[int, float, bool]]:
        """Flag values outside [lower, upper] percentile bounds."""
        arr = _as_float_array(values)
        lo, hi = float(np.percentile(arr, lower)), float(np.percentile(arr, upper))
        return [(i, float(v), True) for i, v in enumerate(arr) if v < lo or v > hi]

    def detect_all(self, values: Sequence[float]) -> Dict[str, Any]:
        """Run every detector and return a combined dict report."""
        return {
            "zscore": self.zscore_detect(values), "iqr": self.iqr_detect(values),
            "modified_zscore": self.modified_zscore_detect(values),
            "grubbs": self.grubbs_test(values), "percentile": self.detect_percentile(values),
        }

    def ensemble_detect(self, values: Sequence[float], methods: Optional[List[str]] = None) -> List[Tuple[int, bool, float]]:
        """Ensemble voting. Returns [(index, is_anomaly, confidence), ...] for every point.

        confidence = fraction of methods that voted anomaly.
        methods: subset of {"zscore","iqr","modified_zscore","grubbs","percentile"}.
        """
        n = len(values)
        all_m = ["zscore", "iqr", "modified_zscore", "grubbs", "percentile"]
        active = methods or all_m
        if methods:
            for m in methods:
                if m not in all_m:
                    raise ValueError(f"Unknown method {m!r}")
        votes = np.zeros(n, dtype=np.float64)
        count = 0
        if "zscore" in active:
            count += 1
            for idx, _v, _z in self.zscore_detect(values): votes[idx] += 1
        if "iqr" in active:
            count += 1
            for idx, _v, _f in self.iqr_detect(values): votes[idx] += 1
        if "modified_zscore" in active:
            count += 1
            for idx, _v, _mz in self.modified_zscore_detect(values): votes[idx] += 1
        if "grubbs" in active:
            count += 1
            for idx in self.grubbs_test(values): votes[idx] += 1
        if "percentile" in active:
            count += 1
            for idx, _v, _f in self.detect_percentile(values): votes[idx] += 1
        return [(i, bool(votes[i] > 0), float(votes[i] / count) if count else 0.0) for i in range(n)]


# ===========================================================================
# 2. ChangePointDetector
# ===========================================================================

class ChangePointDetector:
    """Time-series change-point and distribution-shift detection.

    CUSUM, moving-average residual, entropy-based, and KS test from scratch.
    """

    def detect_cusum(self, values: Sequence[float], threshold: float = 4.0, drift: float = 0.0) -> List[int]:
        """CUSUM change-point detection. Returns list of change-point indices."""
        arr = _as_float_array(values)
        mu = float(np.mean(arr))
        s_pos = s_neg = 0.0
        points: List[int] = []
        for i, v in enumerate(arr):
            s_pos = max(0.0, s_pos + (v - mu - drift))
            s_neg = max(0.0, s_neg - (v - mu - drift))
            if s_pos >= threshold or s_neg >= threshold:
                points.append(i); s_pos = s_neg = 0.0
        return points

    def detect_moving_avg(self, values: Sequence[float], window: int = 10, threshold: float = 2.0) -> List[int]:
        """Flag points where |value - local_mean| > threshold * local_std."""
        arr = _as_float_array(values)
        n = len(arr)
        if n <= window: return []
        points: List[int] = []
        for i in range(window, n):
            seg = arr[i - window : i]
            ls = float(np.std(seg, ddof=1))
            if ls < 1e-12: continue
            if abs(float(arr[i]) - float(np.mean(seg))) / ls >= threshold:
                points.append(i)
        return points

    def detect_entropy_change(self, texts: List[str], window: int = 5, threshold: float = 0.3) -> List[int]:
        """Flag indices where character-level Shannon entropy shifts beyond threshold."""
        if len(texts) <= window: return []
        entropies = [self._shannon_entropy(t) for t in texts]
        return [i for i in range(window, len(entropies))
                if abs(entropies[i] - float(np.mean(entropies[i - window : i]))) >= threshold]

    @staticmethod
    def _shannon_entropy(text: str) -> float:
        """Shannon entropy of character frequencies in *text*."""
        if not text: return 0.0
        counts = Counter(text)
        total = len(text)
        return -sum((c / total) * math.log2(c / total) for c in counts.values())

    def detect_distribution_shift(self, values1: Sequence[float], values2: Sequence[float]) -> Dict[str, float]:
        """Two-sample KS test from scratch. Returns {"ks_statistic", "p_value"}."""
        a1, a2 = _as_float_array(values1), _as_float_array(values2)
        n1, n2 = len(a1), len(a2)
        if n1 == 0 or n2 == 0:
            return {"ks_statistic": 0.0, "p_value": 1.0}
        combined = np.sort(np.concatenate([a1, a2]))
        ecdf1 = np.searchsorted(np.sort(a1), combined, side="right") / n1
        ecdf2 = np.searchsorted(np.sort(a2), combined, side="right") / n2
        stat = float(np.max(np.abs(ecdf1 - ecdf2)))
        return {"ks_statistic": stat, "p_value": max(0.0, 1.0 - _ks_cdf(stat, n1, n2))}


# ===========================================================================
# 3. DataDriftMonitor
# ===========================================================================

class DataDriftMonitor:
    """Monitor a streaming value series for data drift via sliding-window KL divergence."""

    def __init__(self, window_size: int = 50, n_bins: int = 20) -> None:
        self.window_size = window_size
        self.n_bins = n_bins
        self._buffer: List[float] = []
        self._baseline_hist: Optional[NDArray[np.float64]] = None
        self._baseline_edges: Optional[NDArray[np.float64]] = None
        self._baseline_set = False

    def update(self, values: Sequence[float]) -> None:
        """Ingest new observations.  First window_size values form the baseline histogram."""
        self._buffer.extend(float(v) for v in values)
        if len(self._buffer) >= self.window_size and not self._baseline_set:
            base = np.array(self._buffer[:self.window_size], dtype=np.float64)
            self._baseline_hist, self._baseline_edges = np.histogram(base, bins=self.n_bins)
            self._baseline_hist = self._baseline_hist.astype(np.float64)
            t = self._baseline_hist.sum()
            if t > 0: self._baseline_hist /= t
            self._baseline_set = True
        if len(self._buffer) > self.window_size * 2:
            self._buffer = self._buffer[-self.window_size * 2:]

    def get_drift_score(self) -> float:
        """Normalised KL-divergence between current window and baseline (0=identical, 1=max)."""
        if not self._baseline_set or len(self._buffer) < self.window_size:
            return 0.0
        curr = np.array(self._buffer[-self.window_size:], dtype=np.float64)
        hist, _ = np.histogram(curr, bins=self._baseline_edges)  # type: ignore[arg-type]
        hist = hist.astype(np.float64)
        t = hist.sum()
        if t == 0: return 0.0
        hist /= t
        kl = float(_kl_divergence(self._baseline_hist, hist))
        return min(1.0, kl / max(math.log(self.n_bins), 1.0))

    def get_drift_report(self) -> Dict[str, Any]:
        """Detailed drift report: score, means, stds, is_drifting flag."""
        score = self.get_drift_score()
        if self._baseline_set and len(self._buffer) >= self.window_size:
            base = np.array(self._buffer[:self.window_size], dtype=np.float64)
            curr = np.array(self._buffer[-self.window_size:], dtype=np.float64)
            b_m, c_m = float(np.mean(base)), float(np.mean(curr))
            b_s, c_s = float(np.std(base, ddof=1)), float(np.std(curr, ddof=1))
        else:
            b_m = c_m = b_s = c_s = 0.0
        return {
            "drift_score": score, "is_drifting": score >= 0.3,
            "baseline_mean": b_m, "current_mean": c_m, "mean_shift": c_m - b_m,
            "baseline_std": b_s, "current_std": c_s,
            "buffer_size": len(self._buffer), "baseline_set": self._baseline_set,
        }


# ===========================================================================
# 4. PatternAnomalyDetector
# ===========================================================================

class PatternAnomalyDetector:
    """Detect anomalies in sequential/categorical patterns (tags, URLs, extraction order)."""

    def __init__(self, history_size: int = 100) -> None:
        self.history_size = history_size
        self._profiles: Dict[str, List[Dict[str, float]]] = defaultdict(list)

    def profile_sequence(self, seq: Sequence[str], label: str = "default") -> Dict[str, float]:
        """Build a statistical profile for a token sequence.

        Returns dict with unique_ratio, entropy, transition_entropy, repeat_rate, length.
        """
        if not seq:
            return {"unique_ratio": 0.0, "entropy": 0.0, "transition_entropy": 0.0,
                    "repeat_rate": 0.0, "length": 0.0}
        counts = Counter(seq)
        total = len(seq)
        probs = [c / total for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        trans = Counter(zip(seq, seq[1:]))
        t_total = sum(trans.values())
        t_probs = [c / t_total for c in trans.values()] if t_total else [1.0]
        trans_entropy = -sum(p * math.log2(p) for p in t_probs)
        repeats = sum(1 for a, b in zip(seq, seq[1:]) if a == b)
        profile = {
            "unique_ratio": len(counts) / total, "entropy": entropy,
            "transition_entropy": trans_entropy, "repeat_rate": repeats / max(1, total - 1),
            "length": float(total),
        }
        self._profiles[label].append(profile)
        if len(self._profiles[label]) > self.history_size:
            self._profiles[label] = self._profiles[label][-self.history_size:]
        return profile

    def detect_pattern_anomaly(self, seq: Sequence[str], label: str = "default", threshold: float = 2.0) -> Dict[str, Any]:
        """Compare a sequence's profile against history. Returns is_anomaly, anomalous_features, etc."""
        profile = self.profile_sequence(seq, label)
        history = self._profiles[label]
        if len(history) < 3:
            return {"is_anomaly": False, "anomalous_features": [],
                    "current_profile": profile, "baseline_means": {}}
        features = ["unique_ratio", "entropy", "transition_entropy", "repeat_rate"]
        anomalous: List[str] = []
        baseline_means: Dict[str, float] = {}
        for feat in features:
            vals = [p[feat] for p in history[:-1]]
            if not vals: continue
            arr = np.array(vals, dtype=np.float64)
            mu, sigma = float(np.mean(arr)), float(np.std(arr, ddof=1))
            baseline_means[feat] = mu
            if sigma < 1e-12: continue
            if abs(profile[feat] - mu) / sigma >= threshold:
                anomalous.append(feat)
        return {"is_anomaly": len(anomalous) > 0, "anomalous_features": anomalous,
                "current_profile": profile, "baseline_means": baseline_means}


# ===========================================================================
# 5. ScrapingAnomalyDetector
# ===========================================================================

class ScrapingAnomalyDetector:
    """High-level facade monitoring response times, status codes, data sizes,
    extraction counts, and URL patterns for scraping health."""

    def __init__(self) -> None:
        self._stat = StatisticalAnomalyDetector()
        self._cpd = ChangePointDetector()
        self._drift = DataDriftMonitor(window_size=30, n_bins=15)
        self._pattern = PatternAnomalyDetector(history_size=50)
        self._response_times: List[float] = []
        self._status_codes: List[int] = []
        self._data_sizes: List[float] = []
        self._extraction_counts: List[int] = []
        self._url_sequences: List[str] = []

    def record(self, response_time: float, status_code: int, data_size: float,
               extraction_count: int, url: str = "") -> None:
        """Record a single scrape event."""
        self._response_times.append(response_time)
        self._status_codes.append(status_code)
        self._data_sizes.append(data_size)
        self._extraction_counts.append(extraction_count)
        self._url_sequences.append(url)
        self._drift.update([response_time])

    def check_response_times(self) -> Dict[str, Any]:
        """Analyse response times: outliers, change-points, drift."""
        if len(self._response_times) < 5:
            return {"outliers": [], "change_points": [], "current_drift": 0.0}
        outliers = [(i, f, c) for i, f, c in self._stat.ensemble_detect(self._response_times) if f]
        return {"outliers": outliers, "change_points": self._cpd.detect_cusum(self._response_times),
                "current_drift": self._drift.get_drift_score()}

    def check_status_codes(self, anomaly_codes: Optional[Sequence[int]] = None) -> Dict[str, Any]:
        """Analyse HTTP status-code patterns. Defaults: {0, 403, 429, 500, 502, 503}."""
        bad = set(anomaly_codes) if anomaly_codes else {0, 403, 429, 500, 502, 503}
        total = len(self._status_codes)
        if total == 0:
            return {"anomaly_count": 0, "anomaly_rate": 0.0, "code_distribution": {}}
        anom = sum(1 for c in self._status_codes if c in bad)
        return {"anomaly_count": anom, "anomaly_rate": anom / total,
                "code_distribution": dict(Counter(self._status_codes))}

    def check_data_sizes(self) -> Dict[str, Any]:
        """Analyse response payload sizes for anomalies."""
        if len(self._data_sizes) < 5:
            return {"outliers": [], "current_size": 0.0, "mean_size": 0.0, "std_size": 0.0}
        arr = np.array(self._data_sizes, dtype=np.float64)
        return {"outliers": self._stat.iqr_detect(self._data_sizes),
                "current_size": float(arr[-1]), "mean_size": float(np.mean(arr)),
                "std_size": float(np.std(arr, ddof=1))}

    def check_extraction_counts(self) -> Dict[str, Any]:
        """Analyse item extraction counts for anomalies."""
        if len(self._extraction_counts) < 5:
            return {"outliers": [], "change_points": [], "current_count": 0}
        float_counts = [float(c) for c in self._extraction_counts]
        return {"outliers": self._stat.modified_zscore_detect(float_counts),
                "change_points": self._cpd.detect_moving_avg(float_counts, window=5),
                "current_count": self._extraction_counts[-1]}

    def check_url_patterns(self) -> Dict[str, Any]:
        """Analyse URL sequence for structural anomalies."""
        if len(self._url_sequences) < 3:
            return {"is_anomaly": False, "anomalous_features": []}
        return self._pattern.detect_pattern_anomaly(self._url_sequences)

    def health_check(self) -> Dict[str, Any]:
        """Aggregate all sub-checks into a single health report.

        Returns overall_score (0-1, 1=healthy), is_healthy, and per-signal reports.
        """
        rt = self.check_response_times()
        sc = self.check_status_codes()
        ds = self.check_data_sizes()
        ec = self.check_extraction_counts()
        up = self.check_url_patterns()
        penalties = 0.0
        # Response-time outlier rate
        penalties += min(1.0, len(rt["outliers"]) / max(1, len(self._response_times)) * 5)
        penalties += rt["current_drift"]
        # Status code anomaly rate
        penalties += sc["anomaly_rate"] * 5
        # Data-size outlier rate
        penalties += min(1.0, len(ds["outliers"]) / max(1, len(self._data_sizes)) * 5)
        # Extraction-count outlier rate
        penalties += min(1.0, len(ec["outliers"]) / max(1, len(self._extraction_counts)) * 5)
        # URL pattern anomaly
        if up["is_anomaly"]:
            penalties += 1.0
        score = max(0.0, 1.0 - penalties / 6.0)
        return {
            "overall_score": round(score, 4), "is_healthy": score >= 0.6,
            "response_times": rt, "status_codes": sc, "data_sizes": ds,
            "extraction_counts": ec, "url_patterns": up,
        }
