"""
Macroeconomic and Financial Instability Models Module
====================================================
Provides implementations of key macroeconomic models including:
- New Keynesian DSGE (Dynamic Stochastic General Equilibrium)
- Taylor Rule for monetary policy analysis
- Phillips Curve for inflation-unemployment dynamics
- Minsky Financial Instability Hypothesis
- Kondratiev Long Wave detection and analysis
- Capital Structure theories (Modigliani-Miller, Trade-off, Pecking Order)

Dependencies: numpy, pandas, scipy (no external ML libraries)
"""

import numpy as np
import pandas as pd
from scipy import linalg, stats, signal, optimize, sparse
from scipy.sparse.linalg import spsolve


class DSGEModel:
    """
    Simplified New Keynesian Dynamic Stochastic General Equilibrium Model.

    Three-equation model:
      IS Curve:      y_t = E_t[y_{t+1}] - (1/σ)*(i_t - E_t[π_{t+1}] - r_t^n) + ε_t
      Phillips Curve: π_t = β*E_t[π_{t+1}] + κ*y_t + u_t
      Taylor Rule:    i_t = r* + π* + φ_π*(π_t - π*) + φ_y*y_t

    Solved via iterative rational expectations with a 2×2 linear system at each step.
    """

    def __init__(self):
        self.default_params = {
            'sigma': 1.0,        # Intertemporal elasticity of substitution
            'beta': 0.99,        # Discount factor
            'kappa': 0.1,        # Phillips curve slope
            'phi_pi': 1.5,       # Taylor rule inflation coefficient
            'phi_y': 0.5,        # Taylor rule output gap coefficient
            'r_natural': 0.01,   # Natural real interest rate
            'pi_target': 0.02,   # Inflation target
            'shock_std': 0.01,   # Standard deviation of structural shocks
        }

    def _solve_period(self, y_next, pi_next, r_natural, eps_t, u_t, params):
        """Solve the 2×2 linear system for (y_t, pi_t) given expectations."""
        sigma = params['sigma']
        beta = params['beta']
        kappa = params['kappa']
        phi_pi = params['phi_pi']
        phi_y = params['phi_y']
        r_star = params['r_natural']
        pi_star = params['pi_target']

        # Coefficient matrix A * [y_t, pi_t]' = [b1, b2]'
        # From Taylor rule substituted into IS curve, and NKPC
        A = np.array([
            [1.0 + phi_y / sigma, phi_pi / sigma],
            [-kappa, 1.0]
        ])

        # RHS from IS curve (with Taylor rule substitution) and NKPC
        b1 = (y_next
               - (1.0 / sigma) * ((r_star - r_natural)
                                   + (1.0 - phi_pi) * pi_star
                                   - pi_next)
               + eps_t)
        b2 = beta * pi_next + u_t

        return np.linalg.solve(A, np.array([b1, b2]))

    def _taylor_rate(self, pi_t, y_t, params):
        """Compute the policy rate from the Taylor rule."""
        return (params['r_natural'] + params['pi_target']
                + params['phi_pi'] * (pi_t - params['pi_target'])
                + params['phi_y'] * y_t)

    def simulate(self, n_periods=200, params=None):
        """
        Simulate the NK DSGE model under rational expectations.

        Uses iterative convergence: initialize at steady state, then
        repeatedly forward-simulate replacing E_t[x_{t+1}] with the
        value from the previous iteration until paths converge.

        Parameters
        ----------
        n_periods : int
            Number of simulation periods.
        params : dict, optional
            Model parameters. Uses defaults if None.

        Returns
        -------
        dict with keys: output, inflation, interest_rate, params
        """
        p = self.default_params.copy()
        if params is not None:
            p.update(params)

        T = n_periods
        shock_std = p['shock_std']
        np.random.seed(None)

        # Generate structural shocks
        eps = np.random.normal(0, shock_std, T)       # IS curve shock
        u = np.random.normal(0, shock_std, T)         # Phillips curve shock

        # Steady state
        y_ss = 0.0
        pi_ss = p['pi_target']
        i_ss = self._taylor_rate(pi_ss, y_ss, p)

        # Iterative rational expectations solution
        y_path = np.full(T, y_ss)
        pi_path = np.full(T, pi_ss)
        max_iter = 200
        tol = 1e-8

        for iteration in range(max_iter):
            y_old = y_path.copy()
            pi_old = pi_path.copy()

            for t in range(T):
                y_next = y_path[t + 1] if t < T - 1 else y_ss
                pi_next = pi_path[t + 1] if t < T - 1 else pi_ss

                sol = self._solve_period(y_next, pi_next, p['r_natural'],
                                         eps[t], u[t], p)
                y_path[t] = sol[0]
                pi_path[t] = sol[1]

            # Check convergence
            err_y = np.max(np.abs(y_path - y_old))
            err_pi = np.max(np.abs(pi_path - pi_old))
            if max(err_y, err_pi) < tol:
                break

        i_path = np.array([self._taylor_rate(pi_path[t], y_path[t], p)
                           for t in range(T)])

        return {
            'output': y_path,
            'inflation': pi_path,
            'interest_rate': i_path,
            'params': p,
        }

    def impulse_response(self, shock_type='monetary', n_periods=50):
        """
        Compute impulse response functions to a one-time structural shock.

        Parameters
        ----------
        shock_type : str
            'monetary' for a positive interest rate shock (contractionary),
            'fiscal' for a positive demand shock.
        n_periods : int
            Horizon for the IRF.

        Returns
        -------
        dict with keys: output_irf, inflation_irf, interest_rate_irf, shock_type
        """
        p = self.default_params.copy()
        T = n_periods

        y_irf = np.zeros(T)
        pi_irf = np.zeros(T)

        # One-time shock at t=0
        if shock_type == 'monetary':
            # Contractionary monetary shock: raise interest rate
            # Implemented as a negative demand shock equivalent
            eps_0 = -0.01
            u_0 = 0.0
        elif shock_type == 'fiscal':
            # Positive fiscal/demand shock
            eps_0 = 0.01
            u_0 = 0.0
        else:
            raise ValueError(f"Unknown shock type: {shock_type}")

        # Iterative solution with only the t=0 shock
        for iteration in range(300):
            y_old = y_irf.copy()
            pi_old = pi_irf.copy()

            for t in range(T):
                y_next = y_irf[t + 1] if t < T - 1 else 0.0
                pi_next = pi_irf[t + 1] if t < T - 1 else p['pi_target']

                eps_t = eps_0 if t == 0 else 0.0
                u_t = u_0 if t == 0 else 0.0

                sol = self._solve_period(y_next, pi_next, p['r_natural'],
                                         eps_t, u_t, p)
                y_irf[t] = sol[0]
                pi_irf[t] = sol[1]

            if max(np.max(np.abs(y_irf - y_old)),
                   np.max(np.abs(pi_irf - pi_old))) < 1e-10:
                break

        i_irf = np.array([self._taylor_rate(pi_irf[t], y_irf[t], p)
                          for t in range(T)])

        # Subtract steady state for pure impulse response
        i_irf -= self._taylor_rate(p['pi_target'], 0.0, p)

        return {
            'output_irf': y_irf,
            'inflation_irf': pi_irf,
            'interest_rate_irf': i_irf,
            'shock_type': shock_type,
        }

    def var_decomposition(self, n_simulations=1000, n_periods=50):
        """
        Variance decomposition of output and inflation forecast errors.

        Runs multiple simulations isolating each shock type to decompose
        the forecast error variance at each horizon.

        Parameters
        ----------
        n_simulations : int
            Number of simulation draws.
        n_periods : int
            Forecast horizon.

        Returns
        -------
        dict with keys: output_decomp, inflation_decomp, horizons
            Each decomp is a DataFrame with columns for shock contributions.
        """
        p = self.default_params.copy()
        T = n_periods

        # Run simulations with only IS shocks
        y_is_only = np.zeros((n_simulations, T))
        pi_is_only = np.zeros((n_simulations, T))
        # Run simulations with only Phillips curve shocks
        y_pc_only = np.zeros((n_simulations, T))
        pi_pc_only = np.zeros((n_simulations, T))

        for sim in range(n_simulations):
            # --- IS shocks only ---
            eps_is = np.random.normal(0, p['shock_std'], T)
            y_path = np.zeros(T)
            pi_path = np.full(T, p['pi_target'])
            for iteration in range(100):
                y_prev = y_path.copy()
                for t in range(T):
                    y_n = y_path[t + 1] if t < T - 1 else 0.0
                    pi_n = pi_path[t + 1] if t < T - 1 else p['pi_target']
                    sol = self._solve_period(y_n, pi_n, p['r_natural'],
                                             eps_is[t], 0.0, p)
                    y_path[t] = sol[0]
                    pi_path[t] = sol[1]
                if np.max(np.abs(y_path - y_prev)) < 1e-7:
                    break
            y_is_only[sim] = y_path
            pi_is_only[sim] = pi_path

            # --- Phillips curve shocks only ---
            u_pc = np.random.normal(0, p['shock_std'], T)
            y_path = np.zeros(T)
            pi_path = np.full(T, p['pi_target'])
            for iteration in range(100):
                pi_prev = pi_path.copy()
                for t in range(T):
                    y_n = y_path[t + 1] if t < T - 1 else 0.0
                    pi_n = pi_path[t + 1] if t < T - 1 else p['pi_target']
                    sol = self._solve_period(y_n, pi_n, p['r_natural'],
                                             0.0, u_pc[t], p)
                    y_path[t] = sol[0]
                    pi_path[t] = sol[1]
                if np.max(np.abs(pi_path - pi_prev)) < 1e-7:
                    break
            y_pc_only[sim] = y_path
            pi_pc_only[sim] = pi_path

        # Variance decomposition
        horizons = np.arange(1, T + 1)
        var_y_is = np.var(y_is_only, axis=0)
        var_y_pc = np.var(y_pc_only, axis=0)
        var_pi_is = np.var(pi_is_only, axis=0)
        var_pi_pc = np.var(pi_pc_only, axis=0)

        total_var_y = var_y_is + var_y_pc
        total_var_pi = var_pi_is + var_pi_pc

        share_y_is = np.where(total_var_y > 0, var_y_is / total_var_y, 0.5)
        share_y_pc = 1.0 - share_y_is
        share_pi_is = np.where(total_var_pi > 0, var_pi_is / total_var_pi, 0.5)
        share_pi_pc = 1.0 - share_pi_is

        output_decomp = pd.DataFrame({
            'horizon': horizons,
            'IS_shock_share': share_y_is,
            'NKPC_shock_share': share_y_pc,
            'IS_shock_var': var_y_is,
            'NKPC_shock_var': var_y_pc,
        })

        inflation_decomp = pd.DataFrame({
            'horizon': horizons,
            'IS_shock_share': share_pi_is,
            'NKPC_shock_share': share_pi_pc,
            'IS_shock_var': var_pi_is,
            'NKPC_shock_var': var_pi_pc,
        })

        return {
            'output_decomp': output_decomp,
            'inflation_decomp': inflation_decomp,
            'horizons': horizons,
        }


class TaylorRule:
    """
    Taylor Rule for monetary policy analysis.

    i_t = r* + π* + φ_π*(π_t - π*) + φ_y*y_t
    """

    def compute_rate(self, inflation, output_gap, pi_target=0.02, r_natural=0.01,
                     phi_pi=1.5, phi_y=0.5):
        """
        Compute the policy interest rate using the Taylor rule.

        Parameters
        ----------
        inflation : array-like
            Current inflation rates.
        output_gap : array-like
            Output gap (actual - potential) as fraction of potential.
        pi_target : float
            Central bank inflation target (default 2%).
        r_natural : float
            Equilibrium real interest rate (default 1%).
        phi_pi : float
            Weight on inflation deviation (Taylor principle: > 1).
        phi_y : float
            Weight on output gap.

        Returns
        -------
        dict with keys: rate, inflation_gap_contribution, output_gap_contribution, neutral_rate
        """
        inflation = np.asarray(inflation, dtype=float)
        output_gap = np.asarray(output_gap, dtype=float)

        neutral = r_natural + pi_target
        pi_contribution = phi_pi * (inflation - pi_target)
        y_contribution = phi_y * output_gap
        rate = neutral + pi_contribution + y_contribution

        return {
            'rate': rate,
            'inflation_gap_contribution': pi_contribution,
            'output_gap_contribution': y_contribution,
            'neutral_rate': neutral,
        }

    def fit_rule(self, inflation_series, interest_rate_series, output_gap_series):
        """
        Estimate Taylor rule parameters via OLS.

        Regresses: i_t - r* - π* = φ_π*(π_t - π*) + φ_y*y_t + ε_t
        Then recovers r* and π* from the intercept.

        Parameters
        ----------
        inflation_series : array-like
            Observed inflation rates.
        interest_rate_series : array-like
            Observed policy rates.
        output_gap_series : array-like
            Observed output gaps.

        Returns
        -------
        dict with keys: phi_pi, phi_y, r_star, pi_star, R_squared, std_errors, t_stats
        """
        pi = np.asarray(inflation_series, dtype=float)
        i = np.asarray(interest_rate_series, dtype=float)
        y = np.asarray(output_gap_series, dtype=float)

        n = len(i)
        if n < 4:
            raise ValueError("Need at least 4 observations to estimate Taylor rule.")

        # Regress: i_t = a0 + a1*pi_t + a2*y_t + eps
        X = np.column_stack([np.ones(n), pi, y])
        beta_ols = np.linalg.lstsq(X, i, rcond=None)[0]

        residuals = i - X @ beta_ols
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((i - np.mean(i)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        # Standard errors
        sigma2 = ss_res / (n - 3)
        XtX_inv = np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(XtX_inv) * sigma2)
        t_stats = beta_ols / se

        # Recover structural parameters
        # i = (r* + π* - φ_π*π* + φ_y*0) + φ_π*π + φ_y*y
        # intercept = r* + π*(1 - φ_π)
        # Assume π* ≈ mean(inflation) to identify r*
        pi_star_est = np.mean(pi)
        phi_pi = beta_ols[1]
        phi_y = beta_ols[2]
        r_star = beta_ols[0] - pi_star_est * (1.0 - phi_pi)

        return {
            'phi_pi': phi_pi,
            'phi_y': phi_y,
            'r_star': r_star,
            'pi_star': pi_star_est,
            'R_squared': r_squared,
            'std_errors': {'intercept': se[0], 'phi_pi': se[1], 'phi_y': se[2]},
            't_stats': {'intercept': t_stats[0], 'phi_pi': t_stats[1], 'phi_y': t_stats[2]},
        }

    def forecast_rates(self, inflation_forecast, output_gap_forecast, **params):
        """
        Forecast future policy rates using estimated or specified Taylor rule.

        Parameters
        ----------
        inflation_forecast : array-like
            Forecasted inflation path.
        output_gap_forecast : array-like
            Forecasted output gap path.
        **params
            Taylor rule parameters (pi_target, r_natural, phi_pi, phi_y).

        Returns
        -------
        dict with keys: forecast_rates, path, parameters
        """
        pi_target = params.get('pi_target', 0.02)
        r_natural = params.get('r_natural', 0.01)
        phi_pi = params.get('phi_pi', 1.5)
        phi_y = params.get('phi_y', 0.5)

        result = self.compute_rate(inflation_forecast, output_gap_forecast,
                                   pi_target, r_natural, phi_pi, phi_y)
        result['parameters'] = {
            'pi_target': pi_target, 'r_natural': r_natural,
            'phi_pi': phi_pi, 'phi_y': phi_y,
        }
        result['path'] = result['rate']
        return result


class PhillipsCurve:
    """
    Phillips Curve estimation and analysis.

    Traditional form:  π_t = α - β*u_t + γ*π_{t-1} + ε_t
    Expectations-augmented: π = π^e - β*(u - u*) + supply_shock
    """

    def estimate(self, unemployment, inflation, lags=1):
        """
        Estimate the Phillips curve via OLS with lagged inflation.

        π_t = α - β*u_t + γ*π_{t-1} + ε_t

        Parameters
        ----------
        unemployment : array-like
            Unemployment rate series.
        inflation : array-like
            Inflation rate series.
        lags : int
            Number of inflation lags (default 1).

        Returns
        -------
        dict with keys: alpha, beta, gamma, R_squared, nairu, std_errors, predictions
        """
        u = np.asarray(unemployment, dtype=float)
        pi = np.asarray(inflation, dtype=float)

        if len(u) != len(pi):
            raise ValueError("Unemployment and inflation must have same length.")
        if len(u) < lags + 3:
            raise ValueError("Insufficient observations for estimation.")

        # Build lagged inflation matrix
        pi_lagged = np.column_stack([pi[lags-k : len(pi)-k]
                                     for k in range(1, lags + 1)])
        u_trimmed = u[lags:]
        pi_trimmed = pi[lags:]

        n = len(pi_trimmed)
        X = np.column_stack([np.ones(n), -u_trimmed, pi_lagged])
        beta_ols = np.linalg.lstsq(X, pi_trimmed, rcond=None)[0]

        residuals = pi_trimmed - X @ beta_ols
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((pi_trimmed - np.mean(pi_trimmed)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        # Standard errors
        k_params = X.shape[1]
        sigma2 = ss_res / (n - k_params)
        se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * sigma2)

        # NAIRU estimation: steady state where E[π_t] = E[π_{t-1}]
        # π* = α - β*u* + γ*π*  =>  u* = (α - (1-γ)*π*) / β
        # where β is the coefficient on -u (positive means tradeoff exists)
        alpha = beta_ols[0]
        beta_u = beta_ols[1]  # coefficient on -u
        gamma_pi = beta_ols[2] if lags == 1 else np.sum(beta_ols[2:])
        pi_mean = np.mean(pi)

        nairu = None
        if abs(beta_u) > 1e-10:
            nairu = (alpha - (1.0 - gamma_pi) * pi_mean) / beta_u

        # Fitted values for full sample
        pi_fit_full = np.full(len(pi), np.nan)
        pi_fit_full[lags:] = X @ beta_ols

        return {
            'alpha': alpha,
            'beta': beta_u,
            'gamma': gamma_pi,
            'R_squared': r_squared,
            'nairu': nairu,
            'std_errors': se,
            'residuals': residuals,
            'predictions': pi_fit_full,
            'n_observations': n,
        }

    def expectations_augmented(self, unemployment, expected_inflation, params=None):
        """
        Compute inflation from the expectations-augmented Phillips curve.

        π = π^e - β*(u - u*) + supply_shock

        Parameters
        ----------
        unemployment : array-like
            Unemployment rates.
        expected_inflation : array-like
            Expected inflation rates.
        params : dict, optional
            Must contain 'beta' (slope), 'u_star' (NAIRU), 'supply_shock' (scalar).

        Returns
        -------
        dict with keys: inflation, unemployment_gap, expected_inflation_contribution,
                        unemployment_contribution, supply_shock_contribution
        """
        u = np.asarray(unemployment, dtype=float)
        pi_e = np.asarray(expected_inflation, dtype=float)

        if params is None:
            params = {'beta': 0.5, 'u_star': 0.05, 'supply_shock': 0.0}

        beta = params.get('beta', 0.5)
        u_star = params.get('u_star', 0.05)
        shock = params.get('supply_shock', 0.0)

        u_gap = u - u_star
        u_contribution = -beta * u_gap
        inflation = pi_e + u_contribution + shock

        return {
            'inflation': inflation,
            'unemployment_gap': u_gap,
            'expected_inflation_contribution': pi_e,
            'unemployment_contribution': u_contribution,
            'supply_shock_contribution': np.full_like(u, shock),
        }

    def curve_shift(self, base_unemployment, shock_values):
        """
        Simulate Phillips curve shifts under different supply shock scenarios.

        For each supply shock value, computes the Phillips curve:
        π = π_base - β*(u - u*) + shock

        Parameters
        ----------
        base_unemployment : array-like
            Range of unemployment values to evaluate.
        shock_values : array-like
            Supply shock magnitudes (e.g., [0, 0.01, 0.02, -0.01]).

        Returns
        -------
        dict with keys: unemployment_range, curves (dict of shock -> inflation), shifts
        """
        u_range = np.asarray(base_unemployment, dtype=float)
        shocks = np.asarray(shock_values, dtype=float)

        # Baseline Phillips curve parameters
        beta = 0.5
        u_star = 0.05
        pi_base = 0.02  # 2% baseline inflation

        curves = {}
        for s in shocks:
            pi = pi_base - beta * (u_range - u_star) + s
            curves[f'shock_{s:.3f}'] = pi

        # Compute vertical shifts relative to zero-shock curve
        baseline = curves.get('shock_0.000', pi_base - beta * (u_range - u_star))
        shifts = {f'shock_{s:.3f}': float(s) for s in shocks}

        return {
            'unemployment_range': u_range,
            'curves': curves,
            'shifts': shifts,
            'beta': beta,
            'nairu_used': u_star,
        }


class MinskyModel:
    """
    Minsky Financial Instability Hypothesis Model.

    Simulates the evolution of debt-to-income ratios and the transition
    through three financial regimes:
      - Hedge finance:    debt_service/income < 1
      - Speculative finance: 1 ≤ debt_service/income < 1 + margin
      - Ponzi finance:   debt_service/income ≥ 1 + margin

    The model incorporates endogenous risk perception, animal spirits,
    and a pro-cyclical leverage cycle that generates financial crises.
    """

    def __init__(self):
        self.default_params = {
            'base_interest_rate': 0.04,
            'base_profit_rate': 0.06,
            'base_gdp_growth': 0.025,
            'animal_spirits_sensitivity': 2.0,
            'risk_appetite_speed': 0.05,
            'borrowing_sensitivity': 0.8,
            'deleveraging_speed': 0.15,
            'speculative_margin': 0.3,
            'crisis_threshold': 0.6,
            'initial_debt_ratio': 0.5,
            'profit_shock_std': 0.01,
            'interest_shock_std': 0.005,
        }

    def simulate(self, n_periods=200, params=None):
        """
        Simulate the Minsky financial instability model.

        The debt-to-income ratio evolves as:
          d(D/Y)/dt = borrowing_propensity - (D/Y)*g + risk_appetite_feedback

        where borrowing_propensity depends on (profit_rate - interest_rate),
        animal spirits, and endogenous risk appetite.

        Parameters
        ----------
        n_periods : int
            Number of periods to simulate.
        params : dict, optional
            Model parameters overriding defaults.

        Returns
        -------
        dict with keys: debt_ratio, phase, gdp, crisis_flags, risk_appetite,
                        profit_rate, interest_rate
        """
        p = self.default_params.copy()
        if params is not None:
            p.update(params)

        T = n_periods
        margin = p['speculative_margin']
        crisis_thresh = p['crisis_threshold']

        # State variables
        debt_ratio = np.zeros(T)
        risk_appetite = np.zeros(T)
        gdp = np.zeros(T)
        profit_rate = np.zeros(T)
        interest_rate = np.zeros(T)
        animal_spirits = np.zeros(T)
        phase = np.empty(T, dtype=object)
        crisis_flags = np.zeros(T, dtype=bool)

        # Initial conditions
        debt_ratio[0] = p['initial_debt_ratio']
        risk_appetite[0] = 0.5
        gdp[0] = 100.0
        profit_rate[0] = p['base_profit_rate']
        interest_rate[0] = p['base_interest_rate']
        animal_spirits[0] = 0.5

        rng = np.random.default_rng()

        for t in range(T):
            # Stochastic profit and interest rates
            if t > 0:
                profit_rate[t] = p['base_profit_rate'] + rng.normal(0, p['profit_shock_std'])
                interest_rate[t] = (p['base_interest_rate']
                                     + 0.01 * max(0, debt_ratio[t-1] - 1.0)  # risk premium
                                     + rng.normal(0, p['interest_shock_std']))
                interest_rate[t] = max(0.001, interest_rate[t])

            # Debt service to income ratio
            dsr = debt_ratio[t] * interest_rate[t]

            # Classify financial regime
            if dsr < 1.0:
                phase[t] = 'hedge'
            elif dsr < 1.0 + margin:
                phase[t] = 'speculative'
            else:
                phase[t] = 'ponzi'

            # Crisis detection: large share would be ponzi + high debt
            if phase[t] == 'ponzi' and debt_ratio[t] > crisis_thresh:
                crisis_flags[t] = True

            # Animal spirits: pro-cyclical confidence
            # Rises during expansions (positive GDP gap), falls during contractions
            gdp_growth = p['base_gdp_growth']
            if phase[t] == 'hedge':
                gdp_growth += 0.005 * animal_spirits[t]
            elif phase[t] == 'speculative':
                gdp_growth += 0.002 * animal_spirits[t]
            elif phase[t] == 'ponzi':
                gdp_growth -= 0.02 * (dsr - 1.0)

            if crisis_flags[t]:
                gdp_growth -= 0.05

            gdp_growth += rng.normal(0, 0.005)

            # Endogenous risk appetite: adapts to recent conditions
            if t > 0:
                recent_returns = (profit_rate[t] - interest_rate[t])
                # Risk appetite rises when profits exceed interest costs
                risk_target = np.clip(0.5 + p['animal_spirits_sensitivity'] * recent_returns, 0.1, 0.95)
                if crisis_flags[t]:
                    risk_target = 0.1  # Fear sets in during crisis
                risk_appetite[t] += p['risk_appetite_speed'] * (risk_target - risk_appetite[t-1])
                risk_appetite[t] = np.clip(risk_appetite[t], 0.05, 0.98)

            # Animal spirits update
            if t > 0:
                spirits_target = risk_appetite[t]
                animal_spirits[t] = 0.9 * animal_spirits[t-1] + 0.1 * spirits_target

            # Debt ratio dynamics
            if t < T - 1:
                # Borrowing propensity: positive when profits > interest
                spread = profit_rate[t] - interest_rate[t]
                base_borrowing = p['borrowing_sensitivity'] * max(0, spread)
                borrowing = base_borrowing * risk_appetite[t] * (1.0 + animal_spirits[t])

                # Deleveraging pressure (strong during crisis)
                deleveraging = 0.0
                if crisis_flags[t] or phase[t] == 'ponzi':
                    deleveraging = (p['deleveraging_speed']
                                    * max(0, debt_ratio[t] - 0.3))

                # d(D/Y) = borrowing - (D/Y)*g - deleveraging
                debt_ratio[t+1] = (debt_ratio[t]
                                    + borrowing
                                    - debt_ratio[t] * gdp_growth
                                    - deleveraging)
                debt_ratio[t+1] = max(0.01, debt_ratio[t+1])

                # GDP evolution
                gdp[t+1] = gdp[t] * (1.0 + gdp_growth)

        return {
            'debt_ratio': debt_ratio,
            'phase': phase,
            'gdp': gdp,
            'crisis_flags': crisis_flags,
            'risk_appetite': risk_appetite,
            'profit_rate': profit_rate,
            'interest_rate': interest_rate,
            'animal_spirits': animal_spirits,
            'params': p,
        }

    def financial_instability_index(self, debt_ratios, profit_rates, asset_prices):
        """
        Compute a Minsky-inspired Financial Instability Index (0-100).

        Combines four sub-indices:
          1. Leverage index: based on debt-to-income ratio level
          2. Coverage index: based on profit-to-interest coverage
          3. Asset price deviation: bubble detection
          4. Momentum index: rate of change of leverage

        Parameters
        ----------
        debt_ratios : array-like
            Debt-to-income ratio time series.
        profit_rates : array-like
            Profit rate time series.
        asset_prices : array-like
            Asset price index time series.

        Returns
        -------
        dict with keys: index, sub_indices, interpretation
        """
        d = np.asarray(debt_ratios, dtype=float)
        pr = np.asarray(profit_rates, dtype=float)
        ap = np.asarray(asset_prices, dtype=float)
        T = len(d)

        # 1. Leverage sub-index (0-100): higher debt ratio = more unstable
        leverage_index = np.clip(100 * (d - 0.2) / 1.3, 0, 100)

        # 2. Coverage sub-index (0-100): lower coverage = more unstable
        coverage = pr / 0.04  # coverage relative to 4% benchmark
        coverage_index = np.clip(100 * (1.0 - coverage), 0, 100)

        # 3. Asset price deviation from trend (0-100)
        if T >= 8:
            # Use centered moving average as trend
            kernel = np.ones(8) / 8.0
            trend = np.convolve(ap, kernel, mode='same')
            deviation = (ap - trend) / np.where(np.abs(trend) > 1e-10, trend, 1.0)
            bubble_index = np.clip(100 * (1.0 + deviation), 0, 100)
        else:
            bubble_index = np.full(T, 50.0)

        # 4. Leverage momentum (0-100): rising leverage = more unstable
        if T >= 2:
            d_change = np.diff(d, prepend=d[0])
            momentum_index = np.clip(100 * (d_change + 0.02) / 0.06, 0, 100)
        else:
            momentum_index = np.full(T, 50.0)

        # Weighted composite (leverage most important)
        weights = np.array([0.35, 0.25, 0.20, 0.20])
        index = (weights[0] * leverage_index
                 + weights[1] * coverage_index
                 + weights[2] * bubble_index
                 + weights[3] * momentum_index)

        # Interpretation
        def _interpret(val):
            if val < 25:
                return 'Hedge finance dominance — low instability'
            elif val < 50:
                return 'Moderate instability — speculative finance emerging'
            elif val < 75:
                return 'High instability — significant speculative/ponzi activity'
            else:
                return 'Extreme instability — crisis likely imminent'

        return {
            'index': index,
            'sub_indices': {
                'leverage': leverage_index,
                'coverage': coverage_index,
                'asset_bubble': bubble_index,
                'momentum': momentum_index,
            },
            'weights': {'leverage': 0.35, 'coverage': 0.25,
                        'asset_bubble': 0.20, 'momentum': 0.20},
            'interpretation': [_interpret(v) for v in index],
        }

    def detect_ponzi_regime(self, debt_ratios, profit_rates, asset_prices):
        """
        Estimate the probability of being in a Ponzi finance regime.

        Uses a logistic model combining:
          - Debt service burden relative to income
          - Profit-to-interest coverage ratio
          - Asset price trend (falling prices increase Ponzi probability)
          - Leverage trajectory

        Parameters
        ----------
        debt_ratios : array-like
            Debt-to-income ratio series.
        profit_rates : array-like
            Profit rate series.
        asset_prices : array-like
            Asset price index series.

        Returns
        -------
        dict with keys: ponzi_probability, z_score, regime_classification
        """
        d = np.asarray(debt_ratios, dtype=float)
        pr = np.asarray(profit_rates, dtype=float)
        ap = np.asarray(asset_prices, dtype=float)
        T = len(d)

        r_interest = 0.04  # assumed average interest rate

        # Z-score components (higher = more likely Ponzi)
        # 1. Debt service burden
        dsr = d * r_interest
        z_dsr = (dsr - 0.8) / 0.3  # normalized: 0.8 is threshold area

        # 2. Coverage ratio (profit / interest expense)
        interest_expense = d * r_interest
        coverage = pr / np.where(interest_expense > 0.001, interest_expense, 0.001)
        z_coverage = (1.5 - coverage) / 0.5  # low coverage -> high z

        # 3. Asset price trend (negative trend -> higher Ponzi prob)
        if T >= 4:
            ap_trend = np.zeros(T)
            for t in range(T):
                start = max(0, t - 3)
                window = ap[start:t+1]
                if len(window) > 1:
                    ap_trend[t] = (window[-1] - window[0]) / window[0]
            z_trend = -ap_trend / 0.05  # falling prices -> positive z
        else:
            z_trend = np.zeros(T)

        # 4. Leverage acceleration
        if T >= 2:
            d_accel = np.diff(d, prepend=d[0])
            z_accel = d_accel / 0.02
        else:
            z_accel = np.zeros(T)

        # Combined z-score
        z_score = 0.35 * z_dsr + 0.30 * z_coverage + 0.20 * z_trend + 0.15 * z_accel

        # Logistic transformation to probability
        ponzi_prob = 1.0 / (1.0 + np.exp(-z_score))

        # Classification
        regime = np.where(ponzi_prob < 0.33, 'hedge',
                          np.where(ponzi_prob < 0.66, 'speculative', 'ponzi'))

        return {
            'ponzi_probability': ponzi_prob,
            'z_score': z_score,
            'regime_classification': regime,
        }


class KondratievWaves:
    """
    Kondratiev Long Wave detection and analysis.

    Detects 40-60 year economic super-cycles using spectral analysis (FFT),
    Hodrick-Prescott filtering, and Baxter-King bandpass filtering.
    """

    def detect_waves(self, gdp_series, min_cycle_length=40, max_cycle_length=60):
        """
        Detect Kondratiev long waves in a GDP series.

        Uses FFT peak detection within the specified cycle length band
        and HP filtering for trend-cycle separation.

        Parameters
        ----------
        gdp_series : array-like
            GDP time series (annual or quarterly data).
        min_cycle_length : int
            Minimum Kondratiev wave period (default 40 years).
        max_cycle_length : int
            Maximum Kondratiev wave period (default 60 years).

        Returns
        -------
        dict with keys: detected_cycles, wave_periods, current_phase,
                        dominant_frequency, cycle_component
        """
        y = np.asarray(gdp_series, dtype=float)
        T = len(y)
        if T < 20:
            raise ValueError("Series too short for Kondratiev wave detection (need >= 20).")

        # Detrend: take log and remove linear trend
        log_y = np.log(y)
        t_idx = np.arange(T)
        trend_coefs = np.polyfit(t_idx, log_y, 1)
        trend_line = np.polyval(trend_coefs, t_idx)
        detrended = log_y - trend_line

        # FFT analysis
        fft_result = self.fft_analysis(detrended)

        # Find peaks in the Kondratiev frequency band
        freqs = fft_result['frequencies']
        amps = fft_result['amplitudes']
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

        # Identify cycles in the target band
        in_band = (periods >= min_cycle_length) & (periods <= max_cycle_length) & (freqs > 0)
        band_amps = amps.copy()
        band_amps[~in_band] = 0

        # Find dominant cycle in band
        if np.any(in_band & (band_amps > 0)):
            band_indices = np.where(in_band)[0]
            dominant_idx = band_indices[np.argmax(band_amps[band_indices])]
            dominant_period = periods[dominant_idx]
            dominant_freq = freqs[dominant_idx]
            detected = True
        else:
            # Fall back to the closest frequency
            positive = freqs > 0
            if np.any(positive):
                idx = positive.nonzero()[0]
                closest_idx = idx[np.argmin(np.abs(periods[idx] - (min_cycle_length + max_cycle_length) / 2))]
                dominant_period = periods[closest_idx]
                dominant_freq = freqs[closest_idx]
            else:
                dominant_period = (min_cycle_length + max_cycle_length) / 2
                dominant_freq = 1.0 / dominant_period
            detected = False

        # Extract cycle component using HP filter with very high lambda
        # For annual data detecting ~50 year cycles: lambda ~ 6.25 * 50^4 ≈ 390,625
        hp_lambda = 6.25 * dominant_period ** 4
        hp_result = self.hp_filter(detrended, lambda_=min(hp_lambda, 1e7))
        cycle_component = hp_result['cycle']

        # Determine current phase
        phase_info = self.current_wave_phase(y)

        return {
            'detected_cycles': detected,
            'wave_periods': {
                'dominant': dominant_period,
                'min_band': min_cycle_length,
                'max_band': max_cycle_length,
            },
            'current_phase': phase_info,
            'dominant_frequency': dominant_freq,
            'cycle_component': cycle_component,
            'fft_result': fft_result,
        }

    def fft_analysis(self, series):
        """
        FFT-based frequency analysis of a time series.

        Parameters
        ----------
        series : array-like
            Input time series.

        Returns
        -------
        dict with keys: frequencies, amplitudes, dominant_period, power_spectrum, phases
        """
        y = np.asarray(series, dtype=float)
        T = len(y)

        # Demean
        y_centered = y - np.mean(y)

        # Apply Hanning window to reduce spectral leakage
        window = np.hanning(T)
        y_windowed = y_centered * window

        # FFT
        fft_vals = np.fft.rfft(y_windowed)
        n_freq = len(fft_vals)

        # Frequencies (cycles per observation)
        frequencies = np.fft.rfftfreq(T)

        # Amplitudes (normalized)
        amplitudes = 2.0 * np.abs(fft_vals) / np.sum(window)
        amplitudes[0] /= 2.0  # DC component

        # Power spectrum
        power = np.abs(fft_vals) ** 2

        # Phase angles
        phases = np.angle(fft_vals)

        # Dominant period (exclude DC component)
        if n_freq > 1:
            non_dc = np.arange(1, n_freq)
            dom_idx = non_dc[np.argmax(amplitudes[non_dc])]
            dominant_period = 1.0 / frequencies[dom_idx] if frequencies[dom_idx] > 0 else np.inf
        else:
            dominant_period = np.inf
            dom_idx = 0

        return {
            'frequencies': frequencies,
            'amplitudes': amplitudes,
            'dominant_period': dominant_period,
            'power_spectrum': power,
            'phases': phases,
            'dominant_index': dom_idx,
        }

    def hp_filter(self, series, lambda_=100):
        """
        Hodrick-Prescott trend-cycle decomposition, implemented from scratch.

        Minimizes: sum((y_t - τ_t)²) + λ * sum((Δ²τ_t)²)
        Solved as: (I + λ * D'D) * τ = y  using sparse matrices.

        Parameters
        ----------
        series : array-like
            Input time series.
        lambda_ : float
            Smoothing parameter. Common values:
              - 100 for annual data (Ravn-Uhlig convention: 6.25 for annual, 1600 for quarterly)
              - 1600 for quarterly data
              - 100 for monthly data

        Returns
        -------
        dict with keys: trend, cycle, lambda
        """
        y = np.asarray(series, dtype=float)
        T = len(y)

        if T < 4:
            return {
                'trend': y.copy(),
                'cycle': np.zeros(T),
                'lambda': lambda_,
            }

        # Construct second-difference matrix D: (T-2) x T
        # D[i, i] = 1, D[i, i+1] = -2, D[i, i+2] = 1
        diag_main = np.ones(T - 2)
        diag_upper = -2.0 * np.ones(T - 2)
        diag_upper2 = np.ones(T - 2)

        D = sparse.diags([diag_main, diag_upper, diag_upper2], [0, 1, 2],
                         shape=(T - 2, T), format='csc')

        # Construct (I + λ * D'D)
        DtD = D.T @ D
        A = sparse.eye(T, format='csc') + lambda_ * DtD

        # Solve for trend
        trend = spsolve(A, y)
        cycle = y - trend

        return {
            'trend': trend,
            'cycle': cycle,
            'lambda': lambda_,
        }

    def baxter_king_filter(self, series, low=6, high=32, k=12):
        """
        Baxter-King bandpass filter for business cycle extraction.

        Extracts cyclical components with periods between `low` and `high`
        observations using frequency-domain bandpass filtering.

        Parameters
        ----------
        series : array-like
            Input time series.
        low : int
            Minimum period (shortest cycle to keep).
        high : int
            Maximum period (longest cycle to keep).
        k : int
            Number of leading/trailing observations to trim (filter lag).

        Returns
        -------
        dict with keys: filtered_cycle, original, trim_k
        """
        y = np.asarray(series, dtype=float)
        T = len(y)

        if T < 2 * k + 4:
            return {
                'filtered_cycle': np.full(T, np.nan),
                'original': y,
                'trim_k': k,
            }

        # Frequency-domain bandpass filter
        y_centered = y - np.mean(y)

        # Compute ideal bandpass filter weights in frequency domain
        # Band: [2π/high, 2π/low]
        omega_low = 2.0 * np.pi / high
        omega_high = 2.0 * np.pi / low

        # Construct bandpass weights a_j for j = -k, ..., k
        # a_j = (1/π) * [sin(j*ω_high) - sin(j*ω_low)]/j  for j ≠ 0
        # a_0 = (ω_high - ω_low) / π
        weights = np.zeros(2 * k + 1)
        center = k
        weights[center] = (omega_high - omega_low) / np.pi

        for j in range(1, k + 1):
            w_j = (np.sin(j * omega_high) - np.sin(j * omega_low)) / (j * np.pi)
            weights[center + j] = w_j
            weights[center - j] = w_j

        # Apply symmetric moving average filter
        filtered = np.full(T, np.nan)
        for t in range(k, T - k):
            filtered[t] = np.sum(weights * y_centered[t - k:t + k + 1])

        return {
            'filtered_cycle': filtered,
            'original': y,
            'trim_k': k,
            'weights': weights,
            'band': {'low_period': low, 'high_period': high},
        }

    def current_wave_phase(self, gdp_series):
        """
        Determine the current position in the Kondratiev wave.

        Phases:
          - Spring (0-90°):   Expansion begins, rising from trough
          - Summer (90-180°): Prosperity, approaching peak
          - Autumn (180-270°): Contraction begins, past peak
          - Winter (270-360°): Depression, approaching trough

        Parameters
        ----------
        gdp_series : array-like
            GDP time series.

        Returns
        -------
        dict with keys: phase, years_into_phase, description, phase_angle
        """
        y = np.asarray(gdp_series, dtype=float)
        T = len(y)

        if T < 10:
            return {
                'phase': 'unknown',
                'years_into_phase': 0,
                'description': 'Insufficient data for Kondratiev phase detection',
                'phase_angle': None,
            }

        # Extract cycle using HP filter (high lambda for long waves)
        log_y = np.log(y)
        hp_lambda = min(6.25 * 50 ** 4, 1e7)  # tuned for ~50-year cycles
        hp_result = self.hp_filter(log_y, lambda_=hp_lambda)
        cycle = hp_result['cycle']

        # Determine phase from the last portion of the cycle
        # Use the relationship between cycle value and its rate of change
        n_recent = min(20, T // 4)
        recent_cycle = cycle[-n_recent:]
        current_val = cycle[-1]

        # Estimate derivative (rate of change)
        if len(recent_cycle) >= 2:
            derivative = recent_cycle[-1] - recent_cycle[-2]
        else:
            derivative = 0.0

        # Classify phase
        if current_val >= 0 and derivative > 0:
            phase = 'spring'
            description = ('Expansion phase — economy rising from trough. '
                           'Innovations diffuse, new industries emerge, '
                           'credit growth accelerates.')
        elif current_val >= 0 and derivative <= 0:
            phase = 'summer'
            description = ('Prosperity phase — economy near peak. '
                           'Full employment, high asset prices, potential overinvestment, '
                           'inflationary pressures building.')
        elif current_val < 0 and derivative <= 0:
            phase = 'autumn'
            description = ('Contraction phase — economy declining from peak. '
                           'Deleveraging, falling asset prices, rising unemployment, '
                           'financial stress emerges.')
        else:
            phase = 'winter'
            description = ('Depression phase — economy near trough. '
                           'Creative destruction, old industries decline, '
                           'foundation for next wave being laid.')

        # Estimate years into current phase
        # Find the last zero-crossing or turning point
        years_into = 0
        for i in range(T - 2, max(T - n_recent - 1, 0), -1):
            if (cycle[i] * cycle[i + 1] <= 0) or \
               (i > 0 and (cycle[i] - cycle[i-1]) * (cycle[i+1] - cycle[i]) < 0):
                years_into = T - 1 - i
                break
        else:
            years_into = n_recent

        # Estimate phase angle (0-360 degrees)
        cycle_std = np.std(cycle)
        if cycle_std > 1e-12:
            normalized_val = current_val / cycle_std
            normalized_deriv = derivative / cycle_std
            # Use atan2-like logic: angle from positive x-axis
            phase_angle = np.degrees(np.arctan2(-normalized_deriv, normalized_val))
            phase_angle = phase_angle % 360
        else:
            phase_angle = 0.0

        return {
            'phase': phase,
            'years_into_phase': years_into,
            'description': description,
            'phase_angle': phase_angle,
            'cycle_value': current_val,
            'cycle_derivative': derivative,
        }


class CapitalStructure:
    """
    Capital structure theory models.

    Implements Modigliani-Miller propositions, trade-off theory,
    and pecking order theory for optimal capital structure determination.
    """

    def modigliani_miller(self, V_u, debt, r_d, tax_rate=0.0, with_tax=True):
        """
        Modigliani-Miller Propositions I and II.

        Without taxes:  V_L = V_U,  r_E = r_A + (r_A - r_D)*(D/E)
        With taxes:    V_L = V_U + T*D,  r_E = r_A + (r_A - r_D)*(D/E)*(1-T)

        Parameters
        ----------
        V_u : float
            Value of unlevered firm.
        debt : float or array-like
            Market value of debt.
        r_d : float
            Cost of debt.
        tax_rate : float
            Corporate tax rate (default 0).
        with_tax : bool
            Whether to include tax shield (default True).

        Returns
        -------
        dict with keys: V_L, r_E, WACC, r_A, tax_shield, D, E
        """
        D = np.asarray(debt, dtype=float)
        scalar = D.ndim == 0
        D = np.atleast_1d(D)

        # Assume r_A = r_D for unlevered firm (MM assumption)
        r_A = r_d  # In MM world, unlevered cost of capital equals cost of debt
        # More realistically, r_A could be specified separately

        E = V_u - D  # Equity = firm value - debt (for levered firm with tax)
        E = np.maximum(E, 1e-10)  # Avoid division by zero

        if with_tax and tax_rate > 0:
            tax_shield = tax_rate * D
            V_L = V_u + tax_shield
            r_E = r_A + (r_A - r_d) * (D / E) * (1.0 - tax_rate)
        else:
            tax_shield = np.zeros_like(D)
            V_L = np.full_like(D, V_u, dtype=float)
            r_E = r_A + (r_A - r_d) * (D / E)

        # WACC = (D/V_L)*r_D*(1-T) + (E/V_L)*r_E
        WACC = (D / V_L) * r_d * (1.0 - tax_rate) + (E / V_L) * r_E

        result = {
            'V_L': V_L,
            'r_E': r_E,
            'WACC': WACC,
            'r_A': r_A,
            'tax_shield': tax_shield,
            'D': D,
            'E': E,
            'tax_rate': tax_rate,
            'with_tax': with_tax,
        }

        if scalar:
            for key in ['V_L', 'r_E', 'WACC', 'tax_shield', 'D', 'E']:
                result[key] = float(result[key][0])

        return result

    def trade_off_theory(self, V_unlevered, tax_benefit_rate, bankruptcy_cost_func,
                         debt_levels=None):
        """
        Trade-off theory: optimal capital structure balances tax shields
        against bankruptcy costs.

        V_L(D) = V_U + PV(tax_shield) - PV(bankruptcy_costs)

        Optimal D maximizes V_L.

        Parameters
        ----------
        V_unlevered : float
            Value of the all-equity firm.
        tax_benefit_rate : float
            Marginal tax benefit per unit of debt (= corporate tax rate).
        bankruptcy_cost_func : callable
            Function f(D, V_U) -> float giving present value of expected
            bankruptcy costs at debt level D.
        debt_levels : array-like, optional
            Debt levels to evaluate. Auto-generated if None.

        Returns
        -------
        dict with keys: optimal_debt, max_value, curve, WACC_curve
        """
        if debt_levels is None:
            debt_levels = np.linspace(0, V_unlevered * 1.5, 200)
        else:
            debt_levels = np.asarray(debt_levels, dtype=float)

        n = len(debt_levels)
        V_L = np.zeros(n)
        tax_shield = np.zeros(n)
        bank_costs = np.zeros(n)

        for i, D in enumerate(debt_levels):
            ts = tax_benefit_rate * D
            bc = bankruptcy_cost_func(D, V_unlevered)
            tax_shield[i] = ts
            bank_costs[i] = bc
            V_L[i] = V_unlevered + ts - bc

        # Find optimal debt level
        opt_idx = np.argmax(V_L)
        optimal_debt = debt_levels[opt_idx]
        max_value = V_L[opt_idx]

        return {
            'optimal_debt': optimal_debt,
            'max_value': max_value,
            'curve': {
                'debt': debt_levels,
                'firm_value': V_L,
                'tax_shield': tax_shield,
                'bankruptcy_costs': bank_costs,
                'net_benefit': tax_shield - bank_costs,
            },
            'optimal_leverage': optimal_debt / max_value if max_value > 0 else 0,
        }

    def pecking_order(self, internal_funds, debt_capacity, equity_issuance_cost,
                      investment_needed):
        """
        Pecking order theory of capital structure.

        Financing hierarchy: internal funds → debt → equity.
        Each source has increasing costs due to information asymmetry.

        Parameters
        ----------
        internal_funds : float
            Available internal funds (retained earnings).
        debt_capacity : float
            Maximum debt the firm can raise.
        equity_issuance_cost : float
            Cost of issuing equity as a fraction (e.g., 0.15 = 15%).
            Includes underpricing, flotation costs, and signaling costs.
        investment_needed : float
            Total investment required.

        Returns
        -------
        dict with keys: financing_plan, total_cost, cost_breakdown, deficit
        """
        remaining = investment_needed
        plan = {'internal': 0.0, 'debt': 0.0, 'equity': 0.0}
        costs = {'internal': 0.0, 'debt': 0.0, 'equity': 0.0}

        # 1. Internal funds (lowest cost — just opportunity cost, ~0)
        internal_used = min(internal_funds, remaining)
        plan['internal'] = internal_used
        costs['internal'] = 0.0  # Internal funds have negligible explicit cost
        remaining -= internal_used

        # 2. Debt (moderate cost — interest expense, ~6% assumed)
        cost_of_debt = 0.06
        debt_used = 0.0
        if remaining > 0 and debt_capacity > 0:
            debt_used = min(debt_capacity, remaining)
            plan['debt'] = debt_used
            costs['debt'] = debt_used * cost_of_debt
            remaining -= debt_used

        # 3. Equity (highest cost — issuance costs + signaling penalty)
        equity_used = max(0, remaining)
        plan['equity'] = equity_used
        costs['equity'] = equity_used * equity_issuance_cost + equity_used * cost_of_debt * 1.5
        # Cost of equity includes issuance cost plus higher required return
        remaining -= equity_used

        total_cost = sum(costs.values())

        return {
            'financing_plan': plan,
            'total_cost': total_cost,
            'cost_breakdown': costs,
            'deficit': max(0, -remaining),  # Should be 0 if fully financed
            'fully_financed': remaining <= 1e-10,
            'internal_funds_available': internal_funds,
            'debt_capacity_available': debt_capacity,
            'equity_issuance_cost_rate': equity_issuance_cost,
        }
