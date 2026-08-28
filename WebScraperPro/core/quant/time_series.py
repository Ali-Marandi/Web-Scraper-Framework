"""
time_series.py — Comprehensive time-series analysis module for Quantitative Finance Engine.

Implements ARIMA, SARIMA, GARCH/EGARCH, VAR, Cointegration, and VaR models
using ONLY numpy, pandas, and scipy for maximum PyInstaller/Windows compatibility.

No dependency on statsmodels, arch, or sklearn.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import optimize, stats, linalg


# ============================================================================
# Utility helpers
# ============================================================================

def _ensure_array(x, name="values"):
    """Convert input to a flat float64 numpy array."""
    x = np.asarray(x, dtype=np.float64).ravel()
    if len(x) < 5:
        raise ValueError(f"{name} must have at least 5 observations (got {len(x)}).")
    return x


def _diff(x, d=1):
    """Return the d-th order difference of array x."""
    out = x.copy()
    for _ in range(d):
        out = np.diff(out)
    return out


def _lag_matrix(x, max_lag):
    """Build a lagged matrix where column k is x shifted by k+1.
    Returns (y, X) where y = x[max_lag:] and X has shape (n-max_lag, max_lag)."""
    n = len(x)
    X = np.column_stack([x[max_lag - (k + 1): n - (k + 1)] for k in range(max_lag)])
    y = x[max_lag:]
    return y, X


def _ols(y, X, add_intercept=True):
    """Ordinary least-squares. Returns (coeffs, residuals, y_fitted)."""
    if add_intercept:
        X = np.column_stack([np.ones(len(y)), X])
    try:
        XtX = X.T @ X
        XtY = X.T @ y
        coeffs = np.linalg.solve(XtX, XtY)
    except np.linalg.LinAlgError:
        coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_fit = X @ coeffs
    resid = y - y_fit
    return coeffs, resid, y_fit


def _adf_statistic(x, max_lag=10):
    """Compute the Augmented Dickey-Fuller test statistic and approximate p-value.

    Returns dict with 'adf', 'pvalue', 'used_lag'.
    """
    n = len(x)
    if n < max_lag + 5:
        max_lag = max(1, n // 3)

    # Select lag by AIC
    best_aic, best_lag, best_stat = np.inf, 1, 0.0
    for lag in range(1, max_lag + 1):
        dy = np.diff(x)
        y_dep = dy[lag:]
        X_reg = np.column_stack([
            x[lag: -1],
            np.column_stack([dy[lag - (k + 1): n - (k + 1) - 1] for k in range(lag)])
        ])
        if X_reg.shape[0] < X_reg.shape[1] + 1:
            continue
        coefs, resid, _ = _ols(y_dep, X_reg, add_intercept=True)
        sigma2 = np.mean(resid ** 2)
        aic = len(y_dep) * np.log(sigma2) + 2 * (X_reg.shape[1] + 1)
        if aic < best_aic:
            best_aic, best_lag = aic, lag
            best_stat = coefs[1] / (np.sqrt(sigma2) * np.sqrt(np.diag(np.linalg.pinv(X_reg.T @ X_reg)))[1])

    # Approximate p-value using MacKinnon-style critical values
    n_obs = n - best_lag - 1
    stat = best_stat
    # Simple interpolation of Dickey-Fuller critical values
    crit = {"1%": -3.43, "5%": -2.86, "10%": -2.57}
    if stat < crit["1%"]:
        pval = 0.01
    elif stat < crit["5%"]:
        pval = 0.05
    elif stat < crit["10%"]:
        pval = 0.10
    else:
        pval = 0.50  # non-stationary region, approximate
    return {"adf": float(stat), "pvalue": float(pval), "used_lag": int(best_lag)}


# ============================================================================
# 1. ARIMA
# ============================================================================

class ARIMA:
    """Auto-Regressive Integrated Moving Average model.

    Parameters
    ----------
    order : tuple of (p, d, q)
        AR order, differencing order, MA order.

    Notes
    -----
    Fitting uses MLE via scipy.optimize.minimize. Falls back to
    method-of-moments / OLS if optimisation fails.
    """

    def __init__(self, order=(5, 1, 2)):
        self.order = order
        self.p, self.d, self.q = order
        self._fitted = False
        # Storage for fitted coefficients
        self.ar_coefs_ = None
        self.ma_coefs_ = None
        self.sigma2_ = None
        self.aic_ = None
        self.bic_ = None
        self._y_diff = None  # differenced series used for fitting

    # ------------------------------------------------------------------
    def fit(self, values, order=None):
        """Fit the ARIMA model via MLE.

        Parameters
        ----------
        values : array-like
            1-D time series.
        order : tuple or None
            Override (p, d, q) for this fit.

        Returns
        -------
        dict with keys: ar_coefs, ma_coefs, sigma2, aic, bic, n_obs, log_likelihood, method
        """
        if order is not None:
            self.order = order
            self.p, self.d, self.q = order

        y = _ensure_array(values, "values")
        n = len(y)

        # 1. Differencing
        y_diff = _diff(y, self.d)
        n_diff = len(y_diff)
        self._y_diff = y_diff
        self._y_orig = y

        # 2. Initial estimates via OLS on AR part (ignoring MA for speed)
        max_lag = max(self.p, 1)
        if n_diff < max_lag + 2:
            # Fallback: not enough data for the requested order
            self._fitted = True
            return self._result_dict(y_diff, "ols_fallback")

        y_dep, X_ar = _lag_matrix(y_diff, self.p)
        ar_init, resid, _ = _ols(y_dep, X_ar, add_intercept=False)

        # MA initial guess via inverted AR residuals heuristic
        if self.q > 0:
            r_lag = min(self.q, len(resid) - 1)
            y_ma_dep = resid[r_lag:]
            X_ma = np.column_stack([resid[r_lag - (k + 1): len(resid) - (k + 1)] for k in range(r_lag)])
            if X_ma.shape[0] > X_ma.shape[1]:
                ma_init, _, _ = _ols(y_ma_dep, X_ma, add_intercept=False)
            else:
                ma_init = np.zeros(self.q)
            if len(ma_init) < self.q:
                ma_init = np.concatenate([ma_init, np.zeros(self.q - len(ma_init))])
        else:
            ma_init = np.array([])

        # 3. MLE optimisation
        params0 = np.concatenate([ar_init[:self.p], ma_init[:self.q], [np.var(resid)]])
        bounds = [(None, None)] * (self.p + self.q) + [(1e-12, None)]

        method_used = "mle"
        try:
            result = optimize.minimize(
                self._neg_log_likelihood, params0,
                args=(y_diff, self.p, self.q),
                method="L-BFGS-B", bounds=bounds,
                options={"maxiter": 500, "ftol": 1e-8}
            )
            if not result.success and np.isfinite(result.fun):
                # Try Nelder-Mead as fallback
                result2 = optimize.minimize(
                    self._neg_log_likelihood, params0,
                    args=(y_diff, self.p, self.q),
                    method="Nelder-Mead",
                    options={"maxiter": 2000, "xatol": 1e-6}
                )
                if np.isfinite(result2.fun) and result2.fun < result.fun:
                    result = result2
                    method_used = "mle_neldermead"
            params_opt = result.x
        except Exception:
            params_opt = params0
            method_used = "ols_fallback"

        self.ar_coefs_ = params_opt[:self.p]
        self.ma_coefs_ = params_opt[self.p: self.p + self.q]
        self.sigma2_ = max(params_opt[-1], 1e-12)
        self._fitted = True

        # AIC / BIC
        ll = -self._neg_log_likelihood(params_opt, y_diff, self.p, self.q)
        k = self.p + self.q + 1  # number of estimated params
        self.aic_ = 2 * k - 2 * ll
        self.bic_ = k * np.log(n_diff) - 2 * ll

        return self._result_dict(y_diff, method_used)

    # ------------------------------------------------------------------
    @staticmethod
    def _neg_log_likelihood(params, y, p, q):
        """Negative log-likelihood for ARMA(p, q) process (Gaussian).

        Uses the innovations algorithm to compute one-step-ahead prediction
        errors efficiently.
        """
        n = len(y)
        ar = params[:p]
        ma = params[p: p + q]
        sigma2 = max(params[-1], 1e-12)

        max_lag = max(p, q)
        residuals = np.zeros(n)
        for t in range(max_lag, n):
            # AR component
            ar_term = 0.0
            for i in range(p):
                if t - 1 - i >= 0:
                    ar_term += ar[i] * y[t - 1 - i]
            # MA component
            ma_term = 0.0
            for j in range(q):
                if t - 1 - j >= max_lag:
                    ma_term += ma[j] * residuals[t - 1 - j]
            residuals[t] = y[t] - ar_term - ma_term

        res_use = residuals[max_lag:]
        n_use = len(res_use)
        if n_use == 0 or sigma2 <= 0:
            return 1e12
        ll = -0.5 * n_use * np.log(2 * np.pi * sigma2) - 0.5 * np.sum(res_use ** 2) / sigma2
        return -ll

    # ------------------------------------------------------------------
    def _result_dict(self, y_diff, method):
        ar = self.ar_coefs_ if self.ar_coefs_ is not None else np.array([])
        ma = self.ma_coefs_ if self.ma_coefs_ is not None else np.array([])
        sig2 = self.sigma2_ if self.sigma2_ is not None else np.var(y_diff)
        ll = -self._neg_log_likelihood(
            np.concatenate([ar, ma, [sig2]]), y_diff, self.p, self.q
        ) if self.ar_coefs_ is not None else 0.0
        k = self.p + self.q + 1
        return {
            "ar_coefs": ar.tolist(),
            "ma_coefs": ma.tolist(),
            "sigma2": float(sig2),
            "aic": float(2 * k - 2 * ll) if self.aic_ is None else float(self.aic_),
            "bic": float(k * np.log(len(y_diff)) - 2 * ll) if self.bic_ is None else float(self.bic_),
            "n_obs": int(len(y_diff)),
            "log_likelihood": float(ll),
            "method": method,
            "order": (self.p, self.d, self.q),
        }

    # ------------------------------------------------------------------
    def forecast(self, steps=10):
        """Produce out-of-sample forecasts.

        Returns
        -------
        dict with 'forecast' (array), 'lower' and 'upper' (95 % CI).
        """
        if not self._fitted:
            raise RuntimeError("Model must be fitted before forecasting.")

        y = self._y_orig
        n = len(y)
        y_diff = self._y_diff

        # Extend differenced series
        y_ext = np.concatenate([y, np.full(steps, np.nan)])
        y_diff_ext = np.concatenate([y_diff, np.full(steps, np.nan)])

        ar = self.ar_coefs_
        ma = self.ma_coefs_
        p, q = self.p, self.q
        sigma2 = self.sigma2_

        # Compute residuals on training differenced data
        max_lag = max(p, q)
        resid_train = np.zeros(len(y_diff))
        for t in range(max_lag, len(y_diff)):
            ar_t = sum(ar[i] * y_diff[t - 1 - i] for i in range(p) if t - 1 - i >= 0)
            ma_t = sum(ma[j] * resid_train[t - 1 - j] for j in range(q) if t - 1 - j >= max_lag)
            resid_train[t] = y_diff[t] - ar_t - ma_t

        # Forecast differenced series
        for h in range(steps):
            t = len(y_diff) + h
            ar_t = sum(ar[i] * y_diff_ext[t - 1 - i] for i in range(p))
            ma_t = 0.0  # expected MA error = 0
            y_diff_ext[t] = ar_t + ma_t

        # Integrate back d times
        fc_diff = y_diff_ext[len(y_diff):]
        fc_level = np.empty(steps)
        for h in range(steps):
            val = y[-1] if self.d >= 1 else y[-1]
            for dd in range(self.d):
                idx = len(y_diff) - self.d + dd + h + 1
                if idx <= len(y_diff_ext):
                    val = (y_ext[n - self.d + dd] if h == 0 and dd < self.d else fc_level[h - 1] if h > 0 else val)
                    # Simpler: cumulative sum approach
            # Use cumulative integration
            pass

        # Cumulative integration (undo differencing)
        fc = np.empty(steps)
        if self.d == 0:
            fc = fc_diff
        elif self.d == 1:
            fc = np.cumsum(np.concatenate([[y[-1]], fc_diff]))[1:]
        elif self.d == 2:
            d1 = np.cumsum(np.concatenate([[y_diff[-1] if len(y_diff) > 0 else 0], fc_diff]))[1:]
            fc = np.cumsum(np.concatenate([[y[-1]], d1]))[1:]
        else:
            # General d
            extended = y_diff.tolist() + fc_diff.tolist()
            integrated = extended.copy()
            for _ in range(self.d):
                integrated = np.cumsum(integrated)
            fc = np.array(integrated[len(y_diff):])

        # Prediction intervals (expand with horizon)
        se = np.sqrt(sigma2) * np.sqrt(np.arange(1, steps + 1))
        z95 = 1.96
        return {
            "forecast": fc.tolist(),
            "lower": (fc - z95 * se).tolist(),
            "upper": (fc + z95 * se).tolist(),
            "steps": steps,
            "sigma2": float(sigma2),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def select_order(values, max_p=6, max_d=2, max_q=4):
        """Select best ARIMA order by AIC.

        Returns dict with 'best_order', 'aic', 'all_results' list.
        """
        y = _ensure_array(values)
        best_aic = np.inf
        best_order = (0, 0, 0)
        results = []
        for d in range(max_d + 1):
            yd = _diff(y, d)
            if len(yd) < 10:
                continue
            for p in range(max_p + 1):
                for q in range(max_q + 1):
                    if p + q == 0:
                        continue
                    try:
                        model = ARIMA(order=(p, d, q))
                        res = model.fit(yd, order=(p, 0, q))
                        aic = res["aic"]
                        results.append({"order": (p, d, q), "aic": aic})
                        if aic < best_aic:
                            best_aic = aic
                            best_order = (p, d, q)
                    except Exception:
                        continue
        results.sort(key=lambda r: r["aic"])
        return {
            "best_order": best_order,
            "aic": float(best_aic) if best_aic < np.inf else None,
            "all_results": results[:20],
        }


# ============================================================================
# 2. SARIMA
# ============================================================================

class SARIMA(ARIMA):
    """Seasonal ARIMA  (p,d,q)(P,D,Q,s).

    Extends ARIMA with seasonal differencing, seasonal AR and MA terms.
    """

    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)):
        super().__init__(order=order)
        self.seasonal_order = seasonal_order
        self.P, self.D, self.Q, self.s = seasonal_order

    # ------------------------------------------------------------------
    def fit(self, values, order=None, seasonal_order=None):
        """Fit SARIMA model.

        Returns dict similar to ARIMA.fit with extra seasonal keys.
        """
        if order is not None:
            self.order = order
            self.p, self.d, self.q = order
        if seasonal_order is not None:
            self.seasonal_order = seasonal_order
            self.P, self.D, self.Q, self.s = seasonal_order

        y = _ensure_array(values)
        self._y_orig = y
        n = len(y)

        # Seasonal + regular differencing
        y_ds = _diff(y, self.d)
        y_sds = np.copy(y_ds)
        for _ in range(self.D):
            y_sds = y_sds[self.s:] - y_sds[:-self.s]

        self._y_sds = y_sds
        n_eff = len(y_sds)

        # Total number of AR and MA coefficients
        total_ar = self.p + self.P
        total_ma = self.q + self.Q

        if n_eff < total_ar + total_ma + 5:
            return self._seasonal_result(y_sds, "insufficient_data")

        # Build lagged design matrix (regular + seasonal lags)
        y_dep, X_all = self._build_seasonal_lag_matrix(y_sds, total_ar, total_ma)

        if y_dep is None or len(y_dep) < X_all.shape[1] + 1:
            return self._seasonal_result(y_sds, "insufficient_lags")

        # Initial OLS
        ar_init, resid, _ = _ols(y_dep, X_all[:, :total_ar], add_intercept=False)

        ma_init = np.zeros(total_ma)
        if total_ma > 0 and len(resid) > total_ma:
            r_lag = total_ma
            X_ma = np.column_stack([resid[r_lag - (k + 1): len(resid) - (k + 1)] for k in range(r_lag)])
            if X_ma.shape[0] > X_ma.shape[1]:
                ma_init, _, _ = _ols(resid[r_lag:], X_ma, add_intercept=False)

        # MLE
        params0 = np.concatenate([ar_init, ma_init, [np.var(resid)]])
        bounds = [(None, None)] * (total_ar + total_ma) + [(1e-12, None)]

        method_used = "mle"
        try:
            result = optimize.minimize(
                self._sarma_neg_ll, params0,
                args=(y_sds, total_ar, total_ma, self.s),
                method="L-BFGS-B", bounds=bounds,
                options={"maxiter": 600, "ftol": 1e-8}
            )
            if not result.success:
                result2 = optimize.minimize(
                    self._sarma_neg_ll, params0,
                    args=(y_sds, total_ar, total_ma, self.s),
                    method="Nelder-Mead",
                    options={"maxiter": 3000}
                )
                if np.isfinite(result2.fun) and result2.fun <= result.fun:
                    result = result2
                    method_used = "mle_neldermead"
            params_opt = result.x
        except Exception:
            params_opt = params0
            method_used = "ols_fallback"

        self.ar_coefs_ = params_opt[:total_ar]
        self.ma_coefs_ = params_opt[total_ar: total_ar + total_ma]
        self.sigma2_ = max(params_opt[-1], 1e-12)
        self._fitted = True

        ll = -self._sarma_neg_ll(params_opt, y_sds, total_ar, total_ma, self.s)
        k = total_ar + total_ma + 1
        self.aic_ = 2 * k - 2 * ll
        self.bic_ = k * np.log(n_eff) - 2 * ll

        return self._seasonal_result(y_sds, method_used)

    # ------------------------------------------------------------------
    def _build_seasonal_lag_matrix(self, y, n_ar, n_ma):
        """Build lag matrix with both regular and seasonal lags.

        Regular lags: 1, 2, ..., p ;   Seasonal lags: s, 2s, ..., Ps.
        """
        n = len(y)
        max_regular = self.p
        max_seasonal = self.P * self.s
        max_lag = max(max_regular, max_seasonal, self.q, self.Q * self.s)

        if n <= max_lag + 1:
            return None, None

        # AR lags
        ar_lags = list(range(1, self.p + 1)) + [self.s * (k + 1) for k in range(self.P)]
        ar_lags = sorted(set(ar_lags))

        y_dep = y[max(ar_lags):]
        X = np.column_stack([y[max(ar_lags) - lag: n - lag] for lag in ar_lags])
        return y_dep, X

    # ------------------------------------------------------------------
    @staticmethod
    def _sarma_neg_ll(params, y, n_ar, n_ma, s):
        """Negative log-likelihood for SARMA (after differencing)."""
        n = len(y)
        ar = params[:n_ar]
        ma = params[n_ar: n_ar + n_ma]
        sigma2 = max(params[-1], 1e-12)

        # Determine actual lag positions
        # For simplicity, assume lags = 1,2,...,p for regular, s,2s,... for seasonal
        # This is a simplification; the caller is responsible for ordering.
        max_lag = n_ar  # approximate
        if n_ar > n - 2:
            return 1e12

        residuals = np.zeros(n)
        for t in range(max_lag, n):
            ar_term = sum(ar[i] * y[t - 1 - i] for i in range(n_ar) if t - 1 - i >= 0)
            ma_term = sum(ma[j] * residuals[t - 1 - j] for j in range(n_ma) if t - 1 - j >= max_lag)
            residuals[t] = y[t] - ar_term - ma_term

        r = residuals[max_lag:]
        nr = len(r)
        if nr == 0:
            return 1e12
        ll = -0.5 * nr * np.log(2 * np.pi * sigma2) - 0.5 * np.sum(r ** 2) / sigma2
        return -ll

    # ------------------------------------------------------------------
    def _seasonal_result(self, y_sds, method):
        ar = self.ar_coefs_ if self.ar_coefs_ is not None else np.array([])
        ma = self.ma_coefs_ if self.ma_coefs_ is not None else np.array([])
        sig2 = self.sigma2_ if self.sigma2_ is not None else np.var(y_sds) if len(y_sds) > 0 else 1.0
        return {
            "ar_coefs": ar.tolist(),
            "ma_coefs": ma.tolist(),
            "seasonal_ar_coefs": ar[self.p:].tolist() if len(ar) > self.p else [],
            "seasonal_ma_coefs": ma[self.q:].tolist() if len(ma) > self.q else [],
            "sigma2": float(sig2),
            "aic": float(self.aic_) if self.aic_ is not None else None,
            "bic": float(self.bic_) if self.bic_ is not None else None,
            "n_obs": int(len(y_sds)),
            "method": method,
            "order": (self.p, self.d, self.q),
            "seasonal_order": (self.P, self.D, self.Q, self.s),
        }

    # ------------------------------------------------------------------
    def forecast(self, steps=10):
        """Forecast with seasonal integration.

        Returns dict with 'forecast', 'lower', 'upper'.
        """
        if not self._fitted:
            raise RuntimeError("Model must be fitted first.")

        y_sds = self._y_sds
        n_sds = len(y_sds)
        ar = self.ar_coefs_
        ma = self.ma_coefs_
        total_ar = self.p + self.P
        total_ma = self.q + self.Q
        sigma2 = self.sigma2_

        # Compute training residuals
        resid_train = np.zeros(n_sds)
        for t in range(total_ar, n_sds):
            ar_t = sum(ar[i] * y_sds[t - 1 - i] for i in range(total_ar) if t - 1 - i >= 0)
            ma_t = sum(ma[j] * resid_train[t - 1 - j] for j in range(total_ma) if t - 1 - j >= total_ar)
            resid_train[t] = y_sds[t] - ar_t - ma_t

        # Extend
        y_ext = np.concatenate([y_sds, np.full(steps, 0.0)])
        for h in range(steps):
            t = n_sds + h
            ar_t = sum(ar[i] * y_ext[t - 1 - i] for i in range(total_ar))
            y_ext[t] = ar_t  # MA expectation = 0

        fc_sds = y_ext[n_sds:]

        # Undo seasonal differencing: seasonal cumulative sum
        fc_ds = self._undo_seasonal_diff(fc_sds)
        # Undo regular differencing
        fc = self._undo_diff(fc_ds)

        se = np.sqrt(sigma2) * np.sqrt(np.arange(1, steps + 1))
        return {
            "forecast": fc.tolist(),
            "lower": (fc - 1.96 * se).tolist(),
            "upper": (fc + 1.96 * se).tolist(),
            "steps": steps,
        }

    def _undo_seasonal_diff(self, x):
        """Undo D seasonal differences of period s."""
        s = self.s
        if self.D == 0:
            return x
        # Need the last s values from the pre-seasonal-diff series
        y_ds = _diff(self._y_orig, self.d)
        tail = y_ds[-s:] if len(y_ds) >= s else y_ds
        result = np.concatenate([tail, x])
        for _ in range(self.D):
            integrated = np.cumsum(result)
            result = integrated
        return result[len(tail):]

    def _undo_diff(self, x):
        """Undo d regular differences."""
        if self.d == 0:
            return x
        y = self._y_orig
        if self.d == 1:
            return np.cumsum(np.concatenate([[y[-1]], x]))[1:]
        elif self.d == 2:
            d1 = np.cumsum(np.concatenate([[y[-2] - y[-1] if len(y) >= 2 else 0], x]))[1:]
            return np.cumsum(np.concatenate([[y[-1]], d1]))[1:]
        else:
            ext = y.tolist() + x.tolist()
            integrated = np.array(ext, dtype=float)
            for _ in range(self.d):
                integrated = np.cumsum(integrated)
            return integrated[len(y):]


# ============================================================================
# 3. GARCH
# ============================================================================

class GARCH:
    """GARCH(p, q) and EGARCH volatility model.

    Fitted via maximisation of the Gaussian log-likelihood.
    """

    def __init__(self, p=1, q=1):
        self.p = p
        self.q = q
        self._fitted = False
        self.params_ = None
        self.omega_ = None
        self.alpha_ = None
        self.beta_ = None
        self.sigma2_ = None
        self.log_likelihood_ = None
        self.aic_ = None
        self.bic_ = None

    # ------------------------------------------------------------------
    def fit(self, returns, p=None, q=None, model_type="garch"):
        """Fit GARCH or EGARCH model.

        Parameters
        ----------
        returns : array-like
            Zero-mean returns (or raw returns — mean will be subtracted).
        p : int or None
            ARCH order.
        q : int or None
            GARCH order.
        model_type : str
            'garch' or 'egarch'.

        Returns
        -------
        dict with parameter estimates, AIC, BIC, conditional volatilities.
        """
        if p is not None:
            self.p = p
        if q is not None:
            self.q = q

        y = _ensure_array(returns, "returns")
        y = y - np.mean(y)  # de-mean
        n = len(y)
        self._y = y
        self._model_type = model_type

        p, q = self.p, self.q

        # Initial variance
        var0 = np.var(y)

        if model_type == "egarch":
            # EGARCH params: omega, alpha_0..alpha_{p-1}, gamma (leverage), beta_0..beta_{q-1}
            n_params = 1 + p + 1 + q  # +1 for gamma (leverage)
            params0 = np.concatenate([
                [np.log(var0) * 0.1],           # omega (log-scale in EGARCH)
                np.full(p, 0.1),                 # alphas
                [-0.1],                           # gamma (leverage)
                np.full(q, 0.8),                 # betas
            ])
            bounds = [(None, None)] + [(None, None)] * p + [(None, None)] + [(None, None)] * q
        else:
            # GARCH params: omega, alpha_0..alpha_{p-1}, beta_0..beta_{q-1}
            n_params = 1 + p + q
            params0 = np.concatenate([
                [var0 * 0.05],
                np.full(p, 0.1),
                np.full(q, 0.8),
            ])
            bounds = [(1e-10, None)] + [(0, None)] * p + [(0, None)] * q

        method_used = "mle"
        try:
            if model_type == "egarch":
                result = optimize.minimize(
                    self._egarch_neg_ll, params0,
                    args=(y, p, q),
                    method="L-BFGS-B", bounds=bounds,
                    options={"maxiter": 800, "ftol": 1e-9}
                )
            else:
                result = optimize.minimize(
                    self._garch_neg_ll, params0,
                    args=(y, p, q),
                    method="L-BFGS-B", bounds=bounds,
                    options={"maxiter": 800, "ftol": 1e-9}
                )

            if not result.success or not np.isfinite(result.fun):
                result2 = optimize.minimize(
                    self._garch_neg_ll if model_type == "garch" else self._egarch_neg_ll,
                    params0, args=(y, p, q),
                    method="Nelder-Mead",
                    options={"maxiter": 5000}
                )
                if np.isfinite(result2.fun) and result2.fun <= result.fun:
                    result = result2
                    method_used = "mle_neldermead"
            params_opt = result.x
        except Exception:
            # Fallback: simple GARCH(1,1) heuristic
            params_opt = np.concatenate([[var0 * 0.05], [0.1], [0.85]])
            if p > 1 or q > 1:
                params_opt = np.concatenate([
                    [var0 * 0.05],
                    np.full(p, 0.1),
                    np.full(q, 0.8 / max(q, 1)),
                ])
            method_used = "heuristic_fallback"

        self.params_ = params_opt
        self._fitted = True

        # Store named params for standard GARCH
        if model_type == "garch":
            self.omega_ = params_opt[0]
            self.alpha_ = params_opt[1: 1 + p]
            self.beta_ = params_opt[1 + p: 1 + p + q]
            cond_var = self._compute_garch_var(y, params_opt, p, q)
        else:
            self.omega_ = params_opt[0]
            self.alpha_ = params_opt[1: 1 + p]
            self._gamma_ = params_opt[1 + p]  # leverage
            self.beta_ = params_opt[2 + p: 2 + p + q]
            cond_var = self._compute_egarch_var(y, params_opt, p, q)

        self.sigma2_ = cond_var
        self.log_likelihood_ = -result.fun
        k = n_params
        self.aic_ = 2 * k - 2 * self.log_likelihood_
        self.bic_ = k * np.log(n) - 2 * self.log_likelihood_

        return {
            "omega": float(params_opt[0]),
            "alpha": params_opt[1: 1 + p].tolist(),
            "beta": params_opt[1 + p: 1 + p + q].tolist(),
            "gamma": float(params_opt[1 + p]) if model_type == "egarch" else None,
            "conditional_volatility": np.sqrt(cond_var).tolist(),
            "sigma2_final": float(cond_var[-1]),
            "log_likelihood": float(self.log_likelihood_),
            "aic": float(self.aic_),
            "bic": float(self.bic_),
            "model_type": model_type,
            "n_obs": int(n),
            "method": method_used,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_garch_var(y, params, p, q):
        """Compute conditional variance path for GARCH(p, q)."""
        n = len(y)
        omega = params[0]
        alpha = params[1: 1 + p]
        beta = params[1 + p: 1 + p + q]
        sigma2 = np.zeros(n)
        sigma2[0] = np.var(y)
        for t in range(1, n):
            arch = sum(alpha[i] * y[t - 1 - i] ** 2 for i in range(p) if t - 1 - i >= 0)
            garch = sum(beta[j] * sigma2[t - 1 - j] for j in range(q) if t - 1 - j >= 0)
            sigma2[t] = omega + arch + garch
            if sigma2[t] <= 0:
                sigma2[t] = 1e-12
        return sigma2

    # ------------------------------------------------------------------
    @staticmethod
    def _compute_egarch_var(y, params, p, q):
        """Compute conditional variance for EGARCH(p, q)."""
        n = len(y)
        omega = params[0]
        alpha = params[1: 1 + p]
        gamma = params[1 + p]
        beta = params[2 + p: 2 + p + q]
        log_sigma2 = np.zeros(n)
        log_sigma2[0] = np.log(np.var(y))
        eps = 1e-8
        for t in range(1, n):
            arch = sum(
                alpha[i] * (np.abs(y[t - 1 - i]) / (np.sqrt(np.exp(log_sigma2[t - 1 - i])) + eps) - np.sqrt(2 / np.pi))
                for i in range(p) if t - 1 - i >= 0
            )
            leverage = sum(
                gamma * (y[t - 1 - j] / (np.sqrt(np.exp(log_sigma2[t - 1 - j])) + eps))
                for j in range(p) if t - 1 - j >= 0
            )
            garch = sum(beta[j] * log_sigma2[t - 1 - j] for j in range(q) if t - 1 - j >= 0)
            log_sigma2[t] = omega + arch + leverage + garch
        return np.exp(log_sigma2)

    # ------------------------------------------------------------------
    @staticmethod
    def _garch_neg_ll(params, y, p, q):
        """Negative log-likelihood for GARCH(p, q) with Gaussian innovations."""
        n = len(y)
        sigma2 = GARCH._compute_garch_var(y, params, p, q)
        ll = -0.5 * np.sum(np.log(2 * np.pi * sigma2) + y ** 2 / sigma2)
        return -ll

    @staticmethod
    def _egarch_neg_ll(params, y, p, q):
        """Negative log-likelihood for EGARCH(p, q)."""
        n = len(y)
        sigma2 = GARCH._compute_egarch_var(y, params, p, q)
        if np.any(sigma2 <= 0):
            return 1e12
        ll = -0.5 * np.sum(np.log(2 * np.pi * sigma2) + y ** 2 / sigma2)
        return -ll

    # ------------------------------------------------------------------
    def forecast_volatility(self, steps=10):
        """Forecast conditional variance / volatility.

        Returns
        -------
        dict with 'variance', 'volatility' arrays of length *steps*.
        """
        if not self._fitted:
            raise RuntimeError("Model must be fitted before forecasting.")

        p, q = self.p, self.q
        y = self._y
        n = len(y)
        params = self.params_

        if self._model_type == "egarch":
            # Get last log-variance and last squared returns
            sigma2_path = self.sigma2_
            log_s2 = np.log(sigma2_path)
            omega = params[0]
            alpha = params[1: 1 + p]
            gamma = params[1 + p]
            beta = params[2 + p: 2 + p + q]
            eps = 1e-8

            fc_log_s2 = np.zeros(steps)
            for h in range(steps):
                t = n + h
                arch = sum(alpha[i] * np.sqrt(2 / np.pi) for i in range(p))  # E[|z|] - sqrt(2/pi) = 0
                leverage = 0.0  # E[z] = 0
                garch = sum(beta[j] * (fc_log_s2[h - 1 - j] if h - 1 - j >= 0 else log_s2[t - 1 - j])
                           for j in range(q) if t - 1 - j >= 0)
                base = fc_log_s2[h - 1] if h > 0 else log_s2[-1]
                fc_log_s2[h] = omega + arch + leverage + (garch if q > 0 else beta[0] * base if q == 1 else base)
            fc_var = np.exp(fc_log_s2)
        else:
            omega = params[0]
            alpha = params[1: 1 + p]
            beta = params[1 + p: 1 + p + q]
            sigma2_path = self.sigma2_

            fc_var = np.zeros(steps)
            for h in range(steps):
                t = n + h
                # For h=0 use actual past; for h>0 use forecasts (where E[y^2] = sigma2)
                arch = sum(alpha[i] * (fc_var[h - 1 - i] if h - 1 - i >= 0 else sigma2_path[t - 1 - i])
                           for i in range(p) if t - 1 - i >= 0)
                garch = sum(beta[j] * (fc_var[h - 1 - j] if h - 1 - j >= 0 else sigma2_path[t - 1 - j])
                           for j in range(q) if t - 1 - j >= 0)
                fc_var[h] = omega + arch + garch

        return {
            "variance": fc_var.tolist(),
            "volatility": np.sqrt(fc_var).tolist(),
            "steps": steps,
            "model_type": self._model_type,
        }


# ============================================================================
# 4. VAR
# ============================================================================

class VAR:
    """Vector Auto-Regression estimated equation-by-equation via OLS.

    Supports Granger causality, impulse response functions, and FEVD.
    """

    def __init__(self):
        self._fitted = False
        self.coeffs_ = None  # list of (K+1,) per equation
        self.residuals_ = None  # (T, K)
        self.names_ = None
        self.K = 0
        self.lags_ = 0
        self._data = None
        self._y_lagged = None
        self._X_lagged = None

    # ------------------------------------------------------------------
    def fit(self, data_dict, max_lags=5):
        """Fit VAR model.

        Parameters
        ----------
        data_dict : dict
            {variable_name: np.array} — all arrays must have the same length.
        max_lags : int
            Maximum number of lags; selected by BIC.

        Returns
        -------
        dict with coefficient matrices, residuals, BIC-selected lag, etc.
        """
        names = list(data_dict.keys())
        self.names_ = names
        self.K = len(names)

        # Align to DataFrame
        df = pd.DataFrame(data_dict)
        df = df.dropna()
        Y = df.values.astype(np.float64)
        n, K = Y.shape
        self._data = Y

        if n < max_lags + 5:
            max_lags = max(1, n // 3 - 1)

        # Lag selection via BIC
        best_bic, best_lag = np.inf, 1
        for lag in range(1, max_lags + 1):
            y_dep, X_lag = self._build_var_lags(Y, lag)
            if y_dep is None:
                continue
            rss = 0.0
            for eq in range(K):
                _, resid, _ = _ols(y_dep[:, eq], X_lag, add_intercept=False)
                rss += np.sum(resid ** 2)
            bic_val = n * np.log(rss / (n - lag)) + lag * K ** 2 * np.log(n)
            if bic_val < best_bic:
                best_bic = bic_val
                best_lag = lag

        self.lags_ = best_lag
        y_dep, X_lag = self._build_var_lags(Y, best_lag)

        # OLS equation by equation
        coeffs = []
        resid_matrix = np.zeros((y_dep.shape[0], K))
        for eq in range(K):
            c, r, _ = _ols(y_dep[:, eq], X_lag, add_intercept=False)
            coeffs.append(c)
            resid_matrix[:, eq] = r

        self.coeffs_ = coeffs
        self.residuals_ = resid_matrix
        self._y_lagged = y_dep
        self._X_lagged = X_lag
        self._fitted = True

        # ComputeSigma
        Sigma = (resid_matrix.T @ resid_matrix) / (n - best_lag)

        return {
            "lag_order": best_lag,
            "n_variables": K,
            "variable_names": names,
            "coefficients": {names[eq]: coeffs[eq].tolist() for eq in range(K)},
            "residual_covariance": Sigma.tolist(),
            "n_obs_used": int(y_dep.shape[0]),
            "bic": float(best_bic),
        }

    # ------------------------------------------------------------------
    def _build_var_lags(self, Y, lag):
        """Build VAR design matrices.

        Returns (y_dep (T-lag, K), X_lag (T-lag, lag*K)).
        """
        n, K = Y.shape
        if n <= lag:
            return None, None
        T = n - lag
        y_dep = Y[lag:]
        X = np.zeros((T, lag * K))
        for l in range(lag):
            X[:, l * K: (l + 1) * K] = Y[lag - 1 - l: n - 1 - l]
        return y_dep, X

    # ------------------------------------------------------------------
    def _companion_matrix(self):
        """Build the VAR companion matrix of shape (lags*K, lags*K)."""
        p = self.lags_
        K = self.K
        A = np.zeros((p * K, p * K))
        for eq in range(K):
            c = self.coeffs_[eq]
            for l in range(p):
                A[0:K, l * K: (l + 1) * K] += np.diag(c[l * K: (l + 1) * K])
        # Actually, fill properly: row block eq gets its own coefficients
        A = np.zeros((p * K, p * K))
        for eq in range(K):
            c = self.coeffs_[eq]
            for l in range(p):
                for var in range(K):
                    A[eq, l * K + var] = c[l * K + var]
        # Lower shift block
        for l in range(1, p):
            A[l * K: (l + 1) * K, (l - 1) * K: l * K] = np.eye(K)
        return A

    # ------------------------------------------------------------------
    def granger_causality(self, causing, caused, max_lag=None):
        """Test whether *causing* Granger-causes *caused*.

        Returns dict with 'f_statistic', 'p_value', 'df'.
        """
        if not self._fitted:
            raise RuntimeError("VAR must be fitted first.")

        if max_lag is None:
            max_lag = self.lags_

        Y = self._data
        n, K = Y.shape
        idx_cause = self.names_.index(causing)
        idx_caused = self.names_.index(caused)

        # Restricted model: only own lags of 'caused'
        # Unrestricted: own lags + lags of 'causing'
        T = n - max_lag

        # Build restricted X (only caused lags)
        X_restr = np.zeros((T, max_lag))
        for l in range(max_lag):
            X_restr[:, l] = Y[max_lag - 1 - l: n - 1 - l, idx_caused]

        y_caused = Y[max_lag:, idx_caused]

        _, r_resid, _ = _ols(y_caused, X_restr, add_intercept=True)
        rss_r = np.sum(r_resid ** 2)

        # Build unrestricted X (all lags of all vars)
        _, X_full = self._build_var_lags(Y, max_lag)
        _, u_resid, _ = _ols(y_caused, X_full, add_intercept=True)
        rss_u = np.sum(u_resid ** 2)

        df1 = max_lag  # restrictions
        df2 = T - max_lag * K - 1
        if df2 <= 0 or rss_u <= 0:
            return {"f_statistic": None, "p_value": None, "df": (df1, max(df2, 1))}

        f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)
        p_val = 1.0 - stats.f.cdf(f_stat, df1, df2)

        return {
            "causing": causing,
            "caused": caused,
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "df": (int(df1), int(df2)),
            "significant_at_05": bool(p_val < 0.05),
        }

    # ------------------------------------------------------------------
    def impulse_response(self, steps=10):
        """Compute orthogonalised impulse response functions.

        Uses Cholesky decomposition of residual covariance.

        Returns
        -------
        dict with 'irf' (list of steps x K x K arrays) and 'variable_names'.
        """
        if not self._fitted:
            raise RuntimeError("VAR must be fitted first.")

        A = self._companion_matrix()
        pK = A.shape[0]
        Sigma = (self.residuals_.T @ self.residuals_) / len(self.residuals_)
        P = np.linalg.cholesky(Sigma)  # lower triangular

        irf = []
        Phi = np.eye(pK)
        K = self.K
        for h in range(steps + 1):
            # Top K rows of Phi @ P give the IRF
            irf_h = (Phi[:K, :] @ P)
            irf.append(irf_h.tolist())
            Phi = Phi @ A

        return {
            "irf": irf,
            "steps": steps,
            "variable_names": self.names_,
        }

    # ------------------------------------------------------------------
    def fevd(self, steps=10):
        """Forecast Error Variance Decomposition.

        Returns
        -------
        dict with 'fevd' (list of steps x K x K arrays — rows sum to 1).
        """
        if not self._fitted:
            raise RuntimeError("VAR must be fitted first.")

        irf_result = self.impulse_response(steps=steps)
        irf = irf_result["irf"]
        K = self.K

        fevd_out = []
        for h in range(steps + 1):
            irf_h = np.array(irf[h])  # (K, K)
            # MSE = sum_{s=0}^{h} irf_s @ irf_s.T
            mse = np.zeros((K, K))
            for s in range(h + 1):
                irf_s = np.array(irf[s])
                mse += irf_s @ irf_s.T
            # FEVD: contribution of shock j to variance of variable i
            fevd_h = np.zeros((K, K))
            for i in range(K):
                total = mse[i, i]
                if total > 0:
                    for j in range(K):
                        # Contribution of shock j: (irf @ P)[:, j]^2 summed over s
                        contrib = 0.0
                        for s in range(h + 1):
                            contrib += np.array(irf[s])[i, j] ** 2
                        fevd_h[i, j] = contrib / total
            fevd_out.append(fevd_h.tolist())

        return {
            "fevd": fevd_out,
            "steps": steps,
            "variable_names": self.names_,
        }

    # ------------------------------------------------------------------
    def forecast(self, steps=10):
        """Produce VAR forecasts.

        Returns dict with 'forecast' dict {name: [values]}.
        """
        if not self._fitted:
            raise RuntimeError("VAR must be fitted first.")

        Y = self._data
        n, K = Y.shape
        p = self.lags_

        # Build history
        history = list(Y)
        forecasts = np.zeros((steps, K))

        for h in range(steps):
            y_new = np.zeros(K)
            for eq in range(K):
                c = self.coeffs_[eq]
                val = 0.0
                for l in range(p):
                    idx = len(history) - 1 - l
                    if idx >= 0:
                        for var in range(K):
                            val += c[l * K + var] * history[idx][var]
                y_new[eq] = val
            forecasts[h] = y_new
            history.append(y_new)

        result = {self.names_[k]: forecasts[:, k].tolist() for k in range(K)}
        result["steps"] = steps
        return result


# ============================================================================
# 5. Cointegration
# ============================================================================

class Cointegration:
    """Cointegration analysis: Engle-Granger, Johansen, Error Correction Model.
    """

    @staticmethod
    def engle_granger_test(y1, y2, max_lag=10):
        """Two-variable Engle-Granger cointegration test.

        1. Regress y1 on y2 (long-run equation).
        2. Test residuals for stationarity via ADF.

        Returns dict with 'coint_stat' (ADF of residuals), 'p_value',
        'beta' (cointegrating coefficient), 'critical_values'.
        """
        y1 = _ensure_array(y1, "y1")
        y2 = _ensure_array(y2, "y2")
        min_n = min(len(y1), len(y2))
        y1, y2 = y1[:min_n], y2[:min_n]

        # Step 1: Long-run regression y1 = alpha + beta * y2
        coefs, resid, _ = _ols(y1, y2.reshape(-1, 1), add_intercept=True)
        beta = coefs[1]
        alpha = coefs[0]

        # Step 2: ADF on residuals
        adf_result = _adf_statistic(resid, max_lag=max_lag)

        # Engle-Granger critical values (MacKinnon approximate for no trend)
        n = len(resid)
        crit = {
            "1%": -3.90,  # approximate for large n, no trend
            "5%": -3.34,
            "10%": -3.04,
        }

        return {
            "coint_stat": float(adf_result["adf"]),
            "p_value": float(adf_result["pvalue"]),
            "used_lag": int(adf_result["used_lag"]),
            "beta": float(beta),
            "alpha": float(alpha),
            "critical_values": crit,
            "is_cointegrated": bool(adf_result["adf"] < crit["5%"]),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def johansen_test(data_matrix, max_lag=5, det_order=0):
        """Simplified Johansen cointegration test for multiple variables.

        Parameters
        ----------
        data_matrix : 2-D array-like (n x K)
        max_lag : int
            Number of lags in the VAR.
        det_order : int
            0 = no constant in coint space, -1 = no constant at all.

        Returns
        -------
        dict with 'eigenvalues', 'trace_stat', 'trace_cv', 'max_stat', 'max_cv', 'r'.
        """
        Y = np.asarray(data_matrix, dtype=np.float64)
        if Y.ndim == 1:
            Y = Y.reshape(-1, 1)
        n, K = Y.shape

        if n < max_lag + K + 5:
            return {"error": "Insufficient data for Johansen test."}

        # Remove mean if det_order >= 0
        if det_order >= 0:
            Y = Y - Y.mean(axis=0)

        # Build lagged differences and levels
        T = n - max_lag
        dY = np.diff(Y, axis=0)  # (n-1, K)
        dY = dY[max_lag - 1:]  # (T, K)
        Y_lag = Y[max_lag - 1: n - 1]  # (T, K)  —  Y_{t-1}

        # Additional lags for the VAR part (residualisation)
        Z1 = dY.copy()
        Z0 = Y_lag.copy()

        # Residualise: regress dY_t on dY_{t-1}, ..., dY_{t-p+1} and
        # regress Y_{t-1} on dY_{t-1}, ..., dY_{t-p+1}
        if max_lag > 1:
            extra_lags = np.column_stack(
                [np.diff(Y, axis=0)[max_lag - 1 - l: n - 1 - l] for l in range(1, max_lag)]
            )
            # R0 = residual of Y_{t-1} ~ extra_lags
            R0, _, _ = _ols(Y_lag, extra_lags, add_intercept=False)
            # R1 = residual of dY_t ~ extra_lags
            R1, _, _ = _ols(dY, extra_lags, add_intercept=False)
        else:
            R0 = Y_lag
            R1 = dY

        # Compute S_ij matrices
        S00 = R1.T @ R1 / T
        S01 = R1.T @ R0 / T
        S10 = S01.T
        S11 = R0.T @ R0 / T

        # Solve eigenvalue problem:  |S10 S00^{-1} S01 - lambda S11| = 0
        try:
            S00_inv = np.linalg.inv(S00)
        except np.linalg.LinAlgError:
            S00_inv = np.linalg.pinv(S00)

        temp = S00_inv @ S01  # K x K
        # Eigenvalues of S11^{-1} S10 S00^{-1} S01
        try:
            S11_inv = np.linalg.inv(S11)
        except np.linalg.LinAlgError:
            S11_inv = np.linalg.pinv(S11)

        M = S11_inv @ S10 @ S00_inv @ S01
        eigenvalues = np.sort(np.real(np.linalg.eigvals(M)))[::-1]
        eigenvalues = np.clip(eigenvalues, 0, None)

        # Trace statistic: T * sum of (1 - lambda_i) for i=0..r-1
        trace_stats = []
        for r in range(K):
            stat = T * np.sum(1 - eigenvalues[:r + 1])
            trace_stats.append(stat)

        # Max statistic: T * (1 - lambda_r)
        max_stats = [T * (1 - ev) for ev in eigenvalues]

        # Approximate critical values (Johansen, 1995 — simplified)
        # Trace 5% critical values (approximate for n=100, no trend)
        trace_cv_approx = {-1: [12.8, 23.5, 34.2, 44.8, 55.2],
                           0:  [15.5, 28.3, 40.1, 51.7, 63.1],
                           1:  [22.0, 36.2, 49.5, 62.0, 74.5]}
        max_cv_approx = {-1: [11.2, 19.0, 26.7, 33.5, 40.0],
                          0:  [14.0, 21.1, 28.8, 35.7, 42.5],
                          1:  [19.2, 27.5, 35.0, 42.0, 49.0]}

        cv_trace = trace_cv_approx.get(det_order, trace_cv_approx[0])[:K]
        cv_max = max_cv_approx.get(det_order, max_cv_approx[0])[:K]

        # Determine rank r
        r = K
        for i in range(K):
            if i < len(cv_trace) and trace_stats[i] < cv_trace[i]:
                r = i
                break

        return {
            "eigenvalues": eigenvalues.tolist(),
            "trace_statistic": [float(s) for s in trace_stats],
            "trace_cv_5pct": cv_trace,
            "max_statistic": [float(s) for s in max_stats],
            "max_cv_5pct": cv_max,
            "coint_rank": int(r),
            "n_variables": int(K),
            "n_obs": int(T),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def error_correction_model(y1, y2, lags=2):
        """Estimate a two-variable Error Correction Model.

        Δy1_t = α1 * (y1_{t-1} - β * y2_{t-1}) + Σ γ1_i * Δy1_{t-i} + Σ δ1_i * Δy2_{t-i} + ε1_t
        Δy2_t = α2 * (y1_{t-1} - β * y2_{t-1}) + Σ γ2_i * Δy2_{t-i} + Σ δ2_i * Δy1_{t-i} + ε2_t

        Returns dict with 'alpha1', 'alpha2', 'beta', 'speed_of_adjustment'.
        """
        y1 = _ensure_array(y1, "y1")
        y2 = _ensure_array(y2, "y2")
        min_n = min(len(y1), len(y2))
        y1, y2 = y1[:min_n], y2[:min_n]

        # Cointegrating regression
        coefs, resid, _ = _ols(y1, y2.reshape(-1, 1), add_intercept=True)
        beta = coefs[1]
        ecm_term = resid  # y1 - alpha - beta*y2

        # Differenced series
        dy1 = np.diff(y1)
        dy2 = np.diff(y2)
        T = len(dy1)

        if T < lags + 2:
            return {"error": "Insufficient data for ECM estimation."}

        # Build design matrices
        start = lags
        X1_cols = []
        for l in range(1, lags + 1):
            X1_cols.append(dy1[start - l: T - l])
            X1_cols.append(dy2[start - l: T - l])
        X1_cols.append(ecm_term[start: T])  # ECM term
        X1 = np.column_stack(X1_cols)
        y1_dep = dy1[start:]

        c1, r1, _ = _ols(y1_dep, X1, add_intercept=True)
        alpha1 = c1[-1]  # last col is ECM
        gamma1 = c1[1:-1]

        X2_cols = []
        for l in range(1, lags + 1):
            X2_cols.append(dy2[start - l: T - l])
            X2_cols.append(dy1[start - l: T - l])
        X2_cols.append(ecm_term[start: T])
        X2 = np.column_stack(X2_cols)
        y2_dep = dy2[start:]

        c2, r2, _ = _ols(y2_dep, X2, add_intercept=True)
        alpha2 = c2[-1]
        gamma2 = c2[1:-1]

        return {
            "beta": float(beta),
            "alpha1": float(alpha1),
            "alpha2": float(alpha2),
            "speed_of_adjustment_y1": float(alpha1),
            "speed_of_adjustment_y2": float(alpha2),
            "eq1_short_run_coefs": [float(x) for x in gamma1],
            "eq2_short_run_coefs": [float(x) for x in gamma2],
            "eq1_r_squared": float(1 - np.sum(r1 ** 2) / np.sum((y1_dep - np.mean(y1_dep)) ** 2))
            if np.sum((y1_dep - np.mean(y1_dep)) ** 2) > 0 else 0.0,
            "eq2_r_squared": float(1 - np.sum(r2 ** 2) / np.sum((y2_dep - np.mean(y2_dep)) ** 2))
            if np.sum((y2_dep - np.mean(y2_dep)) ** 2) > 0 else 0.0,
            "n_obs_used": int(len(y1_dep)),
        }


# ============================================================================
# 6. VaR (Value at Risk)
# ============================================================================

class VaR:
    """Value at Risk and Conditional VaR (Expected Shortfall) estimators.

    Supported methods:
    - 'historical': Empirical quantile
    - 'parametric_normal': Gaussian VaR
    - 'parametric_t': Student-t VaR
    - 'cornish_fisher': Cornish-Fisher expansion VaR
    - 'cvar' / 'es': Conditional VaR (Expected Shortfall)
    """

    @staticmethod
    def calculate(returns, confidence=0.95, method="historical"):
        """Compute Value at Risk.

        Parameters
        ----------
        returns : array-like
            Portfolio or asset returns.
        confidence : float
            Confidence level (e.g. 0.95, 0.99).
        method : str
            'historical', 'parametric_normal', 'parametric_t',
            'cornish_fisher', 'cvar', 'es'.

        Returns
        -------
        dict with VaR value and auxiliary information.
        """
        r = _ensure_array(returns, "returns")
        alpha = 1.0 - confidence

        if method == "historical":
            return VaR._historical(r, alpha, confidence)
        elif method == "parametric_normal":
            return VaR._parametric_normal(r, alpha, confidence)
        elif method == "parametric_t":
            return VaR._parametric_t(r, alpha, confidence)
        elif method == "cornish_fisher":
            return VaR._cornish_fisher(r, alpha, confidence)
        elif method in ("cvar", "es"):
            return VaR._cvar(r, alpha, confidence)
        else:
            raise ValueError(f"Unknown VaR method: {method}")

    # ------------------------------------------------------------------
    @staticmethod
    def _historical(r, alpha, confidence):
        """Historical (empirical) VaR."""
        var_val = np.percentile(r, alpha * 100)
        n_tail = int(np.sum(r <= var_val))
        return {
            "var": float(var_val),
            "confidence": float(confidence),
            "method": "historical",
            "n_observations": int(len(r)),
            "n_tail_observations": int(n_tail),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _parametric_normal(r, alpha, confidence):
        """Parametric VaR assuming normal distribution."""
        mu = np.mean(r)
        sigma = np.std(r, ddof=1)
        z = stats.norm.ppf(alpha)
        var_val = mu + z * sigma
        return {
            "var": float(var_val),
            "confidence": float(confidence),
            "method": "parametric_normal",
            "mean": float(mu),
            "std": float(sigma),
            "z_score": float(z),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _parametric_t(r, alpha, confidence):
        """Parametric VaR assuming Student-t distribution.

        Degrees of freedom estimated via MLE.
        """
        mu = np.mean(r)
        s = np.std(r, ddof=1)

        # Estimate degrees of freedom by maximising log-likelihood
        def neg_ll_t(nu):
            nu = nu[0] if isinstance(nu, np.ndarray) else nu
            if nu <= 2:
                return 1e12
            # Scale parameter for t-distribution matching variance
            scale = s * np.sqrt((nu - 2) / nu)
            ll = np.sum(stats.t.logpdf(r, df=nu, loc=mu, scale=scale))
            return -ll

        try:
            res = optimize.minimize(neg_ll_t, [5.0], bounds=[(2.01, 100)], method="L-BFGS-B")
            nu = res.x[0]
        except Exception:
            nu = 5.0  # fallback

        scale = s * np.sqrt((nu - 2) / nu)
        t_quantile = stats.t.ppf(alpha, df=nu)
        var_val = mu + t_quantile * scale

        return {
            "var": float(var_val),
            "confidence": float(confidence),
            "method": "parametric_t",
            "mean": float(mu),
            "std": float(s),
            "degrees_of_freedom": float(nu),
            "scale": float(scale),
            "t_quantile": float(t_quantile),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _cornish_fisher(r, alpha, confidence):
        """Cornish-Fisher VaR (skewness & kurtosis adjustment)."""
        mu = np.mean(r)
        sigma = np.std(r, ddof=1)
        z = stats.norm.ppf(alpha)

        S = stats.skew(r)
        K = stats.kurtosis(r, fisher=True)  # excess kurtosis

        # Cornish-Fisher expansion
        z_cf = (z
                + (z ** 2 - 1) * S / 6
                + (z ** 3 - 3 * z) * K / 24
                - (2 * z ** 3 - 5 * z) * S ** 2 / 36)

        var_val = mu + z_cf * sigma

        return {
            "var": float(var_val),
            "confidence": float(confidence),
            "method": "cornish_fisher",
            "mean": float(mu),
            "std": float(sigma),
            "skewness": float(S),
            "excess_kurtosis": float(K),
            "z_normal": float(z),
            "z_cornish_fisher": float(z_cf),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _cvar(r, alpha, confidence):
        """Conditional VaR (Expected Shortfall / CVaR).

        ES = E[Loss | Loss > VaR] = average of returns below the VaR quantile.
        """
        var_val = np.percentile(r, alpha * 100)
        tail = r[r <= var_val]
        es_val = np.mean(tail) if len(tail) > 0 else var_val

        return {
            "var": float(var_val),
            "cvar": float(es_val),
            "expected_shortfall": float(es_val),
            "confidence": float(confidence),
            "method": "cvar",
            "n_tail": int(len(tail)),
            "tail_mean": float(np.mean(tail)) if len(tail) > 0 else None,
            "tail_std": float(np.std(tail)) if len(tail) > 1 else None,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def all_methods(returns, confidence=0.95):
        """Run all VaR methods at once.

        Returns dict keyed by method name, each containing the full result dict.
        """
        methods = ["historical", "parametric_normal", "parametric_t", "cornish_fisher", "cvar"]
        results = {}
        for m in methods:
            try:
                results[m] = VaR.calculate(returns, confidence=confidence, method=m)
            except Exception as e:
                results[m] = {"error": str(e)}
        return results
