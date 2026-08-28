"""
Frontier Models Module
======================
Cutting-edge efficient-frontier and portfolio-boundary models for
quantitative finance.  Built exclusively on *numpy*, *pandas*, and *scipy*
— no sklearn, torch, statsmodels, or qiskit dependencies.

This module provides production-grade implementations of advanced frontier
analysis techniques used in commercial portfolio management and risk
analytics for desktop web-scraping applications.

Classes
--------
    EfficientFrontier        — Full mean-variance efficient frontier with CML/SML
    ResampledFrontier        — Michaud resampled (bootstrap) efficient frontier
    RiskParityOptimizer      — Equal risk contribution (ERC) portfolio
    KellyCriterion           — Kelly / fractional-Kelly bet sizing
    CVaROptimizer            — Conditional Value-at-Risk minimisation
    DrawdownConstrainedOpt   — Maximum drawdown constrained frontier
    HierarchicalRiskParity   — HRP via linkage clustering
    MeanCVaRFrontier         — Mean-CVaR efficient frontier
    RegimeSwitchingFrontier  — Regime-aware efficient frontier
    FrontierAnalytics        — Consolidated analytics & reporting

Typical Usage
-------------
    >>> from core.quant.frontier_models import EfficientFrontier
    >>> ef = EfficientFrontier()
    >>> result = ef.compute(returns_df, n_points=50)
    >>> print(result["frontier_table"].head())
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize, linprog
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
from scipy.stats import norm

__all__ = [
    "EfficientFrontier",
    "ResampledFrontier",
    "RiskParityOptimizer",
    "KellyCriterion",
    "CVaROptimizer",
    "DrawdownConstrainedOpt",
    "HierarchicalRiskParity",
    "MeanCVaRFrontier",
    "RegimeSwitchingFrontier",
    "FrontierAnalytics",
]

# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _validate_returns(returns, name="returns") -> np.ndarray:
    """Coerce *returns* to a 2-D float64 ndarray and validate shape.

    Parameters
    ----------
    returns : pd.DataFrame | pd.Series | np.ndarray
        Asset return matrix (T × N) or return vector (T,).
    name : str
        Variable name used in error messages.

    Returns
    -------
    np.ndarray of shape (T, N)

    Raises
    ------
    TypeError
        If *returns* is not an array-like type.
    ValueError
        If the array is empty, has non-finite values, or fewer than 2
        observations.
    """
    if isinstance(returns, pd.DataFrame):
        returns = returns.values
    elif isinstance(returns, pd.Series):
        returns = returns.values[:, np.newaxis]
    if not isinstance(returns, np.ndarray):
        raise TypeError(
            f"{name} must be a pandas DataFrame/Series or numpy array, "
            f"got {type(returns).__name__}"
        )
    returns = np.asarray(returns, dtype=np.float64)
    if returns.ndim == 1:
        returns = returns[:, np.newaxis]
    if returns.size == 0:
        raise ValueError(f"{name} is empty.")
    if not np.all(np.isfinite(returns)):
        raise ValueError(f"{name} contains non-finite values (NaN / Inf).")
    if returns.shape[0] < 3:
        raise ValueError(
            f"{name} requires at least 3 observations; got {returns.shape[0]}."
        )
    return returns


def _portfolio_return(w: np.ndarray, mu: np.ndarray) -> float:
    return float(w @ mu)


def _portfolio_vol(w: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(w @ cov @ w))


def _portfolio_sharpe(w: np.ndarray, mu: np.ndarray, cov: np.ndarray,
                      rf: float = 0.0) -> float:
    vol = _portfolio_vol(w, cov)
    if vol < 1e-14:
        return 0.0
    return (_portfolio_return(w, mu) - rf) / vol


def _min_var_weights(mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Analytical minimum-variance weights (long/short, fully invested)."""
    n = len(mu)
    ones = np.ones(n)
    inv_cov = np.linalg.inv(cov)
    w = inv_cov @ ones / (ones @ inv_cov @ ones)
    return w


def _max_sharpe_weights(mu: np.ndarray, cov: np.ndarray,
                        rf: float = 0.0) -> np.ndarray:
    """Analytical tangency portfolio weights (unconstrained long/short)."""
    n = len(mu)
    excess = mu - rf
    inv_cov = np.linalg.inv(cov)
    w = inv_cov @ excess
    denom = np.ones(n) @ w
    if abs(denom) < 1e-14:
        return _min_var_weights(mu, cov)
    return w / denom


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EFFICIENT FRONTIER (CML / SML)
# ═══════════════════════════════════════════════════════════════════════════════

class EfficientFrontier:
    """Full mean-variance efficient frontier with Capital Market Line and
    Security Market Line.

    Generates the parabolic efficient frontier in (σ, μ) space, identifies
    the tangency (maximum-Sharpe) and minimum-variance portfolios, and
    optionally overlays the Capital Market Line (CML) and Security Market
    Line (SML).

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate (default 0.02).
    long_only : bool
        If True, enforce non-negative weight constraints (default True).
    """

    def __init__(self, risk_free_rate: float = 0.02, long_only: bool = True):
        self.risk_free_rate = float(risk_free_rate)
        self.long_only = bool(long_only)
        self._frontier = None
        self._mu = None
        self._cov = None
        self._assets = None

    # ------------------------------------------------------------------ public
    def compute(self, returns, n_points: int = 50, include_cml: bool = True,
                include_sml: bool = True):
        """Compute the efficient frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.  If a DataFrame, column names are
            preserved as asset labels.
        n_points : int
            Number of frontier points to generate (default 50).
        include_cml : bool
            Whether to compute the Capital Market Line (default True).
        include_sml : bool
            Whether to compute the Security Market Line (default True).

        Returns
        -------
        dict
            ``frontier_table`` : pd.DataFrame  — σ, μ, Sharpe, weights per point
            ``min_var``        : dict          — min-variance portfolio summary
            ``tangency``       : dict          — max-Sharpe portfolio summary
            ``cml``            : dict | None   — CML data (slope, intercept, points)
            ``sml``            : pd.DataFrame | None — per-asset SML data
            ``assets``         : list[str]     — asset names
        """
        returns = _validate_returns(returns)
        if isinstance(returns, (pd.DataFrame,)):
            self._assets = list(returns.columns)
            returns = returns.values
        else:
            self._assets = [f"A{i}" for i in range(returns.shape[1])]

        T, N = returns.shape
        self._mu = returns.mean(axis=0) * 252          # annualised
        self._cov = np.cov(returns, rowvar=False) * 252

        # --- endpoints -------------------------------------------------
        if self.long_only:
            w_min = self._optimise_target(self._obj_var, N)
            mu_lo = _portfolio_return(w_min, self._mu)
            w_tan = self._optimise_target(self._obj_neg_sharpe, N)
            mu_hi = _portfolio_return(w_tan, self._mu)
        else:
            w_min = _min_var_weights(self._mu, self._cov)
            mu_lo = _portfolio_return(w_min, self._mu)
            w_tan = _max_sharpe_weights(self._mu, self._cov, self.risk_free_rate)
            mu_hi = _portfolio_return(w_tan, self._mu)

        # Ensure range is positive
        if mu_hi - mu_lo < 1e-10:
            mu_hi = mu_lo + 1e-4

        target_mus = np.linspace(mu_lo, mu_hi, n_points)
        rows = []
        for tmu in target_mus:
            if self.long_only:
                w = self._optimise_target(self._obj_var, N,
                                          target_return=tmu)
            else:
                w = self._analytical_frontier_point(tmu)
            mu_p = _portfolio_return(w, self._mu)
            sig_p = _portfolio_vol(w, self._cov)
            sr_p = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            rows.append({"volatility": sig_p, "return": mu_p,
                         "sharpe": sr_p, "weights": w})

        frontier_df = pd.DataFrame(rows)

        # --- CML --------------------------------------------------------
        cml = None
        if include_cml:
            tan_ret = _portfolio_return(w_tan, self._mu)
            tan_vol = _portfolio_vol(w_tan, self._cov)
            cml_slope = (tan_ret - self.risk_free_rate) / max(tan_vol, 1e-14)
            vols = np.linspace(0, frontier_df["volatility"].max() * 1.1, n_points)
            cml = {
                "slope": cml_slope,
                "intercept": self.risk_free_rate,
                "tangency_vol": tan_vol,
                "tangency_return": tan_ret,
                "tangency_sharpe": cml_slope,
                "tangency_weights": w_tan,
                "points": pd.DataFrame({
                    "volatility": vols,
                    "return": self.risk_free_rate + cml_slope * vols,
                }),
            }

        # --- SML --------------------------------------------------------
        sml = None
        if include_sml:
            betas = np.array([
                self._beta(returns[:, i], returns) for i in range(N)
            ])
            expected = self.risk_free_rate + betas * (
                _portfolio_return(w_tan, self._mu) - self.risk_free_rate
            )
            sml = pd.DataFrame({
                "asset": self._assets,
                "beta": betas,
                "actual_return": self._mu,
                "sml_expected_return": expected,
                "alpha": self._mu - expected,
            })

        # --- summary portfolios ------------------------------------------
        min_var_summary = {
            "weights": w_min,
            "return": _portfolio_return(w_min, self._mu),
            "volatility": _portfolio_vol(w_min, self._cov),
            "sharpe": _portfolio_sharpe(w_min, self._mu, self._cov, self.risk_free_rate),
        }
        tan_summary = {
            "weights": w_tan,
            "return": _portfolio_return(w_tan, self._mu),
            "volatility": _portfolio_vol(w_tan, self._cov),
            "sharpe": _portfolio_sharpe(w_tan, self._mu, self._cov, self.risk_free_rate),
        }

        self._frontier = {
            "frontier_table": frontier_df,
            "min_var": min_var_summary,
            "tangency": tan_summary,
            "cml": cml,
            "sml": sml,
            "assets": self._assets,
            "n_assets": N,
            "n_observations": T,
            "mu": self._mu.copy(),
            "cov": self._cov.copy(),
        }
        return self._frontier

    # --------------------------------------------------------------- helpers
    @staticmethod
    def _beta(asset_ret, market_ret):
        """Compute CAPM beta of a single asset vs. equal-weight market."""
        m = market_ret.mean(axis=1)
        cov_am = np.cov(asset_ret, m)[0, 1]
        var_m = np.var(m, ddof=1)
        return cov_am / var_m if var_m > 1e-14 else 0.0

    def _obj_var(self, w, cov):
        return w @ cov @ w

    def _obj_neg_sharpe(self, w, mu, cov):
        vol = np.sqrt(w @ cov @ w)
        if vol < 1e-14:
            return 0.0
        return -(_portfolio_return(w, mu) - self.risk_free_rate) / vol

    def _optimise_target(self, objective, n, target_return=None):
        """Run constrained optimisation with optional return target."""
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        if target_return is not None:
            constraints.append({
                "type": "eq",
                "fun": lambda w, tr=target_return: _portfolio_return(w, self._mu) - tr,
            })
        bounds = [(0.0, 1.0)] * n if self.long_only else [(-2.0, 2.0)] * n
        w0 = np.ones(n) / n
        # Compare underlying functions to avoid bound-method identity issues
        is_var = getattr(objective, '__func__', None) is EfficientFrontier._obj_var
        args = (self._cov,) if is_var else (self._mu, self._cov)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = minimize(objective, w0, args=args, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"maxiter": 1000, "ftol": 1e-12})
        return res.x if res.success else w0

    def _analytical_frontier_point(self, target_mu):
        """Analytical (unconstrained) frontier portfolio for a target return."""
        n = len(self._mu)
        ones = np.ones(n)
        inv_cov = np.linalg.inv(self._cov)
        a = self._mu @ inv_cov @ self._mu
        b = self._mu @ inv_cov @ ones
        c = ones @ inv_cov @ ones
        delta = a * c - b * b
        if abs(delta) < 1e-14:
            return np.ones(n) / n
        g = inv_cov @ ones / c
        d = inv_cov @ self._mu / b if abs(b) > 1e-14 else np.zeros(n)
        lam = (c * target_mu - b) / delta
        w = g + lam * (d - g)
        return w


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RESAMPLED FRONTIER (MICHAUD)
# ═══════════════════════════════════════════════════════════════════════════════

class ResampledFrontier:
    """Michaud resampled efficient frontier via bootstrap.

    Generates many bootstrap resamples of the return matrix, computes
    the efficient frontier for each, and averages the weight vectors at
    each target-return level.  This produces statistically more robust
    portfolios that are less sensitive to estimation error.

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate (default 0.02).
    n_bootstrap : int
        Number of bootstrap resamples (default 500).
    long_only : bool
        Enforce non-negative weights (default True).
    seed : int | None
        Random seed for reproducibility.
    """

    def __init__(self, risk_free_rate: float = 0.02, n_bootstrap: int = 500,
                 long_only: bool = True, seed: int | None = None):
        self.risk_free_rate = float(risk_free_rate)
        self.n_bootstrap = int(n_bootstrap)
        self.long_only = bool(long_only)
        self._rng = np.random.default_rng(seed)

    def compute(self, returns, n_points: int = 50):
        """Compute the resampled efficient frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        n_points : int
            Number of frontier points (default 50).

        Returns
        -------
        dict
            ``avg_frontier``  : pd.DataFrame — averaged frontier points
            ``weight_stds``   : pd.DataFrame — weight uncertainty per point
            ``all_frontiers``  : list[pd.DataFrame] — raw bootstrap frontiers
            ``conf_intervals`` : pd.DataFrame — 95 % confidence bands
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]

        T, N = returns.shape
        mu_full = returns.mean(axis=0) * 252
        cov_full = np.cov(returns, rowvar=False) * 252

        # Determine return range from classical frontier
        ef = EfficientFrontier(self.risk_free_rate, self.long_only)
        classical = ef.compute(returns if returns.ndim == 2 else pd.DataFrame(returns, columns=asset_names),
                               n_points=n_points, include_cml=False, include_sml=False)
        mu_min = classical["min_var"]["return"]
        mu_max = classical["tangency"]["return"]
        if mu_max - mu_min < 1e-10:
            mu_max = mu_min + 1e-4
        target_mus = np.linspace(mu_min, mu_max, n_points)

        # Collect weight matrices  (n_bootstrap × n_points × N)
        all_weights = np.zeros((self.n_bootstrap, n_points, N))

        for b in range(self.n_bootstrap):
            idx = self._rng.choice(T, size=T, replace=True)
            sample = returns[idx]
            mu_b = sample.mean(axis=0) * 252
            cov_b = np.cov(sample, rowvar=False) * 252
            # Regularise small eigenvalues
            eigvals, eigvecs = np.linalg.eigh(cov_b)
            eigvals = np.maximum(eigvals, 1e-10)
            cov_b = eigvecs @ np.diag(eigvals) @ eigvecs.T

            for j, tmu in enumerate(target_mus):
                try:
                    w = self._frontier_weight(mu_b, cov_b, tmu, N)
                except Exception:
                    w = np.ones(N) / N
                all_weights[b, j, :] = w

        # Average weights per target return
        avg_weights = all_weights.mean(axis=0)          # (n_points, N)
        std_weights = all_weights.std(axis=0)

        # Build averaged frontier table
        rows = []
        for j in range(n_points):
            w = avg_weights[j]
            mu_p = _portfolio_return(w, mu_full)
            sig_p = _portfolio_vol(w, cov_full)
            sr_p = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            rows.append({"volatility": sig_p, "return": mu_p, "sharpe": sr_p})
        avg_df = pd.DataFrame(rows)

        # Weight standard deviations table
        ws_rows = []
        for j in range(n_points):
            row = {"frontier_point": j}
            for k, name in enumerate(asset_names):
                row[name] = std_weights[j, k]
            ws_rows.append(row)
        std_df = pd.DataFrame(ws_rows)

        # 95 % confidence intervals
        lo = avg_weights - 1.96 * std_weights
        hi = avg_weights + 1.96 * std_weights
        ci_rows = []
        for j in range(n_points):
            row = {"frontier_point": j}
            for k, name in enumerate(asset_names):
                row[f"{name}_lo"] = lo[j, k]
                row[f"{name}_hi"] = hi[j, k]
            ci_rows.append(row)
        ci_df = pd.DataFrame(ci_rows)

        return {
            "avg_frontier": avg_df,
            "weight_stds": std_df,
            "conf_intervals": ci_df,
            "avg_weights": avg_weights,
            "assets": asset_names,
            "n_bootstrap": self.n_bootstrap,
        }

    def _frontier_weight(self, mu, cov, target_mu, n):
        """Return weights for one frontier point (long-only or unconstrained)."""
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        constraints.append({
            "type": "eq",
            "fun": lambda w, tr=target_mu: _portfolio_return(w, mu) - tr,
        })
        bounds = [(0.0, 1.0)] * n if self.long_only else [(-2.0, 2.0)] * n
        w0 = np.ones(n) / n
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = minimize(lambda w: w @ cov @ w, w0, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"maxiter": 500, "ftol": 1e-12})
        return res.x if res.success else w0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RISK PARITY OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════

class RiskParityOptimizer:
    r"""Equal Risk Contribution (ERC) / Risk Parity portfolio.

    Each asset contributes equally to total portfolio volatility.  The
    objective minimises:

    $$\sum_{i<j} \left( w_i (\Sigma w)_i - w_j (\Sigma w)_j \right)^2$$

    Optionally supports a *budget* vector to specify unequal risk targets.

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate.
    risk_budget : np.ndarray | None
        Per-asset risk budget (default equal weights 1/N).
    """

    def __init__(self, risk_free_rate: float = 0.02,
                 risk_budget: np.ndarray | None = None):
        self.risk_free_rate = float(risk_free_rate)
        self._budget = risk_budget

    def compute(self, returns):
        """Compute the risk-parity portfolio.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.

        Returns
        -------
        dict
            ``weights``            : np.ndarray  — ERC weights
            "risk_contributions"  : np.ndarray  — marginal risk contribution
            "pct_contributions"   : np.ndarray  — percentage risk contribution
            "portfolio_return"    : float
            "portfolio_volatility": float
            "sharpe_ratio"        : float
            "assets"              : list[str]
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
        T, N = returns.shape
        mu = returns.mean(axis=0) * 252
        cov = np.cov(returns, rowvar=False) * 252

        budget = self._budget
        if budget is None:
            budget = np.ones(N) / N
        else:
            budget = np.asarray(budget, dtype=np.float64)
            budget /= budget.sum()

        w0 = np.ones(N) / N
        bounds = [(1e-6, 1.0)] * N
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = minimize(
                self._erc_objective, w0, args=(cov, budget),
                method="SLSQP", bounds=bounds, constraints=constraints,
                options={"maxiter": 2000, "ftol": 1e-14},
            )

        w = res.x if res.success else w0
        w = np.maximum(w, 0.0)
        w /= w.sum()

        sigma_p = _portfolio_vol(w, cov)
        marginal = cov @ w
        risk_contrib = w * marginal
        pct_contrib = risk_contrib / (w @ cov @ w)

        return {
            "weights": w,
            "risk_contributions": risk_contrib,
            "pct_contributions": pct_contrib,
            "portfolio_return": _portfolio_return(w, mu),
            "portfolio_volatility": sigma_p,
            "sharpe_ratio": _portfolio_sharpe(w, mu, cov, self.risk_free_rate),
            "assets": asset_names,
        }

    @staticmethod
    def _erc_objective(w, cov, budget):
        """Sum of squared deviations of risk contributions from budget."""
        sigma_w = np.sqrt(w @ cov @ w)
        if sigma_w < 1e-14:
            return 1e10
        marginal = cov @ w
        rc = w * marginal / sigma_w
        target = budget * sigma_w
        return np.sum((rc - target) ** 2)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. KELLY CRITERION
# ═══════════════════════════════════════════════════════════════════════════════

class KellyCriterion:
    r"""Kelly / fractional-Kelly optimal position sizing.

    For a set of assets with known mean returns and covariance, the
    (full) Kelly portfolio maximises the expected log-utility:

    $$w^{*} = \Sigma^{-1} \mu$$

    Fractional Kelly scales this by *f* ∈ (0, 1] for practical
    risk management.  When ``use_empirical=True`` the mean and
    covariance are estimated from historical returns.

    Parameters
    ----------
    fraction : float
        Kelly fraction in (0, 1].  Use 0.5 for half-Kelly (default 0.5).
    risk_free_rate : float
        Annualised risk-free rate.
    """

    def __init__(self, fraction: float = 0.5, risk_free_rate: float = 0.02):
        if not 0.0 < fraction <= 1.0:
            raise ValueError("fraction must be in (0, 1].")
        self.fraction = float(fraction)
        self.risk_free_rate = float(risk_free_rate)

    def compute(self, returns):
        """Compute the (fractional) Kelly portfolio.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.

        Returns
        -------
        dict
            ``kelly_weights``        : np.ndarray — full Kelly weights
            ``fractional_weights``   : np.ndarray — scaled weights
            "expected_growth"       : float     — E[log(1+r_p)]
            "geometric_return"      : float     — annualised geometric
            "arithmetic_return"     : float
            "volatility"            : float
            "sharpe_ratio"          : float
            ``full_kelly_leverage``  : float     — sum of full Kelly weights
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
        T, N = returns.shape
        mu = returns.mean(axis=0)  # per-period
        cov = np.cov(returns, rowvar=False)

        # Kelly weights: w = Sigma^{-1} mu
        try:
            inv_cov = np.linalg.inv(cov)
            w_kelly = inv_cov @ mu
        except np.linalg.LinAlgError:
            # Fall back to pseudo-inverse
            inv_cov = np.linalg.pinv(cov)
            w_kelly = inv_cov @ mu

        leverage = float(np.sum(np.abs(w_kelly)))
        w_frac = w_kelly * self.fraction

        # Expected growth rate  E[log(1 + w'r)] ≈ w'μ - 0.5 w'Σw  (2nd-order)
        eg_full = float(w_kelly @ mu - 0.5 * w_kelly @ cov @ w_kelly)
        eg_frac = float(w_frac @ mu - 0.5 * w_frac @ cov @ w_frac)

        # Annualise
        ann_mu = mu * 252
        ann_cov = cov * 252
        arith_ret = float(w_frac @ ann_mu)
        vol = _portfolio_vol(w_frac, ann_cov)
        geo_ret = arith_ret - 0.5 * vol ** 2  # approx
        sr = (arith_ret - self.risk_free_rate) / max(vol, 1e-14)

        return {
            "kelly_weights": w_kelly,
            "fractional_weights": w_frac,
            "expected_growth": eg_frac,
            "geometric_return": geo_ret,
            "arithmetic_return": arith_ret,
            "volatility": vol,
            "sharpe_ratio": sr,
            "full_kelly_leverage": leverage,
            "assets": asset_names,
            "fraction": self.fraction,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CVaR OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════════

class CVaROptimizer:
    r"""Conditional Value-at-Risk (CVaR / Expected Shortfall) minimisation.

    Uses the Rockafellar-Uryasev linearisation: CVaR_α is the expected
    loss beyond the α-quantile VaR.  Solved via linear programming.

    For a target return, the optimiser finds the minimum-CVaR portfolio.
    A full frontier can be generated by sweeping target returns.

    Parameters
    ----------
    alpha : float
        CVaR confidence level in (0.5, 1) (default 0.95).
    risk_free_rate : float
        Annualised risk-free rate.
    long_only : bool
        Enforce non-negative weights (default True).
    """

    def __init__(self, alpha: float = 0.95, risk_free_rate: float = 0.02,
                 long_only: bool = True):
        if not 0.5 < alpha < 1.0:
            raise ValueError("alpha must be in (0.5, 1).")
        self.alpha = float(alpha)
        self.risk_free_rate = float(risk_free_rate)
        self.long_only = bool(long_only)

    def compute(self, returns, n_points: int = 30):
        """Compute the mean-CVaR efficient frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix (per-period, e.g. daily).
        n_points : int
            Number of frontier points (default 30).

        Returns
        -------
        dict
            ``frontier_table`` : pd.DataFrame — σ, μ, CVaR, Sharpe per point
            ``min_cvar``      : dict — minimum-CVaR portfolio
            ``best_sharpe``   : dict — best Sharpe on mean-CVaR frontier
            ``alpha``          : float
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
        T, N = returns.shape
        mu = returns.mean(axis=0) * 252

        # Min-CVaR portfolio (no return target)
        w_min, var_min = self._lp_cvar(returns, N, target_return=None)
        mu_min = _portfolio_return(w_min, mu)

        # Max-return portfolio (long-only)
        if self.long_only:
            mu_max = mu.max()
        else:
            mu_max = mu.max() * 1.5

        if mu_max - mu_min < 1e-10:
            mu_max = mu_min + 1e-4

        target_mus = np.linspace(mu_min, mu_max, n_points)
        rows = []
        for tmu in target_mus:
            try:
                w, cvar_val = self._lp_cvar(returns, N, target_return=tmu)
            except Exception:
                w = np.ones(N) / N
                cvar_val = self._cvar_from_weights(returns, w)
            mu_p = _portfolio_return(w, mu)
            cov_ann = np.cov(returns, rowvar=False) * 252
            sig_p = _portfolio_vol(w, cov_ann)
            sr_p = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            rows.append({
                "volatility": sig_p, "return": mu_p,
                "cvar": cvar_val, "sharpe": sr_p, "weights": w,
            })

        frontier_df = pd.DataFrame(rows)

        # Best Sharpe
        best_idx = frontier_df["sharpe"].idxmax()
        best_row = frontier_df.iloc[best_idx]

        return {
            "frontier_table": frontier_df,
            "min_cvar": {
                "weights": w_min,
                "return": mu_min,
                "cvar": var_min,
            },
            "best_sharpe": {
                "weights": best_row["weights"]
                if "weights" in best_row.index else np.ones(N) / N,
                "return": best_row["return"],
                "volatility": best_row["volatility"],
                "sharpe": best_row["sharpe"],
                "cvar": best_row["cvar"],
            },
            "alpha": self.alpha,
            "assets": asset_names,
        }

    def _lp_cvar(self, returns, n, target_return=None):
        """Solve CVaR minimisation via linear programming (Rockafellar-Uryasev)."""
        T = returns.shape[0]
        # Decision variables: [w_1..w_n, VaR, z_1..z_T]
        # min  VaR + 1/(T*(1-alpha)) * sum(z_t)
        # s.t. z_t >= -r_t'w - VaR,  z_t >= 0,  sum(w) = 1
        n_vars = n + 1 + T
        c = np.zeros(n_vars)
        c[n] = 1.0                           # VaR coefficient
        c[n + 1:] = 1.0 / (T * (1.0 - self.alpha))  # z coefficients

        # Inequality: z_t + r_t'w + VaR >= 0  =>  -r_t'w - VaR - z_t <= 0
        A_ub = np.zeros((T, n_vars))
        b_ub = np.zeros(T)
        for t in range(T):
            A_ub[t, :n] = -returns[t, :]   # -r_t'w
            A_ub[t, n] = -1.0              # -VaR
            A_ub[t, n + 1 + t] = -1.0     # -z_t

        # Equality: sum(w) = 1
        A_eq = np.zeros((1, n_vars))
        A_eq[0, :n] = 1.0
        b_eq = np.array([1.0])

        # Optional return target: mu'w >= target  =>  -mu'w <= -target
        if target_return is not None:
            mu_period = returns.mean(axis=0) * 252
            A_ub = np.vstack([A_ub, -mu_period.reshape(1, -1).dot(
                np.eye(n, n_vars))])
            # Pad to n_vars columns
            row = np.zeros(n_vars)
            row[:n] = -mu_period
            A_ub = np.vstack([A_ub, row.reshape(1, -1)])
            b_ub = np.append(b_ub, -target_return)
            # Remove the duplicate row we accidentally added
            A_ub = A_ub[:-2]
            b_ub = b_ub[:-2]
            # Redo properly
            row = np.zeros(n_vars)
            row[:n] = -mu_period
            A_ub = np.vstack([A_ub[:-T if False else T], row.reshape(1, -1)])
            # Simpler: just re-stack
            pass

        # Bounds
        if self.long_only:
            bounds = [(0.0, None)] * n + [(None, None)] + [(0.0, None)] * T
        else:
            bounds = [(None, None)] * n + [(None, None)] + [(0.0, None)] * T

        # Build properly with optional target
        A_ub_final = np.zeros((T, n_vars))
        b_ub_final = np.zeros(T)
        for t in range(T):
            A_ub_final[t, :n] = -returns[t, :]
            A_ub_final[t, n] = -1.0
            A_ub_final[t, n + 1 + t] = -1.0

        if target_return is not None:
            mu_period = returns.mean(axis=0) * 252
            row_ret = np.zeros(n_vars)
            row_ret[:n] = -mu_period
            A_ub_final = np.vstack([A_ub_final, row_ret.reshape(1, -1)])
            b_ub_final = np.append(b_ub_final, -target_return)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = linprog(c, A_ub=A_ub_final, b_ub=b_ub_final,
                          A_eq=A_eq, b_eq=b_eq, bounds=bounds,
                          method="highs", options={"maxiter": 5000})

        if res.success:
            w = res.x[:n]
            var_val = res.x[n]
            cvar_val = var_val + res.x[n + 1:].sum() / (T * (1.0 - self.alpha))
            return w, cvar_val
        else:
            # Fallback: equal weight
            w = np.ones(n) / n
            cvar_val = self._cvar_from_weights(returns, w)
            return w, cvar_val

    def _cvar_from_weights(self, returns, w):
        """Empirical CVaR from portfolio returns."""
        port_ret = returns @ w
        q = np.quantile(port_ret, 1.0 - self.alpha)
        tail = port_ret[port_ret <= q]
        return -tail.mean() if len(tail) > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DRAWDOWN-CONSTRAINED OPTIMISER
# ═══════════════════════════════════════════════════════════════════════════════

class DrawdownConstrainedOpt:
    """Efficient frontier with maximum-drawdown constraint.

    Optimises portfolio weights subject to the constraint that the
    maximum drawdown of the resulting equity curve does not exceed a
    specified threshold.  Uses SLSQP with a smooth drawdown approximation.

    Parameters
    ----------
    max_drawdown : float
        Maximum allowable drawdown as a fraction, e.g. 0.20 for 20 %
        (default 0.20).
    risk_free_rate : float
        Annualised risk-free rate.
    long_only : bool
        Enforce non-negative weights (default True).
    """

    def __init__(self, max_drawdown: float = 0.20, risk_free_rate: float = 0.02,
                 long_only: bool = True):
        if not 0.0 < max_drawdown < 1.0:
            raise ValueError("max_drawdown must be in (0, 1).")
        self.max_dd = float(max_drawdown)
        self.risk_free_rate = float(risk_free_rate)
        self.long_only = bool(long_only)

    def compute(self, returns, n_points: int = 30):
        """Compute drawdown-constrained efficient frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        n_points : int
            Number of frontier points (default 30).

        Returns
        -------
        dict
            ``frontier_table`` : pd.DataFrame
            ``best_sharpe``   : dict
            ``unconstrained_frontier`` : pd.DataFrame — for comparison
            ``max_drawdown_limit``     : float
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
        T, N = returns.shape
        mu = returns.mean(axis=0) * 252
        cov = np.cov(returns, rowvar=False) * 252

        # Unconstrained min-var and tangency for range
        ef = EfficientFrontier(self.risk_free_rate, self.long_only)
        unc = ef.compute(returns if isinstance(returns, np.ndarray)
                         else pd.DataFrame(returns, columns=asset_names),
                         n_points=n_points, include_cml=False, include_sml=False)
        mu_lo = unc["min_var"]["return"]
        mu_hi = unc["tangency"]["return"]
        if mu_hi - mu_lo < 1e-10:
            mu_hi = mu_lo + 1e-4
        target_mus = np.linspace(mu_lo, mu_hi, n_points)

        rows = []
        for tmu in target_mus:
            w = self._optimise_dd_constrained(returns, mu, cov, tmu, N)
            mu_p = _portfolio_return(w, mu)
            sig_p = _portfolio_vol(w, cov)
            dd = self._max_drawdown(returns, w)
            sr = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            rows.append({
                "volatility": sig_p, "return": mu_p,
                "max_drawdown": dd, "sharpe": sr, "weights": w,
            })
        frontier_df = pd.DataFrame(rows)

        best_idx = frontier_df["sharpe"].idxmax()
        best_row = frontier_df.iloc[best_idx]

        return {
            "frontier_table": frontier_df,
            "best_sharpe": {
                "weights": best_row["weights"],
                "return": best_row["return"],
                "volatility": best_row["volatility"],
                "max_drawdown": best_row["max_drawdown"],
                "sharpe": best_row["sharpe"],
            },
            "unconstrained_frontier": unc["frontier_table"],
            "max_drawdown_limit": self.max_dd,
            "assets": asset_names,
        }

    def _optimise_dd_constrained(self, returns, mu, cov, target_mu, n):
        """Minimise variance subject to return target and max-DD constraint."""
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq",
             "fun": lambda w, tr=target_mu: _portfolio_return(w, mu) - tr},
            {"type": "ineq",
             "fun": lambda w: self.max_dd - self._max_drawdown(returns, w)},
        ]
        bounds = [(0.0, 1.0)] * n if self.long_only else [(-2.0, 2.0)] * n
        w0 = np.ones(n) / n
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = minimize(lambda w: w @ cov @ w, w0, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"maxiter": 1000, "ftol": 1e-12})
        return res.x if res.success else w0

    @staticmethod
    def _max_drawdown(returns, w):
        """Compute maximum drawdown of the weighted portfolio equity curve."""
        port_ret = returns @ w
        cumulative = np.cumprod(1.0 + port_ret)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / peak
        return float(drawdown.max())


# ═══════════════════════════════════════════════════════════════════════════════
# 7. HIERARCHICAL RISK PARITY (HRP)
# ═══════════════════════════════════════════════════════════════════════════════

class HierarchicalRiskParity:
    """Hierarchical Risk Parity (de Prado, 2016).

    Uses agglomerative clustering on the correlation matrix to build a
    dendrogram, then recursively allocates capital based on inverse-
    variance weighting within each cluster.  Produces more stable and
    diversified portfolios than traditional mean-variance.

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate.
    linkage_method : str
        Scipy linkage method (default ``"single"`` — use ``"average"`` or
        ``"ward"`` for different behaviours).
    """

    def __init__(self, risk_free_rate: float = 0.02,
                 linkage_method: str = "single"):
        self.risk_free_rate = float(risk_free_rate)
        self.linkage_method = str(linkage_method)

    def compute(self, returns):
        """Compute the HRP portfolio.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.

        Returns
        -------
        dict
            ``weights``            : np.ndarray
            ``linkage_matrix``     : np.ndarray
            ``seriation_order``    : list[int]
            "portfolio_return"    : float
            "portfolio_volatility": float
            "sharpe_ratio"        : float
            "cluster_variances"   : dict — per-cluster variance allocation
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
        T, N = returns.shape
        mu = returns.mean(axis=0) * 252
        cov = np.cov(returns, rowvar=False) * 252
        corr = np.corrcoef(returns, rowvar=False)

        # Distance matrix from correlation
        dist = np.sqrt(np.clip(2.0 * (1.0 - corr), 0.0, None))
        np.fill_diagonal(dist, 0.0)
        condensed = squareform(dist, checks=False)

        # Hierarchical clustering
        link = linkage(condensed, method=self.linkage_method)
        seriation = list(leaves_list(link))

        # Quasi-diagonalise covariance
        cov_qd = cov[np.ix_(seriation, seriation)]

        # Recursive bisection
        weights = self._recursive_bisection(cov_qd, list(range(N)))

        # Map back to original order
        w_original = np.zeros(N)
        for i, idx in enumerate(seriation):
            w_original[idx] = weights[i]

        ret_p = _portfolio_return(w_original, mu)
        vol_p = _portfolio_vol(w_original, cov)
        sr = (ret_p - self.risk_free_rate) / max(vol_p, 1e-14)

        return {
            "weights": w_original,
            "linkage_matrix": link,
            "seriation_order": seriation,
            "portfolio_return": ret_p,
            "portfolio_volatility": vol_p,
            "sharpe_ratio": sr,
            "cluster_variances": self._cluster_vars(cov_qd, list(range(N))),
            "assets": asset_names,
        }

    def _recursive_bisection(self, cov, indices):
        """Recursively split indices and allocate inverse-variance weights."""
        w = np.ones(len(indices))
        if len(indices) <= 1:
            return w
        # Split at midpoint
        mid = len(indices) // 2
        left = indices[:mid]
        right = indices[mid:]
        # Cluster variances
        cov_left = cov[np.ix_(left, left)]
        cov_right = cov[np.ix_(right, right)]
        v_left = self._cluster_var(cov_left)
        v_right = self._cluster_var(cov_right)
        alpha = 1.0 - v_left / (v_left + v_right)
        # Recurse
        w_left = self._recursive_bisection(cov, left)
        w_right = self._recursive_bisection(cov, right)
        w[:mid] = alpha * w_left
        w[mid:] = (1.0 - alpha) * w_right
        return w

    @staticmethod
    def _cluster_var(cov):
        """Variance of inverse-variance weighted cluster."""
        ivp = 1.0 / np.diag(cov)
        ivp /= ivp.sum()
        return float(ivp @ cov @ ivp)

    def _cluster_vars(self, cov, indices, depth=0):
        """Record variance at each cluster level."""
        result = {}
        key = f"level_{depth}"
        result[key] = self._cluster_var(cov)
        if len(indices) > 1:
            mid = len(indices) // 2
            left = indices[:mid]
            right = indices[mid:]
            cov_left = cov[np.ix_(left, left)]
            cov_right = cov[np.ix_(right, right)]
            # Use local (relative) indices for sub-matrices
            result.update(self._cluster_vars(cov_left, list(range(len(left))), depth + 1))
            result.update(self._cluster_vars(cov_right, list(range(len(right))), depth + 1))
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# 8. MEAN-CVaR FRONTIER (Enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

class MeanCVaRFrontier:
    r"""Mean-CVaR efficient frontier using scenario-based optimisation.

    Unlike ``CVaROptimizer`` (which uses LP), this class also supports
    parametric (Gaussian) CVaR and provides scenario-generation via
    Gaussian copula for more robust out-of-sample performance.

    Parameters
    ----------
    alpha : float
        CVaR confidence level (default 0.95).
    risk_free_rate : float
        Annualised risk-free rate.
    n_scenarios : int
        Number of Monte-Carlo scenarios for enhanced estimation (default 10000).
    seed : int | None
        Random seed.
    """

    def __init__(self, alpha: float = 0.95, risk_free_rate: float = 0.02,
                 n_scenarios: int = 10000, seed: int | None = None):
        if not 0.5 < alpha < 1.0:
            raise ValueError("alpha must be in (0.5, 1).")
        self.alpha = float(alpha)
        self.risk_free_rate = float(risk_free_rate)
        self.n_scenarios = int(n_scenarios)
        self._rng = np.random.default_rng(seed)

    def compute(self, returns, n_points: int = 30, method: str = "scenario"):
        """Compute mean-CVaR frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        n_points : int
            Number of frontier points.
        method : str
            ``"scenario"``  — use historical scenarios (default)
            ``"parametric"`` — use Gaussian parametric CVaR
            ``"copula"`` — Gaussian copula scenarios

        Returns
        -------
        dict
            ``frontier_table`` : pd.DataFrame
            ``min_cvar``      : dict
            ``method"          : str
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns_arr = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
            returns_arr = returns
        T, N = returns_arr.shape
        mu = returns_arr.mean(axis=0) * 252
        cov = np.cov(returns_arr, rowvar=False) * 252

        # Generate scenarios
        if method == "copula":
            scenarios = self._copula_scenarios(returns_arr, N)
        elif method == "parametric":
            scenarios = self._parametric_scenarios(returns_arr, N)
        else:
            scenarios = returns_arr

        # Min CVaR
        cvar_opt = CVaROptimizer(self.alpha, self.risk_free_rate)
        base = cvar_opt.compute(returns, n_points=2)
        mu_min = base["min_cvar"]["return"]
        mu_max = mu.max() if True else base["frontier_table"]["return"].max()
        if mu_max - mu_min < 1e-10:
            mu_max = mu_min + 1e-4

        target_mus = np.linspace(mu_min, mu_max, n_points)
        rows = []
        for tmu in target_mus:
            w = self._min_cvar_slsqp(scenarios, mu, cov, tmu, N)
            mu_p = _portfolio_return(w, mu)
            sig_p = _portfolio_vol(w, cov)
            cvar_p = self._empirical_cvar(scenarios, w)
            sr = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            rows.append({
                "volatility": sig_p, "return": mu_p,
                "cvar": cvar_p, "sharpe": sr, "weights": w,
            })
        frontier_df = pd.DataFrame(rows)

        return {
            "frontier_table": frontier_df,
            "min_cvar": {
                "weights": frontier_df.iloc[0]["weights"] if len(frontier_df) > 0 else np.ones(N) / N,
                "return": frontier_df.iloc[0]["return"] if len(frontier_df) > 0 else 0.0,
                "cvar": frontier_df.iloc[0]["cvar"] if len(frontier_df) > 0 else 0.0,
            },
            "method": method,
            "alpha": self.alpha,
            "assets": asset_names,
            "n_scenarios": scenarios.shape[0],
        }

    def _min_cvar_slsqp(self, scenarios, mu, cov, target_mu, n):
        """Minimise empirical CVaR with return constraint via SLSQP."""
        def obj(w):
            return self._empirical_cvar(scenarios, w)
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq",
             "fun": lambda w, tr=target_mu: _portfolio_return(w, mu) - tr},
        ]
        bounds = [(0.0, 1.0)] * n
        w0 = np.ones(n) / n
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = minimize(obj, w0, method="SLSQP", bounds=bounds,
                           constraints=constraints,
                           options={"maxiter": 1000, "ftol": 1e-12})
        return res.x if res.success else w0

    def _empirical_cvar(self, scenarios, w):
        """Empirical CVaR from scenario losses."""
        port_ret = scenarios @ w
        q = np.quantile(port_ret, 1.0 - self.alpha)
        tail = port_ret[port_ret <= q]
        return -tail.mean() if len(tail) > 0 else 0.0

    def _parametric_scenarios(self, returns, n):
        """Generate Gaussian scenarios from estimated params."""
        mu = returns.mean(axis=0)
        cov = np.cov(returns, rowvar=False)
        return self._rng.multivariate_normal(mu, cov, size=self.n_scenarios)

    def _copula_scenarios(self, returns, n):
        """Gaussian copula scenarios preserving marginal distributions."""
        T = returns.shape[0]
        # Rank-transform to uniform, then to normal (Gaussian copula)
        from scipy.stats import rankdata, norm as sp_norm
        ranks = np.apply_along_axis(rankdata, 0, returns) / (T + 1)
        normal_scores = sp_norm.ppf(ranks)
        corr = np.corrcoef(normal_scores, rowvar=False)
        # Generate normal scenarios
        z = self._rng.multivariate_normal(np.zeros(n), corr, size=self.n_scenarios)
        # Map back via empirical quantiles
        scenarios = np.zeros_like(z)
        for j in range(n):
            sorted_ret = np.sort(returns[:, j])
            ecdf_probs = np.linspace(0, 1, T + 2)[1:-1]
            scenarios[:, j] = np.interp(sp_norm.cdf(z[:, j]), ecdf_probs, sorted_ret)
        return scenarios


# ═══════════════════════════════════════════════════════════════════════════════
# 9. REGIME-SWITCHING FRONTIER
# ═══════════════════════════════════════════════════════════════════════════════

class RegimeSwitchingFrontier:
    """Regime-aware efficient frontier using hidden-state detection.

    Detects market regimes (e.g. bull / bear / sideways) via volatility-
    based clustering of rolling windows, computes a separate efficient
    frontier for each regime, and blends them into a weighted composite
    frontier based on regime probabilities.

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate.
    n_regimes : int
        Number of regimes to detect (default 2).
    window : int
        Rolling window size for regime detection (default 60).
    long_only : bool
        Enforce non-negative weights (default True).
    """

    def __init__(self, risk_free_rate: float = 0.02, n_regimes: int = 2,
                 window: int = 60, long_only: bool = True):
        self.risk_free_rate = float(risk_free_rate)
        self.n_regimes = int(n_regimes)
        self.window = int(window)
        self.long_only = bool(long_only)

    def compute(self, returns, n_points: int = 30):
        """Compute regime-switching efficient frontier.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        n_points : int
            Frontier resolution.

        Returns
        -------
        dict
            ``composite_frontier`` : pd.DataFrame — blended frontier
            ``regime_frontiers``   : list[dict] — per-regime frontiers
            ``regime_labels"       : np.ndarray — per-observation regime
            ``regime_probs"        : np.ndarray — regime probabilities
            ``transition_summary"  : pd.DataFrame
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns_arr = returns.values
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
            returns_arr = returns
        T, N = returns_arr.shape

        # --- Regime detection via rolling volatility quantiles -----------
        if T < self.window + 1:
            raise ValueError(
                f"Need at least {self.window + 1} observations for regime "
                f"detection; got {T}."
            )
        rolling_vol = np.array([
            returns_arr[max(0, i - self.window + 1):i + 1].std()
            for i in range(T)
        ])
        # K-means-like assignment by volatility quantile boundaries
        q_bounds = np.quantile(rolling_vol, np.linspace(0, 1, self.n_regimes + 1))
        q_bounds[0] = -np.inf
        q_bounds[-1] = np.inf
        labels = np.digitize(rolling_vol, q_bounds) - 1
        labels = np.clip(labels, 0, self.n_regimes - 1)

        # --- Per-regime efficient frontiers -------------------------------
        mu_full = returns_arr.mean(axis=0) * 252
        cov_full = np.cov(returns_arr, rowvar=False) * 252
        regime_frontiers = []
        regime_probs = []
        composite_rows = []

        for r in range(self.n_regimes):
            mask = labels == r
            n_r = mask.sum()
            if n_r < 3:
                regime_frontiers.append(None)
                regime_probs.append(0.0)
                continue
            regime_probs.append(n_r / T)
            ret_r = returns_arr[mask]
            mu_r = ret_r.mean(axis=0) * 252
            cov_r = np.cov(ret_r, rowvar=False) * 252

            ef = EfficientFrontier(self.risk_free_rate, self.long_only)
            try:
                res = ef.compute(pd.DataFrame(ret_r, columns=asset_names),
                                n_points=n_points, include_cml=False, include_sml=False)
                regime_frontiers.append(res)
            except Exception:
                regime_frontiers.append(None)

        regime_probs = np.array(regime_probs)
        regime_probs /= regime_probs.sum()  # normalise

        # --- Composite frontier: blend regime frontiers ------------------
        for j in range(n_points):
            mu_blended = 0.0
            var_blended = 0.0
            w_blended = np.zeros(N)
            for r in range(self.n_regimes):
                if regime_frontiers[r] is None:
                    continue
                ft = regime_frontiers[r]["frontier_table"]
                if j >= len(ft):
                    continue
                w_r = ft.iloc[j]["weights"] if "weights" in ft.columns else np.ones(N) / N
                prob = regime_probs[r]
                w_blended += prob * w_r
            # Normalise blended weights
            if w_blended.sum() > 1e-14:
                w_blended /= w_blended.sum()
            mu_p = _portfolio_return(w_blended, mu_full)
            sig_p = _portfolio_vol(w_blended, cov_full)
            sr = (mu_p - self.risk_free_rate) / max(sig_p, 1e-14)
            composite_rows.append({
                "volatility": sig_p, "return": mu_p,
                "sharpe": sr, "weights": w_blended,
            })
        composite_df = pd.DataFrame(composite_rows)

        # --- Transition matrix (simplified) ------------------------------
        trans = np.zeros((self.n_regimes, self.n_regimes))
        for t in range(1, T):
            trans[labels[t - 1], labels[t]] += 1
        row_sums = trans.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        trans = trans / row_sums
        trans_df = pd.DataFrame(
            trans,
            index=[f"Regime_{i}" for i in range(self.n_regimes)],
            columns=[f"Regime_{i}" for i in range(self.n_regimes)],
        )

        return {
            "composite_frontier": composite_df,
            "regime_frontiers": regime_frontiers,
            "regime_labels": labels,
            "regime_probs": regime_probs,
            "transition_summary": trans_df,
            "assets": asset_names,
            "n_regimes": self.n_regimes,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 10. FRONTIER ANALYTICS (Consolidated Reporting)
# ═══════════════════════════════════════════════════════════════════════════════

class FrontierAnalytics:
    """Consolidated analytics across all frontier model types.

    Provides a unified interface to run multiple frontier analyses on the
    same return data and produce a comprehensive comparison report.

    Parameters
    ----------
    risk_free_rate : float
        Annualised risk-free rate (default 0.02).
    """

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = float(risk_free_rate)

    def full_analysis(self, returns, n_points: int = 30,
                      n_bootstrap: int = 200, kelly_fraction: float = 0.5,
                      max_drawdown: float = 0.20, cvar_alpha: float = 0.95):
        """Run all frontier analyses and return a consolidated report.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        n_points : int
            Frontier resolution.
        n_bootstrap : int
            Bootstrap resamples for ResampledFrontier.
        kelly_fraction : float
            Kelly fraction.
        max_drawdown : float
            Maximum drawdown constraint.
        cvar_alpha : float
            CVaR confidence level.

        Returns
        -------
        dict
            ``efficient_frontier"       : dict
            ``resampled_frontier"       : dict
            ``risk_parity"              : dict
            ``kelly"                    : dict
            ``cvar_frontier"            : dict
            ``drawdown_constrained"     : dict
            ``hrp"                      : dict
            ``regime_switching"         : dict
            ``comparison_table"         : pd.DataFrame
        """
        returns = _validate_returns(returns)
        if isinstance(returns, pd.DataFrame):
            asset_names = list(returns.columns)
            returns_df = returns.copy()
        else:
            asset_names = [f"A{i}" for i in range(returns.shape[1])]
            returns_df = pd.DataFrame(returns, columns=asset_names)

        results = {}

        # 1. Efficient Frontier
        try:
            ef = EfficientFrontier(self.risk_free_rate)
            results["efficient_frontier"] = ef.compute(returns_df, n_points=n_points)
        except Exception as exc:
            results["efficient_frontier"] = {"error": str(exc)}

        # 2. Resampled Frontier
        try:
            rf = ResampledFrontier(self.risk_free_rate, n_bootstrap=n_bootstrap)
            results["resampled_frontier"] = rf.compute(returns_df, n_points=n_points)
        except Exception as exc:
            results["resampled_frontier"] = {"error": str(exc)}

        # 3. Risk Parity
        try:
            rp = RiskParityOptimizer(self.risk_free_rate)
            results["risk_parity"] = rp.compute(returns_df)
        except Exception as exc:
            results["risk_parity"] = {"error": str(exc)}

        # 4. Kelly
        try:
            kc = KellyCriterion(fraction=kelly_fraction, risk_free_rate=self.risk_free_rate)
            results["kelly"] = kc.compute(returns_df)
        except Exception as exc:
            results["kelly"] = {"error": str(exc)}

        # 5. CVaR Frontier
        try:
            co = CVaROptimizer(alpha=cvar_alpha, risk_free_rate=self.risk_free_rate)
            results["cvar_frontier"] = co.compute(returns_df, n_points=n_points)
        except Exception as exc:
            results["cvar_frontier"] = {"error": str(exc)}

        # 6. Drawdown-Constrained
        try:
            dc = DrawdownConstrainedOpt(max_drawdown=max_drawdown,
                                        risk_free_rate=self.risk_free_rate)
            results["drawdown_constrained"] = dc.compute(returns_df, n_points=n_points)
        except Exception as exc:
            results["drawdown_constrained"] = {"error": str(exc)}

        # 7. HRP
        try:
            hrp = HierarchicalRiskParity(self.risk_free_rate)
            results["hrp"] = hrp.compute(returns_df)
        except Exception as exc:
            results["hrp"] = {"error": str(exc)}

        # 8. Regime-Switching
        try:
            rs = RegimeSwitchingFrontier(self.risk_free_rate)
            results["regime_switching"] = rs.compute(returns_df, n_points=n_points)
        except Exception as exc:
            results["regime_switching"] = {"error": str(exc)}

        # --- Comparison table --------------------------------------------
        comparison_rows = []
        model_names = [
            ("MV Tangency", results.get("efficient_frontier", {}).get("tangency")),
            ("MV Min-Var", results.get("efficient_frontier", {}).get("min_var")),
            ("Risk Parity", results.get("risk_parity")),
            ("HRP", results.get("hrp")),
            ("Kelly (frac)", results.get("kelly")),
            ("CVaR Min", results.get("cvar_frontier", {}).get("min_cvar")),
            ("DD-Constrained", results.get("drawdown_constrained", {}).get("best_sharpe")),
        ]
        for name, info in model_names:
            if info is None or "error" in info:
                continue
            row = {"model": name}
            # Normalise heterogeneous key names across models
            ret_key = next((k for k in ("return", "portfolio_return", "arithmetic_return") if k in info), None)
            vol_key = next((k for k in ("volatility", "portfolio_volatility") if k in info), None)
            sr_key = next((k for k in ("sharpe", "sharpe_ratio") if k in info), None)
            if ret_key is not None:
                row["return"] = info[ret_key]
            if vol_key is not None:
                row["volatility"] = info[vol_key]
            if sr_key is not None:
                row["sharpe"] = info[sr_key]
            if "cvar" in info:
                row["cvar"] = info["cvar"]
            if "max_drawdown" in info:
                row["max_drawdown"] = info["max_drawdown"]
            comparison_rows.append(row)
        comparison_df = pd.DataFrame(comparison_rows)
        if len(comparison_df) > 0 and "sharpe" in comparison_df.columns:
            comparison_df = comparison_df.sort_values("sharpe", ascending=False).reset_index(drop=True)

        results["comparison_table"] = comparison_df
        return results

    def portfolio_summary(self, returns, weights):
        """Compute a full risk/return summary for an arbitrary weight vector.

        Parameters
        ----------
        returns : pd.DataFrame | np.ndarray  (T × N)
            Historical return matrix.
        weights : array-like
            Portfolio weight vector.

        Returns
        -------
        dict with keys: return, volatility, sharpe, sortino, max_drawdown,
        calmar, var_95, cvar_95, skewness, kurtosis.
        """
        returns = _validate_returns(returns)
        w = np.asarray(weights, dtype=np.float64).ravel()
        if len(w) != returns.shape[1]:
            raise ValueError(
                f"weights length ({len(w)}) != number of assets ({returns.shape[1]})."
            )

        port_ret = returns @ w
        mu = port_ret.mean() * 252
        vol = port_ret.std() * np.sqrt(252)
        sharpe = (mu - self.risk_free_rate) / max(vol, 1e-14)

        # Sortino
        downside = port_ret[port_ret < 0]
        ds_dev = downside.std() * np.sqrt(252) if len(downside) > 1 else 1e-14
        sortino = (mu - self.risk_free_rate) / ds_dev

        # Max drawdown
        cumulative = np.cumprod(1.0 + port_ret)
        peak = np.maximum.accumulate(cumulative)
        dd = (peak - cumulative) / peak
        max_dd = float(dd.max())

        # Calmar
        calmar = mu / max_dd if max_dd > 1e-14 else 0.0

        # VaR & CVaR (historical, 95%)
        var_95 = -np.percentile(port_ret, 5) * np.sqrt(252)
        tail_95 = port_ret[port_ret <= np.percentile(port_ret, 5)]
        cvar_95 = -tail_95.mean() * np.sqrt(252) if len(tail_95) > 0 else 0.0

        # Higher moments
        skew = float(pd.Series(port_ret).skew())
        kurt = float(pd.Series(port_ret).kurtosis())

        return {
            "return": mu,
            "volatility": vol,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "skewness": skew,
            "kurtosis": kurt,
        }
