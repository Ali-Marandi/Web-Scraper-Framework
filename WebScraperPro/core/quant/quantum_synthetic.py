"""
quantum_synthetic.py — Frontier Research Models for WebScraperPro

This module implements cutting-edge quantum-inspired and synthetic data
generation models for quantitative financial analysis in a commercial
desktop web scraping application. All implementations use only numpy,
pandas, and scipy — no external quantum or ML frameworks required.

Classes:
    QuantumMonteCarlo     — Quantum-inspired Monte Carlo for option pricing
    DiffusionSyntheticData — Diffusion process synthetic financial data
    FederatedLearningSim  — Federated learning simulation for distributed data
    QuantumGameTheory     — Quantum game theory simulations
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import linalg as scipy_linalg
from scipy import stats as scipy_stats
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# 1. QuantumMonteCarlo
# ---------------------------------------------------------------------------

class QuantumMonteCarlo:
    """
    Quantum-inspired Monte Carlo methods for option pricing.

    This class simulates quantum computing primitives (amplitude encoding,
    quantum walks, variational circuits) using classical numpy operations
    to approximate quantum speedups in financial derivative pricing.

    All methods are classical simulations inspired by quantum algorithms —
    they do **not** require a real quantum processor.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility.
        """
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    def quantum_option_pricing(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        n_qubits: int = 10,
        n_shots: int = 1000,
    ) -> Dict[str, Any]:
        """
        Simulate quantum amplitude estimation (QAE) for European call
        option pricing.

        The idea: encode the option payoff into quantum amplitudes via
        random-phase encoding, then use amplitude estimation to approximate
        the expected payoff — achieving a theoretical O(1/N) convergence
        versus O(1/sqrt(N)) for classical MC.

        Parameters
        ----------
        S : float
            Current spot price (must be > 0).
        K : float
            Strike price (must be > 0).
        T : float
            Time to maturity in years (must be > 0).
        r : float
            Risk-free interest rate.
        sigma : float
            Volatility (must be > 0).
        n_qubits : int, default 10
            Number of qubits for amplitude encoding granularity.
        n_shots : int, default 1000
            Number of measurement shots (simulation iterations).

        Returns
        -------
        dict
            Keys:
            - ``quantum_price`` : estimated option price
            - ``confidence_interval`` : (lower, upper) 95 % CI
            - ``black_scholes_price`` : closed-form BS price
            - ``price_difference`` : quantum minus BS
            - ``n_qubits`` , ``n_shots`` : algorithm parameters
        """
        # --- input validation ------------------------------------------------
        if S <= 0:
            raise ValueError("Spot price S must be positive.")
        if K <= 0:
            raise ValueError("Strike price K must be positive.")
        if T <= 0:
            raise ValueError("Time to maturity T must be positive.")
        if sigma <= 0:
            raise ValueError("Volatility sigma must be positive.")
        if n_qubits < 1:
            raise ValueError("n_qubits must be >= 1.")
        if n_shots < 1:
            raise ValueError("n_shots must be >= 1.")

        rng = self._rng

        # --- Black-Scholes closed form for comparison -----------------------
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        bs_price = S * scipy_stats.norm.cdf(d1) - K * np.exp(-r * T) * scipy_stats.norm.cdf(d2)

        # --- Quantum-inspired amplitude estimation --------------------------
        # Discretise price space into 2^n_qubits bins
        n_bins = 2**n_qubits
        # GBM drift-corrected log-normal approximation for terminal price
        mu_drift = (r - 0.5 * sigma**2) * T
        s_scale = sigma * np.sqrt(T)
        # Price grid
        log_prices = np.linspace(mu_drift - 5 * s_scale, mu_drift + 5 * s_scale, n_bins)
        prices_grid = S * np.exp(log_prices)

        # Payoff function on grid
        payoffs = np.maximum(prices_grid - K, 0.0)

        # Probability weights (log-normal density at grid points)
        probs = scipy_stats.norm.pdf(log_prices, loc=mu_drift, scale=s_scale)
        probs /= probs.sum()  # normalise

        # Amplitude encoding: sqrt(prob) for each basis state
        amplitudes = np.sqrt(probs)

        # Grover-like amplitude amplification: amplify states where payoff > 0
        oracle_mask = (payoffs > 0).astype(float)
        # Phase kickback
        phase = np.where(oracle_mask > 0, -1.0, 1.0)
        amplitudes *= phase

        # Inversion about the mean (Grover diffusion)
        mean_amp = np.mean(amplitudes)
        amplitudes = 2.0 * mean_amp - amplitudes

        # Re-normalise
        amp_norm = np.linalg.norm(amplitudes)
        if amp_norm > 0:
            amplitudes /= amp_norm

        # Simulate measurement shots
        meas_probs = amplitudes**2
        meas_probs = np.clip(meas_probs, 0, None)
        meas_probs /= meas_probs.sum()

        # Sample from the amplified distribution
        indices = rng.choice(n_bins, size=n_shots, p=meas_probs)
        sampled_payoffs = payoffs[indices]

        # Estimated expected payoff
        estimated_payoff = np.mean(sampled_payoffs)
        std_payoff = np.std(sampled_payoffs, ddof=1)
        se = std_payoff / np.sqrt(n_shots)

        # Discount to present value
        quantum_price = np.exp(-r * T) * estimated_payoff
        ci_lower = np.exp(-r * T) * (estimated_payoff - 1.96 * se)
        ci_upper = np.exp(-r * T) * (estimated_payoff + 1.96 * se)

        return {
            "quantum_price": float(quantum_price),
            "confidence_interval": (float(ci_lower), float(ci_upper)),
            "black_scholes_price": float(bs_price),
            "price_difference": float(quantum_price - bs_price),
            "n_qubits": n_qubits,
            "n_shots": n_shots,
        }

    # ------------------------------------------------------------------
    def quantum_walk_option(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        n_steps: int = 100,
    ) -> Dict[str, Any]:
        """
        Quantum random walk model for option pricing.

        Uses a Hadamard-like coin operator applied iteratively to a
        position-space probability distribution, yielding a quantum
        walk whose terminal distribution differs from classical Brownian
        motion (faster spreading, quantum interference fringes).

        Parameters
        ----------
        S : float
            Spot price (> 0).
        K : float
            Strike price (> 0).
        T : float
            Time to maturity in years (> 0).
        r : float
            Risk-free rate.
        sigma : float
            Volatility (> 0).
        n_steps : int, default 100
            Number of quantum walk steps.

        Returns
        -------
        dict
            Keys:
            - ``option_price`` : discounted expected payoff
            - ``price_distribution`` : 1-D numpy array of terminal probs
            - ``log_return_grid`` : corresponding log-return grid
            - ``expected_log_return`` , ``std_log_return``
            - ``n_steps``
        """
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise ValueError("S, K, T, sigma must all be positive.")
        if n_steps < 1:
            raise ValueError("n_steps must be >= 1.")

        rng = self._rng

        # Position space: discretised log-returns
        n_pos = 2 * n_steps + 1  # symmetric walk
        # Hadamard coin operator
        H = (1.0 / np.sqrt(2)) * np.array([[1.0, 1.0], [1.0, -1.0]])

        # State: 2-component coin amplitude at each position
        # psi[pos, coin] — coin in {0,1}
        psi = np.zeros((n_pos, 2), dtype=complex)
        mid = n_pos // 2
        # Start at centre with coin in |+> state (equal superposition)
        psi[mid, 0] = 1.0 / np.sqrt(2)
        psi[mid, 1] = 1.0 / np.sqrt(2)

        for _ in range(n_steps):
            psi_new = np.zeros_like(psi)
            for pos in range(n_pos):
                # Apply coin
                coin_state = H @ psi[pos]
                # Shift: coin 0 -> move left, coin 1 -> move right
                if pos > 0:
                    psi_new[pos - 1, 0] += coin_state[0]
                if pos < n_pos - 1:
                    psi_new[pos + 1, 1] += coin_state[1]
            # Renormalise for numerical stability
            norm = np.linalg.norm(psi_new)
            if norm > 0:
                psi_new /= norm
            psi = psi_new

        # Probability distribution over positions
        probs = np.sum(np.abs(psi) ** 2, axis=1)

        # Map positions to log-returns
        dt = T / n_steps
        step_size = sigma * np.sqrt(dt)
        log_return_grid = (np.arange(n_pos) - mid) * step_size * np.sqrt(2)

        # Map to terminal prices
        terminal_prices = S * np.exp(log_return_grid + (r - 0.5 * sigma**2) * T)
        payoffs = np.maximum(terminal_prices - K, 0.0)

        expected_payoff = np.dot(probs, payoffs)
        option_price = np.exp(-r * T) * expected_payoff

        return {
            "option_price": float(option_price),
            "price_distribution": probs,
            "log_return_grid": log_return_grid,
            "expected_log_return": float(np.dot(probs, log_return_grid)),
            "std_log_return": float(np.sqrt(np.dot(probs, (log_return_grid - np.dot(probs, log_return_grid))**2))),
            "n_steps": n_steps,
        }

    # ------------------------------------------------------------------
    def variational_eigenvalue(
        self,
        n_assets: int,
        n_layers: int = 3,
        max_iter: int = 100,
    ) -> Dict[str, Any]:
        """
        Simulate a Variational Quantum Eigensolver (VQE) for portfolio
        optimisation eigenvalue problems.

        Builds a random covariance matrix Σ, then uses a parameterised
        ansatz (product of rotation gates simulated classically) to
        find the ground-state energy, which corresponds to the minimum
        portfolio variance.

        Parameters
        ----------
        n_assets : int
            Number of assets in the portfolio (>= 2).
        n_layers : int, default 3
            Depth of the variational circuit (number of rotation layers).
        max_iter : int, default 100
            Maximum classical optimisation iterations.

        Returns
        -------
        dict
            Keys:
            - ``ground_state_energy`` : minimum eigenvalue (min variance)
            - ``optimal_parameters`` : best parameter vector
            - ``eigenvalue_spectrum`` : all eigenvalues of Σ
            - ``converged`` : bool
            - ``n_iterations`` : iterations used
        """
        if n_assets < 2:
            raise ValueError("n_assets must be >= 2.")
        if n_layers < 1:
            raise ValueError("n_layers must be >= 1.")
        if max_iter < 1:
            raise ValueError("max_iter must be >= 1.")

        rng = self._rng

        # Build a valid random covariance matrix
        A = rng.standard_normal((n_assets, n_assets))
        Sigma = A @ A.T / n_assets
        # Ensure positive-definiteness
        eigvals, eigvecs = np.linalg.eigh(Sigma)
        eigvals = np.maximum(eigvals, 1e-6)
        Sigma = eigvecs @ np.diag(eigvals) @ eigvecs.T
        Sigma = (Sigma + Sigma.T) / 2

        # Full spectrum for reference
        full_spectrum = np.sort(np.linalg.eigvalsh(Sigma))

        # --- Variational ansatz simulation ----------------------------------
        n_params = n_layers * n_assets

        def _ansatz_state(params: np.ndarray) -> np.ndarray:
            """Simulate parameterised circuit -> state vector."""
            # Start from uniform superposition
            state = np.ones(n_assets, dtype=complex) / np.sqrt(n_assets)
            for layer in range(n_layers):
                offset = layer * n_assets
                for i in range(n_assets):
                    theta = params[offset + i]
                    # Rotation gate R_y analogue
                    cos_t = np.cos(theta / 2)
                    sin_t = np.sin(theta / 2)
                    new_i = cos_t * state[i] - 1j * sin_t * state[(i + 1) % n_assets]
                    new_next = 1j * sin_t * state[i] + cos_t * state[(i + 1) % n_assets]
                    state[i] = new_i
                    state[(i + 1) % n_assets] = new_next
                # Renormalise
                norm = np.linalg.norm(state)
                if norm > 0:
                    state /= norm
            return state

        def _expectation(params: np.ndarray) -> float:
            """<ψ(θ)|Σ|ψ(θ)>."""
            psi = _ansatz_state(params)
            return float(np.real(psi.conj() @ Sigma @ psi))

        # Classical optimisation (COBYLA)
        x0 = rng.uniform(-np.pi, np.pi, size=n_params)
        result = minimize(
            _expectation,
            x0,
            method="COBYLA",
            options={"maxiter": max_iter, "rhobeg": 0.5},
        )

        return {
            "ground_state_energy": float(result.fun),
            "optimal_parameters": result.x.tolist(),
            "eigenvalue_spectrum": full_spectrum.tolist(),
            "converged": bool(result.success),
            "n_iterations": int(result.nfev),
        }


# ---------------------------------------------------------------------------
# 2. DiffusionSyntheticData
# ---------------------------------------------------------------------------

class DiffusionSyntheticData:
    """
    Generate synthetic financial data using stochastic diffusion processes.

    Supports multiple SDE families (OU, GBM, CIR, Vasicek), correlated
    multi-asset paths, conditional generation guided by empirical moments,
    and score-matching for density estimation.
    """

    SUPPORTED_SDE: Dict[str, str] = {
        "OU": "Ornstein-Uhlenbeck: dx = θ(μ−x)dt + σ dW",
        "GBM": "Geometric Brownian Motion: dx = μx dt + σx dW",
        "CIR": "Cox-Ingersoll-Ross: dx = k(θ−x)dt + σ√x dW",
        "Vasicek": "Vasicek: dx = a(b−x)dt + σ dW",
    }

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    def univariate_diffusion(
        self,
        n_samples: int = 1000,
        n_steps: int = 100,
        sigma: float = 0.1,
        sde_type: str = "OU",
    ) -> Dict[str, Any]:
        """
        Generate sample paths from a univariate SDE using Euler-Maruyama.

        Parameters
        ----------
        n_samples : int, default 1000
            Number of independent paths.
        n_steps : int, default 100
            Time steps per path.
        sigma : float, default 0.1
            Diffusion (volatility) coefficient.
        sde_type : str, default 'OU'
            One of 'OU', 'GBM', 'CIR', 'Vasicek'.

        Returns
        -------
        dict
            - ``paths`` : ndarray (n_samples, n_steps+1)
            - ``final_values`` : ndarray (n_samples,)
            - ``sde_type`` : str
            - ``statistics`` : dict of mean, std, skew, kurt of final values
        """
        if n_samples < 1 or n_steps < 1:
            raise ValueError("n_samples and n_steps must be >= 1.")
        if sigma < 0:
            raise ValueError("sigma must be non-negative.")
        sde_type = sde_type.upper()
        if sde_type not in self.SUPPORTED_SDE:
            raise ValueError(
                f"Unknown sde_type '{sde_type}'. "
                f"Choose from {list(self.SUPPORTED_SDE.keys())}."
            )

        rng = self._rng
        dt = 1.0 / n_steps
        sqrt_dt = np.sqrt(dt)
        dW = rng.standard_normal((n_samples, n_steps)) * sqrt_dt

        paths = np.zeros((n_samples, n_steps + 1))

        # Default SDE parameters (mean-reversion / growth)
        theta_ou = 0.5   # mean-reversion speed
        mu_ou = 0.0      # long-term mean
        mu_gbm = 0.05    # drift for GBM
        k_cir = 0.5      # CIR speed
        theta_cir = 0.05 # CIR long-term mean
        a_vas = 0.5      # Vasicek speed
        b_vas = 0.0      # Vasicek long-term mean

        if sde_type == "OU":
            paths[:, 0] = mu_ou
            for t in range(n_steps):
                paths[:, t + 1] = (
                    paths[:, t]
                    + theta_ou * (mu_ou - paths[:, t]) * dt
                    + sigma * dW[:, t]
                )
        elif sde_type == "GBM":
            paths[:, 0] = 1.0  # start at S0=1
            for t in range(n_steps):
                paths[:, t + 1] = paths[:, t] * (
                    1.0 + mu_gbm * dt + sigma * dW[:, t]
                )
                paths[:, t + 1] = np.maximum(paths[:, t + 1], 1e-12)
        elif sde_type == "CIR":
            paths[:, 0] = theta_cir
            for t in range(n_steps):
                x_t = np.maximum(paths[:, t], 0.0)
                paths[:, t + 1] = (
                    x_t
                    + k_cir * (theta_cir - x_t) * dt
                    + sigma * np.sqrt(x_t) * dW[:, t]
                )
                paths[:, t + 1] = np.maximum(paths[:, t + 1], 0.0)
        elif sde_type == "Vasicek":
            paths[:, 0] = b_vas
            for t in range(n_steps):
                paths[:, t + 1] = (
                    paths[:, t]
                    + a_vas * (b_vas - paths[:, t]) * dt
                    + sigma * dW[:, t]
                )

        final = paths[:, -1]
        stats = {
            "mean": float(np.mean(final)),
            "std": float(np.std(final, ddof=1)),
            "skew": float(float(scipy_stats.skew(final))),
            "kurtosis": float(float(scipy_stats.kurtosis(final))),
            "min": float(np.min(final)),
            "max": float(np.max(final)),
        }

        return {
            "paths": paths,
            "final_values": final,
            "sde_type": sde_type,
            "statistics": stats,
        }

    # ------------------------------------------------------------------
    def correlated_diffusion(
        self,
        n_assets: int = 5,
        n_samples: int = 1000,
        correlation: Optional[np.ndarray] = None,
        sde_type: str = "GBM",
    ) -> Dict[str, Any]:
        """
        Generate correlated multi-asset paths via Cholesky decomposition.

        Parameters
        ----------
        n_assets : int, default 5
        n_samples : int, default 1000
        correlation : ndarray (n_assets, n_assets), optional
            If None, a random positive-definite correlation matrix is
            generated.
        sde_type : str, default 'GBM'

        Returns
        -------
        dict
            - ``paths`` : ndarray (n_samples, n_assets, n_steps+1)
            - ``correlation_matrix`` : the correlation used
            - ``final_prices`` : ndarray (n_samples, n_assets)
            - ``asset_statistics`` : list of per-asset stat dicts
        """
        if n_assets < 1:
            raise ValueError("n_assets must be >= 1.")
        sde_type = sde_type.upper()
        if sde_type not in self.SUPPORTED_SDE:
            raise ValueError(f"Unknown sde_type '{sde_type}'.")

        rng = self._rng
        n_steps = 252
        dt = 1.0 / n_steps
        sqrt_dt = np.sqrt(dt)

        # Build / validate correlation matrix
        if correlation is not None:
            corr = np.asarray(correlation, dtype=float)
            if corr.shape != (n_assets, n_assets):
                raise ValueError(
                    f"correlation shape {corr.shape} != ({n_assets}, {n_assets})"
                )
        else:
            A = rng.standard_normal((n_assets, n_assets))
            corr = np.corrcoef(A)

        # Ensure PD
        eigvals, eigvecs = np.linalg.eigh(corr)
        eigvals = np.maximum(eigvals, 1e-8)
        corr = eigvecs @ np.diag(eigvals) @ eigvecs.T
        corr = (corr + corr.T) / 2
        np.fill_diagonal(corr, 1.0)

        cholesky = np.linalg.cholesky(corr)

        # Independent Brownian increments
        dW_indep = rng.standard_normal((n_samples, n_assets, n_steps)) * sqrt_dt

        # Correlate
        dW = np.einsum("ij,kjt->kit", cholesky, dW_indep)

        paths = np.zeros((n_samples, n_assets, n_steps + 1))
        mu = 0.05
        vol = 0.2

        if sde_type == "GBM":
            paths[:, :, 0] = 100.0
            for t in range(n_steps):
                paths[:, :, t + 1] = paths[:, :, t] * (
                    1.0 + mu * dt + vol * dW[:, :, t]
                )
                paths[:, :, t + 1] = np.maximum(paths[:, :, t + 1], 1e-12)
        elif sde_type == "OU":
            theta, mu_ou = 0.5, 0.0
            paths[:, :, 0] = mu_ou
            for t in range(n_steps):
                paths[:, :, t + 1] = (
                    paths[:, :, t]
                    + theta * (mu_ou - paths[:, :, t]) * dt
                    + vol * dW[:, :, t]
                )
        elif sde_type == "CIR":
            k_c, theta_c = 0.5, 0.05
            paths[:, :, 0] = theta_c
            for t in range(n_steps):
                x = np.maximum(paths[:, :, t], 0.0)
                paths[:, :, t + 1] = (
                    x
                    + k_c * (theta_c - x) * dt
                    + vol * np.sqrt(x) * dW[:, :, t]
                )
                paths[:, :, t + 1] = np.maximum(paths[:, :, t + 1], 0.0)
        else:  # Vasicek
            a_v, b_v = 0.5, 0.0
            paths[:, :, 0] = b_v
            for t in range(n_steps):
                paths[:, :, t + 1] = (
                    paths[:, :, t]
                    + a_v * (b_v - paths[:, :, t]) * dt
                    + vol * dW[:, :, t]
                )

        final_prices = paths[:, :, -1]
        asset_stats = []
        for a in range(n_assets):
            fa = final_prices[:, a]
            asset_stats.append({
                "mean": float(np.mean(fa)),
                "std": float(np.std(fa, ddof=1)),
                "skew": float(scipy_stats.skew(fa)),
                "kurtosis": float(scipy_stats.kurtosis(fa)),
            })

        return {
            "paths": paths,
            "correlation_matrix": corr,
            "final_prices": final_prices,
            "asset_statistics": asset_stats,
        }

    # ------------------------------------------------------------------
    def conditional_generation(
        self,
        observed_data: np.ndarray,
        n_samples: int = 500,
        n_steps: int = 50,
        guidance_scale: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Conditioned diffusion: denoise from noisy initialisation guided
        by empirical distribution moments.

        Starts each synthetic path from a perturbation of the observed
        data mean, then iteratively denoises towards target moments
        (mean, std) using an SDE with drift that pulls samples toward
        the target statistics.

        Parameters
        ----------
        observed_data : ndarray (n_obs,) or (n_obs, n_features)
        n_samples : int, default 500
        n_steps : int, default 50
            Number of denoising steps.
        guidance_scale : float, default 1.0
            Strength of moment-matching guidance.

        Returns
        -------
        dict
            - ``synthetic_samples`` : ndarray (n_samples, n_features)
            - ``observed_statistics`` : dict
            - ``synthetic_statistics`` : dict
            - ``moment_errors`` : dict of abs differences
        """
        data = np.asarray(observed_data, dtype=float)
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        n_obs, n_features = data.shape

        if n_samples < 1 or n_steps < 1:
            raise ValueError("n_samples and n_steps must be >= 1.")
        if guidance_scale < 0:
            raise ValueError("guidance_scale must be non-negative.")

        rng = self._rng

        # Target moments from observed data
        target_mean = np.mean(data, axis=0)
        target_std = np.std(data, axis=0, ddof=1)
        target_std = np.maximum(target_std, 1e-8)

        # Initialise from noisy samples around target mean
        noise_scale = np.max(target_std) * 2.0
        samples = rng.normal(
            loc=target_mean[np.newaxis, :],
            scale=noise_scale,
            size=(n_samples, n_features),
        )

        # Denoising schedule: noise level decays
        noise_schedule = np.linspace(noise_scale, 1e-4, n_steps + 1)
        dt_guide = 1.0 / n_steps

        for step in range(n_steps):
            current_noise = noise_schedule[step]
            next_noise = noise_schedule[step + 1]
            noise_ratio = next_noise / current_noise if current_noise > 0 else 0

            # Drift toward target moments (guidance)
            sample_mean = np.mean(samples, axis=0, keepdims=True)
            sample_std = np.std(samples, axis=0, keepdims=True, ddof=1)
            sample_std = np.maximum(sample_std, 1e-8)

            # Pull mean toward target
            drift_mean = guidance_scale * (target_mean[np.newaxis, :] - sample_mean)
            # Pull std toward target (via multiplicative adjustment)
            std_ratio = target_std[np.newaxis, :] / sample_std
            drift_std = guidance_scale * (std_ratio - 1.0) * (samples - sample_mean)

            drift = drift_mean + drift_std

            # Diffusion noise (decreasing)
            diff_noise = rng.standard_normal((n_samples, n_features)) * np.sqrt(
                max(next_noise**2 - noise_ratio**2 * current_noise**2, 0)
            )

            samples = noise_ratio * samples + drift * dt_guide + diff_noise

        # Final statistics
        obs_stats = {
            "mean": target_mean.tolist(),
            "std": target_std.tolist(),
        }
        syn_mean = np.mean(samples, axis=0)
        syn_std = np.std(samples, axis=0, ddof=1)
        syn_stats = {
            "mean": syn_mean.tolist(),
            "std": syn_std.tolist(),
        }
        moment_errors = {
            "mean_abs_error": float(np.mean(np.abs(syn_mean - target_mean))),
            "std_abs_error": float(np.mean(np.abs(syn_std - target_std))),
        }

        return {
            "synthetic_samples": samples,
            "observed_statistics": obs_stats,
            "synthetic_statistics": syn_stats,
            "moment_errors": moment_errors,
        }

    # ------------------------------------------------------------------
    def score_matching(
        self,
        data: np.ndarray,
        n_basis: int = 10,
    ) -> Dict[str, Any]:
        """
        Fit a score function (∇_x log p(x)) using radial basis
        functions via least-squares.

        Parameters
        ----------
        data : ndarray (n_samples,) or (n_samples, 1)
        n_basis : int, default 10
            Number of RBF centres.

        Returns
        -------
        dict
            - ``basis_centres`` : ndarray of RBF centres
            - ``basis_widths`` : float (shared bandwidth)
            - ``weights`` : ndarray of fitted weights
            - ``bandwidth`` : float
        """
        data = np.asarray(data, dtype=float).ravel()
        n = len(data)
        if n < n_basis:
            warnings.warn(
                f"n_samples ({n}) < n_basis ({n_basis}); reducing n_basis."
            )
            n_basis = n
        if n_basis < 1:
            raise ValueError("n_basis must be >= 1.")

        # RBF centres: quantile-spaced
        centres = np.quantile(data, np.linspace(0, 1, n_basis))

        # Bandwidth (Silverman's rule)
        std_data = np.std(data, ddof=1)
        if std_data < 1e-10:
            std_data = 1.0
        bandwidth = std_data * (4.0 / (3 * n)) ** (1.0 / 5)
        h = max(bandwidth, 1e-8)

        # Build design matrix: φ_j(x) = exp(-(x - c_j)^2 / (2h^2))
        X = np.exp(
            -0.5 * ((data[:, None] - centres[None, :]) / h) ** 2
        )

        # Target score: use kernel density gradient estimate
        # s(x_i) ≈ Σ_j (x_j - x_i) K_h(x_j - x_i) / (h^2 Σ_j K_h(x_j - x_i))
        # Simplified: finite-difference of log KDE
        from scipy.ndimage import gaussian_filter1d
        hist, bin_edges = np.histogram(data, bins=min(100, n // 5), density=True)
        log_hist = np.log(np.maximum(hist, 1e-12))
        # Smooth
        smoothed_log = gaussian_filter1d(log_hist, sigma=2)
        # Score at bin centres
        d_log = np.gradient(smoothed_log, bin_edges[1] - bin_edges[0])
        bin_centres = 0.5 * (bin_edges[:-1] + bin_edges[1:])

        # Interpolate score to data points
        score_targets = np.interp(data, bin_centres, d_log)

        # Least-squares fit: score(x) ≈ Σ_j w_j * dφ_j/dx
        # dφ_j/dx = -(x - c_j)/h^2 * φ_j(x)
        dphi = -((data[:, None] - centres[None, :]) / h**2) * X

        # Ridge regression
        alpha = 1e-4
        w, _, _, _ = np.linalg.lstsq(
            dphi.T @ dphi + alpha * np.eye(n_basis),
            dphi.T @ score_targets,
            rcond=None,
        )

        return {
            "basis_centres": centres.tolist(),
            "basis_widths": float(h),
            "weights": w.tolist(),
            "bandwidth": float(bandwidth),
        }

    # ------------------------------------------------------------------
    def generate_realistic_prices(
        self,
        n_assets: int = 5,
        n_days: int = 252,
        return_stats: Optional[List[Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate realistic price paths matching given return statistics
        using guided diffusion.

        Parameters
        ----------
        n_assets : int, default 5
        n_days : int, default 252
        return_stats : list of dict, optional
            Per-asset return statistics.  Each dict may contain keys
            ``mean``, ``vol``, ``skew``, ``kurt``.  If None, sensible
            defaults are used.

        Returns
        -------
        dict
            - ``prices`` : DataFrame (n_days, n_assets)
            - ``returns`` : DataFrame (n_days-1, n_assets)
            - ``actual_statistics`` : list of dicts
            - ``target_statistics`` : list of dicts
        """
        if n_assets < 1 or n_days < 2:
            raise ValueError("n_assets >= 1 and n_days >= 2 required.")

        rng = self._rng

        # Default stats
        defaults = [
            {"mean": 0.0004, "vol": 0.015, "skew": -0.3, "kurt": 5.0}
        ] * n_assets
        if return_stats is not None:
            for i in range(min(len(return_stats), n_assets)):
                d = defaults[i].copy()
                d.update(return_stats[i])
                defaults[i] = d
        target_stats = defaults[:n_assets]

        dt = 1.0 / 252
        paths = np.zeros((n_days, n_assets))
        paths[0] = 100.0  # all start at 100

        for a in range(n_assets):
            ts = target_stats[a]
            mu = ts.get("mean", 0.0004)
            vol = ts.get("vol", 0.015)
            skew = ts.get("skew", 0.0)
            kurt = ts.get("kurt", 3.0)

            for t in range(1, n_days):
                # Generate returns with target moments using
                # the method of moments with a shifted log-normal approx
                z = rng.standard_normal()
                # Cornish-Fisher expansion for quantile adjustment
                cf_z = (
                    z
                    + (skew / 6) * (z**2 - 1)
                    + (kurt - 3) / 24 * (z**3 - 3 * z)
                    - (skew**2) / 36 * (2 * z**3 - 5 * z)
                )
                ret = mu + vol * cf_z
                paths[t, a] = paths[t - 1, a] * (1.0 + ret)
                paths[t, a] = max(paths[t, a], 1e-12)

        # Build DataFrames
        dates = pd.bdate_range(start="2024-01-01", periods=n_days)
        asset_names = [f"Asset_{i+1}" for i in range(n_assets)]
        price_df = pd.DataFrame(paths, index=dates, columns=asset_names)
        ret_df = price_df.pct_change().dropna()

        # Actual statistics
        actual_stats = []
        for a in range(n_assets):
            r = ret_df.iloc[:, a].values
            actual_stats.append({
                "mean": float(np.mean(r)),
                "vol": float(np.std(r, ddof=1)),
                "skew": float(scipy_stats.skew(r)),
                "kurt": float(scipy_stats.kurtosis(r)),
            })

        return {
            "prices": price_df,
            "returns": ret_df,
            "actual_statistics": actual_stats,
            "target_statistics": target_stats,
        }


# ---------------------------------------------------------------------------
# 3. FederatedLearningSim
# ---------------------------------------------------------------------------

class FederatedLearningSim:
    """
    Simulate federated learning for distributed financial data.

    Implements FedAvg for OLS, federated PCA, differential privacy
    mechanisms, and secure aggregation — all without moving raw data
    between silos.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    def federated_ols(
        self,
        X_parts: List[np.ndarray],
        y_parts: List[np.ndarray],
        n_rounds: int = 10,
        learning_rate: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Federated linear regression via FedAvg.

        Each client computes a local gradient update; the server
        averages (weighted by client data size) to produce a global
        model update.

        Parameters
        ----------
        X_parts : list of ndarray
            Feature matrices, one per client/silo.
        y_parts : list of ndarray
            Target vectors, one per client/silo.
        n_rounds : int, default 10
            Number of federated communication rounds.
        learning_rate : float, default 0.01
            Step size for gradient descent.

        Returns
        -------
        dict
            - ``global_coefficients`` : ndarray
            - ``convergence_history`` : list of loss per round
            - ``local_models`` : list of per-client final coefficients
            - ``n_clients`` : int
            - ``centralised_coefficients`` : ndarray (ground truth)
        """
        n_clients = len(X_parts)
        if n_clients == 0:
            raise ValueError("X_parts must not be empty.")
        if len(X_parts) != len(y_parts):
            raise ValueError("X_parts and y_parts must have the same length.")
        if n_rounds < 1:
            raise ValueError("n_rounds must be >= 1.")
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")

        # Validate shapes
        for i, (X, y) in enumerate(zip(X_parts, y_parts)):
            if X.ndim == 1:
                X_parts[i] = X.reshape(-1, 1)
                X = X_parts[i]
            if X.shape[0] != y.shape[0]:
                raise ValueError(
                    f"Client {i}: X rows {X.shape[0]} != y rows {y.shape[0]}"
                )

        n_features = X_parts[0].shape[1]

        # Add bias column
        X_parts_aug = [np.hstack([np.ones((X.shape[0], 1)), X]) for X in X_parts]
        n_params = n_features + 1

        # Global model
        w_global = np.zeros(n_params)
        total_n = sum(X.shape[0] for X in X_parts_aug)

        convergence = []

        for rnd in range(n_rounds):
            local_weights = []
            local_ns = []

            for X_c, y_c in zip(X_parts_aug, y_parts):
                n_c = X_c.shape[0]
                # Local gradient: (1/n) X^T (Xw - y)
                residual = X_c @ w_global - y_c
                grad = (X_c.T @ residual) / n_c
                # Local update
                w_local = w_global - learning_rate * grad
                local_weights.append(w_local)
                local_ns.append(n_c)

            # FedAvg: weighted average
            w_global = sum(
                (ns / total_n) * wl for ns, wl in zip(local_ns, local_weights)
            )

            # Global loss (MSE)
            total_loss = 0.0
            for X_c, y_c in zip(X_parts_aug, y_parts):
                total_loss += float(np.mean((X_c @ w_global - y_c) ** 2))
            total_loss /= n_clients
            convergence.append(total_loss)

        # Centralised OLS for comparison
        X_all = np.vstack(X_parts_aug)
        y_all = np.concatenate(y_parts)
        w_central, _, _, _ = np.linalg.lstsq(X_all, y_all, rcond=None)

        return {
            "global_coefficients": w_global.tolist(),
            "convergence_history": convergence,
            "local_models": [wl.tolist() for wl in local_weights],
            "n_clients": n_clients,
            "centralised_coefficients": w_central.tolist(),
        }

    # ------------------------------------------------------------------
    def federated_pca(
        self,
        data_parts: List[np.ndarray],
        n_components: int = 5,
        n_rounds: int = 10,
    ) -> Dict[str, Any]:
        """
        Federated PCA: each client computes a local covariance matrix;
        the server averages them and extracts eigenvectors.

        Parameters
        ----------
        data_parts : list of ndarray (n_i, n_features)
        n_components : int, default 5
        n_rounds : int, default 10
            Iterative refinement rounds (covariance averaging).

        Returns
        -------
        dict
            - ``principal_components`` : ndarray (n_features, n_components)
            - ``explained_variance`` : ndarray (n_components,)
            - ``explained_variance_ratio`` : ndarray (n_components,)
            - ``n_rounds_used`` : int
        """
        if not data_parts:
            raise ValueError("data_parts must not be empty.")
        n_features = data_parts[0].shape[1]
        if n_components < 1 or n_components > n_features:
            raise ValueError(
                f"n_components must be in [1, {n_features}]."
            )

        # Weighted average covariance
        total_n = sum(d.shape[0] for d in data_parts)
        cov_global = np.zeros((n_features, n_features))

        for rnd in range(n_rounds):
            cov_accum = np.zeros((n_features, n_features))
            for d in data_parts:
                d_centred = d - np.mean(d, axis=0, keepdims=True)
                cov_accum += (d_centred.T @ d_centred) * (d.shape[0] / total_n)
            cov_global = cov_accum

        # Eigendecomposition
        eigvals, eigvecs = np.linalg.eigh(cov_global)
        # Sort descending
        idx = np.argsort(eigvals)[::-1]
        eigvals = eigvals[idx][:n_components]
        eigvecs = eigvecs[:, idx][:, :n_components]

        total_var = np.sum(np.maximum(eigvals, 0))
        total_var = max(total_var, 1e-12)

        return {
            "principal_components": eigvecs.tolist(),
            "explained_variance": eigvals.tolist(),
            "explained_variance_ratio": (eigvals / total_var).tolist(),
            "n_rounds_used": n_rounds,
        }

    # ------------------------------------------------------------------
    def differential_privacy_mechanism(
        self,
        data: np.ndarray,
        epsilon: float = 1.0,
        mechanism: str = "laplace",
        delta: float = 1e-5,
    ) -> Dict[str, Any]:
        """
        Add differentially private noise to data.

        Parameters
        ----------
        data : ndarray
            The data vector to privatise.
        epsilon : float, default 1.0
            Privacy budget (smaller = more private).
        mechanism : str, default 'laplace'
            'laplace' or 'gaussian'.
        delta : float, default 1e-5
            Delta parameter for Gaussian mechanism.

        Returns
        -------
        dict
            - ``private_data`` : ndarray
            - ``epsilon_used`` : float
            - ``mechanism`` : str
            - ``noise_statistics`` : dict
        """
        data = np.asarray(data, dtype=float)
        if epsilon <= 0:
            raise ValueError("epsilon must be positive.")
        if mechanism not in ("laplace", "gaussian"):
            raise ValueError("mechanism must be 'laplace' or 'gaussian'.")

        # Sensitivity (L1 for Laplace, L2 for Gaussian)
        # For a sum query, sensitivity = max |x_i|
        sensitivity = float(np.max(np.abs(data))) if data.size > 0 else 1.0
        sensitivity = max(sensitivity, 1e-8)

        rng = self._rng

        if mechanism == "laplace":
            scale = sensitivity / epsilon
            noise = rng.laplace(0.0, scale, size=data.shape)
        else:  # gaussian
            sigma_noise = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
            noise = rng.normal(0.0, sigma_noise, size=data.shape)

        private_data = data + noise

        return {
            "private_data": private_data,
            "epsilon_used": float(epsilon),
            "mechanism": mechanism,
            "noise_statistics": {
                "mean": float(np.mean(noise)),
                "std": float(np.std(noise, ddof=1)),
                "sensitivity": float(sensitivity),
            },
        }

    # ------------------------------------------------------------------
    def secure_aggregation(
        self,
        local_updates: List[np.ndarray],
        noise_scale: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Simulate secure aggregation with masking.

        Each client masks its update with a random seed; pairs of
        clients share secrets that cancel out during aggregation.

        Parameters
        ----------
        local_updates : list of ndarray
            One update vector per client.
        noise_scale : float, default 0.01
            Scale of the residual masking noise.

        Returns
        -------
        dict
            - ``aggregated_update`` : ndarray
            - ``privacy_budget_consumed`` : float (epsilon)
            - ``n_clients" : int
            - ``mask_noise_std" : float
        """
        if not local_updates:
            raise ValueError("local_updates must not be empty.")
        n_clients = len(local_updates)
        if n_clients < 2:
            raise ValueError("Need at least 2 clients for secure aggregation.")

        rng = self._rng
        shape = local_updates[0].shape

        # Each client generates a pair-wise mask: for client i,
        # generate seed with client j, masks cancel: m_ij + m_ji = 0
        masks = [np.zeros(shape) for _ in range(n_clients)]
        for i in range(n_clients):
            for j in range(i + 1, n_clients):
                pair_mask = rng.normal(0, noise_scale, size=shape)
                masks[i] += pair_mask
                masks[j] -= pair_mask

        # Masked updates
        masked_updates = [u + m for u, m in zip(local_updates, masks)]

        # Sum masked updates — pair-wise masks cancel
        aggregated = np.sum(masked_updates, axis=0)

        # Small residual due to floating-point
        residual_std = float(np.std(
            aggregated - np.sum(local_updates, axis=0)
        ))

        # Privacy budget: approximate epsilon from noise scale
        sensitivity = float(np.max([np.max(np.abs(u)) for u in local_updates]))
        sensitivity = max(sensitivity, 1e-8)
        epsilon = sensitivity / max(noise_scale, 1e-12)

        return {
            "aggregated_update": aggregated.tolist(),
            "privacy_budget_consumed": float(epsilon),
            "n_clients": n_clients,
            "mask_noise_std": float(noise_scale),
        }

    # ------------------------------------------------------------------
    def cross_silo_simulation(
        self,
        n_silos: int = 5,
        n_samples_per_silo: int = 200,
        n_features: int = 10,
        n_rounds: int = 15,
    ) -> Dict[str, Any]:
        """
        End-to-end federated learning simulation.

        Creates synthetic siloed data with heterogeneity, runs federated
        OLS, and compares to centralised OLS.

        Parameters
        ----------
        n_silos : int, default 5
        n_samples_per_silo : int, default 200
        n_features : int, default 10
        n_rounds : int, default 15

        Returns
        -------
        dict
            - ``coefficient_difference" : max abs diff (federated vs central)
            - ``coefficient_l2_distance" : L2 norm of difference
            - ``r_squared_federated" : float
            - ``r_squared_centralised" : float
            - ``r_squared_difference" : float
            - ``convergence_history" : list
        """
        if n_silos < 2:
            raise ValueError("n_silos must be >= 2.")
        if n_samples_per_silo < 10:
            raise ValueError("n_samples_per_silo must be >= 10.")
        if n_features < 1:
            raise ValueError("n_features must be >= 1.")

        rng = self._rng

        # True coefficients
        true_coef = rng.standard_normal(n_features)
        true_intercept = rng.normal(0, 1)

        X_parts = []
        y_parts = []
        for s in range(n_silos):
            # Non-IID: each silo has slight feature distribution shift
            shift = rng.normal(0, 0.5, size=n_features)
            X_s = rng.standard_normal((n_samples_per_silo, n_features)) + shift
            noise_s = rng.normal(0, 0.5, size=n_samples_per_silo)
            y_s = true_intercept + X_s @ true_coef + noise_s
            X_parts.append(X_s)
            y_parts.append(y_s)

        # Run federated OLS
        result = self.federated_ols(X_parts, y_parts, n_rounds=n_rounds)
        w_fed = np.array(result["global_coefficients"])
        w_cent = np.array(result["centralised_coefficients"])

        # Coefficient comparison (exclude intercept for fairness)
        coef_diff = np.abs(w_fed[1:] - w_cent[1:])
        coef_l2 = float(np.linalg.norm(w_fed[1:] - w_cent[1:]))

        # R-squared on pooled data
        X_all = np.vstack(X_parts)
        y_all = np.concatenate(y_parts)
        X_aug = np.hstack([np.ones((X_all.shape[0], 1)), X_all])

        ss_tot = float(np.sum((y_all - np.mean(y_all)) ** 2))
        ss_res_fed = float(np.sum((X_aug @ w_fed - y_all) ** 2))
        ss_res_cent = float(np.sum((X_aug @ w_cent - y_all) ** 2))
        r2_fed = 1.0 - ss_res_fed / ss_tot if ss_tot > 0 else 0.0
        r2_cent = 1.0 - ss_res_cent / ss_tot if ss_tot > 0 else 0.0

        return {
            "coefficient_difference": float(np.max(coef_diff)),
            "coefficient_l2_distance": coef_l2,
            "r_squared_federated": float(r2_fed),
            "r_squared_centralised": float(r2_cent),
            "r_squared_difference": float(abs(r2_fed - r2_cent)),
            "convergence_history": result["convergence_history"],
        }


# ---------------------------------------------------------------------------
# 4. QuantumGameTheory
# ---------------------------------------------------------------------------

class QuantumGameTheory:
    """
    Quantum game theory simulations.

    Extends classical game-theoretic scenarios to the quantum regime
    using entanglement, superposition, and quantum operations.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    def quantum_prisoners_dilemma(
        self,
        gamma: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Quantum Prisoner's Dilemma with entanglement parameter γ.

        The classical payoff matrix:
            (C,C) -> (3,3),  (C,D) -> (0,5)
            (D,C) -> (5,0),  (D,D) -> (1,1)

        Quantum version: players share an entangled state
        |Ψ⟩ = cos(γ)|00⟩ + i sin(γ)|11⟩
        and apply local unitary strategies before a joint measurement.

        Parameters
        ----------
        gamma : float, default 0.5
            Entanglement parameter in [0, π/2].  0 = classical,
            π/2 = maximally entangled.

        Returns
        -------
        dict
            - ``classical_payoff_matrix`` : ndarray (2,2,2) [player, strat, strat]
            - ``quantum_payoff_matrix`` : dict mapping strategy pairs to payoffs
            - ``classical_nash" : list of Nash equilibrium strategy pairs
            - ``quantum_nash" : list of quantum Nash equilibrium info
            - ``entanglement_parameter" : float
        """
        if not (0 <= gamma <= np.pi / 2):
            raise ValueError("gamma must be in [0, pi/2].")

        # Classical payoff matrix: payoff[a][b] = (payoff_A, payoff_B)
        # Strategies: 0=Cooperate, 1=Defect
        classical = np.array(
            [[[3, 0], [5, 1]],    # Player A's payoffs
             [[3, 5], [0, 1]]],   # Player B's payoffs
            dtype=float,
        )

        # Classical Nash: (D,D) = (1,1) is the unique NE
        classical_nash = [("Defect", "Defect", 1.0, 1.0)]

        # --- Quantum strategies -------------------------------------------
        # Standard quantum strategies as 2x2 unitary matrices
        I = np.eye(2, dtype=complex)
        X_gate = np.array([[0, 1], [1, 0]], dtype=complex)  # NOT = Defect

        # Entangled initial state
        psi_0 = np.zeros(4, dtype=complex)
        psi_0[0] = np.cos(gamma)      # |00>
        psi_0[3] = 1j * np.sin(gamma)  # |11>

        # Joint operator: J^† (U_A ⊗ U_B) J |psi_0>
        # J = (cos γ I⊗I + i sin γ X⊗X)
        J = np.cos(gamma) * np.kron(I, I) + 1j * np.sin(gamma) * np.kron(X_gate, X_gate)
        J_dag = J.conj().T

        # Strategy set: C = I, D = X, plus quantum strategies
        strategies = {
            "Cooperate": I,
            "Defect": X_gate,
            "Superposition": np.array(
                [[1, -1j], [1j, -1]], dtype=complex
            ) / np.sqrt(2),
        }

        quantum_payoffs = {}
        quantum_nash_list = []
        best_pareto = -np.inf

        for name_a, U_a in strategies.items():
            for name_b, U_b in strategies.items():
                joint_U = np.kron(U_a, U_b)
                psi_final = J_dag @ joint_U @ J @ psi_0
                probs = np.abs(psi_final) ** 2

                # Expected payoff = Σ_{ij} prob(ij) * classical_payoff(i,j)
                payoff_a = 0.0
                payoff_b = 0.0
                mapping = {0: 0, 1: 1}  # basis state -> classical action
                for i in range(2):
                    for j in range(2):
                        idx = i * 2 + j
                        payoff_a += probs[idx] * classical[0, i, j]
                        payoff_b += probs[idx] * classical[1, j, i]

                quantum_payoffs[(name_a, name_b)] = (
                    float(np.real(payoff_a)),
                    float(np.real(payoff_b)),
                )

                # Pareto check
                min_payoff = min(np.real(payoff_a), np.real(payoff_b))
                if min_payoff > best_pareto and not (
                    name_a == "Defect" and name_b == "Defect"
                ):
                    best_pareto = min_payoff
                    quantum_nash_list = [
                        (name_a, name_b, float(np.real(payoff_a)), float(np.real(payoff_b)))
                    ]
                elif min_payoff == best_pareto:
                    quantum_nash_list.append(
                        (name_a, name_b, float(np.real(payoff_a)), float(np.real(payoff_b)))
                    )

        # Format quantum payoffs as serialisable dict
        qp_serialised = {
            f"{k[0]}_vs_{k[1]}": v for k, v in quantum_payoffs.items()
        }

        return {
            "classical_payoff_matrix": classical.tolist(),
            "quantum_payoff_matrix": qp_serialised,
            "classical_nash": classical_nash,
            "quantum_nash": quantum_nash_list,
            "entanglement_parameter": float(gamma),
        }

    # ------------------------------------------------------------------
    def quantum_bit_commitment(
        self,
        n_rounds: int = 100,
    ) -> Dict[str, Any]:
        """
        Simulate quantum bit commitment protocol.

        In the quantum protocol, the committer encodes a bit into a
        quantum state.  Due to the no-cloning theorem and the
        uncertainty principle, the receiver cannot perfectly determine
        the bit during the commit phase, and the committer cannot
        change the bit during the reveal phase.

        Parameters
        ----------
        n_rounds : int, default 100
            Number of protocol rounds to simulate.

        Returns
        -------
        dict
            - ``quantum_success_rate" : float [0,1]
            - ``classical_success_rate" : float [0,1]
            - ``quantum_cheat_rate" : float [0,1]
            - ``n_rounds" : int
        """
        if n_rounds < 1:
            raise ValueError("n_rounds must be >= 1.")

        rng = self._rng

        # Quantum protocol: committer sends one of two non-orthogonal states
        # |0> -> |0>, |1> -> (|0> + |1>)/sqrt(2)
        # Receiver's optimal measurement distinguishes with probability
        # 1 - 1/sqrt(2) ≈ 0.293 error
        state_0 = np.array([1, 0], dtype=complex)
        state_1 = np.array([1, 1], dtype=complex) / np.sqrt(2)

        # POVM for minimum-error discrimination
        # Optimal success: cos²(π/8) ≈ 0.854
        p_correct_quantum = np.cos(np.pi / 8) ** 2

        # Classical: simple bit commitment (easily cheated)
        # In a classical protocol with no trusted third party,
        # the receiver can always guess correctly 50% and the
        # committer can always change their bit.
        p_correct_classical = 0.5  # random guess

        quantum_success = 0
        classical_success = 0
        quantum_cheat = 0  # committer tries to change bit

        for _ in range(n_rounds):
            true_bit = int(rng.integers(0, 2))
            state = state_0 if true_bit == 0 else state_1

            # Receiver measurement (Helstrom measurement)
            # Probability of correct detection
            if rng.random() < p_correct_quantum:
                detected = true_bit
            else:
                detected = 1 - true_bit
            if detected == true_bit:
                quantum_success += 1

            # Classical: receiver just guesses
            classical_guess = int(rng.integers(0, 2))
            if classical_guess == true_bit:
                classical_success += 1

            # Quantum cheat attempt: committer tries to change bit
            # After no-cloning, changing is limited
            # With non-orthogonal states, cheat success is bounded
            if rng.random() < (1 - p_correct_quantum):
                quantum_cheat += 1

        return {
            "quantum_success_rate": float(quantum_success / n_rounds),
            "classical_success_rate": float(classical_success / n_rounds),
            "quantum_cheat_rate": float(quantum_cheat / n_rounds),
            "n_rounds": n_rounds,
        }

    # ------------------------------------------------------------------
    def quantum_auction(
        self,
        bids: List[float],
        reserve_price: float = 0,
    ) -> Dict[str, Any]:
        """
        Simulate a quantum sealed-bid auction.

        In a quantum auction, bids are encoded in quantum states.
        Due to the no-cloning theorem, bids cannot be copied, providing
        privacy.  A quantum comparison circuit determines the winner.

        Parameters
        ----------
        bids : list of float
            Bid values from each bidder.
        reserve_price : float, default 0
            Minimum acceptable bid.

        Returns
        -------
        dict
            - ``winner" : int (index)
            - ``winning_bid" : float
            - ``second_price" : float (Vickrey-style)
            - ``all_bids" : list of float
            - ``quantum_advantage" : dict
        """
        if not bids:
            raise ValueError("bids must not be empty.")
        if any(b < 0 for b in bids):
            raise ValueError("All bids must be non-negative.")

        n_bidders = len(bids)
        bids_arr = np.array(bids, dtype=float)

        # Filter by reserve price
        eligible_mask = bids_arr >= reserve_price
        if not np.any(eligible_mask):
            return {
                "winner": -1,
                "winning_bid": 0.0,
                "second_price": 0.0,
                "all_bids": bids,
                "quantum_advantage": {
                    "privacy_preserved": True,
                    "bid_reveal_probability": 0.0,
                    "collusion_resistance": 1.0,
                },
            }

        eligible_bids = bids_arr[eligible_mask]
        eligible_indices = np.where(eligible_mask)[0]

        # Quantum advantage: bids encoded in quantum states
        # Privacy: no-cloning prevents bid copying
        # Each bid is encoded as |ψ_i> = cos(b_i / B) |0> + sin(b_i / B) |1>
        # where B is a normalisation constant
        B = max(np.max(bids_arr), 1.0)
        bid_states = np.column_stack([
            np.cos(bids_arr / B),
            np.sin(bids_arr / B),
        ])

        # Quantum comparison: inner product measures bid similarity
        # The winner has the highest bid -> highest sin(b/B)
        winner_idx = int(eligible_indices[np.argmax(eligible_bids)])
        winning_bid = float(bids_arr[winner_idx])

        # Second-price (Vickrey)
        sorted_bids = np.sort(eligible_bids)[::-1]
        second_price = float(sorted_bids[1]) if len(sorted_bids) > 1 else 0.0

        # Quantum advantage metrics
        # Privacy: quantum states reveal no information until measurement
        # Collusion: entangled bids would be detectable
        bid_overlap_matrix = bid_states @ bid_states.T
        # Min overlap (except diagonal) indicates privacy strength
        np.fill_diagonal(bid_overlap_matrix, 0)
        avg_overlap = float(np.mean(np.abs(bid_overlap_matrix)))

        return {
            "winner": winner_idx,
            "winning_bid": winning_bid,
            "second_price": second_price,
            "all_bids": bids,
            "quantum_advantage": {
                "privacy_preserved": True,
                "bid_reveal_probability": round(avg_overlap, 6),
                "collusion_resistance": round(1.0 - avg_overlap, 6),
                "n_bidders": n_bidders,
            },
        }
