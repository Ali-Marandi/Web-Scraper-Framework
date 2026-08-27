"""fuzzy_engine.py — Fuzzy Logic Engine for Web Scraping Applications

Implements Fuzzy Set Theory methodologies tailored for data processing,
matching, classification, and quality assessment in a web scraper context.

Dependencies: numpy (for array operations in defuzzification and membership
function evaluation only).  All string matching is pure Python.

Components
-----------
- FuzzySet               : Core fuzzy set with membership functions and operations
- MembershipFunction      : Factory functions (triangular, trapezoidal, gaussian, sigmoid)
- FuzzyRule               : Single fuzzy if-then rule with AND/OR logic
- FuzzyInferenceSystem    : Mamdani-style fuzzy inference engine
- FuzzyMatcher            : Fuzzy string matching for scraping tasks
- FuzzyClassifier         : Keyword-based fuzzy text classification
- FuzzyDataQuality        : Data quality assessment via fuzzy logic
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np


# ======================================================================== #
#  Membership Function Factory                                            #
# ======================================================================== #

def triangular(
    a: float, b: float, c: float
) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Create a triangular membership function.

    Parameters
    ----------
    a : float
        Left foot (membership = 0).
    b : float
        Peak (membership = 1).
    c : float
        Right foot (membership = 0).

    Returns
    -------
    Callable
        A function that accepts a scalar or numpy array and returns
        membership degrees in [0, 1].
    """
    def _tri(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float64)
        result = np.zeros_like(x)
        if b > a:
            result = np.where((x > a) & (x <= b), (x - a) / (b - a), result)
        else:
            result = np.where((x >= b) & (x <= b), 1.0, result)
        result = np.where(np.isclose(x, b, atol=1e-12), 1.0, result)
        if c > b:
            result = np.where((x > b) & (x < c), (c - x) / (c - b), result)
        else:
            result = np.where((x >= b) & (x <= c) & (c <= b), 1.0, result)
        return float(result) if result.ndim == 0 else result
    return _tri


def trapezoidal(
    a: float, b: float, c: float, d: float
) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Create a trapezoidal membership function.

    Parameters
    ----------
    a : float
        Left foot.
    b : float
        Left shoulder (start of plateau).
    c : float
        Right shoulder (end of plateau).
    d : float
        Right foot.

    Returns
    -------
    Callable
        Membership function accepting scalar or array.
    """
    def _trap(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float64)
        result = np.zeros_like(x)
        left_slope = (x - a) / (b - a) if b != a else 1.0
        result = np.where((x > a) & (x < b), left_slope, result)
        result = np.where((x >= b) & (x <= c), 1.0, result)
        right_slope = (d - x) / (d - c) if d != c else 1.0
        result = np.where((x > c) & (x < d), right_slope, result)
        return float(result) if result.ndim == 0 else result
    return _trap


def gaussian(
    mean: float, sigma: float
) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Create a Gaussian membership function.

    Parameters
    ----------
    mean : float
        Centre of the bell curve.
    sigma : float
        Standard deviation controlling the spread.

    Returns
    -------
    Callable
        mu(x) = exp(-((x - mean)^2) / (2 * sigma^2))
    """
    def _gauss(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float64)
        result: Union[float, np.ndarray] = np.exp(-0.5 * ((x - mean) / sigma) ** 2)
        return float(result) if np.ndim(result) == 0 else result
    return _gauss


def sigmoid(
    a: float, c: float
) -> Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]:
    """Create a sigmoidal membership function.

    Parameters
    ----------
    a : float
        Slope steepness (sign controls direction).
    c : float
        Crossover point where membership = 0.5.

    Returns
    -------
    Callable
        mu(x) = 1 / (1 + exp(-a * (x - c)))
    """
    def _sig(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=np.float64)
        result: Union[float, np.ndarray] = 1.0 / (1.0 + np.exp(-a * (x - c)))
        return float(result) if np.ndim(result) == 0 else result
    return _sig


# Type alias accepted wherever a membership callable is expected.
MembershipFunc = Callable[[Union[float, np.ndarray]], Union[float, np.ndarray]]


# ======================================================================== #
#  FuzzySet                                                                #
# ======================================================================== #

class FuzzySet:
    """A fuzzy set defined over a discrete or continuous universe.

    Stores a name, a membership function, and an optional universe of
    discourse (a 1-D numpy array of sample points used for plotting,
    alpha-cuts, and defuzzification).

    Parameters
    ----------
    name : str
        Human-readable label for this fuzzy set.
    membership_func : Callable
        Any of the factory functions above or a custom callable ``x -> [0, 1]``.
    universe : numpy.ndarray or None
        Optional discretisation of the universe of discourse.

    Attributes
    ----------
    name : str
    membership_func : Callable
    universe : numpy.ndarray | None
    """

    __slots__ = ("name", "membership_func", "universe")

    def __init__(
        self,
        name: str,
        membership_func: MembershipFunc,
        universe: Optional[np.ndarray] = None,
    ) -> None:
        self.name: str = name
        self.membership_func: MembershipFunc = membership_func
        self.universe: Optional[np.ndarray] = (
            np.asarray(universe, dtype=np.float64) if universe is not None else None
        )

    # ------------------------------------------------------------------ #
    #  Evaluation helpers                                                 #
    # ------------------------------------------------------------------ #

    def evaluate(self, x: Union[float, np.ndarray, None] = None) -> np.ndarray:
        """Return membership degrees for *x*, or over the whole universe.

        Parameters
        ----------
        x : float | np.ndarray | None
            Evaluation points.  Falls back to ``self.universe`` when *None*.

        Returns
        -------
        np.ndarray
            Membership degrees clipped to [0, 1].

        Raises
        -----
        ValueError
            If both *x* and ``self.universe`` are ``None``.
        """
        if x is None:
            if self.universe is None:
                raise ValueError(
                    "Cannot evaluate: no evaluation points and no universe set."
                )
            x = self.universe
        raw = self.membership_func(x)
        return np.clip(np.asarray(raw, dtype=np.float64), 0.0, 1.0)

    def membership_at(self, x: float) -> float:
        """Return the scalar membership degree for a single crisp value *x*."""
        return float(np.clip(self.membership_func(x), 0.0, 1.0))

    # ------------------------------------------------------------------ #
    #  Set-theoretic operations                                           #
    # ------------------------------------------------------------------ #

    def union(self, other: "FuzzySet") -> "FuzzySet":
        """Fuzzy union:  max(mu_A(x), mu_B(x)) over the combined universe.

        Parameters
        ----------
        other : FuzzySet
            The other operand.

        Returns
        -------
        FuzzySet
            A new fuzzy set representing A ∪ B.
        """
        universe = self._combined_universe(other)
        mu_a = self.evaluate(universe)
        mu_b = other.evaluate(universe)
        mu = np.maximum(mu_a, mu_b)
        return FuzzySet(f"({self.name} ∪ {other.name})", lambda x, _m=mu, _u=universe: float(  # type: ignore[arg-type]
            np.interp(x, _u, _m)
        ), universe)

    def intersection(self, other: "FuzzySet") -> "FuzzySet":
        """Fuzzy intersection:  min(mu_A(x), mu_B(x)) over the combined universe.

        Parameters
        ----------
        other : FuzzySet
            The other operand.

        Returns
        -------
        FuzzySet
            A new fuzzy set representing A ∩ B.
        """
        universe = self._combined_universe(other)
        mu_a = self.evaluate(universe)
        mu_b = other.evaluate(universe)
        mu = np.minimum(mu_a, mu_b)
        return FuzzySet(f"({self.name} ∩ {other.name})", lambda x, _m=mu, _u=universe: float(  # type: ignore[arg-type]
            np.interp(x, _u, _m)
        ), universe)

    def complement(self) -> "FuzzySet":
        """Fuzzy complement:  1 - mu_A(x).

        Returns
        -------
        FuzzySet
            A new fuzzy set representing ¬A.
        """
        universe = self.universe
        if universe is None:
            raise ValueError("Cannot compute complement without a defined universe.")
        mu = 1.0 - self.evaluate(universe)
        return FuzzySet(f"¬{self.name}", lambda x, _m=mu, _u=universe: float(  # type: ignore[arg-type]
            np.interp(x, _u, _m)
        ), universe)

    def alpha_cut(self, alpha: float) -> Tuple[float, float]:
        """Compute the alpha-cut interval [x_lo, x_hi] at threshold *alpha*.

        Finds the smallest and largest x in ``self.universe`` whose
        membership degree is ≥ *alpha*.

        Parameters
        ----------
        alpha : float
            Threshold in (0, 1].

        Returns
        -------
        tuple[float, float]
            ``(x_lo, x_hi)`` — the interval of the alpha-cut.

        Raises
        -----
        ValueError
            If ``self.universe`` is not set or no element meets the threshold.
        """
        if self.universe is None:
            raise ValueError("Cannot compute alpha-cut without a defined universe.")
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1].")
        mu = self.evaluate()
        mask = mu >= alpha
        if not np.any(mask):
            raise ValueError(f"No element with membership >= {alpha}.")
        indices = np.where(mask)[0]
        return float(self.universe[indices[0]]), float(self.universe[indices[-1]])

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _combined_universe(self, other: "FuzzySet") -> np.ndarray:
        """Return a merged, sorted universe from *self* and *other*."""
        if self.universe is not None and other.universe is not None:
            merged = np.union1d(self.universe, other.universe)
        elif self.universe is not None:
            merged = self.universe
        elif other.universe is not None:
            merged = other.universe
        else:
            raise ValueError("At least one operand must have a defined universe.")
        return merged

    def __repr__(self) -> str:
        u_info = f"universe={len(self.universe)} pts" if self.universe is not None else "no universe"
        return f"FuzzySet(name={self.name!r}, {u_info})"


# ======================================================================== #
#  FuzzyRule                                                               #
# ======================================================================== #

class FuzzyRule:
    """A single fuzzy IF-THEN rule with arbitrary antecedents and a consequent.

    Each antecedent is a ``(variable_name, fuzzy_set_name)`` pair that is
    resolved against the inference system's variable definitions at
    evaluation time.

    Parameters
    ----------
    antecedents : list[tuple[str, str]]
        List of ``(input_variable, fuzzy_set_name)`` pairs.
    consequent : tuple[str, str]
        ``(output_variable, fuzzy_set_name)`` for the THEN part.
    operator : str, default ``"AND"``
        Logical connective joining antecedents — ``"AND"`` (min) or
        ``"OR"`` (max).

    Examples
    --------
    >>> rule = FuzzyRule(
    ...     antecedents=[("temperature", "hot"), ("humidity", "high")],
    ...     consequent=("comfort", "poor"),
    ...     operator="AND",
    ... )
    """

    __slots__ = ("antecedents", "consequent", "operator")

    def __init__(
        self,
        antecedents: List[Tuple[str, str]],
        consequent: Tuple[str, str],
        operator: str = "AND",
    ) -> None:
        if operator.upper() not in ("AND", "OR"):
            raise ValueError("operator must be 'AND' or 'OR'")
        self.antecedents: List[Tuple[str, str]] = list(antecedents)
        self.consequent: Tuple[str, str] = consequent
        self.operator: str = operator.upper()

    def __repr__(self) -> str:
        ants = " {} ".format(self.operator).join(
            f"{v} IS {fs}" for v, fs in self.antecedents
        )
        return f"IF {ants} THEN {self.consequent[0]} IS {self.consequent[1]}"

    def fire_strength(
        self,
        inputs: Dict[str, float],
        input_vars: Dict[str, Dict[str, FuzzySet]],
    ) -> float:
        """Compute the firing strength of this rule given crisp inputs.

        Parameters
        ----------
        inputs : dict[str, float]
            Mapping of input variable name → crisp value.
        input_vars : dict[str, dict[str, FuzzySet]]
            ``{var_name: {set_name: FuzzySet, ...}, ...}``

        Returns
        -------
        float
            The aggregated firing strength in [0, 1].
        """
        degrees: List[float] = []
        for var_name, fs_name in self.antecedents:
            if var_name not in inputs:
                return 0.0
            if var_name not in input_vars or fs_name not in input_vars[var_name]:
                return 0.0
            degree = input_vars[var_name][fs_name].membership_at(inputs[var_name])
            degrees.append(degree)
        if not degrees:
            return 0.0
        if self.operator == "AND":
            return float(min(degrees))
        return float(max(degrees))


# ======================================================================== #
#  FuzzyInferenceSystem  (Mamdani)                                        #
# ======================================================================== #

class FuzzyInferenceSystem:
    """Mamdani-style fuzzy inference engine.

    Supports multiple input and output variables, each with one or more
    fuzzy sets, and an arbitrary number of fuzzy rules.  Defuzzification
    is performed via the centroid (centre-of-gravity) method.

    Usage
    -----
    >>> fis = FuzzyInferenceSystem()
    >>> u = np.linspace(0, 10, 201)
    >>> fis.add_input_variable("temperature", u, {
    ...     "cold": FuzzySet("cold", triangular(0, 0, 4), u),
    ...     "warm": FuzzySet("warm", triangular(3, 5, 7), u),
    ...     "hot":  FuzzySet("hot",  triangular(6, 10, 10), u),
    ... })
    >>> fis.add_output_variable("fan_speed", np.linspace(0, 100, 201), {
    ...     "low":    FuzzySet("low",    triangular(0, 0, 50), u),
    ...     "medium": FuzzySet("medium", triangular(0, 50, 100), u),
    ...     "high":   FuzzySet("high",   triangular(50, 100, 100), u),
    ... })
    >>> fis.add_rule([("temperature", "cold")], ("fan_speed", "low"))
    >>> fis.add_rule([("temperature", "warm")], ("fan_speed", "medium"))
    >>> fis.add_rule([("temperature", "hot")], ("fan_speed", "high"))
    >>> result = fis.evaluate({"temperature": 8.0})
    >>> print(result)  # {'fan_speed': <crisp value near 80-100>}
    """

    def __init__(self) -> None:
        self._input_vars: Dict[str, Dict[str, FuzzySet]] = {}
        self._input_universes: Dict[str, np.ndarray] = {}
        self._output_vars: Dict[str, Dict[str, FuzzySet]] = {}
        self._output_universes: Dict[str, np.ndarray] = {}
        self._rules: List[FuzzyRule] = []

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def add_input_variable(
        self,
        name: str,
        universe: np.ndarray,
        fuzzy_sets: Dict[str, FuzzySet],
    ) -> None:
        """Register an input linguistic variable.

        Parameters
        ----------
        name : str
            Variable name used in rule antecedents.
        universe : numpy.ndarray
            1-D array of sample points for the universe of discourse.
        fuzzy_sets : dict[str, FuzzySet]
            Named fuzzy sets that partition (or cover) this variable's
            universe.
        """
        self._input_vars[name] = dict(fuzzy_sets)
        self._input_universes[name] = np.asarray(universe, dtype=np.float64)

    def add_output_variable(
        self,
        name: str,
        universe: np.ndarray,
        fuzzy_sets: Dict[str, FuzzySet],
    ) -> None:
        """Register an output linguistic variable.

        Parameters
        ----------
        name : str
            Variable name used in rule consequents.
        universe : numpy.ndarray
            1-D array of sample points.
        fuzzy_sets : dict[str, FuzzySet]
            Named output fuzzy sets.
        """
        self._output_vars[name] = dict(fuzzy_sets)
        self._output_universes[name] = np.asarray(universe, dtype=np.float64)

    def add_rule(
        self,
        antecedents: List[Tuple[str, str]],
        consequent: Tuple[str, str],
        operator: str = "AND",
    ) -> None:
        """Add a fuzzy IF-THEN rule.

        Parameters
        ----------
        antecedents : list[tuple[str, str]]
            Each element is ``(variable_name, set_name)``.
        consequent : tuple[str, str]
            ``(output_variable_name, set_name)``.
        operator : str, default ``"AND"``
            Logical connective: ``"AND"`` or ``"OR"``.
        """
        self._rules.append(FuzzyRule(antecedents, consequent, operator))

    def evaluate(self, inputs: Dict[str, float]) -> Dict[str, float]:
        """Evaluate the full inference system and return crisp outputs.

        Steps performed:
        1. **Fuzzification** — map each crisp input to membership
           degrees in every relevant fuzzy set.
        2. **Rule evaluation** — compute each rule's firing strength.
        3. **Aggregation** — for each output variable, take the maximum
           of all clipped consequent sets across all rules.
        4. **Defuzzification** — centroid (centre-of-gravity) method.

        Parameters
        ----------
        inputs : dict[str, float]
            Crisp values for each input variable.

        Returns
        -------
        dict[str, float]
            Crisp output values, one per output variable.
        """
        # Collect per-output-variable clipped sets.
        output_aggregated: Dict[str, np.ndarray] = {}

        for rule in self._rules:
            strength = rule.fire_strength(inputs, self._input_vars)
            if strength < 1e-12:
                continue

            out_var, out_fs_name = rule.consequent
            if out_var not in self._output_vars:
                continue
            if out_fs_name not in self._output_vars[out_var]:
                continue

            universe = self._output_universes[out_var]
            consequent_set = self._output_vars[out_var][out_fs_name]
            consequent_mu = consequent_set.evaluate(universe)
            clipped = np.minimum(consequent_mu, strength)

            if out_var not in output_aggregated:
                output_aggregated[out_var] = clipped
            else:
                output_aggregated[out_var] = np.maximum(
                    output_aggregated[out_var], clipped
                )

        # Defuzzify each output variable
        results: Dict[str, float] = {}
        for out_var in self._output_vars:
            if out_var not in output_aggregated:
                results[out_var] = 0.0
                continue
            agg = output_aggregated[out_var]
            universe = self._output_universes[out_var]
            total = float(np.sum(agg))
            if total < 1e-12:
                results[out_var] = 0.0
            else:
                results[out_var] = float(np.sum(universe * agg) / total)

        return results

    def __repr__(self) -> str:
        return (
            f"FuzzyInferenceSystem("
            f"inputs={list(self._input_vars)}, "
            f"outputs={list(self._output_vars)}, "
            f"rules={len(self._rules)})"
        )


# ======================================================================== #
#  FuzzyMatcher  (Levenshtein + Jaro-Winkler for scraping tasks)          #
# ======================================================================== #

class FuzzyMatcher:
    """Fuzzy string matching utilities for web scraping data deduplication,
    entity resolution, and approximate text comparison.

    Implements Levenshtein distance, Jaro-Winkler similarity, and combines
    them into a robust fuzzy matching score.  All methods are pure Python
    with no external dependencies beyond the standard library.
    """

    @staticmethod
    def levenshtein(s1: str, s2: str) -> int:
        """Compute the Levenshtein (edit) distance between two strings.

        Uses the Wagner-Fischer dynamic-programming algorithm with O(min(m,n))
        space complexity.
        """
        if s1 == s2:
            return 0
        len1, len2 = len(s1), len(s2)
        if len1 == 0:
            return len2
        if len2 == 0:
            return len1
        if len1 < len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        prev = list(range(len2 + 1))
        for i in range(1, len1 + 1):
            curr = [i] + [0] * len2
            for j in range(1, len2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
            prev = curr
        return prev[len2]

    @staticmethod
    def jaro_winkler(s1: str, s2: str, p: float = 0.1) -> float:
        """Compute Jaro-Winkler similarity between two strings.

        The Jaro-Winkler metric gives higher scores to strings that share
        a common prefix (up to 4 characters), making it ideal for
        short strings like product names, URLs, or titles.

        Parameters
        ----------
        s1, s2 : str
            Strings to compare.
        p : float
            Prefix scaling factor (default 0.1, max 0.25).

        Returns
        -------
        float
            Similarity in [0, 1].
        """
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        match_dist = max(len1, len2) // 2 - 1
        if match_dist < 0:
            match_dist = 0
        s1_matches = [False] * len1
        s2_matches = [False] * len2
        matches = 0
        transpositions = 0
        for i in range(len1):
            start = max(0, i - match_dist)
            end = min(i + match_dist + 1, len2)
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        if matches == 0:
            return 0.0
        k = 0
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        jaro = (
            matches / len1
            + matches / len2
            + (matches - transpositions / 2) / matches
        ) / 3.0
        prefix = 0
        for i in range(min(len1, len2, 4)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        p = min(p, 0.25)
        return jaro + prefix * p * (1.0 - jaro)

    def fuzzy_equal(self, s1: str, s2: str) -> float:
        """Compute a combined fuzzy equality score using Levenshtein and Jaro-Winkler.

        Returns a value in [0, 1] where 1.0 means identical strings.
        The score is the weighted average of normalized Levenshtein similarity
        and Jaro-Winkler similarity (60/40 split favouring Jaro-Winkler).
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        jw = self.jaro_winkler(s1, s2)
        max_len = max(len(s1), len(s2))
        lev_sim = 1.0 - (self.levenshtein(s1, s2) / max_len)
        return 0.6 * jw + 0.4 * lev_sim

    def fuzzy_contains(self, haystack: str, needle: str) -> float:
        """Compute fuzzy substring match score.

        Checks if *needle* approximately appears within *haystack*
        by sliding a window and computing fuzzy_equal for each window.
        """
        if not haystack or not needle:
            return 0.0
        if needle in haystack:
            return 1.0
        n_len = len(needle)
        h_len = len(haystack)
        if n_len > h_len:
            return self.fuzzy_equal(haystack, needle)
        best = 0.0
        step = max(1, n_len // 4)
        for i in range(0, h_len - n_len + 1, step):
            window = haystack[i : i + n_len]
            score = self.fuzzy_equal(window, needle)
            if score > best:
                best = score
                if best >= 0.95:
                    break
        return best

    def fuzzy_match_list(
        self, query: str, candidates: List[str], threshold: float = 0.6
    ) -> List[Tuple[str, float]]:
        """Find all candidates that fuzzy-match *query* above *threshold*.

        Returns a list of ``(candidate, score)`` pairs sorted by score descending.
        """
        results = []
        for c in candidates:
            score = self.fuzzy_equal(query, c)
            if score >= threshold:
                results.append((c, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def deduplicate(
        self, items: List[str], threshold: float = 0.85
    ) -> List[str]:
        """Remove fuzzy duplicates from a list of strings.

        Keeps the first occurrence of each near-duplicate group.
        Items are compared pairwise; if two items score above *threshold*,
        the later one is considered a duplicate and dropped.
        """
        unique: List[str] = []
        for item in items:
            is_dup = False
            for u in unique:
                if self.fuzzy_equal(item, u) >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(item)
        return unique


# ======================================================================== #
#  FuzzyClassifier  (keyword-based fuzzy text classification)             #
# ======================================================================== #

class FuzzyClassifier:
    """Classifies text into categories using fuzzy keyword matching.

    Each category is defined by a set of keywords, each with an associated
    membership value in (0, 1].  Classification score is computed by
    aggregating keyword membership degrees across the text.
    """

    def __init__(self) -> None:
        self._categories: Dict[str, Dict[str, float]] = {}
        self._matcher = FuzzyMatcher()

    def add_category(
        self, name: str, keywords: Dict[str, float]
    ) -> None:
        """Register a category with weighted keywords.

        Parameters
        ----------
        name : str
            Category label.
        keywords : dict[str, float]
            Mapping of keyword -> membership value in (0, 1].
            Higher values indicate stronger association.
        """
        self._categories[name] = dict(keywords)

    def classify(
        self, text: str, top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Classify *text* into registered categories.

        For each category, computes a fuzzy score based on how many of
        its keywords (or fuzzy matches) appear in the text, weighted
        by their membership values.

        Parameters
        ----------
        text : str
            The text to classify.
        top_n : int
            Return at most this many categories.

        Returns
        -------
        list[tuple[str, float]]
            Categories sorted by score descending.
        """
        text_lower = text.lower()
        text_words = set(re.findall(r"\w+", text_lower))
        results: List[Tuple[str, float]] = []
        for cat_name, keywords in self._categories.items():
            if not keywords:
                continue
            total_score = 0.0
            matched_count = 0
            for keyword, membership in keywords.items():
                kw_lower = keyword.lower()
                if kw_lower in text_lower:
                    total_score += membership
                    matched_count += 1
                else:
                    best_fuzzy = 0.0
                    for word in text_words:
                        fs = self._matcher.fuzzy_equal(word, kw_lower)
                        if fs > best_fuzzy:
                            best_fuzzy = fs
                    if best_fuzzy >= 0.8:
                        total_score += membership * best_fuzzy
                        matched_count += 1
            if matched_count > 0:
                normalized = total_score / len(keywords)
                results.append((cat_name, min(normalized, 1.0)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def __repr__(self) -> str:
        return f"FuzzyClassifier(categories={list(self._categories.keys())})"


# ======================================================================== #
#  FuzzyDataQuality  (fuzzy quality assessment)                            #
# ======================================================================== #

class FuzzyDataQuality:
    """Assesses data quality of scraped data using fuzzy logic.

    Instead of hard thresholds (e.g. "completeness < 0.8 = bad"), this
    class uses fuzzy sets for linguistic variables like "low completeness",
    "medium consistency", etc., producing a more nuanced quality score.
    """

    def __init__(self) -> None:
        u = np.linspace(0, 1, 101)
        self._fis = FuzzyInferenceSystem()
        self._fis.add_input_variable(
            "completeness", u,
            {
                "poor": FuzzySet("poor", triangular(0, 0, 0.4), u),
                "fair": FuzzySet("fair", triangular(0.2, 0.5, 0.7), u),
                "good": FuzzySet("good", triangular(0.5, 0.8, 1.0), u),
                "excellent": FuzzySet("excellent", triangular(0.85, 1.0, 1.0), u),
            },
        )
        self._fis.add_input_variable(
            "consistency", u,
            {
                "poor": FuzzySet("poor", triangular(0, 0, 0.4), u),
                "fair": FuzzySet("fair", triangular(0.2, 0.5, 0.7), u),
                "good": FuzzySet("good", triangular(0.5, 0.8, 1.0), u),
                "excellent": FuzzySet("excellent", triangular(0.85, 1.0, 1.0), u),
            },
        )
        self._fis.add_output_variable(
            "quality", u,
            {
                "bad": FuzzySet("bad", triangular(0, 0, 0.3), u),
                "acceptable": FuzzySet("acceptable", triangular(0.15, 0.45, 0.65), u),
                "good": FuzzySet("good", triangular(0.5, 0.75, 0.9), u),
                "excellent": FuzzySet("excellent", triangular(0.8, 1.0, 1.0), u),
            },
        )
        rules_data = [
            (["completeness", "poor"], ("quality", "bad")),
            (["completeness", "fair"], ("quality", "acceptable")),
            (["completeness", "good"], ("quality", "good")),
            (["completeness", "excellent"], ("quality", "excellent")),
            (["consistency", "poor"], ("quality", "bad")),
            (["consistency", "fair"], ("quality", "acceptable")),
            (["consistency", "good"], ("quality", "good")),
            (["consistency", "excellent"], ("quality", "excellent")),
        ]
        for ants, cons in rules_data:
            self._fis.add_rule([tuple(ants)], cons, "AND")

    def completeness_score(self, data: List[Dict[str, Any]]) -> float:
        """Compute the completeness score of a list of records.

        Completeness = fraction of non-empty fields across all records.
        """
        if not data:
            return 0.0
        total_fields = 0
        filled_fields = 0
        for record in data:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                total_fields += 1
                if value is not None and str(value).strip():
                    filled_fields += 1
        return filled_fields / total_fields if total_fields > 0 else 0.0

    def consistency_score(
        self, data: List[Dict[str, Any]], rules: Optional[List[Callable]] = None
    ) -> float:
        """Compute a consistency score based on cross-field rules.

        Each rule is a callable that takes a record and returns True if consistent.
        If no rules are provided, checks that fields with the same name
        across records have consistent types.
        """
        if not data:
            return 1.0
        if rules:
            total_checks = 0
            passed = 0
            for record in data:
                for rule in rules:
                    total_checks += 1
                    try:
                        if rule(record):
                            passed += 1
                    except Exception:
                        pass
            return passed / total_checks if total_checks > 0 else 1.0
        type_map: Dict[str, set] = {}
        for record in data:
            if not isinstance(record, dict):
                continue
            for key, value in record.items():
                t = type(value).__name__
                if key not in type_map:
                    type_map[key] = set()
                type_map[key].add(t)
        if not type_map:
            return 1.0
        consistent_keys = sum(1 for types in type_map.values() if len(types) <= 1)
        return consistent_keys / len(type_map)

    def overall_quality(
        self,
        data: List[Dict[str, Any]],
        rules: Optional[List[Callable]] = None,
    ) -> float:
        """Compute the overall fuzzy quality score for a dataset.

        Combines completeness and consistency through a fuzzy inference
        system to produce a nuanced quality score in [0, 1].
        """
        comp = self.completeness_score(data)
        cons = self.consistency_score(data, rules)
        result = self._fis.evaluate({"completeness": comp, "consistency": cons})
        return result.get("quality", 0.0)

    def __repr__(self) -> str:
        return "FuzzyDataQuality(fis_rules={})".format(len(self._fis._rules))
