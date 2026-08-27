"""Data Quality Scoring Module for Web Scraping.

Bayesian inference and information-theoretic methods for assessing and
tracking the quality of web-scraped data. Uses ONLY standard library
and NumPy -- no external ML libraries.

Classes:
    BayesianScorer            - Beta-Bernoulli conjugate model for quality belief.
    QualityDimension         - Enum of six quality dimensions.
    QualityIssue             - Dataclass for a single quality problem.
    QualityReport            - Aggregated assessment result.
    DataQualityAssessor      - Main entry point for full quality assessment.
    InformationTheoryMetrics - Entropy, MI, KL-divergence, and composite scores.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np

# -- Enums & Data Classes ------------------------------------------------

class QualityDimension(Enum):
    """Six quality dimensions for scraped data."""

    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"

@dataclass
class QualityIssue:
    """A single data-quality problem found during assessment.

    Attributes:
        dimension:      Which quality dimension this issue belongs to.
        field:          The data field (column) affected, or empty string for record-level issues.
        description:    Human-readable explanation of the problem.
        severity:       One of "low", "medium", "high", "critical".
        affected_count: Number of records impacted.
    """

    dimension: QualityDimension
    field: str
    description: str
    severity: str
    affected_count: int

@dataclass
class QualityReport:
    """Aggregated quality-assessment result for one batch of records.

    Attributes:
        overall_score:     Unweighted mean of dimension scores in [0, 1].
        dimension_scores:  Per-dimension score mapping.
        issues:            Every issue discovered during assessment.
        timestamp:         Unix-epoch seconds when the report was produced.
        record_count:      Number of records assessed.
        weighted_score:    Dimension scores combined using default weights.
    """

    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    issues: List[QualityIssue]
    timestamp: float
    record_count: int
    weighted_score: float = 0.0

    DEFAULT_WEIGHTS: Dict[QualityDimension, float] = field(
        default_factory=lambda: {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.CONSISTENCY: 0.20,
            QualityDimension.ACCURACY: 0.15,
            QualityDimension.TIMELINESS: 0.10,
            QualityDimension.UNIQUENESS: 0.15,
            QualityDimension.VALIDITY: 0.15,
        }
    )

    def __post_init__(self) -> None:
        if self.weighted_score == 0.0:
            self.weighted_score = self._compute_weighted(self.DEFAULT_WEIGHTS)

    def _compute_weighted(self, weights: Dict[QualityDimension, float]) -> float:
        """Combine dimension scores using *weights* (normalised internally)."""
        total_w = sum(weights.values())
        if total_w == 0:
            return self.overall_score
        return sum(self.dimension_scores.get(d, 0.0) * w
                   for d, w in weights.items()) / total_w

# -- Bayesian Scoring (Beta-Bernoulli conjugate model) ---------------------

class BayesianScorer:
    """Bayesian quality scorer using a Beta-Bernoulli conjugate model.

    Each observation is a Boolean (pass / fail).  The posterior is
    Beta(alpha + successes, beta + failures) whose expected value
    serves as the quality score.  Uses Lentz continued-fraction expansion
    for the regularised incomplete Beta function -- no scipy required.

    Parameters:
        prior_alpha: Shape parameter of the Beta prior (default 1 = uniform).
        prior_beta:  Shape parameter of the Beta prior (default 1 = uniform).
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> None:
        if prior_alpha <= 0 or prior_beta <= 0:
            raise ValueError("Prior parameters must be positive.")
        self._alpha: float = float(prior_alpha)
        self._beta: float = float(prior_beta)
        self._alpha0: float = self._alpha
        self._beta0: float = self._beta

    def update(self, observation: bool) -> None:
        """Incorporate a single Boolean observation (True=pass, False=fail)."""
        if observation:
            self._alpha += 1.0
        else:
            self._beta += 1.0

    def batch_update(self, observations: Sequence[bool]) -> None:
        """Incorporate a batch of Boolean observations at once."""
        obs_list = list(observations)
        successes = sum(1 for o in obs_list if o)
        self._alpha += float(successes)
        self._beta += float(len(obs_list) - successes)

    def reset(self) -> None:
        """Reset the posterior back to the original prior."""
        self._alpha = self._alpha0
        self._beta = self._beta0

    def get_score(self) -> float:
        """Posterior expected value E[theta] = alpha/(alpha+beta) in [0, 1]."""
        return self._alpha / (self._alpha + self._beta)

    def get_confidence(self) -> float:
        """Confidence in [0, 1] from posterior variance.  Approaches 1.0 with more evidence."""
        a, b = self._alpha, self._beta
        variance = (a * b) / ((a + b) ** 2 * (a + b + 1))
        return float(np.clip(1.0 - math.sqrt(variance), 0.0, 1.0))

    def get_credible_interval(self, ci: float = 0.95) -> Tuple[float, float]:
        """Equal-tailed credible interval via Lentz continued-fraction expansion.

        Args:
            ci: Desired credible level (default 0.95).
        Returns:
            (lower_bound, upper_bound) tuple.
        """
        a, b = self._alpha, self._beta
        tail = (1.0 - ci) / 2.0
        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)

        def _beta_cdf(x: float) -> float:
            if x <= 0.0:
                return 0.0
            if x >= 1.0:
                return 1.0
            prefix = math.exp(a * math.log(x) + b * math.log(1.0 - x) - lbeta)
            if x < (a + 1.0) / (a + b + 2.0):
                return prefix * self._betacf(a, b, x) / a
            return 1.0 - prefix * self._betacf(b, a, 1.0 - x) / b

        lo = self._binsearch(_beta_cdf, tail, 0.0, 1.0)
        hi = self._binsearch(_beta_cdf, 1.0 - tail, 0.0, 1.0)
        return (lo, hi)

    @staticmethod
    def _betacf(a: float, b: float, x: float,
                max_iter: int = 200, eps: float = 3e-12) -> float:
        """Evaluate continued fraction for the incomplete Beta (Lentz)."""
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c, d = 1.0, 1.0 - qab * x / qap
        d = 1.0 / (d if abs(d) > 1e-30 else 1e-30)
        h = d
        for m in range(1, max_iter + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 / (1.0 + aa * d) if abs(1.0 + aa * d) > 1e-30 else 1e30
            c = 1.0 + aa / c if abs(c) > 1e-30 else 1e30
            h *= d * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 / (1.0 + aa * d) if abs(1.0 + aa * d) > 1e-30 else 1e30
            c = 1.0 + aa / c if abs(c) > 1e-30 else 1e30
            h *= d * c
            if abs(d * c - 1.0) < eps:
                break
        return h

    @staticmethod
    def _binsearch(fn: Callable[[float], float],
                   target: float, lo: float, hi: float) -> float:
        """Binary search for x where fn(x) ~ target (60 bisections)."""
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if fn(mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

# -- Information-Theory Metrics -------------------------------------------

class InformationTheoryMetrics:
    """Information-theoretic measures over discrete value sequences.

    All methods use NumPy internally.  Entropies are in **nats** (ln base).
    """

    _EPS: float = 1e-12

    @staticmethod
    def shannon_entropy(values: Sequence[Any]) -> float:
        """Shannon entropy H(X) = -Sum p(x) ln p(x) in nats.

        Args:
            values: Sequence of hashable items.

        Returns:
            Entropy (>= 0).  Returns 0.0 for empty or single-value input.
        """
        values = list(values)
        if len(values) == 0:
            return 0.0
        arr = np.array(values, dtype=object)
        _, counts = np.unique(arr, return_counts=True)
        probs = counts.astype(float) / counts.sum()
        return float(max(0.0, -np.sum(probs * np.log(probs + InformationTheoryMetrics._EPS))))

    @staticmethod
    def conditional_entropy(x: Sequence[Any], y: Sequence[Any]) -> float:
        """Conditional entropy H(X|Y) = Sum p(y) H(X|Y=y) in nats.

        Raises:
            ValueError: If x and y differ in length.
        """
        if len(x) != len(y):
            raise ValueError("x and y must have the same length.")
        x_arr, y_arr = np.array(x, dtype=object), np.array(y, dtype=object)
        h, n = 0.0, len(x_arr)
        for y_val in np.unique(y_arr):
            mask = y_arr == y_val
            h += (mask.sum() / n) * InformationTheoryMetrics.shannon_entropy(x_arr[mask])
        return h

    @staticmethod
    def mutual_information(x: Sequence[Any], y: Sequence[Any]) -> float:
        """Mutual information I(X; Y) = H(X) - H(X|Y) in nats.  Returns 0.0 if independent or empty."""
        if not x or not y:
            return 0.0
        return max(0.0, InformationTheoryMetrics.shannon_entropy(x)
               - InformationTheoryMetrics.conditional_entropy(x, y))

    @staticmethod
    def kl_divergence(p: Sequence[float], q: Sequence[float]) -> float:
        """KL divergence D_KL(P || Q) in nats.  Both normalised to sum 1.  Raises ValueError on length mismatch."""
        if len(p) != len(q):
            raise ValueError("p and q must have the same length.")
        pa = np.clip(np.asarray(p, dtype=float), InformationTheoryMetrics._EPS, None)
        qa = np.clip(np.asarray(q, dtype=float), InformationTheoryMetrics._EPS, None)
        pa, qa = pa / pa.sum(), qa / qa.sum()
        return float(np.sum(pa * np.log(pa / qa)))

    @staticmethod
    def data_complexity_score(data: List[Dict[str, Any]]) -> float:
        """Composite complexity in [0, 1] from entropy, cardinality, and non-sparsity."""
        if not data:
            return 0.0
        n = len(data)
        fields = [k for k in data[0] if isinstance(data[0], dict)]
        if not fields:
            return 0.0
        ln_n = math.log(max(n, 2))
        ent_scores, card_scores, missing_t, total_c = [], [], 0, 0

        for f in fields:
            col = [row.get(f) for row in data]
            non_empty = [v for v in col if v is not None and v != ""]
            missing_t += n - len(non_empty)
            total_c += n
            if non_empty:
                ent = InformationTheoryMetrics.shannon_entropy(non_empty)
                ent_scores.append(min(ent / ln_n, 1.0))
                card_scores.append(min(len(set(non_empty)) / n, 1.0))

        avg_ent = float(np.mean(ent_scores)) if ent_scores else 0.0
        avg_card = float(np.mean(card_scores)) if card_scores else 0.0
        density = 1.0 - missing_t / max(total_c, 1)
        return float(np.clip(0.4 * avg_ent + 0.35 * avg_card + 0.25 * density, 0, 1))

    @staticmethod
    def redundancy_ratio(data: List[Dict[str, Any]]) -> float:
        """Fraction of near-duplicate records in [0, 1] via SHA-256 hashing.  1 - unique_hashes/n."""
        if not data:
            return 0.0
        seen: set[str] = set()
        dupes = 0
        for row in data:
            norm = "|".join(f"{k}={row.get(k, '')}" for k in sorted(row))
            h = hashlib.sha256(norm.encode("utf-8", errors="replace")).hexdigest()
            if h in seen:
                dupes += 1
            else:
                seen.add(h)
        return dupes / len(data)

# -- Validation patterns -------------------------------------------------

_PAT_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)
_PAT_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PAT_DATE = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}(?:[ T]\d{2}:\d{2}(:\d{2})?)?")
_PAT_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
_TS_KW = ("date", "time", "created", "updated", "published", "timestamp")
_NUM_KW = ("price", "amount", "count", "rating", "score", "age")

# -- Data Quality Assessor ------------------------------------------------

class DataQualityAssessor:
    """Main entry point for assessing quality of scraped records.

    Runs six quality dimensions and aggregates into a QualityReport.
    Maintains Bayesian scorers per dimension and a report history.

    Parameters:
        rules:          Callables returning str on violation, None on pass.
        reference_data: {field: set_of_valid_values} for accuracy checking.
        field_weights:  Optional per-dimension weight overrides.
    """

    def __init__(
        self,
        rules: Optional[List[Callable[[Dict[str, Any]], Optional[str]]]] = None,
        reference_data: Optional[Dict[str, set]] = None,
        field_weights: Optional[Dict[QualityDimension, float]] = None,
    ) -> None:
        self._rules = rules or []
        self._reference = reference_data or {}
        self._custom_weights = field_weights
        self._history: List[QualityReport] = []
        self._bayesian: Dict[QualityDimension, BayesianScorer] = {
            d: BayesianScorer() for d in QualityDimension
        }

    def assess(self, data: List[Dict[str, Any]],
               rules: Optional[List[Callable]] = None) -> QualityReport:
        """Run a full six-dimension quality assessment.

        Args:
            data:  List of record dicts (same keys expected).
            rules: Override instance rules for this call only.

        Returns:
            QualityReport with scores, issues, and aggregate metrics.
        """
        active_rules = rules if rules is not None else self._rules
        ts = datetime.now(timezone.utc).timestamp()

        if not data:
            empty = {d: 0.0 for d in QualityDimension}
            report = QualityReport(0.0, empty, [], ts, 0)
            self._history.append(report)
            return report

        n = len(data)
        fields = list(data[0].keys()) if data[0] else []
        issues: List[QualityIssue] = []

        # --- Completeness -------------------------------------------------
        missing_pf: Dict[str, int] = {f: 0 for f in fields}
        for row in data:
            for f in fields:
                val = row.get(f)
                if val is None or (isinstance(val, str) and val.strip() == ""):
                    missing_pf[f] += 1
        completeness = float(np.mean([1.0 - c / n for c in missing_pf.values()]))
        self._top_issues(missing_pf, n, QualityDimension.COMPLETENESS, issues)

        # --- Consistency --------------------------------------------------
        cons_viol = 0
        for row in data:
            for rule_fn in active_rules:
                msg = rule_fn(row)
                if msg is not None:
                    cons_viol += 1
                    issues.append(QualityIssue(
                        QualityDimension.CONSISTENCY, "", msg, "medium", 1))
        consistency = 1.0 - cons_viol / (n * max(len(active_rules), 1))

        # --- Uniqueness ---------------------------------------------------
        redundancy = InformationTheoryMetrics.redundancy_ratio(data)
        uniqueness = 1.0 - redundancy
        dupe_n = int(redundancy * n)
        if dupe_n > 0:
            issues.append(QualityIssue(
                QualityDimension.UNIQUENESS, "",
                f"{dupe_n} near-duplicate record(s) detected.",
                "high" if dupe_n > n * 0.1 else "medium", dupe_n))

        # --- Validity -----------------------------------------------------
        val_total = val_pass = 0
        invalid_pf: Dict[str, int] = {}
        for f in fields:
            fi = 0
            for row in data:
                val = row.get(f)
                if val is None or val == "":
                    continue
                val_total += 1
                if self._is_valid(f, val):
                    val_pass += 1
                else:
                    fi += 1
            if fi:
                invalid_pf[f] = fi
        validity = val_pass / max(val_total, 1)
        self._top_issues(invalid_pf, n, QualityDimension.VALIDITY, issues, 2)

        # --- Timeliness ---------------------------------------------------
        timeliness, ts_issues = self._assess_timeliness(data, fields)
        issues.extend(ts_issues)

        # --- Accuracy -----------------------------------------------------
        accuracy, acc_issues = self._assess_accuracy(data)
        issues.extend(acc_issues)

        dim_scores: Dict[QualityDimension, float] = {
            QualityDimension.COMPLETENESS: completeness,
            QualityDimension.CONSISTENCY: consistency,
            QualityDimension.UNIQUENESS: uniqueness,
            QualityDimension.VALIDITY: validity,
            QualityDimension.TIMELINESS: timeliness,
            QualityDimension.ACCURACY: accuracy,
        }

        for dim, score in dim_scores.items():
            self._bayesian[dim].update(score >= 0.8)

        overall = float(np.mean(list(dim_scores.values())))
        report = QualityReport(overall, dim_scores, issues, ts, n)
        if self._custom_weights:
            report.weighted_score = report._compute_weighted(self._custom_weights)
        self._history.append(report)
        return report

    # -- trend & suggestions -----------------------------------------------

    def track_quality_over_time(self) -> List[QualityReport]:
        """Return all historical reports from successive assess() calls."""
        return list(self._history)

    def get_quality_trend(self) -> List[float]:
        """Return overall scores from every historical report, in order."""
        return [r.overall_score for r in self._history]

    def get_improvement_suggestions(
            self) -> List[Tuple[QualityDimension, str, str]]:
        """Analyse the latest report and return (dimension, suggestion, severity) tuples."""
        if not self._history:
            return []
        s = self._history[-1].dimension_scores
        suggestions: List[Tuple[QualityDimension, str, str]] = []

        if s.get(QualityDimension.COMPLETENESS, 1.0) < 0.9:
            suggestions.append((QualityDimension.COMPLETENESS,
                "Increase selector specificity or add fallback extraction to reduce missing fields.",
                "high" if s[QualityDimension.COMPLETENESS] < 0.7 else "medium"))
        if s.get(QualityDimension.CONSISTENCY, 1.0) < 0.9:
            suggestions.append((QualityDimension.CONSISTENCY,
                "Add post-processing validation rules to catch cross-field contradictions early.",
                "medium"))
        if s.get(QualityDimension.UNIQUENESS, 1.0) < 0.95:
            suggestions.append((QualityDimension.UNIQUENESS,
                "Implement deduplication with fuzzy matching before storing records.",
                "high" if s[QualityDimension.UNIQUENESS] < 0.85 else "low"))
        if s.get(QualityDimension.VALIDITY, 1.0) < 0.9:
            suggestions.append((QualityDimension.VALIDITY,
                "Add regex / schema validation during parsing to reject malformed values.",
                "medium"))
        if s.get(QualityDimension.TIMELINESS, 1.0) < 0.8:
            suggestions.append((QualityDimension.TIMELINESS,
                "Reduce scrape intervals or add caching headers for fresher data.",
                "low"))
        if s.get(QualityDimension.ACCURACY, 1.0) < 0.9:
            suggestions.append((QualityDimension.ACCURACY,
                "Cross-reference extracted values against authoritative sources.",
                "high"))
        return suggestions

    # -- internal helpers --------------------------------------------------

    @staticmethod
    def _is_valid(field_name: str, value: Any) -> bool:
        """Heuristic format validator based on field-name keywords.

        Checks URLs, emails, dates, and numeric fields by name pattern.
        Non-string values pass automatically.
        """
        if not isinstance(value, str):
            return True
        fl = field_name.lower()
        if any(kw in fl for kw in ("url", "link", "href")):
            return bool(_PAT_URL.match(value))
        if "email" in fl or "mail" in fl:
            return bool(_PAT_EMAIL.match(value))
        if any(kw in fl for kw in _TS_KW):
            return bool(_PAT_DATE.match(value))
        if any(kw in fl for kw in _NUM_KW):
            return bool(_PAT_NUM.match(value))
        return True

    @staticmethod
    def _assess_timeliness(
            data: List[Dict[str, Any]], fields: List[str],
    ) -> Tuple[float, List[QualityIssue]]:
        """Score recency of timestamp-like fields (30-day exponential decay)."""
        ts_fields = [f for f in fields if any(kw in f.lower() for kw in _TS_KW)]
        issues: List[QualityIssue] = []
        if not ts_fields:
            return 1.0, issues
        now = datetime.now(timezone.utc)
        total_delta, count = 0.0, 0
        for f in ts_fields:
            for row in data:
                val = row.get(f)
                if not isinstance(val, str):
                    continue
                parsed = DataQualityAssessor._parse_ts(val)
                if parsed is None:
                    continue
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                total_delta += (now - parsed).total_seconds() / 86400.0
                count += 1
        if count == 0:
            return 1.0, issues
        avg_days = total_delta / count
        score = float(np.clip(math.exp(-math.log(2) * avg_days / 30.0), 0, 1))
        if score < 0.8:
            issues.append(QualityIssue(
                QualityDimension.TIMELINESS, ts_fields[0],
                f"Average data age is {avg_days:.1f} days.", "low", count))
        return score, issues

    def _assess_accuracy(
            self, data: List[Dict[str, Any]],
    ) -> Tuple[float, List[QualityIssue]]:
        """Cross-reference values against reference_data."""
        issues: List[QualityIssue] = []
        if not self._reference:
            return 1.0, issues
        total = matched = 0
        for kf, valid_set in self._reference.items():
            for row in data:
                val = row.get(kf)
                if val is None:
                    continue
                total += 1
                if val in valid_set:
                    matched += 1
                else:
                    issues.append(QualityIssue(
                        QualityDimension.ACCURACY, kf,
                        f"Value '{val}' not found in reference set.",
                        "high", 1))
        return (matched / total, issues) if total else (1.0, issues)

    @staticmethod
    def _top_issues(
            counts: Dict[str, int], n: int, dim: QualityDimension,
            issues: List[QualityIssue], top_n: int = 3,
    ) -> None:
        """Append issues for fields with the highest missing/invalid counts."""
        for fld, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]:
            if cnt == 0:
                continue
            ratio = cnt / n
            sev = "critical" if ratio > 0.5 else "high" if ratio > 0.25 else "medium" if ratio > 0.1 else "low"
            issues.append(QualityIssue(
                dim, fld, f"{cnt}/{n} records missing or invalid for '{fld}'.", sev, cnt))

    @staticmethod
    def _parse_ts(s: str) -> Optional[datetime]:
        """Best-effort ISO-8601 timestamp parser. Returns None on failure."""
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except (ValueError, TypeError):
                continue
        return None
