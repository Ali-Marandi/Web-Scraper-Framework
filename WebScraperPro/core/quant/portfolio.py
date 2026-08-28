"""
Portfolio Optimization Module
===========================
Comprehensive portfolio optimization for quantitative finance using
numpy, pandas, and scipy only.

Classes:
    MarkowitzOptimizer       — Mean-Variance (Markowitz) portfolio optimization
    BlackLittermanModel      — Black-Litterman Bayesian return estimation
    FuzzyPortfolioOptimizer  — Fuzzy-set based portfolio optimization
    FactorModel              — Factor model analysis (PCA, Fama-French)
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import linregress


# ─────────────────────────────────────────────────────────────────────────────
# 1. MARKOWITZ OPTIMIZER
# ─────────────────────────────────────────────────────────────────────────────

class MarkowitzOptimizer:
    """Classical Mean-Variance (Markowitz) portfolio optimizer.

    Provides Sharpe-ratio maximisation, minimum-variance portfolios,
    efficient-frontier generation, capital-market-line construction,
    and bootstrap resampling for robust weight estimation.
    """

    def __init__(self):
        self.last_optimization_result = None

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _portfolio_stats(weights, mean_returns, cov_matrix):
        """Return (expected_return, volatility, sharpe) for a weight vector."""
        port_ret = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return port_ret, port_vol

    def _min_var_objective(self, weights, mean_returns, cov_matrix):
        return np.dot(weights.T, np.dot(cov_matrix, weights))

    def _neg_sharpe_objective(self, weights, mean_returns, cov_matrix, rf):
        port_ret, port_vol = self._portfolio_stats(weights, mean_returns, cov_matrix)
        if port_vol < 1e-12:
            return 0.0
        return -(port_ret - rf) / port_vol

    def _max_ret_objective(self, weights, mean_returns, cov_matrix):
        return -np.dot(weights, mean_returns)

    # -- main optimise --------------------------------------------------------

    def optimize(self, returns_matrix, method="sharpe", risk_free_rate=0.02):
        """Run Mean-Variance portfolio optimisation.

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray  (T × N)
            Historical asset returns.  Columns = assets.
        method : str
            ``'sharpe'``  — maximise Sharpe ratio (default)
            ``'min_variance'`` — minimise portfolio variance
            ``'max_return'``   — maximise expected return (long-only)
        risk_free_rate : float
            Annualised risk-free rate used in Sharpe computation.

        Returns
        -------
        dict with keys ``weights``, ``expected_return``, ``volatility``,
        ``sharpe_ratio``, ``method``.
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            T, N = returns_matrix.shape

            mean_returns = returns_matrix.mean(axis=0)
            cov_matrix = np.cov(returns_matrix, rowvar=False)
            if cov_matrix.ndim == 0:
                cov_matrix = cov_matrix.reshape(1, 1)

            # Constraints & bounds
            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
            bounds = tuple((0.0, 1.0) for _ in range(N))
            w0 = np.ones(N) / N

            if method == "sharpe":
                obj = lambda w: self._neg_sharpe_objective(w, mean_returns, cov_matrix, risk_free_rate)
            elif method == "min_variance":
                obj = lambda w: self._min_var_objective(w, mean_returns, cov_matrix)
            elif method == "max_return":
                obj = lambda w: self._max_ret_objective(w, mean_returns, cov_matrix)
            else:
                raise ValueError(f"Unknown method '{method}'. Use 'sharpe', 'min_variance', or 'max_return'.")

            result = minimize(obj, w0, method="SLSQP", bounds=bounds,
                              constraints=constraints, options={"ftol": 1e-12, "maxiter": 1000})

            if not result.success:
                raise RuntimeError(f"Optimisation failed: {result.message}")

            w_opt = result.x
            # Clip near-zero negatives from numerical noise
            w_opt = np.clip(w_opt, 0.0, 1.0)
            w_opt /= w_opt.sum()

            exp_ret, vol = self._portfolio_stats(w_opt, mean_returns, cov_matrix)
            sharpe = (exp_ret - risk_free_rate) / vol if vol > 1e-12 else 0.0

            self.last_optimization_result = {
                "weights": w_opt,
                "expected_return": exp_ret,
                "volatility": vol,
                "sharpe_ratio": sharpe,
                "method": method,
            }
            return self.last_optimization_result

        except Exception as exc:
            return {"error": str(exc)}

    # -- efficient frontier ---------------------------------------------------

    def efficient_frontier(self, returns_matrix, n_points=50, risk_free_rate=0.02):
        """Generate efficient frontier (risk-return pairs).

        Returns
        -------
        dict with ``frontier`` (list of dicts), ``min_var_point``,
        ``max_sharpe_point``.
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            N = returns_matrix.shape[1]
            mean_returns = returns_matrix.mean(axis=0)
            cov_matrix = np.cov(returns_matrix, rowvar=False)
            if cov_matrix.ndim == 0:
                cov_matrix = cov_matrix.reshape(1, 1)

            # Find min-variance and max-return portfolios
            min_var = self.optimize(returns_matrix, method="min_variance", risk_free_rate=risk_free_rate)
            if "error" in min_var:
                return {"error": min_var["error"]}
            max_ret = self.optimize(returns_matrix, method="max_return", risk_free_rate=risk_free_rate)

            ret_min = min_var["expected_return"]
            ret_max = max_ret["expected_return"]
            target_returns = np.linspace(ret_min, ret_max, n_points)

            frontier = []
            bounds = tuple((0.0, 1.0) for _ in range(N))
            w0 = np.ones(N) / N

            for target in target_returns:
                cons = [
                    {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
                    {"type": "eq", "fun": lambda w, t=target: np.dot(w, mean_returns) - t},
                ]
                res = minimize(
                    lambda w: np.dot(w.T, np.dot(cov_matrix, w)),
                    w0, method="SLSQP", bounds=bounds, constraints=cons,
                    options={"ftol": 1e-12, "maxiter": 1000},
                )
                if res.success:
                    w = np.clip(res.x, 0.0, 1.0)
                    w /= w.sum()
                    vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                    sharpe = (target - risk_free_rate) / vol if vol > 1e-12 else 0.0
                    frontier.append({"return": target, "volatility": vol, "sharpe_ratio": sharpe, "weights": w})

            # Max-Sharpe point
            ms = self.optimize(returns_matrix, method="sharpe", risk_free_rate=risk_free_rate)

            return {
                "frontier": frontier,
                "min_var_point": min_var,
                "max_sharpe_point": ms,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- capital market line --------------------------------------------------

    def capital_market_line(self, returns_matrix, risk_free_rate=0.02):
        """Construct the Capital Market Line (CML) via the tangency portfolio.

        The tangency (max-Sharpe) portfolio is the single point where the CML
        is tangent to the efficient frontier.

        Returns
        -------
        dict with ``tangency_weights``, ``tangency_return``, ``tangency_vol``,
        ``sharpe_ratio``, ``cml_points`` (list of {risk, return}).
        """
        try:
            tan = self.optimize(returns_matrix, method="sharpe", risk_free_rate=risk_free_rate)
            if "error" in tan:
                return {"error": tan["error"]}

            tan_ret = tan["expected_return"]
            tan_vol = tan["volatility"]
            sharpe = tan["sharpe_ratio"]

            # CML: E[r_p] = r_f + (E[r_t] - r_f) / sigma_t * sigma_p
            cml_points = []
            for sigma in np.linspace(0, tan_vol * 2.0, 100):
                e_ret = risk_free_rate + sharpe * sigma
                cml_points.append({"risk": sigma, "return": e_ret})

            return {
                "tangency_weights": tan["weights"],
                "tangency_return": tan_ret,
                "tangency_volatility": tan_vol,
                "sharpe_ratio": sharpe,
                "cml_points": cml_points,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- bootstrap resampling -------------------------------------------------

    def resample_analysis(self, returns_matrix, n_resamples=500):
        """Bootstrap resampling for robust portfolio weight estimation.

        Resamples the return matrix with replacement ``n_resamples`` times,
        runs min-variance optimisation on each, and returns summary
        statistics of the weight distributions.

        Returns
        -------
        dict with ``mean_weights``, ``std_weights``, ``median_weights``,
        ``all_weights`` (N × n_resamples array).
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            T, N = returns_matrix.shape

            all_weights = np.zeros((N, n_resamples))

            for i in range(n_resamples):
                idx = np.random.choice(T, size=T, replace=True)
                sample = returns_matrix[idx]
                result = self.optimize(sample, method="min_variance")
                if "error" not in result:
                    all_weights[:, i] = result["weights"]
                else:
                    all_weights[:, i] = np.ones(N) / N  # fallback

            return {
                "mean_weights": all_weights.mean(axis=1),
                "std_weights": all_weights.std(axis=1),
                "median_weights": np.median(all_weights, axis=1),
                "min_weights": all_weights.min(axis=1),
                "max_weights": all_weights.max(axis=1),
                "all_weights": all_weights,
                "n_resamples": n_resamples,
            }
        except Exception as exc:
            return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 2. BLACK-LITTERMAN MODEL
# ─────────────────────────────────────────────────────────────────────────────

class BlackLittermanModel:
    """Black-Litterman Bayesian return-estimation and portfolio optimisation.

    Combines equilibrium (market-implied) expected returns with investor
    views to produce a posterior distribution of returns and covariance,
    then optimises a portfolio on the posterior.
    """

    def __init__(self, market_cap_weights, cov_matrix, risk_aversion=2.5, tau=0.05):
        """
        Parameters
        ----------
        market_cap_weights : array-like (N,)
            Market-capitalisation weights (equilibrium weights).
        cov_matrix : array-like (N × N)
            Asset return covariance matrix (annualised).
        risk_aversion : float
            Investor risk-aversion parameter δ (default 2.5).
        tau : float
            Scalar relating the covariance of the prior to the covariance
            of the returns (default 0.05).
        """
        self.weights = np.asarray(market_cap_weights, dtype=np.float64)
        self.cov_matrix = np.asarray(cov_matrix, dtype=np.float64)
        self.delta = float(risk_aversion)
        self.tau = float(tau)
        self.N = len(self.weights)

        # Implied excess equilibrium returns:  π = δ Σ w
        self.pi = self.delta * self.cov_matrix @ self.weights

        # Views storage
        self._views = []  # list of (asset_index, view_return, confidence)
        self._posterior_return = None
        self._posterior_cov = None

    def add_view(self, asset, view_return, confidence=0.5):
        """Add an investor view on an asset.

        Parameters
        ----------
        asset : int or str
            Asset index (int) or name.  If ``cov_matrix`` was a DataFrame,
            string keys are accepted.
        view_return : float
            Investor's expected excess return for the asset.
        confidence : float
            View confidence in [0, 1].  Higher values make the view
            more influential.  Omega diagonal = (1 - confidence) / confidence * tau
            (so confidence → 1 means tight / certain view).
        """
        if isinstance(asset, str):
            # Not directly mappable here without a name list; store as-is
            idx = asset
        else:
            idx = int(asset)
        self._views.append((idx, float(view_return), float(confidence)))

    def compute(self):
        """Compute posterior returns and covariance (Black-Litterman formula).

        Posterior mean:
            μ_BL = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ [(τΣ)⁻¹π + P'Ω⁻¹q]

        Posterior covariance:
            Σ_BL = Σ + [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹

        Returns
        -------
        dict with ``posterior_returns``, ``posterior_covariance``, ``implied_returns``.
        """
        try:
            tau_sigma = self.tau * self.cov_matrix  # τΣ  (N × N)
            tau_sigma_inv = np.linalg.inv(tau_sigma)

            if len(self._views) == 0:
                # No views — posterior equals prior
                self._posterior_return = self.pi.copy()
                self._posterior_cov = self.cov_matrix + np.linalg.inv(tau_sigma_inv)
                return {
                    "posterior_returns": self._posterior_return,
                    "posterior_covariance": self._posterior_cov,
                    "implied_returns": self.pi,
                }

            K = len(self._views)
            P = np.zeros((K, self.N))  # pick matrix
            q = np.zeros(K)            # view returns
            omega_diag = np.zeros(K)   # diagonal of Ω

            for k, (asset_idx, view_ret, conf) in enumerate(self._views):
                P[k, asset_idx] = 1.0
                q[k] = view_ret
                # Ω_kk = (1-c)/c * τ  — confidence scaling
                conf = np.clip(conf, 1e-6, 1.0 - 1e-6)
                omega_diag[k] = ((1.0 - conf) / conf) * self.tau

            Omega = np.diag(omega_diag)
            Omega_inv = np.diag(1.0 / omega_diag)

            # Posterior precision
            M = tau_sigma_inv + P.T @ Omega_inv @ P  # (N × N)
            M_inv = np.linalg.inv(M)

            # Posterior mean
            self._posterior_return = M_inv @ (tau_sigma_inv @ self.pi + P.T @ Omega_inv @ q)

            # Posterior covariance
            self._posterior_cov = self.cov_matrix + M_inv

            return {
                "posterior_returns": self._posterior_return,
                "posterior_covariance": self._posterior_cov,
                "implied_returns": self.pi,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def optimize_portfolio(self, risk_free_rate=0.02):
        """Optimise a portfolio on the posterior distribution.

        Runs max-Sharpe optimisation using the BL posterior mean and
        posterior covariance.

        Returns
        -------
        dict with ``weights``, ``expected_return``, ``volatility``,
        ``sharpe_ratio``, ``posterior_returns``, ``posterior_covariance``.
        """
        try:
            if self._posterior_return is None:
                comp = self.compute()
                if "error" in comp:
                    return {"error": comp["error"]}

            mu = self._posterior_return
            sigma = self._posterior_cov
            N = self.N

            def neg_sharpe(w):
                ret = np.dot(w, mu)
                vol = np.sqrt(np.dot(w.T, np.dot(sigma, w)))
                if vol < 1e-12:
                    return 0.0
                return -(ret - risk_free_rate) / vol

            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
            bounds = tuple((0.0, 1.0) for _ in range(N))
            w0 = np.ones(N) / N

            res = minimize(neg_sharpe, w0, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"ftol": 1e-12, "maxiter": 1000})

            if not res.success:
                raise RuntimeError(f"Optimisation failed: {res.message}")

            w_opt = np.clip(res.x, 0.0, 1.0)
            w_opt /= w_opt.sum()
            exp_ret = np.dot(w_opt, mu)
            vol = np.sqrt(np.dot(w_opt.T, np.dot(sigma, w_opt)))
            sharpe = (exp_ret - risk_free_rate) / vol if vol > 1e-12 else 0.0

            return {
                "weights": w_opt,
                "expected_return": exp_ret,
                "volatility": vol,
                "sharpe_ratio": sharpe,
                "posterior_returns": self._posterior_return,
                "posterior_covariance": self._posterior_cov,
            }
        except Exception as exc:
            return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 3. FUZZY PORTFOLIO OPTIMIZER
# ─────────────────────────────────────────────────────────────────────────────

class FuzzyPortfolioOptimizer:
    """Fuzzy-set based portfolio optimisation.

    Replaces crisp expected returns and covariance estimates with
    fuzzy numbers (triangular or trapezoidal) and solves the portfolio
    problem via α-cut based possibilistic optimisation.
    """

    @staticmethod
    def _to_fuzzy_triangular(values):
        """Estimate triangular fuzzy number (a, b, c) from a 1-D sample.

        a = min(sample) (or percentile-10 for robustness),
        b = mean(sample),
        c = max(sample) (or percentile-90).
        """
        a = np.percentile(values, 10)
        b = np.mean(values)
        c = np.percentile(values, 90)
        return (a, b, c)

    @staticmethod
    def _to_fuzzy_trapezoidal(values):
        """Estimate trapezoidal fuzzy number (a, b, c, d) from a 1-D sample.

        a = p10, b = p30, c = p70, d = p90.
        """
        a = np.percentile(values, 10)
        b = np.percentile(values, 30)
        c = np.percentile(values, 70)
        d = np.percentile(values, 90)
        return (a, b, c, d)

    @staticmethod
    def _alpha_cut_triangular(fuzzy, alpha):
        """Alpha-cut of a triangular fuzzy number (a, b, c).

        Returns (low, high) where
            low  = a + α(b − a)
            high = c − α(c − b)
        """
        a, b, c = fuzzy
        low = a + alpha * (b - a)
        high = c - alpha * (c - b)
        return (low, high)

    @staticmethod
    def _alpha_cut_trapezoidal(fuzzy, alpha):
        """Alpha-cut of a trapezoidal fuzzy number (a, b, c, d)."""
        a, b, c, d = fuzzy
        low = a + alpha * (b - a)
        high = d - alpha * (d - c)
        return (low, high)

    def _build_fuzzy_returns(self, returns_matrix, membership_type):
        """Build fuzzy expected returns for each asset.

        Returns list of fuzzy numbers (one per asset).
        """
        if isinstance(returns_matrix, pd.DataFrame):
            returns_matrix = returns_matrix.values
        returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
        N = returns_matrix.shape[1]

        fuzzy_rets = []
        for j in range(N):
            col = returns_matrix[:, j]
            if membership_type == "triangular":
                fuzzy_rets.append(self._to_fuzzy_triangular(col))
            elif membership_type == "trapezoidal":
                fuzzy_rets.append(self._to_fuzzy_trapezoidal(col))
            else:
                raise ValueError(f"Unknown membership type '{membership_type}'")
        return fuzzy_rets, returns_matrix

    def _build_fuzzy_covariance(self, returns_matrix, membership_type, n_bootstrap=200):
        """Build a fuzzy covariance estimate via bootstrap.

        For each bootstrap sample we compute a covariance matrix, then
        take element-wise percentile bounds to form fuzzy numbers.
        """
        T, N = returns_matrix.shape
        cov_samples = []
        for _ in range(n_bootstrap):
            idx = np.random.choice(T, size=T, replace=True)
            cov_samples.append(np.cov(returns_matrix[idx], rowvar=False))
        cov_samples = np.array(cov_samples)  # (n_bootstrap, N, N)

        # For each element, build a triangular fuzzy number from bootstrap dist
        fuzzy_cov = np.empty((N, N), dtype=object)
        for i in range(N):
            for j in range(N):
                vals = cov_samples[:, i, j]
                if membership_type == "triangular":
                    fuzzy_cov[i, j] = self._to_fuzzy_triangular(vals)
                else:
                    fuzzy_cov[i, j] = self._to_fuzzy_trapezoidal(vals)
        return fuzzy_cov

    def defuzzify(self, fuzzy_result, method="centroid"):
        """Defuzzify a fuzzy number to a crisp value.

        Parameters
        ----------
        fuzzy_result : tuple
            Triangular (a, b, c) or trapezoidal (a, b, c, d).
        method : str
            ``'centroid'``     — centre of gravity
            ``'mean_of_max'`` — mean of values at maximum membership
            ``'bisector'``     — vertical line bisecting area

        Returns
        -------
        float : defuzzified value.
        """
        try:
            n_pts = 1000
            if len(fuzzy_result) == 3:
                a, b, c = fuzzy_result
                x = np.linspace(a, c, n_pts)
                # Triangular membership
                mu = np.where(x <= b,
                              (x - a) / (b - a + 1e-15),
                              (c - x) / (c - b + 1e-15))
                mu = np.clip(mu, 0.0, 1.0)
            elif len(fuzzy_result) == 4:
                a, b, c, d = fuzzy_result
                x = np.linspace(a, d, n_pts)
                mu = np.where(x < b,
                              (x - a) / (b - a + 1e-15),
                              np.where(x <= c,
                                       1.0,
                                       (d - x) / (d - c + 1e-15)))
                mu = np.clip(mu, 0.0, 1.0)
            else:
                raise ValueError("fuzzy_result must be 3-tuple or 4-tuple")

            if method == "centroid":
                return float(np.trapezoid(mu * x, x) / (np.trapezoid(mu, x) + 1e-15))

            elif method == "mean_of_max":
                max_mu = mu.max()
                max_x = x[mu == max_mu]
                return float(max_x.mean())

            elif method == "bisector":
                total_area = np.trapezoid(mu, x)
                if total_area < 1e-15:
                    return float(np.mean(x))
                half = total_area / 2.0
                cum_area = np.zeros(n_pts)
                for k in range(1, n_pts):
                    cum_area[k] = cum_area[k - 1] + 0.5 * (mu[k] + mu[k - 1]) * (x[k] - x[k - 1])
                idx = np.searchsorted(cum_area, half)
                idx = min(idx, n_pts - 1)
                return float(x[idx])

            else:
                raise ValueError(f"Unknown defuzzification method '{method}'")

        except Exception as exc:
            return float("nan")

    # -- fuzzy Sharpe optimisation --------------------------------------------

    def fuzzy_sharpe_optimization(self, returns_matrix, membership_type="triangular"):
        """Maximise a possibilistic Sharpe ratio under fuzzy returns.

        Strategy:
        1. Estimate fuzzy expected returns for each asset.
        2. At a high α-level (e.g. 0.5) take the *lower* bound of each
           fuzzy return (pessimistic / necessity measure).
        3. Use the *crisp* covariance matrix (defuzzified) for risk.
        4. Maximise Sharpe with these inputs.

        Returns
        -------
        dict with ``weights``, ``fuzzy_returns`` (list of tuples),
        ``defuzzified_returns``, ``volatility``, ``sharpe_ratio``.
        """
        try:
            alpha = 0.5
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            T, N = returns_matrix.shape

            fuzzy_rets, returns_matrix = self._build_fuzzy_returns(returns_matrix, membership_type)
            cov_matrix = np.cov(returns_matrix, rowvar=False)
            if cov_matrix.ndim == 0:
                cov_matrix = cov_matrix.reshape(1, 1)

            # Defuzzify returns (centroid) and also get lower α-cut
            crisp_rets = np.array([self.defuzzify(fr, "centroid") for fr in fuzzy_rets])
            lower_rets = np.zeros(N)
            for j, fr in enumerate(fuzzy_rets):
                if membership_type == "triangular":
                    low, _ = self._alpha_cut_triangular(fr, alpha)
                else:
                    low, _ = self._alpha_cut_trapezoidal(fr, alpha)
                lower_rets[j] = low

            # Use the lower α-cut (necessity / pessimistic) returns
            def neg_sharpe(w):
                ret = np.dot(w, lower_rets)
                vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                if vol < 1e-12:
                    return 0.0
                return -ret / vol  # rf=0 for fuzzy context

            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
            bounds = tuple((0.0, 1.0) for _ in range(N))
            w0 = np.ones(N) / N

            res = minimize(neg_sharpe, w0, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"ftol": 1e-12, "maxiter": 1000})

            if not res.success:
                raise RuntimeError(f"Optimisation failed: {res.message}")

            w_opt = np.clip(res.x, 0.0, 1.0)
            w_opt /= w_opt.sum()
            exp_ret = np.dot(w_opt, crisp_rets)
            vol = np.sqrt(np.dot(w_opt.T, np.dot(cov_matrix, w_opt)))
            sharpe = exp_ret / vol if vol > 1e-12 else 0.0

            return {
                "weights": w_opt,
                "fuzzy_returns": fuzzy_rets,
                "defuzzified_returns": crisp_rets,
                "alpha_cut_returns": lower_rets,
                "expected_return": exp_ret,
                "volatility": vol,
                "sharpe_ratio": sharpe,
                "membership_type": membership_type,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- fuzzy mean-variance --------------------------------------------------

    def fuzzy_mean_variance(self, returns_matrix, target_return,
                            membership_type="triangular"):
        """Fuzzy mean-variance optimisation with α-cut.

        At a given α-level, the fuzzy covariance is converted to a
        *crisp* interval matrix.  We minimise the upper bound of the
        portfolio variance (pessimistic risk) subject to the portfolio
        return exceeding the lower α-cut bound of the fuzzy target.

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray  (T × N)
        target_return : float
            Desired (crisp) portfolio return target.
        membership_type : str
            ``'triangular'`` or ``'trapezoidal'``.

        Returns
        -------
        dict with ``weights``, ``expected_return``, ``volatility``,
        ``upper_volatility`` (at α-cut), ``fuzzy_covariance_used``.
        """
        try:
            alpha = 0.5
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            T, N = returns_matrix.shape

            mean_returns = returns_matrix.mean(axis=0)
            cov_matrix = np.cov(returns_matrix, rowvar=False)
            if cov_matrix.ndim == 0:
                cov_matrix = cov_matrix.reshape(1, 1)

            # Build fuzzy covariance (bootstrap-based)
            fuzzy_cov = self._build_fuzzy_covariance(returns_matrix, membership_type)

            # Get upper α-cut of each covariance element (pessimistic risk)
            cov_upper = np.zeros((N, N))
            for i in range(N):
                for j in range(N):
                    fc = fuzzy_cov[i, j]
                    if membership_type == "triangular":
                        _, high = self._alpha_cut_triangular(fc, alpha)
                    else:
                        _, high = self._alpha_cut_trapezoidal(fc, alpha)
                    cov_upper[i, j] = high

            # Ensure symmetry and positive semi-definiteness
            cov_upper = 0.5 * (cov_upper + cov_upper.T)
            eigvals, eigvecs = np.linalg.eigh(cov_upper)
            eigvals = np.maximum(eigvals, 1e-8)
            cov_upper = eigvecs @ np.diag(eigvals) @ eigvecs.T

            # Minimise upper-bound variance s.t. return >= target
            def obj(w):
                return np.dot(w.T, np.dot(cov_upper, w))

            constraints = [
                {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
                {"type": "ineq", "fun": lambda w: np.dot(w, mean_returns) - target_return},
            ]
            bounds = tuple((0.0, 1.0) for _ in range(N))
            w0 = np.ones(N) / N

            res = minimize(obj, w0, method="SLSQP",
                           bounds=bounds, constraints=constraints,
                           options={"ftol": 1e-12, "maxiter": 1000})

            if not res.success:
                raise RuntimeError(f"Optimisation failed: {res.message}")

            w_opt = np.clip(res.x, 0.0, 1.0)
            w_opt /= w_opt.sum()
            exp_ret = np.dot(w_opt, mean_returns)
            vol_crisp = np.sqrt(np.dot(w_opt.T, np.dot(cov_matrix, w_opt)))
            vol_upper = np.sqrt(np.dot(w_opt.T, np.dot(cov_upper, w_opt)))

            return {
                "weights": w_opt,
                "expected_return": exp_ret,
                "volatility": vol_crisp,
                "upper_volatility": vol_upper,
                "alpha": alpha,
                "membership_type": membership_type,
                "fuzzy_covariance_used": cov_upper,
            }
        except Exception as exc:
            return {"error": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# 4. FACTOR MODEL
# ─────────────────────────────────────────────────────────────────────────────

class FactorModel:
    """Factor-model analysis for portfolio returns.

    Supports PCA-based factor extraction, Fama-French 3- and 5-factor
    regressions, and generic factor-exposure computation.
    """

    # -- PCA factors ----------------------------------------------------------

    def pca_factors(self, returns_matrix, n_factors=5):
        """Extract principal-component factors from asset returns.

        Uses eigendecomposition of the correlation matrix to obtain
        factor loadings and factor return time-series.

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray  (T × N)
        n_factors : int
            Number of principal components to retain.

        Returns
        -------
        dict with ``factor_loadings`` (N × n_factors),
        ``factor_returns`` (T × n_factors),
        ``explained_variance_ratio`` (n_factors,),
        ``cumulative_variance_ratio``, ``eigenvalues``.
        """
        try:
            asset_names = None
            if isinstance(returns_matrix, pd.DataFrame):
                asset_names = returns_matrix.columns.tolist()
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            T, N = returns_matrix.shape

            # Demean
            mean_r = returns_matrix.mean(axis=0)
            X = returns_matrix - mean_r

            # Standardise for correlation-based PCA
            std_r = returns_matrix.std(axis=0, ddof=1)
            std_r[std_r < 1e-12] = 1.0
            Z = X / std_r

            # Correlation matrix eigendecomposition
            corr_matrix = np.corrcoef(Z, rowvar=False)
            eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)

            # Sort descending
            idx = np.argsort(eigenvalues)[::-1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

            # Keep top n_factors
            nf = min(n_factors, N)
            eigenvalues_top = eigenvalues[:nf]
            eigenvectors_top = eigenvectors[:, :nf]  # (N × nf)

            # Factor loadings: each column is a factor; rows are assets
            # Loading = eigenvector * sqrt(eigenvalue)
            factor_loadings = eigenvectors_top * np.sqrt(eigenvalues_top)

            # Factor returns: project standardised returns onto loadings
            # F = Z @ V  where V = eigenvectors
            factor_returns = Z @ eigenvectors_top  # (T × nf)

            # Explained variance ratios
            total_var = eigenvalues.sum()
            explained_ratio = eigenvalues_top / total_var
            cumulative_ratio = np.cumsum(explained_ratio)

            result = {
                "factor_loadings": factor_loadings,
                "factor_returns": factor_returns,
                "eigenvalues": eigenvalues_top,
                "explained_variance_ratio": explained_ratio,
                "cumulative_variance_ratio": cumulative_ratio,
                "n_factors": nf,
            }
            if asset_names is not None:
                result["asset_names"] = asset_names
            return result

        except Exception as exc:
            return {"error": str(exc)}

    # -- OLS helper -----------------------------------------------------------

    @staticmethod
    def _ols(Y, X):
        """Ordinary Least Squares:  Y = X β + ε.

        Parameters
        ----------
        Y : np.ndarray (T,)
        X : np.ndarray (T, K)  — includes intercept column of ones

        Returns
        -------
        dict with ``beta``, ``residuals``, ``r_squared``,
        ``adj_r_squared``, ``std_error``.
        """
        # β = (X'X)⁻¹ X'Y
        XtX = X.T @ X
        XtY = X.T @ Y
        try:
            XtX_inv = np.linalg.inv(XtX)
        except np.linalg.LinAlgError:
            XtX_inv = np.linalg.pinv(XtX)
        beta = XtX_inv @ XtY

        fitted = X @ beta
        residuals = Y - fitted
        T, K = X.shape

        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((Y - Y.mean()) ** 2)
        r_sq = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 0.0
        adj_r_sq = 1.0 - (1.0 - r_sq) * (T - 1) / (T - K) if T > K else 0.0
        std_err = np.sqrt(ss_res / (T - K)) if T > K else 0.0

        # Standard errors of coefficients
        try:
            cov_beta = std_err ** 2 * XtX_inv
            beta_std_err = np.sqrt(np.diag(cov_beta))
        except Exception:
            beta_std_err = np.full(K, np.nan)

        return {
            "beta": beta,
            "residuals": residuals,
            "fitted": fitted,
            "r_squared": r_sq,
            "adj_r_squared": adj_r_sq,
            "std_error": std_err,
            "beta_std_error": beta_std_err,
        }

    # -- Fama-French 3-factor --------------------------------------------------

    def fama_french_3factor(self, returns_matrix, smb, hml):
        """Fama-French 3-factor model regression.

        R_it = α + β_MK R_Mt + β_SMB SMB_t + β_HML HML_t + ε_it

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray (T × N)
            Asset (or portfolio) returns.
        smb : array-like (T,)
            Small-Minus-Big factor returns.
        hml : array-like (T,)
            High-Minus-Low factor returns.

        Returns
        -------
        dict with ``results`` (list of per-asset dicts),
        ``avg_betas`` (N × 3).
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            smb = np.asarray(smb, dtype=np.float64).ravel()
            hml = np.asarray(hml, dtype=np.float64).ravel()
            T, N = returns_matrix.shape

            # Market factor = equal-weighted portfolio return
            market = returns_matrix.mean(axis=1)

            # Design matrix: intercept, MKT, SMB, HML
            X = np.column_stack([np.ones(T), market, smb, hml])

            results = []
            all_betas = np.zeros((N, 4))  # alpha, mkt, smb, hml

            for j in range(N):
                ols = self._ols(returns_matrix[:, j], X)
                results.append({
                    "asset": j,
                    "alpha": ols["beta"][0],
                    "beta_mkt": ols["beta"][1],
                    "beta_smb": ols["beta"][2],
                    "beta_hml": ols["beta"][3],
                    "r_squared": ols["r_squared"],
                    "adj_r_squared": ols["adj_r_squared"],
                    "residual_std": ols["std_error"],
                    "beta_std_errors": ols["beta_std_error"],
                })
                all_betas[j] = ols["beta"]

            return {
                "results": results,
                "avg_betas": all_betas,
                "model": "fama_french_3factor",
                "n_assets": N,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- Fama-French 5-factor --------------------------------------------------

    def fama_french_5factor(self, returns_matrix, smb, hml, rmw, cma):
        """Fama-French 5-factor model regression.

        R_it = α + β_MK R_Mt + β_SMB SMB_t + β_HML HML_t
               + β_RMW RMW_t + β_CMA CMA_t + ε_it

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray (T × N)
        smb, hml, rmw, cma : array-like (T,)
            Factor return series.

        Returns
        -------
        dict with ``results`` (list of per-asset dicts),
        ``avg_betas`` (N × 6).
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            smb = np.asarray(smb, dtype=np.float64).ravel()
            hml = np.asarray(hml, dtype=np.float64).ravel()
            rmw = np.asarray(rmw, dtype=np.float64).ravel()
            cma = np.asarray(cma, dtype=np.float64).ravel()
            T, N = returns_matrix.shape

            market = returns_matrix.mean(axis=1)

            # Design matrix: intercept, MKT, SMB, HML, RMW, CMA
            X = np.column_stack([np.ones(T), market, smb, hml, rmw, cma])

            results = []
            all_betas = np.zeros((N, 6))

            for j in range(N):
                ols = self._ols(returns_matrix[:, j], X)
                results.append({
                    "asset": j,
                    "alpha": ols["beta"][0],
                    "beta_mkt": ols["beta"][1],
                    "beta_smb": ols["beta"][2],
                    "beta_hml": ols["beta"][3],
                    "beta_rmw": ols["beta"][4],
                    "beta_cma": ols["beta"][5],
                    "r_squared": ols["r_squared"],
                    "adj_r_squared": ols["adj_r_squared"],
                    "residual_std": ols["std_error"],
                    "beta_std_errors": ols["beta_std_error"],
                })
                all_betas[j] = ols["beta"]

            return {
                "results": results,
                "avg_betas": all_betas,
                "model": "fama_french_5factor",
                "n_assets": N,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- generic factor exposure ----------------------------------------------

    def factor_exposure(self, returns_matrix, factor_returns):
        """Compute factor betas and idiosyncratic risk for each asset.

        R_it = α_i + Σ_k β_ik F_kt + ε_it

        Parameters
        ----------
        returns_matrix : pd.DataFrame or np.ndarray (T × N)
        factor_returns : pd.DataFrame or np.ndarray (T × K)
            Factor return time-series.

        Returns
        -------
        dict with ``betas`` (N × K), ``alphas`` (N,),
        ``idiosyncratic_risk`` (N,), ``r_squared`` (N,),
        ``residuals`` (T × N).
        """
        try:
            if isinstance(returns_matrix, pd.DataFrame):
                returns_matrix = returns_matrix.values
            if isinstance(factor_returns, pd.DataFrame):
                factor_returns = factor_returns.values
            returns_matrix = np.asarray(returns_matrix, dtype=np.float64)
            factor_returns = np.asarray(factor_returns, dtype=np.float64)
            T, N = returns_matrix.shape
            K = factor_returns.shape[1]

            # Design matrix: intercept + factors
            X = np.column_stack([np.ones(T), factor_returns])  # (T, K+1)

            betas = np.zeros((N, K))
            alphas = np.zeros(N)
            idio_risk = np.zeros(N)
            r_squared = np.zeros(N)
            residuals = np.zeros((T, N))

            for j in range(N):
                ols = self._ols(returns_matrix[:, j], X)
                alphas[j] = ols["beta"][0]
                betas[j, :] = ols["beta"][1:]
                idio_risk[j] = ols["std_error"]
                r_squared[j] = ols["r_squared"]
                residuals[:, j] = ols["residuals"]

            return {
                "betas": betas,
                "alphas": alphas,
                "idiosyncratic_risk": idio_risk,
                "r_squared": r_squared,
                "residuals": residuals,
                "n_assets": N,
                "n_factors": K,
            }
        except Exception as exc:
            return {"error": str(exc)}
