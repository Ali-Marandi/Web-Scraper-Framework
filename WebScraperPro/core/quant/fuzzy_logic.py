"""
Fuzzy Logic Module for Quantitative Finance.

Provides comprehensive fuzzy logic tools including fuzzy numbers, Mamdani inference,
credit scoring, trading signal generation, Fuzzy AHP, Fuzzy TOPSIS, and a simplified
ANFIS implementation. Depends only on numpy, pandas, and scipy.
"""

import numpy as np
import pandas as pd
from scipy import integrate
from typing import Dict, List, Tuple, Optional, Union, Any


# --------------------------------------------------------------------------- #
#  FuzzyNumber                                                              #
# --------------------------------------------------------------------------- #

class FuzzyNumber:
    """Triangular or Trapezoidal fuzzy number with arithmetic operations.

    Triangular  : (a, b, c)   — peak at *b*.
    Trapezoidal : (a, b, c, d) — flat top from *b* to *c*.
    """

    def __init__(self, a: float, b: float, c: float, d: float = None):
        self.a = float(a)
        self.b = float(b)
        self.c = float(c)
        self.d = float(d) if d is not None else None
        if self.d is not None:
            assert self.a <= self.b <= self.c <= self.d, "Trapezoidal params must be ordered a<=b<=c<=d"
        else:
            assert self.a <= self.b <= self.c, "Triangular params must be ordered a<=b<=c"

    # ---- helpers -------------------------------------------------------- #

    @staticmethod
    def is_fuzzy(other) -> bool:
        return isinstance(other, FuzzyNumber)

    @property
    def is_trapezoidal(self) -> bool:
        return self.d is not None

    # ---- membership ------------------------------------------------------ #

    def membership(self, x: float) -> float:
        """Return the membership degree μ(x) ∈ [0, 1]."""
        x = float(x)
        if self.is_trapezoidal:
            if x <= self.a or x >= self.d:
                return 0.0
            if self.a < x < self.b:
                return (x - self.a) / (self.b - self.a) if self.b != self.a else 1.0
            if self.b <= x <= self.c:
                return 1.0
            if self.c < x < self.d:
                return (self.d - x) / (self.d - self.c) if self.d != self.c else 1.0
        else:
            if x <= self.a or x >= self.c:
                return 0.0
            if self.a < x < self.b:
                return (x - self.a) / (self.b - self.a) if self.b != self.a else 1.0
            if self.b <= x <= self.c:
                return (self.c - x) / (self.c - self.b) if self.c != self.b else 1.0
        return 0.0

    # ---- alpha-cut ------------------------------------------------------- #

    def alpha_cut(self, alpha: float) -> List[float]:
        """Return [lower, upper] at the given alpha level ∈ [0, 1]."""
        alpha = float(np.clip(alpha, 0.0, 1.0))
        if self.is_trapezoidal:
            lower = self.a + alpha * (self.b - self.a)
            upper = self.d - alpha * (self.d - self.c)
        else:
            lower = self.a + alpha * (self.b - self.a)
            upper = self.c - alpha * (self.c - self.b)
        return [lower, upper]

    # ---- defuzzification -------------------------------------------------- #

    def defuzzify(self, method: str = 'centroid') -> float:
        """Defuzzify the fuzzy number.

        Methods: 'centroid', 'mean_of_max', 'bisector'.
        """
        if method == 'centroid':
            return self._defuzz_centroid()
        elif method == 'mean_of_max':
            return self._defuzz_mean_of_max()
        elif method == 'bisector':
            return self._defuzz_bisector()
        else:
            raise ValueError(f"Unknown defuzzification method: {method}")

    def _defuzz_centroid(self) -> float:
        """Center of gravity via numerical integration."""
        if self.is_trapezoidal:
            lo, hi = self.a, self.d
        else:
            lo, hi = self.a, self.c

        def _integrand(x):
            return x * self.membership(x)
        def _area(x):
            return self.membership(x)

        num, _ = integrate.quad(_integrand, lo, hi)
        den, _ = integrate.quad(_area, lo, hi)
        return num / den if den > 1e-15 else (lo + hi) / 2.0

    def _defuzz_mean_of_max(self) -> float:
        """Mean of the x-values where μ(x) = 1."""
        if self.is_trapezoidal:
            return (self.b + self.c) / 2.0
        else:
            return self.b

    def _defuzz_bisector(self) -> float:
        """The x-value that splits the area under the curve in half."""
        if self.is_trapezoidal:
            lo, hi = self.a, self.d
        else:
            lo, hi = self.a, self.c

        total_area, _ = integrate.quad(self.membership, lo, hi)
        if total_area < 1e-15:
            return (lo + hi) / 2.0
        half = total_area / 2.0

        # bisection search
        x_lo, x_hi = lo, hi
        for _ in range(200):
            x_mid = (x_lo + x_hi) / 2.0
            area_left, _ = integrate.quad(self.membership, lo, x_mid)
            if area_left < half:
                x_lo = x_mid
            else:
                x_hi = x_mid
        return (x_lo + x_hi) / 2.0

    # ---- arithmetic via interval arithmetic on alpha cuts ---------------- #

    @staticmethod
    def _interval_op(a_cut, b_cut, op) -> list:
        """Apply *op* element-wise to two intervals [a1,a2], [b1,b2]."""
        corners = [op(a_cut[0], b_cut[0]), op(a_cut[0], b_cut[1]),
                   op(a_cut[1], b_cut[0]), op(a_cut[1], b_cut[1])]
        return [min(corners), max(corners)]

    def _arith(self, other, op) -> 'FuzzyNumber':
        if not self.is_fuzzy(other):
            other = FuzzyNumber(other, other, other)
        alphas = np.linspace(0, 1, 101)
        cuts = [self._interval_op(self.alpha_cut(a), other.alpha_cut(a), op) for a in alphas]
        # reconstruct piecewise-linear fuzzy number from alpha-cut envelope
        lower_env = np.array([c[0] for c in cuts])
        upper_env = np.array([c[1] for c in cuts])
        # alpha=0 → a, d  ;  alpha=1 → b, c
        a_val = lower_env[0]
        d_val = upper_env[0]
        b_val = lower_env[-1]
        c_val = upper_env[-1]
        if abs(b_val - c_val) < 1e-12:
            return FuzzyNumber(a_val, b_val, c_val)
        return FuzzyNumber(a_val, b_val, c_val, d_val)

    def __add__(self, other) -> 'FuzzyNumber':
        return self._arith(other, lambda x, y: x + y)

    def __radd__(self, other) -> 'FuzzyNumber':
        return self.__add__(other)

    def __sub__(self, other) -> 'FuzzyNumber':
        return self._arith(other, lambda x, y: x - y)

    def __rsub__(self, other) -> 'FuzzyNumber':
        return FuzzyNumber(other, other, other).__sub__(self)

    def __mul__(self, other) -> 'FuzzyNumber':
        return self._arith(other, lambda x, y: x * y)

    def __rmul__(self, other) -> 'FuzzyNumber':
        return self.__mul__(other)

    def __repr__(self) -> str:
        if self.is_trapezoidal:
            return f"FuzzyNumber(trapezoidal, {self.a}, {self.b}, {self.c}, {self.d})"
        return f"FuzzyNumber(triangular, {self.a}, {self.b}, {self.c})"


# --------------------------------------------------------------------------- #
#  FuzzyInferenceSystem (Mamdani)                                           #
# --------------------------------------------------------------------------- #

class FuzzyInferenceSystem:
    """Mamdani-style fuzzy inference system."""

    def __init__(self):
        self.variables: Dict[str, dict] = {}      # name -> {universe, mfs}
        self.rules: List[dict] = []

    def add_variable(self, name: str, universe_min: float, universe_max: float,
                     mf_configs: List[Tuple[str, list, str]]):
        """Add a linguistic variable.

        mf_configs : list of (type, params, label)
            type   = 'triangular' or 'trapezoidal'
            params = [a, b, c] or [a, b, c, d]
            label  = linguistic label string
        """
        mfs = {}
        for mf_type, params, label in mf_configs:
            if mf_type == 'triangular':
                mfs[label] = FuzzyNumber(*params)
            elif mf_type == 'trapezoidal':
                mfs[label] = FuzzyNumber(*params)
            else:
                raise ValueError(f"Unknown MF type: {mf_type}")
        self.variables[name] = {
            'universe_min': universe_min,
            'universe_max': universe_max,
            'mfs': mfs,
        }

    def add_rule(self, antecedents: List[Tuple[str, str]],
                 consequent: Tuple[str, str], operator: str = 'and'):
        """Add a rule.

        antecedents : [(var_name, label), ...]
        consequent  : (var_name, label)
        operator    : 'and' (min) or 'or' (max)
        """
        self.rules.append({
            'antecedents': antecedents,
            'consequent': consequent,
            'operator': operator,
        })

    # ---- internal helpers ------------------------------------------------ #

    def _fuzzify(self, var_name: str, crisp_val: float) -> Dict[str, float]:
        """Return {label: μ(crisp_val)} for every MF of *var_name*."""
        var = self.variables[var_name]
        return {label: mf.membership(crisp_val)
                for label, mf in var['mfs'].items()}

    def _evaluate_rule(self, rule: dict,
                       fuzzified: Dict[str, Dict[str, float]]) -> Tuple[float, str, str]:
        """Compute firing strength for a single rule.

        Returns (strength, out_var, out_label).
        """
        strengths = []
        for var_name, label in rule['antecedents']:
            strengths.append(fuzzified[var_name][label])
        if rule['operator'] == 'and':
            firing = min(strengths)
        else:  # 'or'
            firing = max(strengths)
        out_var, out_label = rule['consequent']
        return firing, out_var, out_label

    def _aggregate_and_defuzzify(self, output_var: str,
                                  rule_outputs: List[Tuple[float, str]]) -> float:
        """Aggregate clipped MFs via max and defuzzify using centroid."""
        var = self.variables[output_var]
        lo = var['universe_min']
        hi = var['universe_max']
        n_points = 500
        xs = np.linspace(lo, hi, n_points)

        aggregated = np.zeros(n_points)
        for strength, out_label in rule_outputs:
            mf = var['mfs'][out_label]
            clipped = np.minimum(strength, np.array([mf.membership(x) for x in xs]))
            aggregated = np.maximum(aggregated, clipped)

        total = np.sum(aggregated)
        if total < 1e-15:
            return (lo + hi) / 2.0
        return float(np.sum(xs * aggregated) / total)

    # ---- public evaluate ------------------------------------------------- #

    def evaluate(self, inputs: Dict[str, float]) -> Dict[str, Any]:
        """Run full Mamdani inference.

        Returns {output_values: {var: crisp}, firing_strengths: [float],
                 rules_fired: [int], details: [...]}.
        """
        # 1. Fuzzify
        fuzzified = {var: self._fuzzify(var, val) for var, val in inputs.items()}

        # 2. Evaluate each rule
        rule_results = []
        firing_strengths = []
        rules_fired = []
        output_groups: Dict[str, List[Tuple[float, str]]] = {}

        for idx, rule in enumerate(self.rules):
            strength, out_var, out_label = self._evaluate_rule(rule, fuzzified)
            firing_strengths.append(strength)
            rule_results.append({
                'rule_index': idx,
                'firing_strength': strength,
                'antecedents': rule['antecedents'],
                'consequent': rule['consequent'],
            })
            if strength > 1e-9:
                rules_fired.append(idx)
                output_groups.setdefault(out_var, []).append((strength, out_label))

        # 3. Aggregate & defuzzify per output variable
        output_values = {}
        for out_var, rule_outputs in output_groups.items():
            output_values[out_var] = self._aggregate_and_defuzzify(out_var, rule_outputs)

        # If an output variable had no fired rules, use midpoint
        for var_name, var_info in self.variables.items():
            if var_name not in output_values:
                output_values[var_name] = (var_info['universe_min'] + var_info['universe_max']) / 2.0

        return {
            'output_values': output_values,
            'firing_strengths': firing_strengths,
            'rules_fired': rules_fired,
            'details': rule_results,
        }


# --------------------------------------------------------------------------- #
#  FuzzyCreditScoring                                                       #
# --------------------------------------------------------------------------- #

class FuzzyCreditScoring:
    """Pre-built fuzzy credit scoring system (0-100 scale)."""

    def __init__(self):
        self.fis = FuzzyInferenceSystem()
        self._build_variables()
        self._build_rules()

    def _build_variables(self):
        # Income ($k)
        self.fis.add_variable('income', 0, 200, [
            ('triangular', [0, 25, 55], 'low'),
            ('triangular', [30, 70, 110], 'medium'),
            ('triangular', [70, 140, 200], 'high'),
        ])
        # Debt-to-income ratio (0–1)
        self.fis.add_variable('debt_ratio', 0, 1, [
            ('triangular', [0, 0.1, 0.3], 'low'),
            ('triangular', [0.2, 0.45, 0.65], 'medium'),
            ('triangular', [0.5, 0.8, 1.0], 'high'),
        ])
        # Credit history (years)
        self.fis.add_variable('credit_history', 0, 20, [
            ('triangular', [0, 1.5, 4], 'poor'),
            ('triangular', [2, 6, 10], 'fair'),
            ('triangular', [6, 13, 20], 'good'),
        ])
        # Employment years
        self.fis.add_variable('employment_years', 0, 25, [
            ('triangular', [0, 1.5, 4], 'short'),
            ('triangular', [2, 6, 10], 'medium'),
            ('triangular', [6, 15, 25], 'long'),
        ])
        # Credit score output (0–100)
        self.fis.add_variable('credit_score', 0, 100, [
            ('triangular', [0, 10, 30], 'very_low'),
            ('triangular', [20, 40, 55], 'low'),
            ('triangular', [45, 62, 75], 'medium'),
            ('triangular', [65, 80, 92], 'high'),
            ('triangular', [85, 95, 100], 'very_high'),
        ])

    def _build_rules(self):
        R = self.fis.add_rule
        # --- Strong positive signals ---
        R([('income', 'high'), ('debt_ratio', 'low'), ('credit_history', 'good')],
          ('credit_score', 'very_high'))
        R([('income', 'high'), ('employment_years', 'long'), ('debt_ratio', 'low')],
          ('credit_score', 'very_high'))
        R([('income', 'medium'), ('debt_ratio', 'low'), ('credit_history', 'good'), ('employment_years', 'long')],
          ('credit_score', 'very_high'))

        # --- Good signals ---
        R([('income', 'high'), ('debt_ratio', 'medium'), ('credit_history', 'fair')],
          ('credit_score', 'high'))
        R([('income', 'medium'), ('debt_ratio', 'low'), ('credit_history', 'fair')],
          ('credit_score', 'high'))
        R([('income', 'medium'), ('debt_ratio', 'medium'), ('credit_history', 'good')],
          ('credit_score', 'high'))
        R([('income', 'high'), ('credit_history', 'good')],
          ('credit_score', 'high'))

        # --- Medium signals ---
        R([('income', 'medium'), ('debt_ratio', 'medium'), ('credit_history', 'fair')],
          ('credit_score', 'medium'))
        R([('income', 'low'), ('debt_ratio', 'low'), ('credit_history', 'fair'), ('employment_years', 'medium')],
          ('credit_score', 'medium'))
        R([('income', 'medium'), ('debt_ratio', 'medium'), ('employment_years', 'short')],
          ('credit_score', 'medium'))
        R([('income', 'low'), ('debt_ratio', 'low'), ('credit_history', 'good')],
          ('credit_score', 'medium'))
        R([('income', 'medium'), ('debt_ratio', 'low'), ('employment_years', 'short')],
          ('credit_score', 'medium'))

        # --- Weak / negative signals ---
        R([('income', 'low'), ('debt_ratio', 'high'), ('credit_history', 'poor')],
          ('credit_score', 'low'))
        R([('income', 'medium'), ('debt_ratio', 'high'), ('credit_history', 'poor')],
          ('credit_score', 'low'))
        R([('income', 'low'), ('debt_ratio', 'medium'), ('credit_history', 'poor')],
          ('credit_score', 'low'))
        R([('employment_years', 'short'), ('debt_ratio', 'high')],
          ('credit_score', 'low'))

        # --- Very weak signals ---
        R([('income', 'low'), ('debt_ratio', 'high'), ('credit_history', 'poor'), ('employment_years', 'short')],
          ('credit_score', 'very_low'))
        R([('debt_ratio', 'high'), ('credit_history', 'poor')],
          ('credit_score', 'very_low'))

    def _rating_label(self, score: float) -> str:
        if score >= 80:
            return 'Excellent'
        elif score >= 65:
            return 'Good'
        elif score >= 45:
            return 'Fair'
        elif score >= 25:
            return 'Poor'
        else:
            return 'Very Poor'

    def score(self, income: float, debt_ratio: float,
              credit_history_years: float, employment_years: float) -> Dict[str, Any]:
        """Score a borrower.

        Parameters
        ----------
        income : float — annual income in $thousands.
        debt_ratio : float — debt-to-income ratio in [0, 1].
        credit_history_years : float — length of credit history in years.
        employment_years : float — current employment duration in years.

        Returns
        -------
        dict with keys: score, rating, details.
        """
        result = self.fis.evaluate({
            'income': income,
            'debt_ratio': debt_ratio,
            'credit_history': credit_history_years,
            'employment_years': employment_years,
        })
        raw = result['output_values']['credit_score']
        score_val = float(np.clip(raw, 0, 100))
        return {
            'score': round(score_val, 2),
            'rating': self._rating_label(score_val),
            'details': result,
        }


# --------------------------------------------------------------------------- #
#  FuzzyTradingSystem                                                      #
# --------------------------------------------------------------------------- #

class FuzzyTradingSystem:
    """Pre-built fuzzy trading signal generator."""

    def __init__(self):
        self.fis = FuzzyInferenceSystem()
        self._build_variables()
        self._build_rules()

    def _build_variables(self):
        # RSI (0–100)
        self.fis.add_variable('rsi', 0, 100, [
            ('triangular', [0, 15, 35], 'oversold'),
            ('triangular', [25, 50, 75], 'neutral'),
            ('triangular', [65, 85, 100], 'overbought'),
        ])
        # Volume normalised (0–1)
        self.fis.add_variable('volume', 0, 1, [
            ('triangular', [0, 0.2, 0.45], 'low'),
            ('triangular', [0.3, 0.55, 0.75], 'medium'),
            ('triangular', [0.6, 0.85, 1.0], 'high'),
        ])
        # Price trend % change
        self.fis.add_variable('price_trend', -10, 10, [
            ('triangular', [-10, -5, -1], 'falling'),
            ('triangular', [-3, 0, 3], 'flat'),
            ('triangular', [1, 5, 10], 'rising'),
        ])
        # Volatility (e.g. annualised std %)
        self.fis.add_variable('volatility', 0, 60, [
            ('triangular', [0, 8, 18], 'low'),
            ('triangular', [12, 28, 42], 'medium'),
            ('triangular', [30, 48, 60], 'high'),
        ])
        # Signal output (0 strong_sell → 100 strong_buy)
        self.fis.add_variable('signal', 0, 100, [
            ('triangular', [0, 10, 25], 'strong_sell'),
            ('triangular', [15, 32, 48], 'sell'),
            ('triangular', [38, 52, 62], 'hold'),
            ('triangular', [52, 68, 82], 'buy'),
            ('triangular', [75, 92, 100], 'strong_buy'),
        ])

    def _build_rules(self):
        R = self.fis.add_rule
        # --- Strong buy ---
        R([('rsi', 'oversold'), ('price_trend', 'rising'), ('volume', 'high')],
          ('signal', 'strong_buy'))
        R([('rsi', 'oversold'), ('price_trend', 'flat'), ('volatility', 'low')],
          ('signal', 'strong_buy'))
        R([('rsi', 'oversold'), ('volume', 'high'), ('volatility', 'low')],
          ('signal', 'strong_buy'))
        R([('rsi', 'oversold'), ('price_trend', 'rising')],
          ('signal', 'strong_buy'))

        # --- Buy ---
        R([('rsi', 'oversold'), ('price_trend', 'falling'), ('volume', 'medium')],
          ('signal', 'buy'))
        R([('rsi', 'neutral'), ('price_trend', 'rising'), ('volume', 'high'), ('volatility', 'low')],
          ('signal', 'buy'))
        R([('rsi', 'neutral'), ('price_trend', 'rising'), ('volatility', 'low')],
          ('signal', 'buy'))
        R([('rsi', 'oversold'), ('volatility', 'medium')],
          ('signal', 'buy'))

        # --- Hold ---
        R([('rsi', 'neutral'), ('price_trend', 'flat'), ('volume', 'medium')],
          ('signal', 'hold'))
        R([('rsi', 'neutral'), ('volatility', 'medium')],
          ('signal', 'hold'))
        R([('rsi', 'neutral'), ('price_trend', 'rising'), ('volatility', 'high')],
          ('signal', 'hold'))
        R([('rsi', 'neutral'), ('price_trend', 'falling'), ('volatility', 'high')],
          ('signal', 'hold'))
        R([('rsi', 'neutral'), ('price_trend', 'flat')],
          ('signal', 'hold'))

        # --- Sell ---
        R([('rsi', 'overbought'), ('price_trend', 'falling'), ('volume', 'high')],
          ('signal', 'sell'))
        R([('rsi', 'overbought'), ('price_trend', 'flat'), ('volatility', 'medium')],
          ('signal', 'sell'))
        R([('rsi', 'overbought'), ('volatility', 'high')],
          ('signal', 'sell'))
        R([('rsi', 'neutral'), ('price_trend', 'falling'), ('volume', 'high'), ('volatility', 'low')],
          ('signal', 'sell'))

        # --- Strong sell ---
        R([('rsi', 'overbought'), ('price_trend', 'falling'), ('volatility', 'high')],
          ('signal', 'strong_sell'))
        R([('rsi', 'overbought'), ('price_trend', 'falling'), ('volume', 'high')],
          ('signal', 'strong_sell'))
        R([('rsi', 'overbought'), ('price_trend', 'rising'), ('volatility', 'high')],
          ('signal', 'strong_sell'))
        R([('rsi', 'overbought'), ('price_trend', 'falling')],
          ('signal', 'strong_sell'))

    @staticmethod
    def _signal_label(val: float) -> str:
        if val <= 20:
            return 'strong_sell'
        elif val <= 40:
            return 'sell'
        elif val <= 60:
            return 'hold'
        elif val <= 80:
            return 'buy'
        else:
            return 'strong_buy'

    @staticmethod
    def _signal_strength(val: float) -> str:
        dist = abs(val - 50.0)
        if dist >= 30:
            return 'very_strong'
        elif dist >= 15:
            return 'strong'
        elif dist >= 5:
            return 'moderate'
        else:
            return 'weak'

    def evaluate_signal(self, rsi: float, volume_norm: float,
                        price_trend_pct: float, volatility: float) -> Dict[str, Any]:
        """Generate a trading signal.

        Parameters
        ----------
        rsi : float — RSI value, typically 0–100.
        volume_norm : float — normalised volume in [0, 1].
        price_trend_pct : float — price change % (can be negative).
        volatility : float — volatility measure (e.g. annualised std %).

        Returns
        -------
        dict with keys: signal, strength, rule_fired, details.
        """
        result = self.fis.evaluate({
            'rsi': rsi,
            'volume': volume_norm,
            'price_trend': price_trend_pct,
            'volatility': volatility,
        })
        raw = result['output_values']['signal']
        raw = float(np.clip(raw, 0, 100))
        return {
            'signal': self._signal_label(raw),
            'strength': self._signal_strength(raw),
            'raw_value': round(raw, 2),
            'rule_fired': result['rules_fired'],
            'details': result,
        }


# --------------------------------------------------------------------------- #
#  FuzzyAHP                                                                #
# --------------------------------------------------------------------------- #

# Saaty Random Index for matrices of size 1–15
_RANDOM_INDEX = {
    1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
}


class FuzzyAHP:
    """Fuzzy Analytic Hierarchy Process using triangular fuzzy comparisons."""

    def __init__(self, criteria: List[str]):
        self.criteria = list(criteria)
        self.n = len(criteria)
        # Upper-triangular matrix of fuzzy numbers; lower-triangular is reciprocal
        self._pairwise: Dict[Tuple[int, int], FuzzyNumber] = {}

    def set_pairwise_comparison(self, i: int, j: int,
                                value: Union[float, Tuple[float, float, float],
                                             Tuple[float, float, float, float],
                                             FuzzyNumber]):
        """Set the fuzzy comparison between criterion *i* and *j*.

        *value* can be a crisp float, a (l, m, u) tuple, a (a, b, c, d) tuple,
        or a FuzzyNumber instance.  The reciprocal is stored automatically.
        """
        if isinstance(value, FuzzyNumber):
            fn = value
        elif isinstance(value, (list, tuple)):
            if len(value) == 3:
                fn = FuzzyNumber(*value)
            else:
                fn = FuzzyNumber(*value)
        else:
            v = float(value)
            fn = FuzzyNumber(max(v - 0.5, 0.1), v, v + 0.5)
        self._pairwise[(i, j)] = fn
        # Reciprocal
        self._pairwise[(j, i)] = self._reciprocal(fn)

    @staticmethod
    def _reciprocal(fn: FuzzyNumber) -> FuzzyNumber:
        eps = 1e-12
        if fn.is_trapezoidal:
            return FuzzyNumber(
                1.0 / (fn.d + eps), 1.0 / (fn.c + eps),
                1.0 / (fn.b + eps), 1.0 / (fn.a + eps))
        return FuzzyNumber(
            1.0 / (fn.c + eps), 1.0 / (fn.b + eps), 1.0 / (fn.a + eps))

    def _build_crisp_matrix(self, alpha: float = 0.5) -> np.ndarray:
        """Build a crisp pairwise comparison matrix at a given alpha-cut (midpoint)."""
        M = np.ones((self.n, self.n))
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if (i, j) in self._pairwise:
                    cut = self._pairwise[(i, j)].alpha_cut(alpha)
                    M[i, j] = (cut[0] + cut[1]) / 2.0
                    M[j, i] = 1.0 / M[i, j]
        return M

    # ---- consistency ratio ----------------------------------------------- #

    def consistency_ratio(self, matrix: np.ndarray) -> float:
        """Compute CR = (λ_max - n) / (n - 1) / RI.

        Parameters
        ----------
        matrix : np.ndarray — crisp n×n pairwise comparison matrix.
        """
        n = matrix.shape[0]
        eigenvalues = np.linalg.eigvals(matrix)
        lambda_max = float(np.max(np.real(eigenvalues)))
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = _RANDOM_INDEX.get(n, 1.59)
        return ci / ri if ri > 0 else 0.0

    # ---- compute weights ------------------------------------------------- #

    def compute_weights(self) -> Dict[str, Any]:
        """Compute priority weights using geometric mean method with
        alpha-cut aggregation (α = 0, 0.5, 1.0).

        Returns {weights: dict, consistency_ratio: float, is_consistent: bool}.
        """
        # Aggregate over multiple alpha levels
        alphas = [0.0, 0.5, 1.0]
        weight_sets = []
        for alpha in alphas:
            M = self._build_crisp_matrix(alpha)
            # Geometric mean of each row
            geo_means = np.prod(M, axis=1) ** (1.0 / self.n)
            total = np.sum(geo_means)
            w = geo_means / total if total > 0 else np.ones(self.n) / self.n
            weight_sets.append(w)

        # Average across alpha levels
        avg_weights = np.mean(weight_sets, axis=0)
        avg_weights = avg_weights / np.sum(avg_weights)

        # Consistency at alpha = 0.5
        M_mid = self._build_crisp_matrix(0.5)
        cr = self.consistency_ratio(M_mid)

        weights_dict = {name: round(float(avg_weights[i]), 6)
                        for i, name in enumerate(self.criteria)}
        return {
            'weights': weights_dict,
            'consistency_ratio': round(cr, 6),
            'is_consistent': cr < 0.10,
            'weight_vector': avg_weights.tolist(),
        }


# --------------------------------------------------------------------------- #
#  FuzzyTOPSIS                                                             #
# --------------------------------------------------------------------------- #

class FuzzyTOPSIS:
    """Fuzzy TOPSIS for multi-criteria decision making with triangular fuzzy ratings."""

    def __init__(self, alternatives: List[str], criteria: List[str],
                 weights: List[float], benefit_criteria: List[bool]):
        """
        Parameters
        ----------
        alternatives : list of alternative names.
        criteria : list of criterion names.
        weights : list of criterion weights (should sum to 1).
        benefit_criteria : list of bools — True if criterion is benefit (higher is better).
        """
        self.alternatives = list(alternatives)
        self.criteria = list(criteria)
        self.weights = np.array(weights, dtype=float)
        self.weights = self.weights / self.weights.sum()
        self.benefit = np.array(benefit_criteria, dtype=bool)
        self.n_alt = len(alternatives)
        self.n_crit = len(criteria)

    def evaluate(self, decision_matrix: np.ndarray) -> Dict[str, Any]:
        """Run Fuzzy TOPSIS.

        Parameters
        ----------
        decision_matrix : np.ndarray of shape (n_alt, n_crit, 3)
            Each entry is a triangular fuzzy number [l, m, u].

        Returns
        -------
        dict with keys: rankings, scores, best_alternative, distances.
        """
        F = np.asarray(decision_matrix, dtype=float)
        assert F.shape == (self.n_alt, self.n_crit, 3), \
            f"Expected shape ({self.n_alt}, {self.n_crit}, 3), got {F.shape}"

        # 1. Normalise fuzzy decision matrix (linear scale normalisation)
        F_norm = np.zeros_like(F)
        for j in range(self.n_crit):
            u_max = np.max(F[:, j, 2])  # max of upper bounds
            if u_max < 1e-15:
                F_norm[:, j, :] = F[:, j, :]
            else:
                F_norm[:, j, 0] = F[:, j, 0] / u_max
                F_norm[:, j, 1] = F[:, j, 1] / u_max
                F_norm[:, j, 2] = F[:, j, 2] / u_max

        # 2. Weighted normalised fuzzy decision matrix
        F_w = F_norm.copy()
        for j in range(self.n_crit):
            F_w[:, j, :] *= self.weights[j]

        # 3. Fuzzy Positive Ideal Solution (FPIS) and Fuzzy Negative Ideal Solution (FNIS)
        fpis = np.zeros((self.n_crit, 3))
        fnis = np.zeros((self.n_crit, 3))
        for j in range(self.n_crit):
            if self.benefit[j]:
                fpis[j] = [F_w[:, j, k].max() for k in range(3)]
                fnis[j] = [F_w[:, j, k].min() for k in range(3)]
            else:
                fpis[j] = [F_w[:, j, k].min() for k in range(3)]
                fnis[j] = [F_w[:, j, k].max() for k in range(3)]

        # 4. Distance of each alternative to FPIS and FNIS
        #    Using vertex method for distance between two triangular fuzzy numbers
        d_pos = np.zeros(self.n_alt)
        d_neg = np.zeros(self.n_alt)
        for i in range(self.n_alt):
            for j in range(self.n_crit):
                a = F_w[i, j]
                d_pos[i] += self._fuzzy_distance(a, fpis[j])
                d_neg[i] += self._fuzzy_distance(a, fnis[j])

        # 5. Closeness coefficient
        cc = d_neg / (d_pos + d_neg + 1e-15)

        # 6. Rank
        rank_idx = np.argsort(-cc)
        rankings = [self.alternatives[idx] for idx in rank_idx]
        scores = {self.alternatives[i]: round(float(cc[i]), 6) for i in range(self.n_alt)}

        return {
            'rankings': rankings,
            'scores': scores,
            'best_alternative': rankings[0],
            'distances': {
                'positive': {self.alternatives[i]: round(float(d_pos[i]), 6)
                             for i in range(self.n_alt)},
                'negative': {self.alternatives[i]: round(float(d_neg[i]), 6)
                             for i in range(self.n_alt)},
                'closeness': scores,
            },
        }

    @staticmethod
    def _fuzzy_distance(a: np.ndarray, b: np.ndarray) -> float:
        """Vertex method distance between two triangular fuzzy numbers.

        d(A, B) = sqrt(1/3 * Σ_{k=1}^{3} (a_k - b_k)^2)
        """
        return float(np.sqrt(np.mean((a - b) ** 2)))


# --------------------------------------------------------------------------- #
#  ANFIS (Simplified Adaptive Neuro-Fuzzy Inference System)                 #
# --------------------------------------------------------------------------- #

class ANFIS:
    """Simplified first-order Sugeno ANFIS with Gaussian membership functions.

    Layer 1: Gaussian MFs  μ(x) = exp(-((x - c)^2) / (2 σ^2))
    Layer 2: Rule firing strengths  w_i = Π μ_ij  (product t-norm)
    Layer 3: Normalised firing  w̄_i = w_i / Σ w_j
    Layer 4: Consequent  f_i = w̄_i * (p_i·x_1 + q_i·x_2 + ... + r_i)
    Layer 5: Sum  y = Σ f_i
    """

    def __init__(self, n_inputs: int, n_mfs_per_input: int = 3,
                 learning_rate: float = 0.01):
        self.n_inputs = n_inputs
        self.n_mfs = n_mfs_per_input
        self.lr = learning_rate
        self.n_rules = n_mfs_per_input ** n_inputs

        # MF parameters: shape (n_inputs, n_mfs, 2) -> [sigma, centre]
        self.mf_params = np.random.randn(n_inputs, n_mfs_per_input, 2) * 0.5
        self.mf_params[:, :, 0] = np.abs(self.mf_params[:, :, 0]) + 0.3   # sigma > 0

        # Consequent parameters: (n_rules, n_inputs + 1) -> [p1, p2, ..., pn, r]
        self.consequents = np.random.randn(self.n_rules, n_inputs + 1) * 0.1

        self._trained = False
        self._losses: List[float] = []

    def _gaussian_mf(self, x: np.ndarray, sigma: float, centre: float) -> np.ndarray:
        """Vectorised Gaussian membership function."""
        return np.exp(-((x - centre) ** 2) / (2.0 * sigma ** 2 + 1e-15))

    def _forward(self, X: np.ndarray):
        """Forward pass. Returns (output, cache) where cache stores
        intermediates needed for back-propagation.

        Parameters
        ----------
        X : (n_samples, n_inputs)
        """
        n = X.shape[0]

        # Layer 1: MF activations  (n, n_inputs, n_mfs)
        mf_out = np.zeros((n, self.n_inputs, self.n_mfs))
        for i in range(self.n_inputs):
            for j in range(self.n_mfs):
                sigma = self.mf_params[i, j, 0]
                centre = self.mf_params[i, j, 1]
                mf_out[:, i, j] = self._gaussian_mf(X[:, i], sigma, centre)

        # Layer 2: Rule firing strengths via product t-norm
        # Build rule index combinations
        rule_indices = self._rule_index_grid()  # (n_rules, n_inputs)
        w = np.ones((n, self.n_rules))
        for r in range(self.n_rules):
            for i in range(self.n_inputs):
                w[:, r] *= mf_out[:, i, rule_indices[r, i]]

        # Layer 3: Normalise
        w_sum = np.sum(w, axis=1, keepdims=True) + 1e-15
        w_norm = w / w_sum

        # Layer 4: Consequent  f_i = w̄_i * (Σ p_k x_k + r)
        X_aug = np.hstack([X, np.ones((n, 1))])  # (n, n_inputs+1)
        # (n, n_rules) * (n_rules, n_inputs+1) @ (n_inputs+1, n) -> element wise
        linear = X_aug @ self.consequents.T  # (n, n_rules)
        f = w_norm * linear

        # Layer 5: Sum
        output = np.sum(f, axis=1)  # (n,)

        cache = {
            'mf_out': mf_out,
            'w': w,
            'w_norm': w_norm,
            'w_sum': w_sum,
            'linear': linear,
            'f': f,
            'X': X,
            'X_aug': X_aug,
            'rule_indices': rule_indices,
        }
        return output, cache

    def _rule_index_grid(self) -> np.ndarray:
        """Return array of shape (n_rules, n_inputs) mapping each rule to MF index per input."""
        grids = np.meshgrid(*[np.arange(self.n_mfs) for _ in range(self.n_inputs)],
                            indexing='ij')
        shape = grids[0].shape
        return np.column_stack([g.ravel() for g in grids])

    def fit(self, X: np.ndarray, y: np.ndarray,
            epochs: int = 100) -> Dict[str, Any]:
        """Train ANFIS using gradient descent (hybrid-style single pass).

        Parameters
        ----------
        X : (n_samples, n_inputs)
        y : (n_samples,)
        epochs : int

        Returns
        -------
        {losses: list, trained_params: {mf_params, consequents}}
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self._losses = []
        n = X.shape[0]

        for epoch in range(epochs):
            output, cache = self._forward(X)
            error = output - y
            loss = float(np.mean(error ** 2))
            self._losses.append(loss)

            # ---- Backward pass (gradient descent) ----
            # dL/dy = 2*error/n
            dL_dy = 2.0 * error / n  # (n,)

            # Layer 5 → 4: dL/df_i = dL_dy (summed over rules)
            # Since y = Σ f_i, ∂y/∂f_i = 1
            # dL/df_i (per sample, per rule) = dL_dy broadcast
            dL_df = np.outer(dL_dy, np.ones(self.n_rules))  # (n, n_rules)

            # f_i = w̄_i * linear_i
            # ∂f_i/∂linear_i = w̄_i
            # ∂f_i/∂w̄_i = linear_i
            w_norm = cache['w_norm']
            linear = cache['linear']
            X_aug = cache['X_aug']
            w = cache['w']
            w_sum = cache['w_sum']
            mf_out = cache['mf_out']
            rule_indices = cache['rule_indices']

            dL_dlinear = dL_df * w_norm  # (n, n_rules)
            dL_dwnorm = dL_df * linear  # (n, n_rules)

            # Update consequent parameters: dL/d(consequent) = X_aug.T @ dL_dlinear
            grad_conseq = X_aug.T @ dL_dlinear  # (n_inputs+1, n_rules)
            self.consequents -= self.lr * grad_conseq.T

            # Layer 3: w̄_i = w_i / Σw
            # ∂w̄_i/∂w_i = (Σw - w_i) / (Σw)^2
            # ∂w̄_i/∂w_j = -w_i / (Σw)^2  (for j ≠ i)
            dL_dw = np.zeros_like(w)  # (n, n_rules)
            for r in range(self.n_rules):
                dL_dw[:, r] = dL_dwnorm[:, r] * (w_sum[:, 0] - w[:, r]) / (w_sum[:, 0] ** 2)
                for rr in range(self.n_rules):
                    if rr != r:
                        dL_dw[:, r] += dL_dwnorm[:, rr] * (-w[:, r]) / (w_sum[:, 0] ** 2)

            # Layer 2: w_r = Π μ_ij  →  ∂w_r/∂μ_ij = w_r / μ_ij
            dL_dmf = np.zeros_like(mf_out)  # (n, n_inputs, n_mfs)
            for r in range(self.n_rules):
                for i in range(self.n_inputs):
                    j = rule_indices[r, i]
                    mu_ij = mf_out[:, i, j] + 1e-15
                    dL_dmf[:, i, j] += dL_dw[:, r] * (w[:, r] / mu_ij)

            # Layer 1: Gaussian MF  μ = exp(-((x-c)^2)/(2σ^2))
            # ∂μ/∂σ = μ * ((x-c)^2) / σ^3
            # ∂μ/∂c = μ * (x-c) / σ^2
            for i in range(self.n_inputs):
                for j in range(self.n_mfs):
                    sigma = self.mf_params[i, j, 0]
                    centre = self.mf_params[i, j, 1]
                    mu = mf_out[:, i, j]
                    x_col = X[:, i]

                    dmu_dsigma = mu * ((x_col - centre) ** 2) / (sigma ** 3 + 1e-15)
                    dmu_dcentre = mu * (x_col - centre) / (sigma ** 2 + 1e-15)

                    grad_sigma = float(np.mean(dL_dmf[:, i, j] * dmu_dsigma))
                    grad_centre = float(np.mean(dL_dmf[:, i, j] * dmu_dcentre))

                    self.mf_params[i, j, 0] -= self.lr * grad_sigma
                    self.mf_params[i, j, 1] -= self.lr * grad_centre
                    # Keep sigma positive
                    self.mf_params[i, j, 0] = max(self.mf_params[i, j, 0], 1e-6)

        self._trained = True
        return {
            'losses': self._losses,
            'trained_params': {
                'mf_params': self.mf_params.copy(),
                'consequents': self.consequents.copy(),
            },
            'final_loss': self._losses[-1] if self._losses else None,
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Forward-pass prediction on new data.

        Parameters
        ----------
        X : (n_samples, n_inputs)

        Returns
        -------
        np.ndarray of shape (n_samples,)
        """
        X = np.asarray(X, dtype=float)
        output, _ = self._forward(X)
        return output
