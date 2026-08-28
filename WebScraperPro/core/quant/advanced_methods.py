"""
Advanced Quantitative Finance Methods Module.

Provides CausalInference, TransferEntropy, TopologicalDataAnalysis,
ReinforcementLearning, and GameTheory classes with real mathematical
implementations using only numpy, pandas, and scipy.
"""

import math

import numpy as np
import pandas as pd
from scipy import stats
from itertools import product
from typing import Dict, List, Tuple, Optional, Callable
import warnings

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# 1. Causal Inference
# ---------------------------------------------------------------------------


class CausalInference:
    """Causal inference methods including OLS, Double/Debiased ML,
    propensity score estimation, and simplified do-calculus."""

    def linear_regression(self, X, y):
        """Ordinary Least Squares regression from scratch.

        Parameters
        ----------
        X : array-like of shape (n, p)
        y : array-like of shape (n,)

        Returns
        -------
        dict with coefficients, standard_errors, t_stats, p_values,
        r_squared, adjusted_r_squared, residuals, predictions.
        """
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64).ravel()
        n, p = X.shape

        # Add intercept
        X_aug = np.column_stack([np.ones(n), X])
        p_aug = p + 1

        # OLS: beta = (X'X)^{-1} X'y
        XtX = X_aug.T @ X_aug
        Xty = X_aug.T @ y
        beta = np.linalg.solve(XtX, Xty)

        # Residuals
        residuals = y - X_aug @ beta
        predictions = X_aug @ beta

        # Sum of squares
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot
        adj_r_squared = 1.0 - (1.0 - r_squared) * (n - 1) / (n - p_aug)

        # Standard errors: sigma^2 * (X'X)^{-1}
        sigma2 = ss_res / (n - p_aug)
        cov_matrix = sigma2 * np.linalg.inv(XtX)
        std_errors = np.sqrt(np.diag(cov_matrix))

        # t-statistics and p-values (two-tailed)
        t_stats = beta / std_errors
        df = n - p_aug
        p_values = 2.0 * stats.t.sf(np.abs(t_stats), df)

        # F-statistic for overall significance
        ss_reg = ss_tot - ss_res
        f_stat = (ss_reg / p) / (ss_res / (n - p_aug))
        f_pvalue = stats.f.sf(f_stat, p, n - p_aug)

        return {
            "coefficients": beta,
            "standard_errors": std_errors,
            "t_stats": t_stats,
            "p_values": p_values,
            "r_squared": r_squared,
            "adjusted_r_squared": adj_r_squared,
            "residuals": residuals,
            "predictions": predictions,
            "f_statistic": f_stat,
            "f_pvalue": f_pvalue,
            "n_observations": n,
            "n_parameters": p_aug,
            "covariance_matrix": cov_matrix,
        }

    def double_ml(self, X, treatment, outcome, n_folds=5):
        """Double/Debiased Machine Learning for Average Treatment Effect.

        Residualizes treatment and outcome using OLS within folds,
        then regresses outcome residuals on treatment residuals.

        Parameters
        ----------
        X : array-like of shape (n, p) — confounders
        treatment : array-like of shape (n,) — binary treatment
        outcome : array-like of shape (n,) — outcome variable
        n_folds : int

        Returns
        -------
        dict with ate, std_error, ci_lower, ci_upper, p_value.
        """
        X = np.asarray(X, dtype=np.float64)
        treatment = np.asarray(treatment, dtype=np.float64).ravel()
        outcome = np.asarray(outcome, dtype=np.float64).ravel()
        n = len(treatment)
        indices = np.arange(n)
        np.random.shuffle(indices)
        folds = np.array_split(indices, n_folds)

        residual_t = np.zeros(n)
        residual_y = np.zeros(n)

        for fold_idx in range(n_folds):
            test_idx = folds[fold_idx]
            train_idx = np.concatenate([folds[j] for j in range(n_folds) if j != fold_idx])

            X_train, X_test = X[train_idx], X[test_idx]
            t_train, t_test = treatment[train_idx], treatment[test_idx]
            y_train, y_test = outcome[train_idx], outcome[test_idx]

            # Residualize treatment: t ~ X
            if X_train.shape[1] > 0 and np.linalg.matrix_rank(X_train) >= X_train.shape[1]:
                Xtr = np.column_stack([np.ones(len(t_train)), X_train])
                beta_t = np.linalg.lstsq(Xtr, t_train, rcond=None)[0]
                Xte = np.column_stack([np.ones(len(t_test)), X_test])
                residual_t[test_idx] = t_test - Xte @ beta_t
            else:
                residual_t[test_idx] = t_test - np.mean(t_train)

            # Residualize outcome: y ~ X
            if X_train.shape[1] > 0 and np.linalg.matrix_rank(X_train) >= X_train.shape[1]:
                Xyr = np.column_stack([np.ones(len(y_train)), X_train])
                beta_y = np.linalg.lstsq(Xyr, y_train, rcond=None)[0]
                Xye = np.column_stack([np.ones(len(y_test)), X_test])
                residual_y[test_idx] = y_test - Xye @ beta_y
            else:
                residual_y[test_idx] = y_test - np.mean(y_train)

        # Final stage: residual_y ~ residual_t (no intercept, or with intercept)
        # The coefficient on residual_t is the ATE
        A_res = np.column_stack([residual_t])
        ate = np.linalg.lstsq(A_res, residual_y, rcond=None)[0][0]
        resid_final = residual_y - A_res @ np.linalg.lstsq(A_res, residual_y, rcond=None)[0]
        sigma2 = np.sum(resid_final ** 2) / (n - 1)
        var_ate = sigma2 / np.sum(residual_t ** 2)
        std_error = np.sqrt(var_ate)

        t_stat = ate / std_error
        p_value = 2.0 * stats.norm.sf(np.abs(t_stat))
        z_crit = stats.norm.ppf(0.975)
        ci_lower = ate - z_crit * std_error
        ci_upper = ate + z_crit * std_error

        return {
            "ate": ate,
            "std_error": std_error,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "p_value": p_value,
            "t_statistic": t_stat,
            "n_folds": n_folds,
        }

    def propensity_score(self, X, treatment, max_iter=10000, lr=0.01, tol=1e-7):
        """Estimate propensity scores via logistic regression from scratch.

        Uses sigmoid activation and gradient descent.

        Parameters
        ----------
        X : array-like of shape (n, p)
        treatment : array-like of shape (n,) — binary (0/1)
        max_iter : int
        lr : float
        tol : float

        Returns
        -------
        dict with scores, balance_metrics, coefficients.
        """
        X = np.asarray(X, dtype=np.float64)
        treatment = np.asarray(treatment, dtype=np.float64).ravel()
        n, p = X.shape

        # Standardize features
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0) + 1e-8
        Xs = (X - X_mean) / X_std
        X_aug = np.column_stack([np.ones(n), Xs])
        p_aug = p + 1

        # Initialize weights
        np.random.seed(42)
        beta = np.zeros(p_aug)

        def sigmoid(z):
            z = np.clip(z, -500, 500)
            return 1.0 / (1.0 + np.exp(-z))

        # Gradient descent
        for i in range(max_iter):
            z = X_aug @ beta
            pred = sigmoid(z)
            gradient = X_aug.T @ (pred - treatment) / n
            beta -= lr * gradient
            if np.linalg.norm(gradient) < tol:
                break

        # Predict propensity scores (on original scale for interpretability)
        z = X_aug @ beta
        scores = sigmoid(z)
        scores = np.clip(scores, 1e-6, 1.0 - 1e-6)

        # Balance metrics: standardized mean differences
        treated_mask = treatment == 1
        control_mask = treatment == 0
        smd = {}
        for j in range(p):
            mean_t = X[treated_mask, j].mean()
            mean_c = X[control_mask, j].mean()
            pooled_std = np.sqrt(
                (X[treated_mask, j].var() + X[control_mask, j].var()) / 2 + 1e-10
            )
            smd[f"feature_{j}"] = (mean_t - mean_c) / pooled_std

        # Weighted balance (IPTW)
        weights_t = 1.0 / scores[treated_mask]
        weights_c = 1.0 / (1.0 - scores[control_mask])
        weighted_smd = {}
        for j in range(p):
            wt_mean = np.average(X[treated_mask, j], weights=weights_t)
            wc_mean = np.average(X[control_mask, j], weights=weights_c)
            wt_var = np.average(
                (X[treated_mask, j] - wt_mean) ** 2, weights=weights_t
            )
            wc_var = np.average(
                (X[control_mask, j] - wc_mean) ** 2, weights=weights_c
            )
            pooled = np.sqrt((wt_var + wc_var) / 2 + 1e-10)
            weighted_smd[f"feature_{j}"] = (wt_mean - wc_mean) / pooled

        return {
            "scores": scores,
            "coefficients": beta,
            "balance_metrics": {
                "unweighted_smd": smd,
                "weighted_smd": weighted_smd,
                "mean_abs_smd": np.mean(np.abs(list(smd.values()))),
            },
        }

    def do_calculus_simple(self, data, treatment_col, outcome_col, adjustment_cols):
        """Simplified do-calculus via adjustment formula.

        E[Y|do(X=x)] = sum_z E[Y|X=x, Z=z] * P(Z=z)

        For continuous Z, discretizes into quantile bins.

        Parameters
        ----------
        data : pd.DataFrame
        treatment_col : str
        outcome_col : str
        adjustment_cols : list of str

        Returns
        -------
        dict with causal_effects, counterfactual_predictions.
        """
        df = data.copy()
        treatment = df[treatment_col].values
        outcome = df[outcome_col].values

        # Discretize adjustment variables into quantile bins
        n_bins = min(10, max(3, len(df) // 20))
        adjustment_strata = pd.DataFrame()
        for col in adjustment_cols:
            adjustment_strata[col] = pd.qcut(
                df[col], q=n_bins, labels=False, duplicates="drop"
            )

        # Build stratum labels
        stratum_codes = adjustment_strata.apply(
            lambda row: "_".join(str(int(v)) for v in row), axis=1
        )
        df["_stratum"] = stratum_codes

        unique_treatments = np.sort(np.unique(treatment))
        causal_effects = {}
        detailed = {}

        for x_val in unique_treatments:
            causal_estimate = 0.0
            strata_details = []

            for stratum in df["_stratum"].unique():
                mask_s = df["_stratum"] == stratum
                p_z = mask_s.mean()  # P(Z=z)

                # Observations with treatment = x_val in this stratum
                mask_xz = mask_s & (df[treatment_col] == x_val)
                if mask_xz.sum() > 0:
                    e_y_xz = df.loc[mask_xz, outcome_col].mean()
                else:
                    # Fallback: interpolate from nearby strata
                    e_y_xz = np.nan

                if not np.isnan(e_y_xz):
                    causal_estimate += e_y_xz * p_z
                    strata_details.append(
                        {
                            "stratum": stratum,
                            "p_z": p_z,
                            "e_y_xz": e_y_xz,
                            "contribution": e_y_xz * p_z,
                            "n_observations": int(mask_xz.sum()),
                        }
                    )

            causal_effects[float(x_val)] = causal_estimate
            detailed[float(x_val)] = strata_details

        # ATE if binary treatment
        ate = None
        if len(unique_treatments) == 2:
            t_vals = list(causal_effects.keys())
            ate = causal_effects[t_vals[1]] - causal_effects[t_vals[0]]

        return {
            "causal_effects": causal_effects,
            "ate": ate,
            "treatment_values": unique_treatments.tolist(),
            "n_strata": len(df["_stratum"].unique()),
            "strata_details": detailed,
        }


# ---------------------------------------------------------------------------
# 2. Transfer Entropy
# ---------------------------------------------------------------------------


class TransferEntropy:
    """Information-theoretic measures of directional information flow."""

    @staticmethod
    def _histogram_count(data, n_bins):
        """Discretize 1D data and return binned indices."""
        data = np.asarray(data).ravel()
        bins = np.linspace(data.min() - 1e-10, data.max() + 1e-10, n_bins + 1)
        indices = np.digitize(data, bins[1:-1])
        return indices, n_bins

    @staticmethod
    def _joint_histogram(a, b, n_bins_a, n_bins_b):
        """Joint histogram of two discrete sequences."""
        joint = np.zeros((n_bins_a, n_bins_b))
        for ai, bi in zip(a, b):
            if 0 <= ai < n_bins_a and 0 <= bi < n_bins_b:
                joint[ai, bi] += 1
        return joint

    @staticmethod
    def _joint_histogram_3d(a, b, c, nb_a, nb_b, nb_c):
        """Joint histogram of three discrete sequences."""
        joint = np.zeros((nb_a, nb_b, nb_c))
        for ai, bi, ci in zip(a, b, c):
            if 0 <= ai < nb_a and 0 <= bi < nb_b and 0 <= ci < nb_c:
                joint[ai, bi, ci] += 1
        return joint

    @staticmethod
    def _entropy_from_joint_1d(marginal):
        """Shannon entropy from marginal counts."""
        p = marginal[marginal > 0].astype(np.float64)
        p = p / p.sum()
        return -np.sum(p * np.log2(p + 1e-15))

    def compute(self, source, target, lag=1, k=1, n_bins=10):
        """Compute Shannon Transfer Entropy TE(X->Y).

        TE(X->Y) = sum p(y_t, y_{t-k}, x_{t-lag}) * log2(
            p(y_t | y_{t-k}, x_{t-lag}) / p(y_t | y_{t-k})
        )

        Parameters
        ----------
        source : array-like — source time series X
        target : array-like — target time series Y
        lag : int — lag of source
        k : int — lag of target auto-history
        n_bins : int — number of histogram bins

        Returns
        -------
        dict with transfer_entropy, direction, normalized_te.
        """
        source = np.asarray(source, dtype=np.float64).ravel()
        target = np.asarray(target, dtype=np.float64).ravel()
        n = len(target)
        max_lag = max(lag, k)
        if n <= max_lag + 1:
            return {"transfer_entropy": 0.0, "direction": "none", "normalized_te": 0.0}

        # Discretize
        x_disc, nb_x = self._histogram_count(source, n_bins)
        y_disc, nb_y = self._histogram_count(target, n_bins)

        y_t = y_disc[max_lag:]
        y_past = y_disc[max_lag - k: n - k]
        x_past = x_disc[max_lag - lag: n - lag]

        # Joint p(y_t, y_{t-k}, x_{t-lag})
        joint_3d = self._joint_histogram_3d(y_t, y_past, x_past, nb_y, nb_y, nb_x)
        p_3d = joint_3d / (joint_3d.sum() + 1e-15)

        # Joint p(y_t, y_{t-k})
        joint_yy = self._joint_histogram(y_t, y_past, nb_y, nb_y)
        p_yy = joint_yy / (joint_yy.sum() + 1e-15)

        # Marginal p(y_{t-k})
        p_y_past = joint_yy.sum(axis=0) / (joint_yy.sum() + 1e-15)

        te = 0.0
        for iyt in range(nb_y):
            for iyp in range(nb_y):
                for ixp in range(nb_x):
                    p_joint = p_3d[iyt, iyp, ixp]
                    if p_joint < 1e-15:
                        continue
                    # p(y_t | y_{t-k}, x_{t-lag})
                    p_cond_full = p_joint / (p_3d[:, iyp, ixp].sum() + 1e-15)
                    # p(y_t | y_{t-k})
                    p_cond_reduced = p_yy[iyt, iyp] / (p_y_past[iyp] + 1e-15)
                    if p_cond_full > 1e-15 and p_cond_reduced > 1e-15:
                        te += p_joint * np.log2(p_cond_full / p_cond_reduced)

        te = max(te, 0.0)

        # Normalize by entropy of target
        h_y = self._entropy_from_joint_1d(np.bincount(y_t.astype(int), minlength=nb_y))
        normalized = te / (h_y + 1e-15)
        normalized = min(normalized, 1.0)

        direction = "source -> target" if te > 0.01 else "none"

        return {
            "transfer_entropy": float(te),
            "direction": direction,
            "normalized_te": float(normalized),
            "target_entropy": float(h_y),
            "lag": lag,
            "n_bins": n_bins,
        }

    def multivariate_transfer_entropy(
        self, sources: Dict[str, np.ndarray], target, lag=1, n_bins=8
    ):
        """Compute TE from multiple sources to one target and rank them.

        Parameters
        ----------
        sources : dict mapping source name to array
        target : array-like
        lag : int
        n_bins : int

        Returns
        -------
        dict with ranking, individual_te, combined_te.
        """
        target = np.asarray(target, dtype=np.float64).ravel()
        individual_te = {}

        for name, src in sources.items():
            src = np.asarray(src, dtype=np.float64).ravel()
            min_len = min(len(src), len(target))
            result = self.compute(src[:min_len], target[:min_len], lag=lag, n_bins=n_bins)
            individual_te[name] = result["transfer_entropy"]

        # Rank by TE value (descending)
        ranking = sorted(individual_te.items(), key=lambda x: x[1], reverse=True)

        # Combined TE: concatenate all sources into a single multivariate source
        # Approximate by treating each source independently and summing unique info
        # (This is a simplification; true multivariate TE uses joint source states)
        if len(sources) > 1:
            # Create joint source by combining discretized sources
            all_arrays = [np.asarray(s, dtype=np.float64).ravel() for s in sources.values()]
            min_len = min(len(target), *[len(a) for a in all_arrays])
            target_trimmed = target[:min_len]

            # Discretize all
            disc_sources = []
            for arr in all_arrays:
                d, nb = self._histogram_count(arr[:min_len], n_bins)
                disc_sources.append(d)

            # Joint source index (product space)
            joint_src = np.zeros(min_len, dtype=int)
            multiplier = 1
            for d in disc_sources:
                joint_src += d * multiplier
                multiplier *= n_bins

            result_combined = self.compute(
                joint_src.astype(float), target_trimmed, lag=lag, n_bins=multiplier
            )
            combined_te = result_combined["transfer_entropy"]
        else:
            combined_te = list(individual_te.values())[0] if individual_te else 0.0

        return {
            "ranking": ranking,
            "individual_te": individual_te,
            "combined_te": float(combined_te),
            "n_sources": len(sources),
        }

    def mutual_information(self, x, y, n_bins=10):
        """Shannon mutual information: MI(X;Y) = sum p(x,y) log2(p(x,y)/(p(x)p(y))).

        Parameters
        ----------
        x, y : array-like
        n_bins : int

        Returns
        -------
        dict with mi, normalized_mi, entropy_x, entropy_y.
        """
        x = np.asarray(x, dtype=np.float64).ravel()
        y = np.asarray(y, dtype=np.float64).ravel()

        x_disc, nb_x = self._histogram_count(x, n_bins)
        y_disc, nb_y = self._histogram_count(y, n_bins)

        joint = self._joint_histogram(x_disc, y_disc, nb_x, nb_y)
        p_xy = joint / (joint.sum() + 1e-15)
        p_x = p_xy.sum(axis=1)
        p_y = p_xy.sum(axis=0)

        mi = 0.0
        for i in range(nb_x):
            for j in range(nb_y):
                if p_xy[i, j] > 1e-15 and p_x[i] > 1e-15 and p_y[j] > 1e-15:
                    mi += p_xy[i, j] * np.log2(p_xy[i, j] / (p_x[i] * p_y[j]))

        mi = max(mi, 0.0)
        h_x = self._entropy_from_joint_1d(np.bincount(x_disc.astype(int), minlength=nb_x))
        h_y = self._entropy_from_joint_1d(np.bincount(y_disc.astype(int), minlength=nb_y))
        nmi = mi / (np.sqrt(h_x * h_y) + 1e-15)
        nmi = min(nmi, 1.0)

        return {
            "mi": float(mi),
            "normalized_mi": float(nmi),
            "entropy_x": float(h_x),
            "entropy_y": float(h_y),
        }

    def conditional_mutual_information(self, x, y, z, n_bins=8):
        """Conditional mutual information: MI(X;Y|Z).

        MI(X;Y|Z) = sum_{x,y,z} p(x,y,z) log(p(x,y|z) / (p(x|z) p(y|z)))

        Parameters
        ----------
        x, y, z : array-like
        n_bins : int

        Returns
        -------
        dict with cmi, mi_xy, reduction_ratio.
        """
        x = np.asarray(x, dtype=np.float64).ravel()
        y = np.asarray(y, dtype=np.float64).ravel()
        z = np.asarray(z, dtype=np.float64).ravel()
        n = min(len(x), len(y), len(z))
        x, y, z = x[:n], y[:n], z[:n]

        x_disc, nb_x = self._histogram_count(x, n_bins)
        y_disc, nb_y = self._histogram_count(y, n_bins)
        z_disc, nb_z = self._histogram_count(z, n_bins)

        joint_xyz = self._joint_histogram_3d(x_disc, y_disc, z_disc, nb_x, nb_y, nb_z)
        p_xyz = joint_xyz / (joint_xyz.sum() + 1e-15)

        # Marginals
        p_z = p_xyz.sum(axis=(0, 1))
        p_xz = p_xyz.sum(axis=1)  # shape (nb_x, nb_z)
        p_yz = p_xyz.sum(axis=0)  # shape (nb_y, nb_z)

        cmi = 0.0
        for ix in range(nb_x):
            for iy in range(nb_y):
                for iz in range(nb_z):
                    p_xyz_val = p_xyz[ix, iy, iz]
                    if p_xyz_val < 1e-15 or p_z[iz] < 1e-15:
                        continue
                    p_x_given_z = p_xz[ix, iz] / (p_z[iz] + 1e-15)
                    p_y_given_z = p_yz[iy, iz] / (p_z[iz] + 1e-15)
                    p_xy_given_z = p_xyz_val / (p_z[iz] + 1e-15)
                    if p_xy_given_z > 1e-15 and p_x_given_z > 1e-15 and p_y_given_z > 1e-15:
                        cmi += p_xyz_val * np.log2(
                            p_xy_given_z / (p_x_given_z * p_y_given_z)
                        )

        cmi = max(cmi, 0.0)

        # Compare with unconditional MI
        mi_result = self.mutual_information(x, y, n_bins)
        mi_xy = mi_result["mi"]
        reduction = 1.0 - cmi / (mi_xy + 1e-15) if mi_xy > 0 else 0.0

        return {
            "cmi": float(cmi),
            "mi_xy": float(mi_xy),
            "reduction_ratio": float(max(reduction, 0.0)),
        }

    def granger_causality_matrix(self, data_matrix, max_lag=3):
        """Granger causality F-test for all pairs of variables.

        For each pair (i, j), test whether i Granger-causes j by comparing
        restricted model (j_t ~ j_{t-1..t-k}) vs unrestricted (j_t ~ j_{t-1..t-k} + i_{t-1..t-k}).

        Parameters
        ----------
        data_matrix : array-like of shape (T, n_vars)
        max_lag : int

        Returns
        -------
        dict with f_matrix, p_matrix, significant_pairs.
        """
        data = np.asarray(data_matrix, dtype=np.float64)
        T, n_vars = data.shape

        f_matrix = np.zeros((n_vars, n_vars))
        p_matrix = np.ones((n_vars, n_vars))

        for j in range(n_vars):  # target
            for i in range(n_vars):  # source (candidate cause)
                if i == j:
                    continue

                # Build lagged matrices
                y_target = data[max_lag:, j]
                n = len(y_target)

                # Restricted: only own lags
                X_restricted = np.column_stack(
                    [data[max_lag - lag: T - lag, j] for lag in range(1, max_lag + 1)]
                )
                X_restricted = np.column_stack([np.ones(n), X_restricted])

                # Unrestricted: own lags + other's lags
                X_unrestricted = np.column_stack(
                    [data[max_lag - lag: T - lag, j] for lag in range(1, max_lag + 1)]
                    + [data[max_lag - lag: T - lag, i] for lag in range(1, max_lag + 1)]
                )
                X_unrestricted = np.column_stack([np.ones(n), X_unrestricted])

                # Fit both models
                try:
                    beta_r = np.linalg.lstsq(X_restricted, y_target, rcond=None)[0]
                    beta_u = np.linalg.lstsq(X_unrestricted, y_target, rcond=None)[0]

                    rss_r = np.sum((y_target - X_restricted @ beta_r) ** 2)
                    rss_u = np.sum((y_target - X_unrestricted @ beta_u) ** 2)

                    p_r = X_restricted.shape[1]
                    p_u = X_unrestricted.shape[1]
                    df1 = p_u - p_r  # number of extra restrictions
                    df2 = n - p_u

                    if df2 > 0 and rss_u > 1e-15:
                        f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)
                        f_stat = max(f_stat, 0.0)
                        p_val = stats.f.sf(f_stat, df1, df2)
                        f_matrix[i, j] = f_stat
                        p_matrix[i, j] = p_val
                except np.linalg.LinAlgError:
                    pass

        # Find significant pairs
        significant = []
        for i in range(n_vars):
            for j in range(n_vars):
                if i != j and p_matrix[i, j] < 0.05:
                    significant.append(
                        {
                            "source": i,
                            "target": j,
                            "f_stat": float(f_matrix[i, j]),
                            "p_value": float(p_matrix[i, j]),
                        }
                    )
        significant.sort(key=lambda x: x["p_value"])

        return {
            "f_matrix": f_matrix,
            "p_matrix": p_matrix,
            "significant_pairs": significant,
            "max_lag": max_lag,
            "n_variables": n_vars,
        }


# ---------------------------------------------------------------------------
# 3. Topological Data Analysis
# ---------------------------------------------------------------------------


class TopologicalDataAnalysis:
    """Topological Data Analysis methods for financial time series."""

    def persistent_homology_1d(self, values, n_points=100):
        """Simplified persistent homology for a 1D signal via sublevel sets.

        Tracks connected components: as the threshold increases, intervals
        merge. Birth = value at which a component appears, death = value
        at which it merges with an older component.

        Parameters
        ----------
        values : array-like of shape (n,)
        n_points : int — resolution for persistence landscape

        Returns
        -------
        dict with diagram, betti_numbers, persistence_landscape.
        """
        values = np.asarray(values, dtype=np.float64).ravel()
        n = len(values)

        # Sort indices by value (ascending = sublevel set filtration)
        sorted_idx = np.argsort(values)
        sorted_values = values[sorted_idx]

        # Union-Find to track connected components
        parent = list(range(n))
        rank_uf = [0] * n
        birth_time = list(sorted_values)
        death_time = [np.inf] * n

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b, death_val):
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            # Attach younger to older
            if birth_time[ra] <= birth_time[rb]:
                parent[rb] = ra
                death_time[rb] = death_val
            else:
                parent[ra] = rb
                death_time[ra] = death_val

        # Process points in order of increasing value
        # Each point connects to its left neighbor if it exists
        pos_to_orig = {sorted_idx[i]: i for i in range(n)}
        orig_to_pos = {i: sorted_idx[i] for i in range(n)}

        for step in range(n):
            orig_idx = sorted_idx[step]
            # Check left neighbor in original ordering
            if orig_idx > 0:
                left_orig = orig_idx - 1
                left_step = pos_to_orig[left_orig]
                if left_step <= step:  # already added
                    union(step, left_step, sorted_values[step])
            # Check right neighbor
            if orig_idx < n - 1:
                right_orig = orig_idx + 1
                right_step = pos_to_orig[right_orig]
                if right_step <= step:
                    union(step, right_step, sorted_values[step])

        # Build persistence diagram
        diagram = []
        for i in range(n):
            if find(i) == i:  # root component
                b = birth_time[i]
            else:
                b = birth_time[i]
            d = death_time[i]
            if d > b and np.isfinite(d):
                diagram.append((float(b), float(d)))
            elif d == np.inf and find(i) == i:
                diagram.append((float(b), float(sorted_values.max() + sorted_values.std())))

        # Sort by persistence (death - birth)
        diagram.sort(key=lambda x: x[1] - x[0], reverse=True)

        # Betti numbers at various scales
        betti_numbers = self.betti_numbers(diagram)

        # Persistence landscape
        landscape = self.persistence_landscape(diagram, n_layers=3, n_points=n_points)

        return {
            "diagram": diagram,
            "betti_numbers": betti_numbers,
            "persistence_landscape": landscape,
            "n_features": len(diagram),
        }

    def betti_numbers(self, diagram, epsilon=0.1):
        """Count topological features at a given scale epsilon.

        A feature is alive at scale epsilon if birth < epsilon <= death.

        Parameters
        ----------
        diagram : list of (birth, death) tuples
        epsilon : float

        Returns
        -------
        dict with betti_0, alive_features, scale.
        """
        alive = [(b, d) for b, d in diagram if b < epsilon <= d]
        return {
            "betti_0": len(alive),
            "alive_features": alive,
            "scale": epsilon,
        }

    def persistence_landscape(self, diagram, n_layers=3, n_points=100):
        """Compute persistence landscape functions.

        For each persistence pair (b, d), define a "tent" function:
            lambda_k(t) = max(0, min(t - b, d - t))
        Then the k-th landscape function is the k-th largest tent value at each t.

        Parameters
        ----------
        diagram : list of (birth, death)
        n_layers : int
        n_points : int

        Returns
        -------
        dict with layers (list of arrays), grid, total_persistence.
        """
        if not diagram:
            grid = np.linspace(0, 1, n_points)
            layers = [np.zeros(n_points) for _ in range(n_layers)]
            return {"layers": layers, "grid": grid, "total_persistence": 0.0}

        births = np.array([b for b, d in diagram])
        deaths = np.array([d for b, d in diagram])
        all_vals = np.concatenate([births, deaths])
        t_min, t_max = all_vals.min(), all_vals.max()
        grid = np.linspace(t_min, t_max, n_points)

        # Compute tent functions for all pairs
        tents = np.zeros((len(diagram), n_points))
        for idx, (b, d) in enumerate(diagram):
            mid = (b + d) / 2.0
            tents[idx] = np.where(
                grid < mid,
                np.maximum(0, grid - b),
                np.maximum(0, d - grid),
            )

        # Sort tents in descending order at each grid point
        tents_sorted = np.sort(tents, axis=0)[::-1]

        layers = []
        for k in range(n_layers):
            if k < tents_sorted.shape[0]:
                layers.append(tents_sorted[k])
            else:
                layers.append(np.zeros(n_points))

        total_persistence = float(np.sum([d - b for b, d in diagram]))

        return {
            "layers": layers,
            "grid": grid,
            "total_persistence": total_persistence,
            "n_layers": n_layers,
        }

    def wasserstein_distance(self, diag1, diag2, p=2):
        """Compute p-Wasserstein distance between two persistence diagrams.

        Uses the greedy matching algorithm (permutation matching) which
        gives the exact 1-Wasserstein distance for 1D diagrams.

        Parameters
        ----------
        diag1, diag2 : list of (birth, death) tuples
        p : int — order of the distance

        Returns
        -------
        dict with distance, matching, n_matched.
        """
        d1 = [(b, d) for b, d in diag1 if d > b]
        d2 = [(b, d) for b, d in diag2 if d > b]

        if not d1 and not d2:
            return {"distance": 0.0, "matching": [], "n_matched": 0}

        # Pad shorter diagram with diagonal projections (b, b)
        max_len = max(len(d1), len(d2))
        while len(d1) < max_len:
            d1.append((0.0, 0.0))
        while len(d2) < max_len:
            d2.append((0.0, 0.0))

        # Cost matrix: |p1 - p2|_inf where p1 and p2 are points,
        # and matching to diagonal has cost ||(b,d) - (m,m)||_inf where m=(b+d)/2
        def point_dist(p1, p2):
            return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

        def diag_dist(p):
            m = (p[0] + p[1]) / 2.0
            return max(abs(p[0] - m), abs(p[1] - m))

        # Build full cost matrix including diagonal matchings
        n1, n2 = len(d1), len(d2)
        n_total = n1 + n2
        cost = np.zeros((n_total, n_total))

        for i in range(n_total):
            for j in range(n_total):
                if i < n1 and j < n2:
                    cost[i, j] = point_dist(d1[i], d2[j])
                elif i < n1 and j >= n2:
                    cost[i, j] = diag_dist(d1[i])
                elif i >= n1 and j < n2:
                    cost[i, j] = diag_dist(d2[j])
                else:
                    cost[i, j] = 0.0

        # Use scipy linear_sum_assignment for optimal matching
        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost)
        total_cost = cost[row_ind, col_ind].sum()

        # For p != 1, raise to power p and take p-th root
        distance = total_cost ** (p / 1.0) if p != 1 else total_cost
        # Note: for p-Wasserstein with p>1 on 1D, the L_inf matching
        # gives a valid upper bound. For exact p-Wasserstein, we'd need
        # a different cost function. Here we use L_inf matching.
        # Recompute with Lp distance in cost matrix for correctness:
        cost_p = np.zeros((n_total, n_total))
        for i in range(n_total):
            for j in range(n_total):
                if i < n1 and j < n2:
                    cost_p[i, j] = np.linalg.norm(np.array(d1[i]) - np.array(d2[j]), ord=p)
                elif i < n1 and j >= n2:
                    m = (d1[i][0] + d1[i][1]) / 2.0
                    cost_p[i, j] = np.linalg.norm(
                        np.array(d1[i]) - np.array([m, m]), ord=p
                    ) ** p
                elif i >= n1 and j < n2:
                    m = (d2[j][0] + d2[j][1]) / 2.0
                    cost_p[i, j] = np.linalg.norm(
                        np.array(d2[j]) - np.array([m, m]), ord=p
                    ) ** p
                else:
                    cost_p[i, j] = 0.0

        row_ind, col_ind = linear_sum_assignment(cost_p)
        distance = cost_p[row_ind, col_ind].sum() ** (1.0 / p)

        matching = []
        for r, c in zip(row_ind, col_ind):
            if r < n1 and c < n2:
                matching.append((d1[r], d2[c]))

        return {
            "distance": float(distance),
            "matching": matching,
            "n_matched": len(matching),
            "p": p,
        }

    def detect_regime_changes(
        self, values, window=50, threshold=None
    ):
        """Detect regime changes using TDA on rolling windows.

        Computes persistence diagrams on rolling windows, measures
        Wasserstein distances between consecutive landscapes, and
        flags significant changes.

        Parameters
        ----------
        values : array-like
        window : int
        threshold : float or None (auto-computed if None)

        Returns
        -------
        dict with change_points, landscape_distances.
        """
        values = np.asarray(values, dtype=np.float64).ravel()
        n = len(values)
        if n < 2 * window:
            return {
                "change_points": [],
                "landscape_distances": [],
                "threshold": 0.0,
            }

        n_windows = n - window + 1
        landscapes = []
        landscape_distances = []

        for start in range(0, n - window + 1, max(1, window // 4)):
            window_data = values[start: start + window]
            ph = self.persistent_homology_1d(window_data, n_points=50)
            landscapes.append(ph["persistence_landscape"])

        # Compute distances between consecutive landscapes
        for i in range(1, len(landscapes)):
            l1 = landscapes[i - 1]
            l2 = landscapes[i]
            # L2 distance between first layer of landscapes
            layer_dist = np.sqrt(
                np.sum((np.array(l1["layers"][0]) - np.array(l2["layers"][0])) ** 2)
            )
            landscape_distances.append(float(layer_dist))

        # Auto-compute threshold if not provided
        if threshold is None:
            if landscape_distances:
                dist_arr = np.array(landscape_distances)
                threshold = float(np.mean(dist_arr) + 2.0 * np.std(dist_arr))
            else:
                threshold = 0.0

        # Detect change points
        change_points = []
        step = max(1, window // 4)
        for idx, dist in enumerate(landscape_distances):
            if dist > threshold:
                change_point = (idx + 1) * step + window
                if change_point < n:
                    change_points.append(
                        {
                            "index": int(change_point),
                            "distance": dist,
                            "threshold": threshold,
                        }
                    )

        return {
            "change_points": change_points,
            "landscape_distances": landscape_distances,
            "threshold": threshold,
            "n_regimes": len(change_points) + 1,
        }


# ---------------------------------------------------------------------------
# 4. Reinforcement Learning
# ---------------------------------------------------------------------------


class ReinforcementLearning:
    """Tabular reinforcement learning algorithms for trading."""

    def __init__(
        self, n_states, n_actions, learning_rate=0.1, discount=0.95, epsilon=0.1
    ):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        self.q_table = np.zeros((n_states, n_actions))

    def _epsilon_greedy(self, state, q_table):
        """Select action using epsilon-greedy policy."""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(q_table[state]))

    def _compute_convergence_info(self, rewards_per_episode):
        """Compute convergence diagnostics."""
        rpe = np.array(rewards_per_episode)
        window = min(100, len(rpe))
        if len(rpe) < 2:
            return {"converged": False, "final_avg_reward": 0.0, "trend": "unknown"}

        # Check if last 10% is stable
        tail_size = max(10, len(rpe) // 10)
        tail = rpe[-tail_size:]
        tail_std = np.std(tail)
        tail_mean = np.mean(tail)

        # Linear trend on last portion
        x = np.arange(len(tail))
        if len(x) > 1 and np.std(x) > 0:
            slope = np.polyfit(x, tail, 1)[0]
            trend = "improving" if slope > 0.01 else ("declining" if slope < -0.01 else "stable")
        else:
            slope = 0.0
            trend = "stable"

        converged = tail_std < 0.1 * (np.std(rpe) + 1e-10) and abs(slope) < 0.01

        return {
            "converged": bool(converged),
            "final_avg_reward": float(tail_mean),
            "trend": trend,
            "tail_std": float(tail_std),
            "slope": float(slope),
        }

    def train_q_learning(self, env_step_fn, n_episodes=1000, max_steps=200):
        """Q-learning (off-policy TD control).

        Q(s,a) <- Q(s,a) + lr * [r + gamma * max_a' Q(s',a') - Q(s,a)]

        Parameters
        ----------
        env_step_fn : callable(state, action) -> (next_state, reward, done)
        n_episodes : int
        max_steps : int

        Returns
        -------
        dict with q_table, rewards_per_episode, convergence_info.
        """
        q = np.zeros((self.n_states, self.n_actions))
        rewards_per_episode = []

        for ep in range(n_episodes):
            # Decay epsilon
            eps = max(0.01, self.epsilon * (1.0 - ep / (0.8 * n_episodes)))
            state = 0  # Assume environment resets to state 0
            total_reward = 0.0

            for step in range(max_steps):
                # Epsilon-greedy action selection
                if np.random.random() < eps:
                    action = np.random.randint(self.n_actions)
                else:
                    action = int(np.argmax(q[state]))

                next_state, reward, done = env_step_fn(state, action)
                total_reward += reward

                # Q-learning update
                best_next = np.max(q[next_state]) if not done else 0.0
                td_target = reward + self.gamma * best_next
                td_error = td_target - q[state, action]
                q[state, action] += self.lr * td_error

                state = next_state
                if done:
                    break

            rewards_per_episode.append(total_reward)

        self.q_table = q
        return {
            "q_table": q,
            "rewards_per_episode": rewards_per_episode,
            "convergence_info": self._compute_convergence_info(rewards_per_episode),
            "n_episodes": n_episodes,
            "algorithm": "q_learning",
        }

    def train_sarsa(self, env_step_fn, n_episodes=1000, max_steps=200):
        """SARSA (on-policy TD control).

        Q(s,a) <- Q(s,a) + lr * [r + gamma * Q(s',a') - Q(s,a)]
        where a' is selected using the same epsilon-greedy policy.

        Parameters
        ----------
        env_step_fn : callable(state, action) -> (next_state, reward, done)
        n_episodes : int
        max_steps : int

        Returns
        -------
        dict with q_table, rewards_per_episode, convergence_info.
        """
        q = np.zeros((self.n_states, self.n_actions))
        rewards_per_episode = []

        for ep in range(n_episodes):
            eps = max(0.01, self.epsilon * (1.0 - ep / (0.8 * n_episodes)))
            state = 0
            total_reward = 0.0

            # Select initial action
            if np.random.random() < eps:
                action = np.random.randint(self.n_actions)
            else:
                action = int(np.argmax(q[state]))

            for step in range(max_steps):
                next_state, reward, done = env_step_fn(state, action)
                total_reward += reward

                # Select next action using same policy
                if np.random.random() < eps:
                    next_action = np.random.randint(self.n_actions)
                else:
                    next_action = int(np.argmax(q[next_state]))

                # SARSA update
                next_q = q[next_state, next_action] if not done else 0.0
                td_target = reward + self.gamma * next_q
                td_error = td_target - q[state, action]
                q[state, action] += self.lr * td_error

                state = next_state
                action = next_action
                if done:
                    break

            rewards_per_episode.append(total_reward)

        self.q_table = q
        return {
            "q_table": q,
            "rewards_per_episode": rewards_per_episode,
            "convergence_info": self._compute_convergence_info(rewards_per_episode),
            "n_episodes": n_episodes,
            "algorithm": "sarsa",
        }

    def train_expected_sarsa(self, env_step_fn, n_episodes=1000, max_steps=200):
        """Expected SARSA.

        Q(s,a) <- Q(s,a) + lr * [r + gamma * E_a'[Q(s',a')] - Q(s,a)]
        where the expectation is over the current policy.

        Parameters
        ----------
        env_step_fn : callable(state, action) -> (next_state, reward, done)
        n_episodes : int
        max_steps : int

        Returns
        -------
        dict with q_table, rewards_per_episode, convergence_info.
        """
        q = np.zeros((self.n_states, self.n_actions))
        rewards_per_episode = []

        for ep in range(n_episodes):
            eps = max(0.01, self.epsilon * (1.0 - ep / (0.8 * n_episodes)))
            state = 0
            total_reward = 0.0

            for step in range(max_steps):
                if np.random.random() < eps:
                    action = np.random.randint(self.n_actions)
                else:
                    action = int(np.argmax(q[state]))

                next_state, reward, done = env_step_fn(state, action)
                total_reward += reward

                # Expected value under epsilon-greedy policy
                if not done:
                    q_next = q[next_state]
                    # Expected Q = (1-eps) * max(Q) + eps * mean(Q)
                    expected_q = (1.0 - eps) * np.max(q_next) + eps * np.mean(q_next)
                else:
                    expected_q = 0.0

                td_target = reward + self.gamma * expected_q
                td_error = td_target - q[state, action]
                q[state, action] += self.lr * td_error

                state = next_state
                if done:
                    break

            rewards_per_episode.append(total_reward)

        self.q_table = q
        return {
            "q_table": q,
            "rewards_per_episode": rewards_per_episode,
            "convergence_info": self._compute_convergence_info(rewards_per_episode),
            "n_episodes": n_episodes,
            "algorithm": "expected_sarsa",
        }

    def trading_env(self, prices):
        """Create a trading environment step function from price data.

        State: (discretized normalized return, position)
            - return discretized into n_return_bins levels
            - position: 0=flat, 1=long, 2=short
        Actions: 0=buy, 1=sell, 2=hold
        Reward: PnL change from position.

        Parameters
        ----------
        prices : array-like of price data

        Returns
        -------
        dict with step_fn, n_states, n_actions, state_description.
        """
        prices = np.asarray(prices, dtype=np.float64).ravel()
        n_prices = len(prices)
        returns = np.diff(prices) / (prices[:-1] + 1e-10)

        # Discretize returns
        n_return_bins = 5
        ret_std = np.std(returns) + 1e-10
        ret_mean = np.mean(returns)

        def discretize_return(r):
            normalized = (r - ret_mean) / ret_std
            normalized = np.clip(normalized, -2.5, 2.5)
            bin_idx = int((normalized + 2.5) / 5.0 * n_return_bins)
            return min(bin_idx, n_return_bins - 1)

        n_positions = 3  # flat, long, short
        n_states = n_return_bins * n_positions
        n_actions = 3  # buy, sell, hold

        # Mutable state for the environment
        env_state = {
            "t": 0,
            "position": 0,  # 0=flat, 1=long, 2=short
            "entry_price": 0.0,
            "done": False,
        }

        def reset():
            env_state["t"] = 0
            env_state["position"] = 0
            env_state["entry_price"] = 0.0
            env_state["done"] = False

        def step(state, action):
            t = env_state["t"]
            if t >= n_prices - 1:
                env_state["done"] = True
                return 0, 0.0, True

            position = env_state["position"]
            reward = 0.0
            current_price = prices[t]
            next_price = prices[t + 1]
            price_change = (next_price - current_price) / (current_price + 1e-10)

            # Execute action
            new_position = position
            if action == 0:  # buy
                if position == 0:  # enter long
                    new_position = 1
                    env_state["entry_price"] = current_price
                elif position == 2:  # close short, go long
                    reward += (env_state["entry_price"] - current_price) / (
                        env_state["entry_price"] + 1e-10
                    )
                    new_position = 1
                    env_state["entry_price"] = current_price
            elif action == 1:  # sell
                if position == 0:  # enter short
                    new_position = 2
                    env_state["entry_price"] = current_price
                elif position == 1:  # close long, go short
                    reward += (current_price - env_state["entry_price"]) / (
                        env_state["entry_price"] + 1e-10
                    )
                    new_position = 2
                    env_state["entry_price"] = current_price
            # action == 2: hold

            # Mark-to-market PnL for open position
            if new_position == 1:
                reward += price_change
            elif new_position == 2:
                reward -= price_change

            env_state["position"] = new_position
            env_state["t"] = t + 1

            # Next state
            if t + 1 < len(returns):
                ret_bin = discretize_return(returns[t])
            else:
                ret_bin = n_return_bins // 2

            next_state = ret_bin * n_positions + new_position
            done = env_state["t"] >= n_prices - 1
            env_state["done"] = done

            return next_state, reward, done

        reset()  # Initialize

        return {
            "step_fn": step,
            "reset_fn": reset,
            "n_states": n_states,
            "n_actions": n_actions,
            "state_description": {
                "n_return_bins": n_return_bins,
                "n_positions": n_positions,
                "position_labels": ["flat", "long", "short"],
                "action_labels": ["buy", "sell", "hold"],
            },
        }


# ---------------------------------------------------------------------------
# 5. Game Theory
# ---------------------------------------------------------------------------


class GameTheory:
    """Game-theoretic methods for strategic analysis."""

    def nash_equilibrium_2x2(self, payoff_a, payoff_b):
        """Find all pure-strategy Nash equilibria in a 2x2 game.

        A strategy profile (i, j) is a NE if:
            payoff_a[i, j] >= payoff_a[i', j] for all i'
            payoff_b[i, j] >= payoff_b[i, j'] for all j'

        Parameters
        ----------
        payoff_a : array-like of shape (2, 2) — Player A's payoffs
        payoff_b : array-like of shape (2, 2) — Player B's payoffs

        Returns
        -------
        dict with equilibria, is_pure_dominant.
        """
        pa = np.asarray(payoff_a, dtype=np.float64)
        pb = np.asarray(payoff_b, dtype=np.float64)

        equilibria = []
        for i in range(2):
            for j in range(2):
                a_best = all(pa[i, j] >= pa[i2, j] for i2 in range(2))
                b_best = all(pb[i, j] >= pb[i, j2] for j2 in range(2))
                if a_best and b_best:
                    equilibria.append(
                        {
                            "player1_action": int(i),
                            "player2_action": int(j),
                            "payoff_a": float(pa[i, j]),
                            "payoff_b": float(pb[i, j]),
                        }
                    )

        # Check for pure dominant strategies
        # Player A: action i dominates i' if pa[i, j] >= pa[i', j] for all j (strict >)
        dominant_a = None
        for i in range(2):
            other = 1 - i
            if all(pa[i, j] >= pa[other, j] for j in range(2)) and any(
                pa[i, j] > pa[other, j] for j in range(2)
            ):
                dominant_a = int(i)
                break

        dominant_b = None
        for j in range(2):
            other = 1 - j
            if all(pb[i, j] >= pb[i, other] for i in range(2)) and any(
                pb[i, j] > pb[i, other] for i in range(2)
            ):
                dominant_b = int(j)
                break

        return {
            "equilibria": equilibria,
            "is_pure_dominant": {
                "player1_dominant": dominant_a,
                "player2_dominant": dominant_b,
                "has_dominant_strategy_equilibrium": (
                    dominant_a is not None or dominant_b is not None
                ),
            },
            "n_equilibria": len(equilibria),
        }

    def mixed_nash_2x2(self, payoff_a, payoff_b):
        """Compute mixed-strategy Nash equilibrium using indifference principle.

        For a 2x2 game, Player 1 plays action 0 with probability p:
            p * pa[0,0] + (1-p) * pa[1,0] = p * pa[0,1] + (1-p) * pa[1,1]

        Player 2 plays action 0 with probability q:
            q * pb[0,0] + (1-q) * pb[0,1] = q * pb[1,0] + (1-q) * pb[1,1]

        Parameters
        ----------
        payoff_a : array-like of shape (2, 2)
        payoff_b : array-like of shape (2, 2)

        Returns
        -------
        dict with player1_strategy, player2_strategy.
        """
        pa = np.asarray(payoff_a, dtype=np.float64)
        pb = np.asarray(payoff_b, dtype=np.float64)

        # Player 1's mixed strategy (probability of playing action 0)
        # Indifference for Player 2:
        # q * pb[0,0] + (1-q) * pb[0,1] = q * pb[1,0] + (1-q) * pb[1,1]
        # q * (pb[0,0] - pb[0,1] - pb[1,0] + pb[1,1]) = pb[1,1] - pb[0,1]
        denom_b = (
            pb[0, 0] - pb[0, 1] - pb[1, 0] + pb[1, 1]
        )
        if abs(denom_b) > 1e-10:
            p1_action0 = (pb[1, 1] - pb[0, 1]) / denom_b
        else:
            p1_action0 = None  # No unique mixed strategy

        # Player 2's mixed strategy (probability of playing action 0)
        # Indifference for Player 1:
        denom_a = (
            pa[0, 0] - pa[0, 1] - pa[1, 0] + pa[1, 1]
        )
        if abs(denom_a) > 1e-10:
            p2_action0 = (pa[1, 1] - pa[1, 0]) / denom_a
        else:
            p2_action0 = None

        # Clip to valid probabilities
        def clip_prob(val):
            if val is None:
                return None
            val = float(val)
            if 0.0 <= val <= 1.0:
                return val
            return None  # Mixed NE doesn't exist in (0,1)

        p1 = clip_prob(p1_action0)
        p2 = clip_prob(p2_action0)

        p1_strategy = [p1, 1.0 - p1] if p1 is not None else None
        p2_strategy = [p2, 1.0 - p2] if p2 is not None else None

        return {
            "player1_strategy": p1_strategy,
            "player2_strategy": p2_strategy,
            "player1_prob_action0": p1,
            "player2_prob_action0": p2,
            "exists": p1 is not None and p2 is not None,
        }

    def shapley_value(self, contributions: Dict[str, List[float]]):
        """Compute Shapley values for a cooperative game.

        For each player i:
            phi_i = sum over S subset N-{i} of |S|!(|N|-|S|-1)!/|N|! * [v(S+{i}) - v(S)]

        Here, the characteristic function v(S) is approximated by the mean
        contribution when players in S are present.

        Parameters
        ----------
        contributions : dict mapping player name to list of marginal
            contribution values across different coalitions/contexts.

        Returns
        -------
        dict with shapley_values, total_value.
        """
        players = list(contributions.keys())
        n = len(players)

        if n == 0:
            return {"shapley_values": {}, "total_value": 0.0}

        # Simple Shapley value approximation:
        # For n players, the Shapley value of player i is the average
        # marginal contribution across all possible orderings.
        # We approximate this using the provided contribution lists.
        # Exact computation uses all 2^n subsets.

        shapley_values = {}

        if n <= 20:  # Exact computation for small n
            # Characteristic function: v(S) = mean contribution of S
            all_subsets = []
            for size in range(n + 1):
                for combo in product(range(n), repeat=size):
                    all_subsets.append(set(combo))

            def v(coalition):
                """Value of coalition as sum of mean contributions."""
                if not coalition:
                    return 0.0
                total = 0.0
                for idx in coalition:
                    name = players[idx]
                    vals = contributions[name]
                    total += np.mean(vals) if vals else 0.0
                return total

            for i in range(n):
                phi_i = 0.0
                for S in all_subsets:
                    if i not in S:
                        S_with_i = S | {i}
                        s_size = len(S)
                        # Weight: |S|!(n-|S|-1)! / n!
                        weight = (
                            math.factorial(s_size)
                            * math.factorial(n - s_size - 1)
                            / math.factorial(n)
                        )
                        marginal = v(S_with_i) - v(S)
                        phi_i += weight * marginal
                shapley_values[players[i]] = float(phi_i)
        else:
            # Approximate using random permutations
            n_permutations = min(10000, math.factorial(n))
            marginals = {p: [] for p in players}

            for _ in range(n_permutations):
                perm = list(range(n))
                np.random.shuffle(perm)
                for pos, i in enumerate(perm):
                    name = players[i]
                    vals = contributions[name]
                    marginal = np.mean(vals) if vals else 0.0
                    marginals[name].append(marginal)

            for p in players:
                shapley_values[p] = float(np.mean(marginals[p]))

        total_value = sum(shapley_values.values())

        return {
            "shapley_values": shapley_values,
            "total_value": total_value,
            "efficiency": (
                abs(total_value - sum(
                    np.mean(v) for v in contributions.values() if v
                ))
                if contributions
                else 0.0
            ),
        }

    def mechanism_design_vcg(self, valuations: List[float], cost: float = 0):
        """Vickrey-Clarke-Groves mechanism for allocative efficiency.

        Allocates item to highest bidder. Winner pays externality:
        payment = sum of others' valuations - value without winner.

        Parameters
        ----------
        valuations : list of bidder valuations
        cost : float — cost of providing the good

        Returns
        -------
        dict with winner, payment, welfare.
        """
        valuations = list(valuations)
        n = len(valuations)
        if n == 0:
            return {"winner": None, "payment": 0.0, "welfare": 0.0, "allocative_efficiency": 0.0}

        # Find winner (highest valuation, above cost)
        max_val = max(valuations)
        if max_val < cost:
            return {
                "winner": None,
                "payment": 0.0,
                "welfare": 0.0,
                "allocative_efficiency": 0.0,
                "no_allocation": True,
            }

        winner_idx = int(np.argmax(valuations))

        # VCG payment = externality imposed on others
        # = (sum of others' values without winner) - (sum of others' values with winner)
        # Since allocating to winner removes the item for others:
        # payment = second_highest_valuation (Vickrey auction)
        other_vals = [v for i, v in enumerate(valuations) if i != winner_idx]
        second_highest = max(other_vals) if other_vals else 0.0

        # Generalized VCG: payment = (welfare without i) - (welfare without i but item allocated to i)
        # welfare without i: max(0, max(other_vals) - cost)
        # welfare with i allocated: max(0, valuations[winner_idx] - cost)
        # payment = welfare_without_i - (welfare_with_i - valuations[winner_idx] + cost)
        welfare_without_winner = max(0.0, max(other_vals) - cost) if other_vals else 0.0
        welfare_with_winner = max(0.0, max_val - cost)
        payment = welfare_without_winner - welfare_with_winner + max_val - cost
        payment = max(payment, second_highest - cost, 0.0)  # Ensure non-negative
        payment = second_highest if second_highest > cost else cost  # Vickrey price

        # Winner surplus
        winner_surplus = max_val - payment
        total_welfare = winner_surplus

        # Allocative efficiency: ratio of achieved welfare to maximum possible
        max_possible_welfare = max(0.0, max_val - cost)
        efficiency = total_welfare / (max_possible_welfare + 1e-15)

        return {
            "winner": winner_idx,
            "winner_valuation": float(max_val),
            "payment": float(payment),
            "winner_surplus": float(winner_surplus),
            "welfare": float(total_welfare),
            "allocative_efficiency": float(min(efficiency, 1.0)),
            "second_highest_bid": float(second_highest),
            "n_bidders": n,
            "cost": cost,
        }

    def cournot_duopoly(self, demand_a, demand_b, cost1, cost2):
        """Solve Cournot duopoly with linear demand P = a - b*Q.

        Each firm maximizes profit: pi_i = (P - c_i) * q_i
        Best response: q_i = (a - c_i - b * q_j) / (2 * b)

        Solving the system of best responses:
            q1* = (a - 2*c1 + c2) / (3*b)
            q2* = (a - 2*c2 + c1) / (3*b)

        Parameters
        ----------
        demand_a : float — intercept of demand curve (P = a - b*Q)
        demand_b : float — slope coefficient
        cost1 : float — marginal cost of firm 1
        cost2 : float — marginal cost of firm 2

        Returns
        -------
        dict with q1, q2, price, profits, consumer_surplus, total_welfare.
        """
        a, b = demand_a, demand_b
        c1, c2 = cost1, cost2

        if b <= 0:
            return {"error": "demand_b must be positive"}

        # Nash equilibrium quantities
        q1 = (a - 2 * c1 + c2) / (3 * b)
        q2 = (a - 2 * c2 + c1) / (3 * b)

        # Ensure non-negative
        q1 = max(q1, 0.0)
        q2 = max(q2, 0.0)

        Q = q1 + q2
        price = a - b * Q
        price = max(price, 0.0)

        # Profits
        profit1 = (price - c1) * q1
        profit2 = (price - c2) * q2

        # Consumer surplus: integral from P to a of Q dP = (a - P) * Q / 2
        consumer_surplus = (a - price) * Q / 2.0
        consumer_surplus = max(consumer_surplus, 0.0)

        # Total welfare
        total_welfare = consumer_surplus + profit1 + profit2

        # HHI (Herfindahl-Hirschman Index)
        total_q = q1 + q2
        if total_q > 0:
            hhi = (q1 / total_q) ** 2 + (q2 / total_q) ** 2
        else:
            hhi = 0.0

        # Collusive (monopoly) outcome for comparison
        q_monopoly = (a - (c1 + c2) / 2) / (2 * b)
        q_monopoly = max(q_monopoly, 0.0)
        p_monopoly = a - b * q_monopoly
        profit_monopoly = (p_monopoly - (c1 + c2) / 2) * q_monopoly

        # Perfect competition outcome
        p_competitive = (c1 + c2) / 2.0
        q_competitive = (a - p_competitive) / b if b > 0 else 0.0
        q_competitive = max(q_competitive, 0.0)

        return {
            "q1": float(q1),
            "q2": float(q2),
            "total_quantity": float(Q),
            "price": float(price),
            "profit1": float(profit1),
            "profit2": float(profit2),
            "consumer_surplus": float(consumer_surplus),
            "total_welfare": float(total_welfare),
            "hhi": float(hhi),
            "market_share_1": float(q1 / (Q + 1e-15)),
            "market_share_2": float(q2 / (Q + 1e-15)),
            "comparison": {
                "monopoly_quantity": float(q_monopoly),
                "monopoly_price": float(p_monopoly),
                "monopoly_profit": float(profit_monopoly),
                "competitive_price": float(p_competitive),
                "competitive_quantity": float(q_competitive),
                "deadweight_loss": float(
                    0.5 * b * (q_competitive - Q) ** 2
                    if q_competitive > Q > 0
                    else 0.0
                ),
            },
        }
