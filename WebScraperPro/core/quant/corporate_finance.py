"""corporate_finance.py -- Corporate Finance Models for WebScraper Pro

Production-quality implementations of core corporate finance and quantitative
finance models using only numpy, pandas, and scipy.  All classes return
dictionaries with clear, machine-readable keys.

Classes
-------
CAPMModel         Capital Asset Pricing Model (single & multi-factor)
APTModel          Arbitrage Pricing Theory with PCA factor extraction
EMHTester         Efficient Market Hypothesis test battery
AltmanZScore      Bankruptcy-prediction Z-Score family
BeneishMScore     Earnings-manipulation detection M-Score
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from scipy import linalg, stats


# --------------------------------------------------------------------------- #
#  Internal OLS helper                                                       #
# --------------------------------------------------------------------------- #
def _ols(y: np.ndarray, X: np.ndarray) -> Dict[str, Any]:
    """Ordinary Least Squares via scipy.linalg.solve.

    Returns dict: coefficients, residuals, r_squared, adj_r_squared,
    std_errors, t_values, p_values, n_observations, degrees_of_freedom,
    f_statistic.
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    X = np.asarray(X, dtype=np.float64)
    if y.size == 0 or X.shape[0] == 0:
        raise ValueError("Empty input arrays passed to OLS.")
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    n, k = X.shape
    if n <= k:
        raise ValueError(f"Need more obs ({n}) than regressors ({k}).")
    XtX = X.T @ X
    try:
        beta = linalg.solve(XtX, X.T @ y, assume_a="pos")
    except linalg.LinAlgError:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_sq = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    dof = max(n - k, 1)
    sigma2 = ss_res / dof
    try:
        cov = sigma2 * linalg.inv(XtX)
    except linalg.LinAlgError:
        cov = np.full((k, k), np.nan)
    se = np.sqrt(np.diag(cov))
    with np.errstate(invalid="ignore", divide="ignore"):
        t_vals = np.where(se > 0, beta / se, np.nan)
    p_vals = 2.0 * stats.t.sf(np.abs(t_vals), dof)
    f_stat = np.nan
    if k > 1 and sigma2 > 0:
        f_stat = float(((ss_tot - ss_res) / (k - 1)) / sigma2)
    return {
        "coefficients": beta, "residuals": resid,
        "r_squared": r_sq,
        "adjusted_r_squared": 1.0 - (1.0 - r_sq) * (n - 1) / max(n - k, 1),
        "std_errors": se, "t_values": t_vals, "p_values": p_vals,
        "n_observations": n, "degrees_of_freedom": dof,
        "f_statistic": f_stat,
    }


# =========================================================================== #
#  1. CAPMModel                                                              #
# =========================================================================== #
class CAPMModel:
    """Capital Asset Pricing Model and extensions.

    Methods: estimate, security_market_line, rolling_beta, fama_french_3factor.
    Every public method returns a dict.
    """

    def estimate(self, returns, market_returns, risk_free_rate=0.02):
        """Single-factor CAPM: r_i - rf = alpha + beta*(r_m - rf) + eps.

        Parameters
        ----------
        returns : array-like, shape (n,) -- asset returns (decimal)
        market_returns : array-like, shape (n,) -- market returns
        risk_free_rate : float -- annualised rf (default 0.02)

        Returns
        -------
        dict with alpha, beta, r_squared, adj_r_squared, std_errors,
        t_values, p_values, treynor_ratio, jensens_alpha,
        mean_excess_return, std_excess_return, security_characteristic_line.
        """
        r = np.asarray(returns, dtype=np.float64).ravel()
        rm = np.asarray(market_returns, dtype=np.float64).ravel()
        if r.size == 0 or rm.size == 0:
            raise ValueError("Empty return series.")
        n = min(r.size, rm.size)
        r, rm = r[:n], rm[:n]
        rf_p = risk_free_rate / 252.0
        ex_r, ex_m = r - rf_p, rm - rf_p
        X = np.column_stack([np.ones(n), ex_m])
        res = _ols(ex_r, X)
        alpha_a = float(res["coefficients"][0]) * 252
        beta = float(res["coefficients"][1])
        mean_ex = float(np.mean(ex_r))
        std_ex = float(np.std(ex_r, ddof=1))
        treynor = (mean_ex * 252) / beta if abs(beta) > 1e-12 else np.nan
        return {
            "alpha": alpha_a, "beta": beta,
            "r_squared": float(res["r_squared"]),
            "adj_r_squared": float(res["adjusted_r_squared"]),
            "std_errors": res["std_errors"].tolist(),
            "t_values": res["t_values"].tolist(),
            "p_values": res["p_values"].tolist(),
            "treynor_ratio": treynor, "jensens_alpha": alpha_a,
            "mean_excess_return": mean_ex * 252,
            "std_excess_return": std_ex * np.sqrt(252),
            "security_characteristic_line": {
                "fitted": (X @ res["coefficients"]).tolist(),
                "residuals": res["residuals"].tolist(),
            },
        }

    def security_market_line(self, returns_dict, market_returns, risk_free_rate=0.02):
        """Compute SML data for multiple assets.

        Parameters
        ----------
        returns_dict : dict {name: return_series}
        market_returns : array-like
        risk_free_rate : float

        Returns
        -------
        dict with 'assets' (list), 'risk_free_rate', 'market_premium'.
        Each asset has name, beta, expected_return, sml_return, excess_return.
        """
        rm = np.asarray(market_returns, dtype=np.float64).ravel()
        if rm.size == 0:
            raise ValueError("Empty market returns.")
        rf_p = risk_free_rate / 252.0
        mkt_prem = float(np.mean(rm - rf_p)) * 252
        assets = []
        for name, rets in returns_dict.items():
            r = np.asarray(rets, dtype=np.float64).ravel()
            nn = min(r.size, rm.size)
            capm = self.estimate(r[:nn], rm[:nn], risk_free_rate)
            b = capm["beta"]
            exp_r = capm["mean_excess_return"] + risk_free_rate
            sml_r = risk_free_rate + b * mkt_prem
            assets.append({
                "name": name, "beta": b, "expected_return": exp_r,
                "sml_return": sml_r, "excess_return": exp_r - sml_r,
            })
        return {"assets": assets, "risk_free_rate": risk_free_rate,
                "market_premium": mkt_prem}

    def rolling_beta(self, returns, market_returns, window=60):
        """Rolling-window CAPM beta estimation.

        Parameters
        ----------
        returns, market_returns : array-like, shape (n,)
        window : int (default 60)

        Returns
        -------
        dict with betas, alphas, r_squareds (ndarray, NaN where no fit), window.
        """
        r = np.asarray(returns, dtype=np.float64).ravel()
        rm = np.asarray(market_returns, dtype=np.float64).ravel()
        n = min(r.size, rm.size)
        r, rm = r[:n], rm[:n]
        if n < window:
            raise ValueError(f"Length ({n}) < window ({window}).")
        betas = np.full(n, np.nan)
        alphas = np.full(n, np.nan)
        r2s = np.full(n, np.nan)
        for i in range(window - 1, n):
            sr = r[i - window + 1: i + 1]
            srm = rm[i - window + 1: i + 1]
            X = np.column_stack([np.ones(window), srm])
            try:
                o = _ols(sr, X)
                alphas[i] = float(o["coefficients"][0]) * 252
                betas[i] = float(o["coefficients"][1])
                r2s[i] = float(o["r_squared"])
            except Exception:
                pass
        return {"betas": betas, "alphas": alphas, "r_squareds": r2s, "window": window}

    def fama_french_3factor(self, asset_returns, smb, hml, market_returns,
                            risk_free_rate=0.02):
        """Fama-French 3-factor: r_i-rf = a + b1*(rM-rf) + b2*SMB + b3*HML + e.

        Parameters
        ----------
        asset_returns, smb, hml, market_returns : array-like, shape (n,)
        risk_free_rate : float

        Returns
        -------
        dict with alpha, beta_market, beta_smb, beta_hml, r_squared,
        adj_r_squared, coefficients, std_errors, t_values, p_values, f_statistic.
        """
        ra = np.asarray(asset_returns, dtype=np.float64).ravel()
        rm = np.asarray(market_returns, dtype=np.float64).ravel()
        sa = np.asarray(smb, dtype=np.float64).ravel()
        ha = np.asarray(hml, dtype=np.float64).ravel()
        n = min(ra.size, rm.size, sa.size, ha.size)
        ra, rm, sa, ha = ra[:n], rm[:n], sa[:n], ha[:n]
        rf_p = risk_free_rate / 252.0
        X = np.column_stack([np.ones(n), rm - rf_p, sa, ha])
        res = _ols(ra - rf_p, X)
        return {
            "alpha": float(res["coefficients"][0]) * 252,
            "beta_market": float(res["coefficients"][1]),
            "beta_smb": float(res["coefficients"][2]),
            "beta_hml": float(res["coefficients"][3]),
            "r_squared": float(res["r_squared"]),
            "adj_r_squared": float(res["adjusted_r_squared"]),
            "coefficients": res["coefficients"].tolist(),
            "std_errors": res["std_errors"].tolist(),
            "t_values": res["t_values"].tolist(),
            "p_values": res["p_values"].tolist(),
            "f_statistic": float(res["f_statistic"]),
        }


# =========================================================================== #
#  2. APTModel                                                               #
# =========================================================================== #
class APTModel:
    """Arbitrage Pricing Theory with PCA factor extraction.

    Methods: estimate, factor_analysis, arbitrage_test.
    """

    def estimate(self, returns, factor_returns):
        """Multi-factor APT via OLS: r_i = alpha + sum(b_j * f_j) + eps.

        Parameters
        ----------
        returns : array-like, shape (n,)
        factor_returns : array-like, shape (n, k) -- factor series

        Returns
        -------
        dict with factor_loadings, residuals, r_squared, adj_r_squared,
        std_errors, t_values, p_values, factor_premia.
        """
        y = np.asarray(returns, dtype=np.float64).ravel()
        F = np.asarray(factor_returns, dtype=np.float64)
        if F.ndim == 1:
            F = F.reshape(-1, 1)
        n = min(y.size, F.shape[0])
        y, F = y[:n], F[:n]
        if F.shape[1] == 0 or not np.allclose(F[:, 0], 1.0, atol=1e-8):
            F = np.column_stack([np.ones(n), F])
        ols_res = _ols(y, F)
        return {
            "factor_loadings": ols_res["coefficients"].tolist(),
            "residuals": ols_res["residuals"].tolist(),
            "r_squared": float(ols_res["r_squared"]),
            "adj_r_squared": float(ols_res["adjusted_r_squared"]),
            "std_errors": ols_res["std_errors"].tolist(),
            "t_values": ols_res["t_values"].tolist(),
            "p_values": ols_res["p_values"].tolist(),
            "factor_premia": np.mean(F[:, 1:], axis=0).tolist() if F.shape[1] > 1 else [],
        }

    def factor_analysis(self, returns, n_factors=5):
        """PCA-based factor extraction for APT.

        Parameters
        ----------
        returns : array-like, shape (n_obs, n_assets)
        n_factors : int (default 5)

        Returns
        -------
        dict with eigenvalues, explained_variance_ratio, cumulative_variance,
        factor_loadings (n_assets x n_factors), factor_returns (n_obs x n_factors),
        n_factors.
        """
        R = np.asarray(returns, dtype=np.float64)
        if R.ndim == 1:
            R = R.reshape(-1, 1)
        n_obs, n_assets = R.shape
        if n_obs < 2 or n_assets < 2:
            raise ValueError("Need >=2 obs and >=2 assets for PCA.")
        n_factors = min(n_factors, n_obs, n_assets)
        Rc = R - np.mean(R, axis=0)
        cov = np.cov(Rc, rowvar=False)
        evals, evecs = linalg.eigh(cov)
        idx = np.argsort(evals)[::-1]
        evals, evecs = evals[idx], evecs[:, idx]
        et = evals[:n_factors]
        ev = evecs[:, :n_factors]
        tv = max(np.sum(evals), 1e-300)
        vr = et / tv
        return {
            "eigenvalues": et.tolist(),
            "explained_variance_ratio": vr.tolist(),
            "cumulative_variance": np.cumsum(vr).tolist(),
            "factor_loadings": ev.tolist(),
            "factor_returns": (Rc @ ev).tolist(),
            "n_factors": n_factors,
        }

    def arbitrage_test(self, factor_loadings, factor_returns, risk_free_rate=0.02,
                       threshold=0.01):
        """Test for approximate arbitrage opportunities.

        Constructs zero-investment portfolio; flags if expected return > threshold.

        Parameters
        ----------
        factor_loadings : array-like, shape (n_assets, n_factors)
        factor_returns : array-like, shape (n_obs, n_factors)
        risk_free_rate : float
        threshold : float (default 0.01)

        Returns
        -------
        dict with has_arbitrage, max_expected_return, arbitrage_weights,
        factor_premia, n_tested_assets.
        """
        B = np.asarray(factor_loadings, dtype=np.float64)
        F = np.asarray(factor_returns, dtype=np.float64)
        if B.ndim == 1:
            B = B.reshape(-1, 1)
        na = B.shape[0]
        if F.shape[0] == 0:
            raise ValueError("Empty factor returns.")
        lam = np.mean(F, axis=0)
        er = B @ lam
        proj = er - np.mean(er)
        w = np.zeros(na)
        lm, sm = proj > 0, proj < 0
        if np.any(lm) and np.any(sm):
            ls, ss = np.sum(proj[lm]), np.abs(np.sum(proj[sm]))
            sc = min(ls, ss)
            if sc > 0:
                w[lm] = proj[lm] / ls * sc
                w[sm] = proj[sm] / ss * sc
        pr = float(np.dot(w, er)) * 252
        return {
            "has_arbitrage": bool(pr > threshold),
            "max_expected_return": pr,
            "arbitrage_weights": w.tolist(),
            "factor_premia": lam.tolist(),
            "n_tested_assets": na,
        }


# =========================================================================== #
#  3. EMHTester                                                              #
# =========================================================================== #
class EMHTester:
    """Efficient Market Hypothesis test battery.

    Methods: runs_test, autocorrelation_test, variance_ratio_test,
    engle_granger_adf, half_life_of_mean_reversion, summary.
    """

    def runs_test(self, returns):
        """Wald-Wolfowitz runs test for randomness.

        Parameters
        ----------
        returns : array-like, shape (n,)

        Returns
        -------
        dict with n_runs, expected_runs, std_runs, z_statistic, p_value, is_random.
        """
        r = np.asarray(returns, dtype=np.float64).ravel()
        if r.size < 2:
            raise ValueError("Need >=2 obs.")
        sgn = np.sign(r); sgn[sgn == 0] = 1
        runs = 1 + int(np.sum(np.diff(sgn) != 0))
        n_pos = int(np.sum(sgn > 0))
        n_neg = int(np.sum(sgn < 0))
        n = n_pos + n_neg
        if n_pos == 0 or n_neg == 0:
            return {"n_runs": runs, "expected_runs": float(n),
                    "std_runs": 0.0, "z_statistic": np.nan,
                    "p_value": np.nan, "is_random": False}
        exp = 2.0 * n_pos * n_neg / n + 1.0
        vn = 2.0 * n_pos * n_neg * (2.0 * n_pos * n_neg - n)
        vd = n * n * (n - 1)
        var = vn / vd if vd > 0 else 0.0
        std = np.sqrt(var) if var > 0 else 0.0
        z = (runs - exp) / std if std > 0 else 0.0
        p = float(2.0 * stats.norm.sf(abs(z)))
        return {"n_runs": runs, "expected_runs": exp, "std_runs": std,
                "z_statistic": z, "p_value": p, "is_random": bool(p > 0.05)}

    def autocorrelation_test(self, returns, max_lag=20):
        """Ljung-Box Q-test for serial correlation.

        Parameters
        ----------
        returns : array-like
        max_lag : int (default 20)

        Returns
        -------
        dict with lb_statistic, p_value, is_independent, autocorrelations.
        """
        r = np.asarray(returns, dtype=np.float64).ravel()
        if r.size < max_lag + 1:
            raise ValueError(f"Need >= {max_lag+1} obs.")
        mu, vr, n = np.mean(r), np.var(r, ddof=0), len(r)
        if vr < 1e-16:
            return {"lb_statistic": np.nan, "p_value": np.nan,
                    "is_independent": True,
                    "autocorrelations": [0.0] * max_lag}
        acf = []
        for lag in range(1, max_lag + 1):
            acf.append(float(np.mean((r[:n-lag]-mu)*(r[lag:]-mu)) / vr))
        q = sum(rho**2 / (n-k) for k, rho in enumerate(acf, 1)) * n * (n+2)
        pv = float(1.0 - stats.chi2.cdf(q, max_lag))
        return {"lb_statistic": float(q), "p_value": pv,
                "is_independent": bool(pv > 0.05), "autocorrelations": acf}

    def variance_ratio_test(self, returns, holding_periods=None):
        """Lo-Mackinlay variance ratio test.

        Parameters
        ----------
        returns : array-like
        holding_periods : list[int] (default [2,4,8,16])

        Returns
        -------
        dict with 'results' (list per period) and 'overall_is_random_walk'.
        """
        r = np.asarray(returns, dtype=np.float64).ravel()
        if holding_periods is None:
            holding_periods = [2, 4, 8, 16]
        n = len(r)
        if n < max(holding_periods) + 2:
            raise ValueError("Not enough observations.")
        mu = np.mean(r)
        v1 = np.sum((r[1:] - mu)**2) / (n - 1)
        if v1 < 1e-16:
            return {"results": [], "overall_is_random_walk": False}
        rw, results = True, []
        for q in holding_periods:
            nq = n - q
            if nq <= 0:
                continue
            rq = np.array([np.sum(r[i:i+q]) for i in range(nq)])
            vq = np.sum((rq - q*mu)**2) / (nq - 1)
            vr = vq / (q * v1)
            m2 = sum(2.0*(q-j)/q * (np.sum((r[j:]-mu)*(r[:n-j]-mu))
                      / max(np.sum((r-mu)**2), 1e-300)) for j in range(1, q))
            z = (vr-1.0)/np.sqrt(abs(m2)) if m2 != 0 else np.nan
            pv = float(2*stats.norm.sf(abs(z))) if not np.isnan(z) else np.nan
            isw = bool(pv > 0.05) if not np.isnan(pv) else False
            if not isw:
                rw = False
            results.append({"holding_period": q, "variance_ratio": float(vr),
                            "z_statistic": None if np.isnan(z) else float(z),
                            "p_value": None if np.isnan(pv) else float(pv),
                            "is_random_walk": isw})
        return {"results": results, "overall_is_random_walk": rw}

    def engle_granger_adf(self, prices, max_lag=None):
        """Augmented Dickey-Fuller test. H0: unit root.

        Parameters
        ----------
        prices : array-like
        max_lag : int (Schwert 1989 default if None)

        Returns
        -------
        dict with adf_statistic, p_value, used_lag, is_stationary, critical_values.
        """
        p = np.asarray(prices, dtype=np.float64).ravel()
        n = len(p)
        if n < 10:
            raise ValueError("Need >=10 price obs.")
        if max_lag is None:
            max_lag = max(1, min(int(np.ceil(12*(n/100)**0.25)), n // 3))
        dy, yl = np.diff(p), p[:-1]
        best_aic, best = np.inf, None
        for lag in range(max_lag + 1):
            T = n - 1 - lag
            if T < 3:
                continue
            Y = dy[lag:]
            cols = [np.ones(T), yl[lag:]]
            for j in range(1, lag + 1):
                cols.append(dy[lag-j: lag-j+T])
            X = np.column_stack(cols)
            try:
                o = _ols(Y, X)
                ssr = float(np.sum(o["residuals"]**2))
                aic = T * np.log(max(ssr/T, 1e-300)) + 2*X.shape[1]
                if aic < best_aic:
                    best_aic = aic
                    best = {"g_t": float(o["t_values"][1]), "lag": lag, "T": T}
            except Exception:
                continue
        if best is None:
            raise RuntimeError("ADF failed for all lags.")
        T = best["T"]
        crit = {"1%": -3.43-6.0/T-25.0/T**2,
                "5%": -2.86-4.1/T-13.5/T**2,
                "10%": -2.57-3.3/T-7.5/T**2}
        s = best["g_t"]
        vals = sorted(crit.values(), reverse=True)
        probs = [0.01, 0.05, 0.10]
        if s <= vals[0]: pv = 0.005
        elif s >= vals[-1]: pv = 0.20
        else:
            pv = 0.10
            for i in range(len(vals)-1):
                if vals[i] >= s >= vals[i+1]:
                    f = (vals[i]-s)/(vals[i]-vals[i+1]+1e-30)
                    pv = probs[i] + f*(probs[i+1]-probs[i]); break
        return {"adf_statistic": s, "p_value": pv, "used_lag": best["lag"],
                "is_stationary": bool(pv < 0.05), "critical_values": crit}

    def half_life_of_mean_reversion(self, prices):
        """Ornstein-Uhlenbeck half-life: dy = a + lam*y_{t-1} + e.

        Parameters
        ----------
        prices : array-like

        Returns
        -------
        dict with half_life, lambda_, alpha, r_squared, is_mean_reverting.
        """
        p = np.asarray(prices, dtype=np.float64).ravel()
        if p.size < 10:
            raise ValueError("Need >=10 price obs.")
        dy, yl = np.diff(p), p[:-1]
        o = _ols(dy, np.column_stack([np.ones(len(dy)), yl]))
        a = float(o["coefficients"][0])
        lam = float(o["coefficients"][1])
        lp = float(o["p_values"][1])
        hl = np.nan; mr = False
        if lam < 0:
            hl = -np.log(2.0) / lam
            mr = bool(lp < 0.05)
        return {"half_life": hl, "lambda_": lam, "alpha": a,
                "r_squared": float(o["r_squared"]), "is_mean_reverting": mr}

    def summary(self, returns, prices):
        """Full EMH test battery.

        Parameters
        ----------
        returns : array-like
        prices : array-like

        Returns
        -------
        dict with individual test results, overall_verdict (efficient/mixed/
        inefficient), inefficiency_signals, total_tests.
        """
        r, adf, hl = self.runs_test(returns), self.engle_granger_adf(prices), \
            self.half_life_of_mean_reversion(prices)
        ac, vr = self.autocorrelation_test(returns), self.variance_ratio_test(returns)
        sig = sum([not r["is_random"], not ac["is_independent"],
                   not vr["overall_is_random_walk"], adf["is_stationary"],
                   hl["is_mean_reverting"]])
        f = sig / 5.0
        v = "efficient" if f <= 0.2 else ("mixed" if f <= 0.6 else "inefficient")
        return {"runs_test": r, "autocorrelation_test": ac,
                "variance_ratio_test": vr, "adf_test": adf,
                "half_life": hl, "overall_verdict": v,
                "inefficiency_signals": sig, "total_tests": 5}


# =========================================================================== #
#  4. AltmanZScore                                                           #
# =========================================================================== #
class AltmanZScore:
    """Altman Z-Score bankruptcy prediction (1968, Z', Z'').

    Methods: manufacturing, private_non_manufacturing, emerging_markets,
    interpret, bond_equivalent, discriminant_analysis.
    """

    def manufacturing(self, wc_ta, re_ta, ebit_ta, mv_de, sales_ta):
        """Original Z-Score for public manufacturing firms.

        Z = 1.2*WC/TA + 1.4*RE/TA + 3.3*EBIT/TA + 0.6*MV/DE + 1.0*Sales/TA

        Returns dict with z_score, components, model_type.
        """
        z = 1.2*wc_ta + 1.4*re_ta + 3.3*ebit_ta + 0.6*mv_de + 1.0*sales_ta
        return {"z_score": z, "components": {"wc_ta": wc_ta, "re_ta": re_ta,
                "ebit_ta": ebit_ta, "mv_de": mv_de, "sales_ta": sales_ta},
                "model_type": "manufacturing"}

    def private_non_manufacturing(self, wc_ta, re_ta, ebit_ta, mv_de, sales_ta):
        """Z'-Score for private non-manufacturing firms.

        Z' = 6.56*WC/TA + 3.26*RE/TA + 6.72*EBIT/TA + 1.05*MV/DE + 3.25

        Returns dict with z_score, components, model_type.
        """
        z = 6.56*wc_ta + 3.26*re_ta + 6.72*ebit_ta + 1.05*mv_de + 3.25
        return {"z_score": z, "components": {"wc_ta": wc_ta, "re_ta": re_ta,
                "ebit_ta": ebit_ta, "mv_de": mv_de},
                "model_type": "private_non_manufacturing"}

    def emerging_markets(self, wc_ta, re_ta, ebit_ta, book_de, sales_ta):
        """Z''-Score for emerging markets.

        Z'' = 6.56*WC/TA + 3.26*RE/TA + 6.72*EBIT/TA + 1.05*Book/DE + 3.25

        Returns dict with z_score, components, model_type.
        """
        z = 6.56*wc_ta + 3.26*re_ta + 6.72*ebit_ta + 1.05*book_de + 3.25
        return {"z_score": z, "components": {"wc_ta": wc_ta, "re_ta": re_ta,
                "ebit_ta": ebit_ta, "book_de": book_de, "sales_ta": sales_ta},
                "model_type": "emerging_markets"}

    def interpret(self, z_score, model_type="manufacturing"):
        """Risk zone classification.

        Parameters
        ----------
        z_score : float
        model_type : str (manufacturing / private_non_manufacturing / emerging_markets)

        Returns dict with z_score, zone (Safe/Grey/Distress), description, model_type.
        """
        if model_type == "manufacturing":
            if z_score >= 2.99:
                z, d = "Safe", "Low bankruptcy probability (safe zone)."
            elif z_score >= 1.81:
                z, d = "Grey", "Moderate distress risk (grey zone)."
            else:
                z, d = "Distress", "High bankruptcy probability (distress zone)."
        else:
            if z_score >= 2.60:
                z, d = "Safe", "Low bankruptcy probability (Z'/Z'' model)."
            elif z_score >= 1.10:
                z, d = "Grey", "Moderate distress risk (Z'/Z'' model)."
            else:
                z, d = "Distress", "High bankruptcy probability (Z'/Z'' model)."
        return {"z_score": z_score, "zone": z, "description": d,
                "model_type": model_type}

    def bond_equivalent(self, z_score, model_type="manufacturing"):
        """Map Z-Score to credit rating and default probability.

        Parameters
        ----------
        z_score : float
        model_type : str

        Returns dict with z_score, model_type, credit_rating_sp,
        credit_rating_moodys, approx_default_probability, rating_outlook.
        """
        if model_type == "manufacturing":
            dp = 1.0 / (1.0 + np.exp(-(-4.5 + 1.5 * z_score)))
            if z_score >= 3.0:
                sp, my, ol = "AAA/AA+", "Aaa/Aa1", "Stable"
            elif z_score >= 2.7:
                sp, my, ol = "AA/AA-", "Aa2/Aa3", "Stable"
            elif z_score >= 2.3:
                sp, my, ol = "A+/A", "A1/A2", "Stable"
            elif z_score >= 1.8:
                sp, my, ol = "BBB+/BBB", "Baa1/Baa2", "Watch Negative"
            else:
                sp, my, ol = "BB+ or below", "Ba1 or below", "Negative"
        else:
            dp = 1.0 / (1.0 + np.exp(-(-3.0 + 2.0 * z_score)))
            if z_score >= 3.5:
                sp, my, ol =                 "AAA/AA+", "Aaa/Aa1", "Stable"
            elif z_score >= 2.6:
                sp, my, ol = "A/BBB+", "A2/Baa1", "Stable"
            elif z_score >= 1.1:
                sp, my, ol = "BBB-/BB+", "Ba2/Ba3", "Watch Negative"
            else:
                sp, my, ol = "BB or below", "B1 or below", "Negative"
        return {
            "z_score": z_score, "model_type": model_type,
            "credit_rating_sp": sp, "credit_rating_moodys": my,
            "approx_default_probability": float(dp), "rating_outlook": ol,
        }

    def discriminant_analysis(self, financial_data, default_flags):
        """Stepwise discriminant analysis to derive custom Z-Score coefficients.

        Parameters
        ----------
        financial_data : array-like, shape (n_firms, n_variables)
            Financial ratios for each firm.
        default_flags : array-like, shape (n_firms,)
            1 = defaulted, 0 = solvent.

        Returns
        -------
        dict with coefficients, intercept, discriminant_direction, threshold,
        classification_accuracy, confusion_matrix, n_variables, n_firms.
        """
        X = np.asarray(financial_data, dtype=np.float64)
        y = np.asarray(default_flags, dtype=np.float64).ravel()
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        n, p = X.shape
        if n <= p + 1:
            raise ValueError("Need more firms than variables.")
        g0, g1 = y == 0, y == 1
        n0, n1 = max(int(np.sum(g0)), 1), max(int(np.sum(g1)), 1)
        m0 = np.mean(X[g0], axis=0) if np.any(g0) else np.zeros(p)
        m1 = np.mean(X[g1], axis=0) if np.any(g1) else np.zeros(p)
        Sw = (np.cov(X[g0].T, bias=True) * (n0 - 1) / n
              + np.cov(X[g1].T, bias=True) * (n1 - 1) / n)
        Sw += np.eye(p) * 1e-8
        try:
            w = linalg.solve(Sw, m1 - m0, assume_a="pos")
        except linalg.LinAlgError:
            w = np.linalg.lstsq(Sw, m1 - m0, rcond=None)[0]
        scores = X @ w
        s0 = np.mean(scores[g0]) if np.any(g0) else 0.0
        s1 = np.mean(scores[g1]) if np.any(g1) else 0.0
        threshold = (s0 + s1) / 2.0
        preds = (scores >= threshold).astype(float)
        acc = float(np.mean(preds == y))
        tp = int(np.sum((preds == 1) & (y == 1)))
        fp = int(np.sum((preds == 1) & (y == 0)))
        fn = int(np.sum((preds == 0) & (y == 1)))
        tn = int(np.sum((preds == 0) & (y == 0)))
        X_std = (X - np.mean(X, axis=0)) / (np.std(X, axis=0, ddof=1) + 1e-10)
        Xs = np.column_stack([np.ones(n), X_std])
        try:
            ols_res = _ols(y, Xs)
            coeffs = ols_res["coefficients"]
            intercept = float(coeffs[0])
            disc_coeffs = coeffs[1:].tolist()
        except Exception:
            disc_coeffs = w.tolist()
            intercept = float(-threshold)
        return {
            "coefficients": disc_coeffs, "intercept": intercept,
            "discriminant_direction": w.tolist(),
            "threshold": float(threshold),
            "classification_accuracy": acc,
            "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
            "n_variables": p, "n_firms": n,
        }


# =========================================================================== #
#  5. BeneishMScore                                                           #
# =========================================================================== #
class BeneishMScore:
    """Beneish M-Score earnings manipulation detection (1999).

    Methods: m_score, days_sales_inventory, gross_margin_index,
    asset_quality_index, sales_growth_index, depreciation_index,
    sga_index, leverage_index, total_accruals_to_assets,
    probability_of_manipulation, detect_from_financials.
    """

    def m_score(self, dsri, gmri, aqi, sgi, depi, sgai, tgai, lvgi, tata):
        """Compute 8-component Beneish M-Score.

        M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
            + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI

        Parameters
        ----------
        dsri, gmri, aqi, sgi, depi, sgai, tgai, lvgi, tata : float

        Returns
        -------
        dict with m_score, components, is_manipulation_likely (M > -1.78).
        """
        m = (-4.84 + 0.920 * dsri + 0.528 * gmri + 0.404 * aqi
             + 0.892 * sgi + 0.115 * depi - 0.172 * sgai
             + 4.679 * tata - 0.327 * lvgi)
        return {
            "m_score": m,
            "components": {
                "dsri": dsri, "gmri": gmri, "aqi": aqi, "sgi": sgi,
                "depi": depi, "sgai": sgai, "tgai": tgai, "lvgi": lvgi,
                "tata": tata,
            },
            "is_manipulation_likely": bool(m > -1.78),
        }

    def days_sales_inventory(self, current_dsi, prior_dsi):
        """DSRI = Days Sales in Receivables Index.

        DSRI = (DSR_t / DSR_{t-1}).  Values > 1 are suspicious.

        Parameters
        ----------
        current_dsi, prior_dsi : float

        Returns
        -------
        dict with dsri, description.
        """
        if abs(prior_dsi) < 1e-12:
            return {"dsri": np.nan,
                    "description": "Prior DSI is zero; index undefined."}
        idx = current_dsi / prior_dsi
        desc = ("Receivables growing faster than sales" if idx > 1.0
                else "Normal or declining receivables")
        return {"dsri": idx, "description": desc}

    def gross_margin_index(self, current_gm, prior_gm):
        """GMI = Gross Margin Index.

        GMI = GM_{t-1} / GM_t.  Values > 1 indicate deteriorating margins.

        Parameters
        ----------
        current_gm, prior_gm : float

        Returns
        -------
        dict with gmi, description.
        """
        if abs(current_gm) < 1e-12:
            return {"gmi": np.nan,
                    "description": "Current GM is zero; index undefined."}
        idx = prior_gm / current_gm
        desc = ("Deteriorating gross margins" if idx > 1.0
                else "Stable or improving margins")
        return {"gmi": idx, "description": desc}

    def asset_quality_index(self, current_ta, current_ppe, prior_ta, prior_ppe):
        """AQI = Asset Quality Index.

        AQI = (1 - PPE_t/TA_t) / (1 - PPE_{t-1}/TA_{t-1}).
        Higher values indicate more intangible / non-current assets.

        Parameters
        ----------
        current_ta, current_ppe, prior_ta, prior_ppe : float

        Returns
        -------
        dict with aqi, description.
        """
        if prior_ta == 0:
            return {"aqi": np.nan, "description": "Prior TA is zero."}
        curr_nca = 1.0 - current_ppe / current_ta if current_ta != 0 else 1.0
        prior_nca = 1.0 - prior_ppe / prior_ta
        if abs(prior_nca) < 1e-12:
            return {"aqi": np.nan,
                    "description": "Prior non-current assets ~ 0."}
        idx = curr_nca / prior_nca
        desc = ("Increasing share of soft assets" if idx > 1.0
                else "Stable or decreasing soft assets")
        return {"aqi": idx, "description": desc}

    def sales_growth_index(self, current_sales, prior_sales):
        """SGI = Sales Growth Index.

        SGI = Sales_t / Sales_{t-1}.  High growth may pressure earnings mgmt.

        Parameters
        ----------
        current_sales, prior_sales : float

        Returns
        -------
        dict with sgi, description.
        """
        if abs(prior_sales) < 1e-12:
            return {"sgi": np.nan, "description": "Prior sales ~ 0."}
        idx = current_sales / prior_sales
        desc = ("Rapid sales growth" if idx > 1.15
                else "Normal sales growth")
        return {"sgi": idx, "description": desc}

    def depreciation_index(self, current_dp, current_ppe, prior_dp, prior_ppe):
        """DEPI = Depreciation Index.

        DEPI = (DP_{t-1}/PPE_{t-1}) / (DP_t/PPE_t).
        > 1 signals slowing depreciation.

        Parameters
        ----------
        current_dp, current_ppe, prior_dp, prior_ppe : float

        Returns
        -------
        dict with depi, description.
        """
        curr_rate = current_dp / current_ppe if current_ppe != 0 else np.nan
        prior_rate = prior_dp / prior_ppe if prior_ppe != 0 else np.nan
        if np.isnan(curr_rate) or abs(curr_rate) < 1e-12:
            return {"depi": np.nan,
                    "description": "Current depreciation rate undefined."}
        if np.isnan(prior_rate):
            return {"depi": np.nan,
                    "description": "Prior depreciation rate undefined."}
        idx = prior_rate / curr_rate
        desc = ("Declining depreciation rate" if idx > 1.0
                else "Stable or increasing depreciation")
        return {"depi": idx, "description": desc}

    def sga_index(self, current_sga, current_sales, prior_sga, prior_sales):
        """SGAI = SGA Expense Index.

        SGAI = (SGA_t/Sales_t) / (SGA_{t-1}/Sales_{t-1}).
        > 1 suggests declining efficiency.

        Parameters
        ----------
        current_sga, current_sales, prior_sga, prior_sales : float

        Returns
        -------
        dict with sgai, description.
        """
        cs = current_sga / current_sales if current_sales != 0 else np.nan
        ps = prior_sga / prior_sales if prior_sales != 0 else np.nan
        if np.isnan(cs) or np.isnan(ps) or abs(ps) < 1e-12:
            return {"sgai": np.nan, "description": "SGA ratio undefined."}
        idx = cs / ps
        desc = ("Declining SGA efficiency" if idx > 1.0
                else "Stable or improving SGA efficiency")
        return {"sgai": idx, "description": desc}

    def leverage_index(self, current_ltd, current_mve, prior_ltd, prior_mve):
        """LVGI = Leverage Index.

        LVGI = (LTD_t/MVE_t) / (LTD_{t-1}/MVE_{t-1}).
        > 1 signals increasing leverage.

        Parameters
        ----------
        current_ltd, current_mve, prior_ltd, prior_mve : float

        Returns
        -------
        dict with lvgi, description.
        """
        cl = current_ltd / current_mve if current_mve != 0 else np.nan
        pl = prior_ltd / prior_mve if prior_mve != 0 else np.nan
        if np.isnan(cl) or np.isnan(pl) or abs(pl) < 1e-12:
            return {"lvgi": np.nan, "description": "Leverage ratio undefined."}
        idx = cl / pl
        desc = ("Increasing leverage" if idx > 1.0
                else "Stable or decreasing leverage")
        return {"lvgi": idx, "description": desc}

    def total_accruals_to_assets(self, net_income, cfo, total_assets):
        """TATA = Total Accruals to Total Assets.

        TATA = (NI - CFO) / TA.  Positive = earnings > cash flow.

        Parameters
        ----------
        net_income, cfo, total_assets : float

        Returns
        -------
        dict with tata, description.
        """
        if abs(total_assets) < 1e-12:
            return {"tata": np.nan, "description": "Total assets ~ 0."}
        tata = (net_income - cfo) / total_assets
        desc = ("Positive accruals (aggressive accounting)" if tata > 0
                else "Conservative or normal accruals")
        return {"tata": tata, "description": desc}

    def probability_of_manipulation(self, m_score):
        """P(manipulation) = 1 - exp(-7.89 + 2.53 * M-Score).

        Parameters
        ----------
        m_score : float

        Returns
        -------
        dict with m_score, probability, risk_level.
        """
        p = 1.0 - np.exp(-7.89 + 2.53 * m_score)
        p = float(np.clip(p, 0.0, 1.0))
        if p > 0.5:
            risk = "High"
        elif p > 0.2:
            risk = "Moderate"
        else:
            risk = "Low"
        return {"m_score": m_score, "probability": p, "risk_level": risk}

    def detect_from_financials(self, financials):
        """Compute all 8 Beneish component indices + M-Score + P(manipulation).

        Parameters
        ----------
        financials : dict with keys:
            current_receivables_days, prior_receivables_days,
            current_gross_margin, prior_gross_margin,
            current_total_assets, current_ppe,
            prior_total_assets, prior_ppe,
            current_sales, prior_sales,
            current_depreciation, current_sga,
            prior_depreciation, prior_sga,
            current_ltd, current_mve,
            prior_ltd, prior_mve,
            net_income, cfo

        Returns
        -------
        dict with dsri, gmri, aqi, sgi, depi, sgai, lvgi, tata,
        m_score, probability_of_manipulation, is_manipulation_likely,
        risk_level, all component details.
        """
        f = financials
        dsri_r = self.days_sales_inventory(f["current_receivables_days"],
                                            f["prior_receivables_days"])
        gmri_r = self.gross_margin_index(f["current_gross_margin"],
                                           f["prior_gross_margin"])
        aqi_r = self.asset_quality_index(f["current_total_assets"], f["current_ppe"],
                                           f["prior_total_assets"], f["prior_ppe"])
        sgi_r = self.sales_growth_index(f["current_sales"], f["prior_sales"])
        depi_r = self.depreciation_index(f["current_depreciation"], f["current_ppe"],
                                          f["prior_depreciation"], f["prior_ppe"])
        sgai_r = self.sga_index(f["current_sga"], f["current_sales"],
                                f["prior_sga"], f["prior_sales"])
        lvgi_r = self.leverage_index(f["current_ltd"], f["current_mve"],
                                     f["prior_ltd"], f["prior_mve"])
        tata_r = self.total_accruals_to_assets(f["net_income"], f["cfo"],
                                               f["current_total_assets"])

        dsri_v = dsri_r["dsri"]
        gmri_v = gmri_r["gmi"]
        aqi_v = aqi_r["aqi"]
        sgi_v = sgi_r["sgi"]
        depi_v = depi_r["depi"]
        sgai_v = sgai_r["sgai"]
        lvgi_v = lvgi_r["lvgi"]
        tata_v = tata_r["tata"]
        tgai_v = 0.0  # placeholder; not used directly in M-score formula

        # Fill NaN with 1.0 (neutral) for score computation
        def _safe(v):
            return v if not np.isnan(v) else 1.0

        ms = self.m_score(_safe(dsri_v), _safe(gmri_v), _safe(aqi_v),
                          _safe(sgi_v), _safe(depi_v), _safe(sgai_v),
                          tgai_v, _safe(lvgi_v), _safe(tata_v))
        prob = self.probability_of_manipulation(ms["m_score"])

        return {
            "dsri": dsri_r, "gmri": gmri_r, "aqi": aqi_r, "sgi": sgi_r,
            "depi": depi_r, "sgai": sgai_r, "lvgi": lvgi_r, "tata": tata_r,
            "m_score": ms["m_score"],
            "probability_of_manipulation": prob["probability"],
            "is_manipulation_likely": ms["is_manipulation_likely"],
            "risk_level": prob["risk_level"],
            "component_values": {
                "dsri": dsri_v, "gmri": gmri_v, "aqi": aqi_v, "sgi": sgi_v,
                "depi": depi_v, "sgai": sgai_v, "lvgi": lvgi_v, "tata": tata_v,
            },
        }
