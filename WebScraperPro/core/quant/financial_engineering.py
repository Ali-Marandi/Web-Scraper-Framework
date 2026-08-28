"""
Financial Engineering Module for Quantitative Finance Engine.

Provides Black-Scholes pricing, Monte Carlo simulation, interest rate models,
and option strategy analysis. All mathematical implementations are from scratch
using numpy, pandas, and scipy.special (ndtr only). No statsmodels dependency.
"""

import numpy as np
import pandas as pd
from scipy.special import ndtr
from typing import Dict, List, Optional, Tuple, Union


class BlackScholes:
    """Black-Scholes option pricing model and related computations."""

    def _d1_d2(self, S: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
        """Compute d1 and d2 for the Black-Scholes formula.

        Parameters
        ----------
        S : float
            Current underlying price.
        K : float
            Strike price.
        T : float
            Time to expiry in years.
        r : float
            Risk-free interest rate (annualized, continuous).
        sigma : float
            Volatility (annualized).

        Returns
        -------
        tuple (d1, d2)
        """
        if T <= 0:
            return 0.0, 0.0
        sqrt_T = np.sqrt(T)
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        return d1, d2

    def european_call(self, S: float, K: float, T: float, r: float, sigma: float) -> Dict:
        """Price a European call option using the Black-Scholes formula.

        C = S * N(d1) - K * exp(-rT) * N(d2)

        Returns dict with price, d1, d2.
        """
        if T <= 0:
            intrinsic = max(S - K, 0.0)
            return {"price": intrinsic, "d1": 0.0, "d2": 0.0}
        if sigma <= 0:
            intrinsic = max(S - K, 0.0)
            return {"price": np.exp(-r * T) * intrinsic, "d1": 0.0, "d2": 0.0}
        d1, d2 = self._d1_d2(S, K, T, r, sigma)
        price = S * ndtr(d1) - K * np.exp(-r * T) * ndtr(d2)
        return {"price": price, "d1": d1, "d2": d2}

    def european_put(self, S: float, K: float, T: float, r: float, sigma: float) -> Dict:
        """Price a European put option using the Black-Scholes formula.

        P = K * exp(-rT) * N(-d2) - S * N(-d1)

        Returns dict with price, d1, d2.
        """
        if T <= 0:
            intrinsic = max(K - S, 0.0)
            return {"price": intrinsic, "d1": 0.0, "d2": 0.0}
        if sigma <= 0:
            intrinsic = max(K - S, 0.0)
            return {"price": np.exp(-r * T) * intrinsic, "d1": 0.0, "d2": 0.0}
        d1, d2 = self._d1_d2(S, K, T, r, sigma)
        price = K * np.exp(-r * T) * ndtr(-d2) - S * ndtr(-d1)
        return {"price": price, "d1": d1, "d2": d2}

    def greeks(self, S: float, K: float, T: float, r: float, sigma: float) -> Dict:
        """Compute Black-Scholes Greeks for a European call option.

        Delta  = N(d1)
        Gamma  = n(d1) / (S * sigma * sqrt(T))
        Theta  = -(S * n(d1) * sigma) / (2*sqrt(T)) - r*K*exp(-rT)*N(d2)
        Vega   = S * n(d1) * sqrt(T)
        Rho    = K * T * exp(-rT) * N(d2)

        where n(x) is the standard normal PDF.
        """
        if T <= 0 or sigma <= 0:
            return {
                "delta": float(S > K),
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0,
            }

        d1, d2 = self._d1_d2(S, K, T, r, sigma)
        sqrt_T = np.sqrt(T)
        exp_neg_rT = np.exp(-r * T)

        # Standard normal PDF: n(x) = exp(-x^2/2) / sqrt(2*pi)
        nd1_pdf = np.exp(-0.5 * d1 ** 2) / np.sqrt(2.0 * np.pi)

        delta = ndtr(d1)
        gamma = nd1_pdf / (S * sigma * sqrt_T)
        theta = (-(S * nd1_pdf * sigma) / (2.0 * sqrt_T)
                 - r * K * exp_neg_rT * ndtr(d2))
        # Vega is per 1.0 change in sigma (not per 0.01)
        vega = S * nd1_pdf * sqrt_T
        rho = K * T * exp_neg_rT * ndtr(d2)

        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega,
            "rho": rho,
        }

    def implied_volatility(self, market_price: float, S: float, K: float, T: float,
                           r: float, option_type: str = 'call',
                           max_iter: int = 200, tol: float = 1e-10) -> Dict:
        """Estimate implied volatility via Newton-Raphson.

        Iterates: sigma_{n+1} = sigma_n - (BS_price - market_price) / vega

        Parameters
        ----------
        market_price : float
            Observed market price of the option.
        option_type : str
            'call' or 'put'.

        Returns dict with implied_vol, iterations, converged.
        """
        if T <= 0:
            return {"implied_vol": 0.0, "iterations": 0, "converged": False,
                    "error": "Time to expiry must be positive."}

        if market_price < 0:
            return {"implied_vol": np.nan, "iterations": 0, "converged": False,
                    "error": "Market price must be non-negative."}

        # Initial guess: use Brenner-Subrahmanyam approximation for ATM calls
        if option_type == 'call':
            intrinsic = max(S - K, 0.0)
            time_value = market_price - intrinsic
            if time_value <= 0:
                sigma = 0.01
            else:
                sigma = time_value * np.sqrt(2.0 * np.pi) / (S * 0.4 * np.sqrt(T))
        else:
            intrinsic = max(K - S, 0.0)
            time_value = market_price - intrinsic
            if time_value <= 0:
                sigma = 0.01
            else:
                sigma = time_value * np.sqrt(2.0 * np.pi) / (S * 0.4 * np.sqrt(T))

        sigma = max(sigma, 1e-6)

        converged = False
        for i in range(max_iter):
            d1, d2 = self._d1_d2(S, K, T, r, sigma)
            sqrt_T = np.sqrt(T)
            nd1_pdf = np.exp(-0.5 * d1 ** 2) / np.sqrt(2.0 * np.pi)

            if option_type == 'call':
                price = S * ndtr(d1) - K * np.exp(-r * T) * ndtr(d2)
            else:
                price = K * np.exp(-r * T) * ndtr(-d2) - S * ndtr(-d1)

            vega = S * nd1_pdf * sqrt_T
            if vega < 1e-16:
                break

            diff = price - market_price
            if abs(diff) < tol:
                converged = True
                break

            sigma = sigma - diff / vega
            sigma = max(sigma, 1e-8)

        return {
            "implied_vol": float(sigma),
            "iterations": i + 1,
            "converged": converged,
            "final_price": float(price),
        }

    def binomial_tree(self, S: float, K: float, T: float, r: float,
                      sigma: float, steps: int = 100,
                      option_type: str = 'call', american: bool = False) -> Dict:
        """Cox-Ross-Rubinstein binomial tree option pricing.

        Up factor:   u = exp(sigma * sqrt(dt))
        Down factor: d = 1/u
        Risk-neutral prob: p = (exp(r*dt) - d) / (u - d)

        For American options, checks early exercise at each node.
        """
        if T <= 0:
            if option_type == 'call':
                return {"price": max(S - K, 0.0), "steps": 0, "american": american}
            else:
                return {"price": max(K - S, 0.0), "steps": 0, "american": american}

        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        disc = np.exp(-r * dt)
        p = (np.exp(r * dt) - d) / (u - d)

        # Clamp probability
        p = max(0.0, min(1.0, p))

        # Terminal payoffs
        if option_type == 'call':
            terminal = np.maximum(S * u ** np.arange(steps, -1, -1) * d ** np.arange(steps + 1) - K, 0.0)
        else:
            terminal = np.maximum(K - S * u ** np.arange(steps, -1, -1) * d ** np.arange(steps + 1), 0.0)

        option_values = terminal.copy()

        # Backward induction
        for j in range(steps - 1, -1, -1):
            underlying = S * u ** np.arange(j, -1, -1) * d ** np.arange(j + 1)
            option_values = disc * (p * option_values[1:] + (1.0 - p) * option_values[:-1])

            if american:
                if option_type == 'call':
                    exercise = np.maximum(underlying - K, 0.0)
                else:
                    exercise = np.maximum(K - underlying, 0.0)
                option_values = np.maximum(option_values, exercise)

        return {
            "price": float(option_values[0]),
            "steps": steps,
            "american": american,
            "option_type": option_type,
        }

    def monte_carlo_option(self, S: float, K: float, T: float, r: float,
                           sigma: float, steps: int = 10000,
                           option_type: str = 'call') -> Dict:
        """Monte Carlo option pricing with antithetic variates.

        Simulates S_T = S * exp((r - 0.5*sigma^2)*T + sigma*sqrt(T)*Z)
        and its antithetic counterpart S_T' = S * exp((r - 0.5*sigma^2)*T - sigma*sqrt(T)*Z).

        The final estimate uses the average of both paths.
        """
        if T <= 0:
            if option_type == 'call':
                return {"price": max(S - K, 0.0), "std_error": 0.0, "paths": 1}
            else:
                return {"price": max(K - S, 0.0), "std_error": 0.0, "paths": 1}

        half = steps // 2
        Z = np.random.standard_normal(half)

        drift = (r - 0.5 * sigma ** 2) * T
        vol_sqrt_T = sigma * np.sqrt(T)

        S_T_1 = S * np.exp(drift + vol_sqrt_T * Z)
        S_T_2 = S * np.exp(drift - vol_sqrt_T * Z)  # antithetic

        if option_type == 'call':
            payoffs_1 = np.maximum(S_T_1 - K, 0.0)
            payoffs_2 = np.maximum(S_T_2 - K, 0.0)
        else:
            payoffs_1 = np.maximum(K - S_T_1, 0.0)
            payoffs_2 = np.maximum(K - S_T_2, 0.0)

        discounted_1 = payoffs_1 * np.exp(-r * T)
        discounted_2 = payoffs_2 * np.exp(-r * T)

        all_payoffs = np.concatenate([discounted_1, discounted_2])
        price = np.mean(all_payoffs)
        std_error = np.std(all_payoffs, ddof=1) / np.sqrt(len(all_payoffs))

        return {
            "price": float(price),
            "std_error": float(std_error),
            "paths": steps,
            "option_type": option_type,
        }


class MonteCarloSimulator:
    """Monte Carlo simulation engine for asset paths and portfolios."""

    def geometric_brownian_motion(self, S0: float, mu: float, sigma: float,
                                  T: float = 1.0, n_paths: int = 1000,
                                  n_steps: int = 252) -> Dict:
        """Simulate geometric Brownian motion paths.

        dS = mu*S*dt + sigma*S*dW

        Discretized via Euler-Maruyama:
        S_{t+dt} = S_t * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)

        Returns paths array (n_paths x n_steps+1), time array, and summary stats.
        """
        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        drift = (mu - 0.5 * sigma ** 2) * dt

        Z = np.random.standard_normal((n_paths, n_steps))
        log_increments = drift + sigma * sqrt_dt * Z
        log_paths = np.cumsum(log_increments, axis=1)
        log_paths = np.hstack([np.zeros((n_paths, 1)), log_paths])
        paths = S0 * np.exp(log_paths)

        terminal_prices = paths[:, -1]
        returns = (terminal_prices - S0) / S0

        return {
            "paths": paths,
            "time": np.linspace(0, T, n_steps + 1),
            "terminal_prices": terminal_prices,
            "mean_return": float(np.mean(returns)),
            "std_return": float(np.std(returns, ddof=1)),
            "mean_terminal": float(np.mean(terminal_prices)),
            "percentiles": {
                "p5": float(np.percentile(terminal_prices, 5)),
                "p25": float(np.percentile(terminal_prices, 25)),
                "p50": float(np.percentile(terminal_prices, 50)),
                "p75": float(np.percentile(terminal_prices, 75)),
                "p95": float(np.percentile(terminal_prices, 95)),
            },
            "n_paths": n_paths,
            "n_steps": n_steps,
        }

    def correlated_gbm(self, S0_list: List[float], mu_list: List[float],
                       sigma_list: List[float], corr_matrix: np.ndarray,
                       T: float = 1.0, n_paths: int = 1000,
                       n_steps: int = 252) -> Dict:
        """Simulate correlated geometric Brownian motion using Cholesky decomposition.

        L = cholesky(correlation_matrix)
        Z_independent ~ N(0, I)
        Z_correlated = Z_independent @ L.T

        Each asset: S_{t+dt} = S_t * exp((mu_i - 0.5*sigma_i^2)*dt + sigma_i*sqrt(dt)*Z_corr_i)
        """
        n_assets = len(S0_list)
        S0_arr = np.array(S0_list, dtype=float)
        mu_arr = np.array(mu_list, dtype=float)
        sigma_arr = np.array(sigma_list, dtype=float)

        corr = np.array(corr_matrix, dtype=float)
        if corr.shape != (n_assets, n_assets):
            raise ValueError(f"Correlation matrix must be {n_assets}x{n_assets}.")

        try:
            L = np.linalg.cholesky(corr)
        except np.linalg.LinAlgError:
            # Fallback: regularize slightly
            eigvals = np.linalg.eigvalsh(corr)
            min_eig = np.min(eigvals)
            if min_eig < 0:
                corr = corr + (abs(min_eig) + 1e-8) * np.eye(n_assets)
                L = np.linalg.cholesky(corr)
            else:
                raise

        dt = T / n_steps
        sqrt_dt = np.sqrt(dt)
        drift_arr = (mu_arr - 0.5 * sigma_arr ** 2) * dt

        Z_indep = np.random.standard_normal((n_paths, n_steps, n_assets))
        # Reshape: (n_paths, n_steps, n_assets) @ L.T -> (n_paths, n_steps, n_assets)
        Z_corr = Z_indep @ L.T

        # Compute log increments for each asset
        # drift_arr shape (n_assets,), Z_corr shape (n_paths, n_steps, n_assets)
        log_increments = drift_arr + sigma_arr * sqrt_dt * Z_corr
        log_paths = np.cumsum(log_increments, axis=1)  # (n_paths, n_steps, n_assets)
        # Prepend zeros for t=0
        zeros = np.zeros((n_paths, 1, n_assets))
        log_paths = np.concatenate([zeros, log_paths], axis=1)
        paths = S0_arr * np.exp(log_paths)

        # Correlation of terminal log-returns
        terminal = paths[:, -1, :]  # (n_paths, n_assets)
        log_returns = np.log(terminal / S0_arr)
        empirical_corr = np.corrcoef(log_returns.T)

        return {
            "paths": paths,
            "time": np.linspace(0, T, n_steps + 1),
            "terminal_prices": terminal,
            "empirical_correlation": empirical_corr,
            "n_assets": n_assets,
            "n_paths": n_paths,
            "n_steps": n_steps,
        }

    def portfolio_simulation(self, weights: np.ndarray, returns_matrix: np.ndarray,
                             n_simulations: int = 10000) -> Dict:
        """Simulate portfolio return distribution.

        Assumes returns_matrix columns represent assets and rows represent
        historical return observations. Portfolio returns are computed as
        w' @ r for each simulated scenario (bootstrapped or parametric).

        Uses a parametric approach: estimate mean and covariance from
        returns_matrix, then draw from multivariate normal.
        """
        weights = np.array(weights, dtype=float)
        returns_matrix = np.array(returns_matrix, dtype=float)

        if weights.ndim == 1:
            weights = weights.reshape(-1, 1)

        n_obs, n_assets = returns_matrix.shape
        if weights.shape[0] != n_assets:
            raise ValueError(f"Weights length {weights.shape[0]} != assets {n_assets}.")

        w = weights.flatten()
        mean_returns = np.mean(returns_matrix, axis=0)
        cov_matrix = np.cov(returns_matrix, rowvar=False, ddof=1)

        # Cholesky of covariance
        try:
            L = np.linalg.cholesky(cov_matrix)
        except np.linalg.LinAlgError:
            cov_matrix += 1e-8 * np.eye(n_assets)
            L = np.linalg.cholesky(cov_matrix)

        Z = np.random.standard_normal((n_simulations, n_assets))
        simulated_returns = Z @ L.T + mean_returns
        portfolio_returns = simulated_returns @ w

        # VaR and CVaR
        sorted_returns = np.sort(portfolio_returns)
        var_95 = float(np.percentile(portfolio_returns, 5))
        cvar_95 = float(np.mean(sorted_returns[sorted_returns <= var_95]))

        return {
            "portfolio_returns": portfolio_returns,
            "mean": float(np.mean(portfolio_returns)),
            "std": float(np.std(portfolio_returns, ddof=1)),
            "min": float(np.min(portfolio_returns)),
            "max": float(np.max(portfolio_returns)),
            "sharpe_ratio": float(np.mean(portfolio_returns) / np.std(portfolio_returns, ddof=1))
            if np.std(portfolio_returns, ddof=1) > 0 else 0.0,
            "VaR_95": var_95,
            "CVaR_95": cvar_95,
            "percentiles": {
                "p1": float(np.percentile(portfolio_returns, 1)),
                "p5": float(np.percentile(portfolio_returns, 5)),
                "p25": float(np.percentile(portfolio_returns, 25)),
                "p50": float(np.percentile(portfolio_returns, 50)),
                "p75": float(np.percentile(portfolio_returns, 75)),
                "p95": float(np.percentile(portfolio_returns, 95)),
                "p99": float(np.percentile(portfolio_returns, 99)),
            },
            "n_simulations": n_simulations,
        }

    def stress_test(self, portfolio_value: float, shocks: Dict[str, float],
                    n_sims: int = 10000) -> Dict:
        """Apply scenario shocks to portfolio and simulate outcomes.

        Parameters
        ----------
        portfolio_value : float
            Current total portfolio value.
        shocks : dict
            Mapping of scenario_name -> shock_multiplier.
            E.g., {"equity_crash": -0.20, "rate_spike": -0.05}

        Returns dict with scenario impacts, worst-case, and distribution.
        """
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive.")

        results = {}
        all_impacted = []

        for scenario_name, shock in shocks.items():
            # shock is a multiplicative factor on returns (e.g., -0.20 = -20%)
            # Add some randomness around the shock to simulate uncertainty
            shock_std = max(abs(shock) * 0.1, 0.005)  # 10% of shock magnitude
            random_component = np.random.normal(0, shock_std, n_sims)
            scenario_returns = shock + random_component
            impacted_values = portfolio_value * (1.0 + scenario_returns)

            results[scenario_name] = {
                "shock": shock,
                "mean_value": float(np.mean(impacted_values)),
                "std_value": float(np.std(impacted_values, ddof=1)),
                "worst_case": float(np.min(impacted_values)),
                "best_case": float(np.max(impacted_values)),
                "loss_probability": float(np.mean(impacted_values < portfolio_value)),
                "mean_loss": float(max(portfolio_value - np.mean(impacted_values), 0)),
                "VaR_95": float(np.percentile(impacted_values, 5)),
            }
            all_impacted.append(impacted_values)

        # Combined worst case across all scenarios
        all_impacted = np.array(all_impacted)  # (n_scenarios, n_sims)
        global_worst = float(np.min(all_impacted))

        return {
            "portfolio_value": portfolio_value,
            "scenarios": results,
            "global_worst_case": global_worst,
            "global_max_loss": portfolio_value - global_worst,
            "n_simulations": n_sims,
        }


class InterestRateModels:
    """Short-rate interest rate models: Vasicek, CIR, Hull-White."""

    def vasicek(self, r0: float, kappa: float, theta: float, sigma: float,
                T: float = 1.0, n_steps: int = 252, n_paths: int = 1000) -> Dict:
        """Vasicek (Ornstein-Uhlenbeck) mean-reverting short rate model.

        dr = kappa * (theta - r) * dt + sigma * dW

        Exact discretization:
        r_{t+dt} = theta + (r_t - theta) * exp(-kappa*dt) + sigma * sqrt((1-exp(-2*kappa*dt))/(2*kappa)) * Z
        """
        dt = T / n_steps
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = r0

        exp_neg_kdt = np.exp(-kappa * dt)

        if kappa > 1e-10:
            vol_factor = sigma * np.sqrt((1.0 - exp_neg_kdt ** 2) / (2.0 * kappa))
        else:
            # When kappa -> 0, Vasicek reduces to arithmetic Brownian motion
            vol_factor = sigma * np.sqrt(dt)
            exp_neg_kdt = 1.0

        for t in range(n_steps):
            Z = np.random.standard_normal(n_paths)
            paths[:, t + 1] = (theta + (paths[:, t] - theta) * exp_neg_kdt
                               + vol_factor * Z)

        terminal = paths[:, -1]
        return {
            "paths": paths,
            "time": np.linspace(0, T, n_steps + 1),
            "terminal_rates": terminal,
            "mean_terminal": float(np.mean(terminal)),
            "std_terminal": float(np.std(terminal, ddof=1)),
            "model": "vasicek",
            "params": {"r0": r0, "kappa": kappa, "theta": theta, "sigma": sigma},
            "n_paths": n_paths,
            "n_steps": n_steps,
        }

    def cir(self, r0: float, kappa: float, theta: float, sigma: float,
            T: float = 1.0, n_steps: int = 252, n_paths: int = 1000) -> Dict:
        """Cox-Ingersoll-Ross (CIR) mean-reverting short rate model.

        dr = kappa * (theta - r) * dt + sigma * sqrt(r) * dW

        Exact discretization (conditional non-central chi-squared):
        r_{t+dt} | r_t ~ (2*kappa / (sigma^2*(1-exp(-kappa*dt)))) * ncx2(d, lambda)

        where d = 4*kappa*theta/sigma^2, lambda = 2*kappa*exp(-kappa*dt)*r_t / (sigma^2*(1-exp(-kappa*dt)))

        For numerical stability with small sigma, falls back to Euler scheme with reflection.
        """
        dt = T / n_steps
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = r0

        # Feller condition: 2*kappa*theta >= sigma^2 ensures r stays positive
        feller = 2.0 * kappa * theta - sigma ** 2

        exp_neg_kdt = np.exp(-kappa * dt)
        one_minus_exp = 1.0 - exp_neg_kdt

        if sigma > 1e-10 and kappa > 1e-10:
            # Use exact transition
            d_freed = 4.0 * kappa * theta / (sigma ** 2)
            scale_factor = sigma ** 2 * one_minus_exp / (4.0 * kappa)

            for t in range(n_steps):
                r_t = paths[:, t]
                lambda_nc = 2.0 * kappa * exp_neg_kdt * r_t / (sigma ** 2 * one_minus_exp)

                # Draw from non-central chi-squared: we use the fact that
                # ncx2(d, lambda) can be sampled as: (Z + sqrt(lambda))^2 + chi2_{d-1}
                # for integer d, but more generally we use numpy's chi-squared.
                # Instead, implement via the Gaussian mixture approach for stability.
                # Direct approach: sample chi2(d) and Poisson(lambda/2)
                # ncx2(d, l) ~ chi2(d + 2*Poisson(l/2))
                # This is the standard representation.
                poissons = np.random.poisson(lambda_nc / 2.0, n_paths)
                chis = np.random.chisquare(d_freed + 2.0 * poissons)
                r_next = scale_factor * chis

                paths[:, t + 1] = r_next
        else:
            # Euler-Maruyama with reflection for positivity
            for t in range(n_steps):
                Z = np.random.standard_normal(n_paths)
                sqrt_r = np.sqrt(np.maximum(paths[:, t], 0.0))
                r_next = paths[:, t] + kappa * (theta - paths[:, t]) * dt + sigma * sqrt_r * np.sqrt(dt) * Z
                r_next = np.maximum(r_next, 0.0)  # reflection
                paths[:, t + 1] = r_next

        terminal = paths[:, -1]
        return {
            "paths": paths,
            "time": np.linspace(0, T, n_steps + 1),
            "terminal_rates": terminal,
            "mean_terminal": float(np.mean(terminal)),
            "std_terminal": float(np.std(terminal, ddof=1)),
            "feller_condition_met": feller >= 0,
            "model": "cir",
            "params": {"r0": r0, "kappa": kappa, "theta": theta, "sigma": sigma},
            "n_paths": n_paths,
            "n_steps": n_steps,
        }

    def hull_white(self, r0: float, kappa: float, theta_t: np.ndarray,
                   sigma: float, T: float = 1.0, n_steps: int = 252,
                   n_paths: int = 1000) -> Dict:
        """Hull-White (extended Vasicek) model with time-dependent theta.

        dr = (theta(t) - kappa * r) * dt + sigma * dW

        theta_t is an array of length (n_steps+1) representing the
        time-dependent drift at each discretization point.

        Exact discretization:
        r_{t+dt} = r_t * exp(-kappa*dt) + integral + sigma * vol_factor * Z
        """
        dt = T / n_steps
        theta_t = np.array(theta_t, dtype=float)

        if len(theta_t) != n_steps + 1:
            raise ValueError(f"theta_t must have length {n_steps + 1}, got {len(theta_t)}.")

        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = r0

        exp_neg_kdt = np.exp(-kappa * dt)

        if kappa > 1e-10:
            vol_factor = sigma * np.sqrt((1.0 - exp_neg_kdt ** 2) / (2.0 * kappa))
        else:
            vol_factor = sigma * np.sqrt(dt)
            exp_neg_kdt = 1.0

        for t in range(n_steps):
            Z = np.random.standard_normal(n_paths)
            # Deterministic part: integral of theta(s)*exp(-kappa*(t+dt-s)) from t to t+dt
            # Approximated by theta_t[t] * (1 - exp(-kappa*dt)) / kappa
            if kappa > 1e-10:
                theta_integral = theta_t[t] * (1.0 - exp_neg_kdt) / kappa
            else:
                theta_integral = theta_t[t] * dt

            paths[:, t + 1] = (paths[:, t] * exp_neg_kdt
                               + theta_integral
                               + vol_factor * Z)

        terminal = paths[:, -1]
        return {
            "paths": paths,
            "time": np.linspace(0, T, n_steps + 1),
            "terminal_rates": terminal,
            "mean_terminal": float(np.mean(terminal)),
            "std_terminal": float(np.std(terminal, ddof=1)),
            "model": "hull_white",
            "params": {"r0": r0, "kappa": kappa, "sigma": sigma},
            "n_paths": n_paths,
            "n_steps": n_steps,
        }

    def zero_coupon_bond_price(self, model: str, r: float, T: float,
                                model_params: Dict) -> Dict:
        """Compute zero-coupon bond price P(0, T) under a given short-rate model.

        Vasicek analytical formula:
        A(t,T) = exp((B(t,T) - (T-t))*(B(t,T)*sigma^2/(2*kappa) - theta/kappa)
                     - sigma^2*B(t,T)^2/(4*kappa))
        B(t,T) = (1 - exp(-kappa*(T-t))) / kappa
        P = A * exp(-B * r)

        For CIR, uses the analogous closed-form.
        For Hull-White, returns Vasicek-like formula with theta(0) substitution.
        """
        kappa = model_params.get("kappa", 0.1)
        theta = model_params.get("theta", 0.05)
        sigma = model_params.get("sigma", 0.01)

        if model == "vasicek" or model == "hull_white":
            if kappa > 1e-10:
                B = (1.0 - np.exp(-kappa * T)) / kappa
            else:
                B = T

            A = np.exp(
                (B - T) * (B * sigma ** 2 / (2.0 * kappa) - theta / kappa)
                - sigma ** 2 * B ** 2 / (4.0 * kappa)
            )
            price = A * np.exp(-B * r)

            # Continuously compounded yield
            y = -np.log(price) / T if T > 0 else r

            return {
                "price": float(price),
                "yield": float(y),
                "A": float(A),
                "B": float(B),
                "model": model,
            }

        elif model == "cir":
            if kappa > 1e-10:
                h1 = np.sqrt(kappa ** 2 + 2.0 * sigma ** 2)
                h2 = (kappa + h1) / 2.0
                h3 = 2.0 * kappa * theta / (sigma ** 2)

                exp_h1T = np.exp(h1 * T)
                B = 2.0 * (exp_h1T - 1.0) / ((h1 + kappa) * (exp_h1T - 1.0) + 2.0 * h1)
                A = (h1 * exp_h1T / ((h1 + kappa) * (exp_h1T - 1.0) + 2.0 * h1)) ** h3
                price = A * np.exp(-B * r)
            else:
                # Degenerate case
                price = np.exp(-r * T)

            y = -np.log(price) / T if T > 0 else r

            return {
                "price": float(price),
                "yield": float(y),
                "A": float(A) if kappa > 1e-10 else 1.0,
                "B": float(B) if kappa > 1e-10 else T,
                "model": model,
            }

        else:
            raise ValueError(f"Unknown model: {model}. Use 'vasicek', 'cir', or 'hull_white'.")

    def yield_curve_fit(self, rates: np.ndarray, maturities: np.ndarray,
                        model: str = 'vasicek') -> Dict:
        """Calibrate a short-rate model to observed zero-coupon rates.

        Uses least-squares minimization (scipy.optimize) to find model
        parameters that best fit the observed yield curve.

        For Vasicek: P(0,T) = A(T)*exp(-B(T)*r0)
        Yield y(T) = -ln(P)/T
        We calibrate kappa, theta, sigma, and r0.
        """
        from scipy.optimize import minimize

        rates = np.array(rates, dtype=float)
        maturities = np.array(maturities, dtype=float)

        # Remove zero maturities
        mask = maturities > 0
        rates = rates[mask]
        maturities = maturities[mask]

        def _vasicek_yield(params, T, r0, kappa, theta, sigma):
            """Compute Vasicek yield for given parameters."""
            if kappa > 1e-10:
                B = (1.0 - np.exp(-kappa * T)) / kappa
                A = np.exp(
                    (B - T) * (B * sigma ** 2 / (2.0 * kappa) - theta / kappa)
                    - sigma ** 2 * B ** 2 / (4.0 * kappa)
                )
            else:
                B = T
                A = np.exp(-theta * T ** 2 / 2.0)
            P = A * np.exp(-B * r0)
            return -np.log(np.maximum(P, 1e-16)) / T

        def _cir_yield(params, T, r0, kappa, theta, sigma):
            """Compute CIR yield for given parameters."""
            if kappa > 1e-10 and sigma > 1e-10:
                h1 = np.sqrt(kappa ** 2 + 2.0 * sigma ** 2)
                h3 = 2.0 * kappa * theta / (sigma ** 2)
                exp_h1T = np.exp(h1 * T)
                B = 2.0 * (exp_h1T - 1.0) / ((h1 + kappa) * (exp_h1T - 1.0) + 2.0 * h1)
                A = (h1 * exp_h1T / ((h1 + kappa) * (exp_h1T - 1.0) + 2.0 * h1)) ** h3
                P = A * np.exp(-B * r0)
            else:
                P = np.exp(-r0 * T)
            return -np.log(np.maximum(P, 1e-16)) / T

        def objective(params):
            r0, kappa, theta, sigma = params
            if kappa < 0 or sigma < 0 or r0 < 0:
                return 1e10
            sigma = max(sigma, 1e-10)
            try:
                if model == 'vasicek':
                    model_yields = _vasicek_yield(params, maturities, r0, kappa, theta, sigma)
                else:
                    model_yields = _cir_yield(params, maturities, r0, kappa, theta, sigma)
                return np.sum((model_yields - rates) ** 2)
            except (ValueError, RuntimeWarning, FloatingPointError):
                return 1e10

        # Initial guess: r0 ~ short rate, kappa ~ 0.5, theta ~ mean rate, sigma ~ 0.01
        r0_init = rates[0]
        theta_init = np.mean(rates)
        x0 = [r0_init, 0.5, theta_init, 0.01]

        result = minimize(objective, x0, method='Nelder-Mead',
                         options={'maxiter': 10000, 'xatol': 1e-12, 'fatol': 1e-12})

        r0_opt, kappa_opt, theta_opt, sigma_opt = result.x
        sigma_opt = max(sigma_opt, 1e-10)

        # Compute fitted yields
        if model == 'vasicek':
            fitted = _vasicek_yield(result.x, maturities, r0_opt, kappa_opt, theta_opt, sigma_opt)
        else:
            fitted = _cir_yield(result.x, maturities, r0_opt, kappa_opt, theta_opt, sigma_opt)

        residuals = rates - fitted
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((rates - np.mean(rates)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        return {
            "model": model,
            "params": {
                "r0": float(r0_opt),
                "kappa": float(kappa_opt),
                "theta": float(theta_opt),
                "sigma": float(sigma_opt),
            },
            "observed_maturities": maturities.tolist(),
            "observed_rates": rates.tolist(),
            "fitted_rates": fitted.tolist(),
            "residuals": residuals.tolist(),
            "r_squared": float(r_squared),
            "rmse": float(np.sqrt(np.mean(residuals ** 2))),
            "optimization_success": result.success,
            "optimization_message": result.message,
        }


class OptionStrategyAnalyzer:
    """Analyzes multi-leg option strategies: payoffs, risk metrics, breakevens."""

    def _bs_price(self, S: float, K: float, T: float, r: float, sigma: float,
                  option_type: str) -> float:
        """Helper: compute BS price for a single option."""
        bs = BlackScholes()
        if option_type == 'call':
            return bs.european_call(S, K, T, r, sigma)["price"]
        else:
            return bs.european_put(S, K, T, r, sigma)["price"]

    def _payoff_array(self, S_range: np.ndarray, K: float, option_type: str,
                      quantity: int = 1, premium: float = 0.0) -> np.ndarray:
        """Compute payoff at expiry for a single option leg."""
        if option_type == 'call':
            intrinsic = np.maximum(S_range - K, 0.0)
        else:
            intrinsic = np.maximum(K - S_range, 0.0)
        return quantity * (intrinsic - premium)

    def _generate_range(self, S: float, T: float, r: float, sigma: float,
                        n_points: int = 500, width_factor: float = 0.5) -> np.ndarray:
        """Generate a reasonable range of terminal prices for analysis.
        Based on expected move = S * sigma * sqrt(T)."""
        expected_move = S * sigma * np.sqrt(T)
        low = S - width_factor * expected_move * 3
        high = S + width_factor * expected_move * 3
        low = max(low, S * 0.1)  # floor at 10% of spot
        return np.linspace(low, high, n_points)

    def bull_call_spread(self, S: float, K1: float, K2: float, T: float,
                         r: float, sigma: float) -> Dict:
        """Bull call spread: long call at K1, short call at K2 (K1 < K2).

        Max profit = (K2 - K1) - net premium paid
        Max loss = net premium paid
        Breakeven = K1 + net premium paid
        """
        if K1 >= K2:
            raise ValueError("K1 must be less than K2 for a bull call spread.")

        price_long = self._bs_price(S, K1, T, r, sigma, 'call')
        price_short = self._bs_price(S, K2, T, r, sigma, 'call')
        net_premium = price_long - price_short

        S_range = self._generate_range(S, T, r, sigma)
        long_payoff = self._payoff_array(S_range, K1, 'call', 1, price_long)
        short_payoff = self._payoff_array(S_range, K2, 'call', -1, -price_short)
        total_payoff = long_payoff + short_payoff

        max_profit = (K2 - K1) - net_premium
        max_loss = net_premium
        breakeven = K1 + net_premium

        return {
            "strategy": "bull_call_spread",
            "S_range": S_range,
            "payoff_at_expiry": total_payoff,
            "max_profit": float(max_profit),
            "max_loss": float(max_loss),
            "breakeven": float(breakeven),
            "net_premium": float(net_premium),
            "long_call_price": float(price_long),
            "short_call_price": float(price_short),
            "K1": K1, "K2": K2,
        }

    def straddle(self, S: float, K: float, T: float, r: float,
                 sigma: float) -> Dict:
        """Long straddle: long call + long put at same strike K.

        Max loss = net premium paid (call + put)
        Max profit = unlimited (upside) / K - premium (downside)
        Breakevens = K +/- net premium
        """
        call_price = self._bs_price(S, K, T, r, sigma, 'call')
        put_price = self._bs_price(S, K, T, r, sigma, 'put')
        net_premium = call_price + put_price

        S_range = self._generate_range(S, T, r, sigma)
        call_payoff = self._payoff_array(S_range, K, 'call', 1, call_price)
        put_payoff = self._payoff_array(S_range, K, 'put', 1, put_price)
        total_payoff = call_payoff + put_payoff

        breakeven_upper = K + net_premium
        breakeven_lower = K - net_premium
        max_loss = net_premium

        return {
            "strategy": "straddle",
            "S_range": S_range,
            "payoff_at_expiry": total_payoff,
            "max_profit": np.inf,
            "max_loss": float(max_loss),
            "breakeven": [float(breakeven_lower), float(breakeven_upper)],
            "net_premium": float(net_premium),
            "call_price": float(call_price),
            "put_price": float(put_price),
            "K": K,
        }

    def iron_condor(self, S: float, K1: float, K2: float, K3: float,
                    K4: float, T: float, r: float, sigma: float) -> Dict:
        """Iron condor: long put K1, short put K2, short call K3, long call K4.

        Requires K1 < K2 < K3 < K4.

        Max profit = net premium received
        Max loss = max(K2-K1, K4-K3) - net premium
        Breakevens = K2 - net_premium, K3 + net_premium
        """
        if not (K1 < K2 < K3 < K4):
            raise ValueError("Requires K1 < K2 < K3 < K4 for iron condor.")

        price_long_put = self._bs_price(S, K1, T, r, sigma, 'put')
        price_short_put = self._bs_price(S, K2, T, r, sigma, 'put')
        price_short_call = self._bs_price(S, K3, T, r, sigma, 'call')
        price_long_call = self._bs_price(S, K4, T, r, sigma, 'call')

        net_premium = (price_short_put + price_short_call
                       - price_long_put - price_long_call)

        S_range = self._generate_range(S, T, r, sigma)
        p1 = self._payoff_array(S_range, K1, 'put', 1, price_long_put)
        p2 = self._payoff_array(S_range, K2, 'put', -1, -price_short_put)
        p3 = self._payoff_array(S_range, K3, 'call', -1, -price_short_call)
        p4 = self._payoff_array(S_range, K4, 'call', 1, price_long_call)
        total_payoff = p1 + p2 + p3 + p4

        max_profit = net_premium
        wing_width = max(K2 - K1, K4 - K3)
        max_loss = wing_width - net_premium

        breakeven_lower = K2 - net_premium
        breakeven_upper = K3 + net_premium

        return {
            "strategy": "iron_condor",
            "S_range": S_range,
            "payoff_at_expiry": total_payoff,
            "max_profit": float(max_profit),
            "max_loss": float(max_loss),
            "breakeven": [float(breakeven_lower), float(breakeven_upper)],
            "net_premium": float(net_premium),
            "prices": {
                "long_put_K1": float(price_long_put),
                "short_put_K2": float(price_short_put),
                "short_call_K3": float(price_short_call),
                "long_call_K4": float(price_long_call),
            },
            "K1": K1, "K2": K2, "K3": K3, "K4": K4,
        }

    def butterfly_spread(self, S: float, K1: float, K2: float, K3: float,
                         T: float, r: float, sigma: float) -> Dict:
        """Butterfly spread: long 1 call K1, short 2 calls K2, long 1 call K3.

        Requires K1 < K2 < K3, typically K2 = (K1+K3)/2.

        Using calls (can also use puts for put butterfly).

        Max profit = (K2 - K1) - net premium paid
        Max loss = net premium paid
        Breakevens = K1 + net_premium, K3 - net_premium
        """
        if not (K1 < K2 < K3):
            raise ValueError("Requires K1 < K2 < K3 for butterfly spread.")

        price_long_call_1 = self._bs_price(S, K1, T, r, sigma, 'call')
        price_short_call_2 = self._bs_price(S, K2, T, r, sigma, 'call')
        price_long_call_3 = self._bs_price(S, K3, T, r, sigma, 'call')

        net_premium = price_long_call_1 - 2.0 * price_short_call_2 + price_long_call_3

        S_range = self._generate_range(S, T, r, sigma)
        p1 = self._payoff_array(S_range, K1, 'call', 1, price_long_call_1)
        p2 = self._payoff_array(S_range, K2, 'call', -2, -price_short_call_2)
        p3 = self._payoff_array(S_range, K3, 'call', 1, price_long_call_3)
        total_payoff = p1 + p2 + p3

        max_profit = (K2 - K1) - net_premium
        max_loss = net_premium

        breakeven_lower = K1 + net_premium
        breakeven_upper = K3 - net_premium

        return {
            "strategy": "butterfly_spread",
            "S_range": S_range,
            "payoff_at_expiry": total_payoff,
            "max_profit": float(max_profit),
            "max_loss": float(max_loss),
            "breakeven": [float(breakeven_lower), float(breakeven_upper)],
            "net_premium": float(net_premium),
            "prices": {
                "long_call_K1": float(price_long_call_1),
                "short_call_K2": float(price_short_call_2),
                "long_call_K3": float(price_long_call_3),
            },
            "K1": K1, "K2": K2, "K3": K3,
        }
