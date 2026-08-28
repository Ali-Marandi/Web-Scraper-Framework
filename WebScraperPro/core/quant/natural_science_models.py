"""
natural_science_models.py

Models from the natural sciences applied to financial analysis:
  - Climate Value-at-Risk (ClimateVaR): climate-adjusted risk measurement
  - Hotelling Rule (HotellingRule): exhaustible resource extraction economics
  - SIR/SEIR Epidemic Models (SIRModel): compartmental disease models
  - Innovation S-Curves (InnovationSCurve): technology diffusion and adoption
  - Epidemic-Finance Bridge (EpidemicFinance): epidemic impact on markets

Dependencies: numpy, pandas, scipy only.
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint
from scipy.optimize import minimize, curve_fit
from typing import Optional, Dict, Any, List, Tuple
import warnings
warnings.filterwarnings("ignore")


# ===========================================================================
# 1. Climate Value-at-Risk
# ===========================================================================

class ClimateVaR:
    """Climate-adjusted Value-at-Risk and physical/transitional risk models.

    Applies climate science frameworks (temperature anomalies, carbon
    intensity, physical hazard functions) to financial risk measurement,
    aligned with TCFD recommendations.
    """

    def estimate(self, asset_returns: np.ndarray, temperature_data: np.ndarray,
                 transition_scenario: str = 'gradual') -> Dict[str, Any]:
        """Climate Value-at-Risk via regression of returns on temperature anomalies.

        Regresses asset returns on temperature anomaly data to extract a
        *climate beta*.  The adjusted VaR is then:

            VaR_climate = VaR_market + climate_beta * temperature_shock

        Parameters
        ----------
        asset_returns : np.ndarray, shape (T,)
            Periodic (e.g. daily or monthly) asset returns.
        temperature_data : np.ndarray, shape (T,)
            Temperature anomaly series (same length as returns).
        transition_scenario : str
            One of ``'gradual'``, ``'rapid'``, ``'disorderly'``.  Controls
            the magnitude of the assumed temperature shock used for the
            VaR adjustment.

        Returns
        -------
        dict with keys ``climate_beta``, ``var_adjusted``,
        ``temperature_sensitivity``, ``carbon_exposure``.
        """
        returns = np.asarray(asset_returns, dtype=np.float64).ravel()
        temp = np.asarray(temperature_data, dtype=np.float64).ravel()
        n = min(len(returns), len(temp))
        returns = returns[:n]
        temp = temp[:n]

        # --- OLS: r_t = alpha + beta_climate * T_t + epsilon_t ---
        X = np.column_stack([np.ones(n), temp])
        y = returns
        beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]
        alpha, climate_beta = beta_hat

        residuals = y - X @ beta_hat
        sigma = np.std(residuals, ddof=2)

        # Standard market VaR (parametric, 95 %)
        var_market = np.percentile(returns, 5)

        # Temperature shock depends on transition scenario
        shock_map = {'gradual': 1.5, 'rapid': 2.5, 'disorderly': 4.0}
        temperature_shock = shock_map.get(transition_scenario.lower(), 1.5)

        var_adjusted = var_market + climate_beta * temperature_shock * sigma

        # Temperature sensitivity: correlation and elasticity
        temp_sensitivity = np.corrcoef(returns, temp)[0, 1]

        # Carbon exposure proxy: proportion of return variance explained by temp
        ss_total = np.var(returns, ddof=1) * (n - 1)
        ss_resid = np.sum(residuals ** 2)
        r_squared = 1.0 - ss_resid / ss_total if ss_total > 0 else 0.0
        carbon_exposure = float(np.clip(r_squared, 0, 1))

        return {
            'climate_beta': float(climate_beta),
            'var_adjusted': float(var_adjusted),
            'temperature_sensitivity': float(temp_sensitivity),
            'carbon_exposure': carbon_exposure,
        }

    # ------------------------------------------------------------------
    def tcfd_disclosure(self, portfolio_weights: np.ndarray,
                        sector_carbon_intensity: np.ndarray,
                        temperature_paths: Optional[Dict[str, np.ndarray]] = None
                        ) -> Dict[str, Any]:
        """TCFD-aligned scenario analysis across temperature pathways.

        For each temperature path the portfolio-level impact is estimated
        as a dot-product of sector exposures (weights * carbon intensity)
        with a damage function that is quadratic in the temperature level:

            impact(theta) = w^T * c * [0.5 * theta^2]

        Parameters
        ----------
        portfolio_weights : array-like, shape (n_sectors,)
            Portfolio weight per sector (must sum to 1).
        sector_carbon_intensity : array-like, shape (n_sectors,)
            Carbon intensity (e.g. tCO2e / $M revenue) per sector.
        temperature_paths : dict or None
            Mapping from scenario name (e.g. ``'1.5C'``) to an array of
            projected temperature anomalies over the horizon.  If *None*,
            default paths for 1.5  degC, 2  degC, and 3  degC+ are generated.

        Returns
        -------
        dict with ``scenario_impacts`` and ``weighted_avg_exposure``.
        """
        w = np.asarray(portfolio_weights, dtype=np.float64).ravel()
        c = np.asarray(sector_carbon_intensity, dtype=np.float64).ravel()
        n = min(len(w), len(c))
        w, c = w[:n], c[:n]
        w = w / w.sum()  # normalise

        # Default temperature paths (annual, 30-year horizon)
        if temperature_paths is None:
            years = 30
            temperature_paths = {
                '1.5C': np.linspace(0.8, 1.5, years),
                '2C':   np.linspace(0.8, 2.0, years),
                '3C+':  np.linspace(0.8, 3.5, years),
            }

        weighted_carbon = float(w @ c)
        scenario_impacts = {}

        for name, path in temperature_paths.items():
            path = np.asarray(path, dtype=np.float64).ravel()
            # Quadratic damage: damage(theta) ~ 0.5 * theta^2  (Nordhaus-style)
            damage = 0.5 * path ** 2
            # Portfolio impact = weighted carbon intensity x damage
            impact = weighted_carbon * damage
            scenario_impacts[name] = {
                'annual_impact': impact.tolist(),
                'cumulative_impact': float(np.sum(impact)),
                'terminal_impact': float(impact[-1]),
                'path': path.tolist(),
            }

        return {
            'scenario_impacts': scenario_impacts,
            'weighted_avg_exposure': weighted_carbon,
        }

    # ------------------------------------------------------------------
    def physical_risk(self, asset_values: np.ndarray, hazard_probability: np.ndarray,
                      damage_function: str = 'linear') -> Dict[str, Any]:
        """Physical climate risk: expected loss from natural hazards.

        Computes:

            E[Loss] = sum_j  P(hazard_j) * damage(asset_j, hazard_j)

        Supported damage functions:
        * ``'linear'``:     damage = asset * prob
        * ``'quadratic'``:  damage = asset * prob^2
        * ``'exponential'``: damage = asset * (exp(prob) - 1)

        Parameters
        ----------
        asset_values : array-like, shape (n_assets,)
            Current market or book value of each asset.
        hazard_probability : array-like, shape (n_hazards, n_assets)
            Probability (or intensity in [0,1]) of each hazard affecting
            each asset.
        damage_function : str
            Functional form of the damage curve.

        Returns
        -------
        dict with ``expected_loss`` and ``risk_by_hazard``.
        """
        assets = np.asarray(asset_values, dtype=np.float64).ravel()
        P = np.asarray(hazard_probability, dtype=np.float64)

        if P.ndim == 1:
            P = P.reshape(1, -1)

        n_hazards, n_assets = P.shape
        n = min(n_assets, len(assets))
        assets = assets[:n]
        P = P[:, :n]

        if damage_function == 'linear':
            damage = lambda p: p
        elif damage_function == 'quadratic':
            damage = lambda p: p ** 2
        elif damage_function == 'exponential':
            damage = lambda p: np.expm1(np.clip(p, 0, 0.7))  # exp(p)-1, clipped
        else:
            damage = lambda p: p

        # E[Loss] per hazard, summed over assets
        loss_matrix = P * np.tile(damage(P), (1, 1)) * assets[np.newaxis, :]
        # More precisely: for each hazard j and asset i:
        #   loss_ji = P_ji * damage(P_ji) * asset_i
        # but the intent is E[Loss] = sum_j P_j * damage(asset, hazard)
        # Using: per hazard expected loss = sum_i P_ji * f(P_ji) * asset_i
        risk_by_hazard = {}
        total_expected_loss = 0.0
        for j in range(n_hazards):
            d = damage(P[j])
            expected_loss_j = float(np.sum(P[j] * d * assets))
            total_expected_loss += expected_loss_j
            risk_by_hazard[f'hazard_{j}'] = {
                'expected_loss': expected_loss_j,
                'max_loss': float(np.max(P[j] * d * assets)),
                'affected_assets': int(np.sum(P[j] > 0)),
                'avg_damage_rate': float(np.mean(P[j] * d)),
            }

        return {
            'expected_loss': total_expected_loss,
            'risk_by_hazard': risk_by_hazard,
        }


# ===========================================================================
# 2. Hotelling Rule - Exhaustible Resource Extraction
# ===========================================================================

class HotellingRule:
    """Hotelling rule for optimal extraction of exhaustible resources.

    The Hotelling rule states that the net price (price minus marginal cost)
    of an exhaustible resource must grow at the rate of interest:

        (P_t - MC) = (P_0 - MC) * (1 + r)^t

    implying:

        P_t = MC + (P_0 - MC) * (1 + r)^t

    Extraction is optimal where the Hotelling price path exceeds marginal
    cost; beyond that point the resource is economically depleted.
    """

    def optimal_extraction(self, initial_price: float, marginal_cost: float,
                           interest_rate: float, reserves: float,
                           n_periods: int = 50) -> Dict[str, Any]:
        """Compute Hotelling-optimal extraction path.

        Price path:
            P(t) = MC + (P_0 - MC) * (1 + r)^t

        Extraction ends when P(t) < MC * (1 + extraction_cost_growth)
        or reserves are exhausted.

        Quantity path is derived so that cumulative extraction equals
        reserves over the extraction horizon, with extraction declining
        as the resource becomes scarcer (to keep price on the Hotelling
        path under iso-elastic demand).

        Parameters
        ----------
        initial_price : float
            Current market price of the resource.
        marginal_cost : float
            Constant marginal extraction cost.
        interest_rate : float
            Annual interest (discount) rate, e.g. 0.05 for 5 %.
        reserves : float
            Total proven reserves in physical units.
        n_periods : int
            Maximum number of periods to consider.

        Returns
        -------
        dict with ``price_path``, ``quantity_path``, ``extraction_period``,
        ``total_revenue``.
        """
        r = interest_rate
        MC = marginal_cost
        P0 = initial_price

        # --- Price path via Hotelling rule ---
        t = np.arange(n_periods)
        net_price_0 = max(P0 - MC, 1e-12)
        price_path = MC + net_price_0 * (1.0 + r) ** t

        # --- Determine extraction period ---
        # Extraction continues while price >= MC (i.e. net price > 0)
        # In practice we stop when price exceeds a demand-backstop price
        # approximated as when net price grows too large relative to MC.
        # Use a backstop: stop when P(t) > 10 * MC or price is unreasonable.
        backstop = 10.0 * MC if MC > 0 else np.inf
        extraction_mask = (price_path >= MC) & (price_path <= backstop)
        if not np.any(extraction_mask):
            extraction_period = 1
        else:
            extraction_period = int(np.max(np.where(extraction_mask)) + 1)
        extraction_period = min(extraction_period, n_periods)

        # --- Quantity path ---
        # Under Hotelling with iso-elastic demand q = A * P^(-e), the
        # optimal extraction declines over time as price rises.
        # We use a simple declining allocation: allocate reserves so that
        # extraction in period t is proportional to 1/(1+r)^t (declining).
        t_ext = np.arange(extraction_period)
        decline_weights = (1.0 + r) ** (-t_ext)  # higher weight early
        total_weight = np.sum(decline_weights)
        quantity_path = reserves * decline_weights / total_weight

        # --- Revenue ---
        total_revenue = float(np.sum(price_path[:extraction_period] * quantity_path))

        return {
            'price_path': price_path[:extraction_period].tolist(),
            'quantity_path': quantity_path.tolist(),
            'extraction_period': extraction_period,
            'total_revenue': total_revenue,
        }

    # ------------------------------------------------------------------
    def resource_value(self, reserves: float, price: float,
                       extraction_cost: float, interest_rate: float
                       ) -> Dict[str, Any]:
        """Net present value of an exhaustible resource.

        V = sum_t  q_t * (P_t - C_t) / (1 + r)^t

        Uses Hotelling price path and declining extraction schedule.

        Parameters
        ----------
        reserves : float
            Total reserves.
        price : float
            Current spot price.
        extraction_cost : float
            Per-unit extraction cost (assumed constant).
        interest_rate : float
            Discount rate.

        Returns
        -------
        dict with ``npv``, ``per_unit_value``, ``optimal_extraction_rate``.
        """
        r = interest_rate
        MC = extraction_cost
        P0 = price

        ext = self.optimal_extraction(P0, MC, r, reserves, n_periods=50)
        q = np.array(ext['quantity_path'])
        p = np.array(ext['price_path'])
        T = len(q)

        # NPV of each period's profit, discounted
        t_idx = np.arange(T)
        profit = q * (p - MC)
        discount_factors = (1.0 + r) ** t_idx
        npv = float(np.sum(profit / discount_factors))

        per_unit_value = npv / reserves if reserves > 0 else 0.0
        optimal_extraction_rate = float(q[0]) if len(q) > 0 else 0.0

        return {
            'npv': npv,
            'per_unit_value': float(per_unit_value),
            'optimal_extraction_rate': optimal_extraction_rate,
        }

    # ------------------------------------------------------------------
    def compare_renewable(self, fossil_npv: float, renewable_cost_curve: np.ndarray,
                          time_horizon: int = 30) -> Dict[str, Any]:
        """Crossover analysis: when does renewable become cheaper than fossil?

        Parameters
        ----------
        fossil_npv : float
            Net present value (or levelised cost) of the fossil option.
        renewable_cost_curve : array-like, shape (time_horizon,)
            Annualised cost of the renewable alternative for each year.
        time_horizon : int
            Number of years to consider.

        Returns
        -------
        dict with ``crossover_year``, ``cumulative_savings``.
        """
        rc = np.asarray(renewable_cost_curve, dtype=np.float64).ravel()
        n = min(len(rc), time_horizon)
        rc = rc[:n]

        # Levelised fossil cost: spread fossil NPV evenly over horizon
        fossil_annual = fossil_npv / time_horizon if time_horizon > 0 else fossil_npv
        fossil_curve = np.full(n, fossil_annual)

        # Crossover year: first year where renewable < fossil
        diff = fossil_curve - rc
        crossover_idx = np.where(diff > 0)[0]
        crossover_year = int(crossover_idx[0]) if len(crossover_idx) > 0 else None

        # Cumulative savings from that point onward
        if crossover_year is not None:
            cumulative_savings = float(np.sum(diff[crossover_year:]))
        else:
            cumulative_savings = 0.0

        return {
            'crossover_year': crossover_year,
            'cumulative_savings': cumulative_savings,
        }


# ===========================================================================
# 3. SIR / SEIR Epidemic Models
# ===========================================================================

class SIRModel:
    """Classical SIR and SEIR compartmental epidemic models with RK4 integration.

    The SIR model:
        dS/dt = -beta * S * I / N
        dI/dt =  beta * S * I / N  -  gamma * I
        dR/dt =  gamma * I

    Basic reproduction number:  R0 = beta / gamma
    """

    @staticmethod
    def _sir_ode(y, t, N, beta, gamma):
        """SIR system of ODEs (for scipy.integrate.odeint)."""
        S, I, R = y
        dSdt = -beta * S * I / N
        dIdt = beta * S * I / N - gamma * I
        dRdt = gamma * I
        return [dSdt, dIdt, dRdt]

    @staticmethod
    def _rk4_step(f, y, t, dt, *args):
        """Single RK4 step for the system dy/dt = f(y, t, *args)."""
        k1 = np.array(f(y, t, *args))
        k2 = np.array(f(y + 0.5 * dt * k1, t + 0.5 * dt, *args))
        k3 = np.array(f(y + 0.5 * dt * k2, t + 0.5 * dt, *args))
        k4 = np.array(f(y + dt * k3, t + dt, *args))
        return y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    def simulate(self, N: int = 1000, I0: int = 1, beta: float = 0.3,
                 gamma: float = 0.1, n_days: int = 200) -> Dict[str, Any]:
        """Simulate SIR epidemic using RK4 integration.

        Parameters
        ----------
        N : int
            Total population.
        I0 : int
            Initial number of infected individuals.
        beta : float
            Transmission rate (contacts per day x transmission probability).
        gamma : float
            Recovery rate (1 / mean infectious period in days).
        n_days : int
            Number of days to simulate.

        Returns
        -------
        dict with ``S``, ``I``, ``R``, ``R0``, ``peak_infected``, ``peak_day``.
        """
        I0 = int(min(I0, N - 1))
        S0 = N - I0
        R0_param = beta / gamma if gamma > 0 else np.inf

        # Time grid
        dt = 0.1  # sub-daily steps for accuracy
        t_full = np.arange(0, n_days, dt)
        n_steps = len(t_full)

        # Storage (store at daily resolution)
        S_out = np.zeros(n_days)
        I_out = np.zeros(n_days)
        R_out = np.zeros(n_days)

        y = np.array([float(S0), float(I0), 0.0])

        day_idx = 0
        for i in range(n_steps):
            current_day = int(t_full[i])
            if current_day < n_days and i > 0 and int(t_full[i - 1]) != current_day:
                S_out[day_idx] = y[0]
                I_out[day_idx] = y[1]
                R_out[day_idx] = y[2]
                day_idx += 1
            if i < n_steps - 1:
                y = self._rk4_step(self._sir_ode, y, t_full[i], dt, N, beta, gamma)
                y = np.clip(y, 0, N)

        # Fill remaining days
        for d in range(day_idx, n_days):
            S_out[d] = y[0]
            I_out[d] = y[1]
            R_out[d] = y[2]

        peak_infected = float(np.max(I_out))
        peak_day = int(np.argmax(I_out))

        return {
            'S': S_out.tolist(),
            'I': I_out.tolist(),
            'R': R_out.tolist(),
            'R0': float(R0_param),
            'peak_infected': peak_infected,
            'peak_day': peak_day,
        }

    # ------------------------------------------------------------------
    def economic_impact(self, sir_result: Dict[str, Any], gdp_daily: np.ndarray,
                        lockdown_threshold: float = 0.05,
                        productivity_loss_per_infected: float = 0.001
                        ) -> Dict[str, Any]:
        """Estimate GDP impact from an epidemic using SIR output.

        When the infection rate I/N exceeds *lockdown_threshold*, a
        lockdown is triggered and productivity drops to
        (1 - severity), where severity scales with I/N.

        Parameters
        ----------
        sir_result : dict
            Output of :meth:`simulate` (must contain ``I`` and ``R0``).
        gdp_daily : array-like
            Daily GDP (or output proxy) in the absence of the epidemic.
        lockdown_threshold : float
            Fraction of population infected that triggers lockdown.
        productivity_loss_per_infected : float
            Productivity loss per unit of infection rate (I/N).

        Returns
        -------
        dict with ``gdp_impact_path``, ``total_gdp_loss``, ``peak_impact``.
        """
        I = np.asarray(sir_result['I'], dtype=np.float64).ravel()
        n_days = len(I)
        N_est = max(np.max(I) / 0.1, 1)  # rough population estimate

        gdp = np.asarray(gdp_daily, dtype=np.float64).ravel()
        n = min(n_days, len(gdp))
        I = I[:n]
        gdp = gdp[:n]

        infection_rate = I / N_est

        gdp_impact_path = np.zeros(n)
        for t in range(n):
            if infection_rate[t] > lockdown_threshold:
                # Lockdown: productivity drops proportionally to severity
                severity = min(infection_rate[t] * productivity_loss_per_infected * 10, 0.5)
                gdp_impact_path[t] = gdp[t] * severity
            else:
                # Mild impact: linear in infection rate
                gdp_impact_path[t] = gdp[t] * infection_rate[t] * productivity_loss_per_infected

        total_gdp_loss = float(np.sum(gdp_impact_path))
        peak_impact = float(np.max(gdp_impact_path))

        return {
            'gdp_impact_path': gdp_impact_path.tolist(),
            'total_gdp_loss': total_gdp_loss,
            'peak_impact': peak_impact,
        }

    # ------------------------------------------------------------------
    def seir_model(self, N: int, I0: int, E0: int, beta: float,
                   sigma: float, gamma: float, n_days: int
                   ) -> Dict[str, Any]:
        """SEIR epidemic model with exposed compartment.

        dS/dt = -beta * S * I / N
        dE/dt =  beta * S * I / N  -  sigma * E
        dI/dt =  sigma * E          -  gamma * I
        dR/dt =  gamma * I

        Parameters
        ----------
        N : int       - Total population.
        I0 : int      - Initial infected.
        E0 : int      - Initial exposed (not yet infectious).
        beta : float  - Transmission rate.
        sigma : float - Incubation rate (1 / mean incubation period).
        gamma : float - Recovery rate.
        n_days : int  - Simulation horizon.

        Returns
        -------
        dict with ``S``, ``E``, ``I``, ``R``, ``R0``, ``peak_infected``, ``peak_day``.
        """
        I0 = int(min(I0, N - E0 - 1))
        E0 = int(min(E0, N - I0 - 1))
        S0 = N - I0 - E0
        R0_param = beta / gamma if gamma > 0 else np.inf

        def seir_ode(y, t, N, beta, sigma, gamma):
            S, E, I, R = y
            dSdt = -beta * S * I / N
            dEdt = beta * S * I / N - sigma * E
            dIdt = sigma * E - gamma * I
            dRdt = gamma * I
            return [dSdt, dEdt, dIdt, dRdt]

        dt = 0.1
        t_full = np.arange(0, n_days, dt)
        n_steps = len(t_full)

        S_out = np.zeros(n_days)
        E_out = np.zeros(n_days)
        I_out = np.zeros(n_days)
        R_out = np.zeros(n_days)

        y = np.array([float(S0), float(E0), float(I0), 0.0])
        day_idx = 0

        for i in range(n_steps):
            current_day = int(t_full[i])
            if current_day < n_days and i > 0 and int(t_full[i - 1]) != current_day:
                S_out[day_idx] = y[0]
                E_out[day_idx] = y[1]
                I_out[day_idx] = y[2]
                R_out[day_idx] = y[3]
                day_idx += 1
            if i < n_steps - 1:
                y = self._rk4_step(seir_ode, y, t_full[i], dt, N, beta, sigma, gamma)
                y = np.clip(y, 0, N)

        for d in range(day_idx, n_days):
            S_out[d] = y[0]
            E_out[d] = y[1]
            I_out[d] = y[2]
            R_out[d] = y[3]

        peak_infected = float(np.max(I_out))
        peak_day = int(np.argmax(I_out))

        return {
            'S': S_out.tolist(),
            'E': E_out.tolist(),
            'I': I_out.tolist(),
            'R': R_out.tolist(),
            'R0': float(R0_param),
            'peak_infected': peak_infected,
            'peak_day': peak_day,
        }

    # ------------------------------------------------------------------
    def fit_to_data(self, observed_infected: np.ndarray, N: int,
                    initial_guess: Optional[Tuple[float, float]] = None
                    ) -> Dict[str, Any]:
        """Fit SIR parameters (beta, gamma) to observed infection data.

        Uses scipy.optimize.minimize to minimise the sum of squared
        residuals between the SIR-predicted I(t) and the observed series.

        Parameters
        ----------
        observed_infected : array-like, shape (n_days,)
            Daily cumulative or prevalence counts.
        N : int
            Total population.
        initial_guess : tuple or None
            (beta, gamma) starting values.  Defaults to (0.3, 0.1).

        Returns
        -------
        dict with ``beta_hat``, ``gamma_hat``, ``R0_hat``, ``fitted_curve``.
        """
        obs = np.asarray(observed_infected, dtype=np.float64).ravel()
        n_days = len(obs)

        if initial_guess is None:
            initial_guess = (0.3, 0.1)

        # Work with log-space for better optimisation landscape
        log_obs = np.log(np.maximum(obs, 1.0))

        def objective(params):
            beta, gamma = params
            if beta <= 0 or gamma <= 0:
                return 1e12
            try:
                result = self.simulate(N=N, I0=max(1, int(obs[0])),
                                       beta=beta, gamma=gamma,
                                       n_days=n_days)
                pred = np.array(result['I'])
                log_pred = np.log(np.maximum(pred, 1.0))
                return float(np.sum((log_pred - log_obs) ** 2))
            except Exception:
                return 1e12

        bounds = [(1e-4, 2.0), (1e-4, 1.0)]
        res = minimize(objective, initial_guess, method='L-BFGS-B',
                       bounds=bounds, options={'maxiter': 500, 'ftol': 1e-12})

        beta_hat, gamma_hat = res.x
        R0_hat = beta_hat / gamma_hat

        fitted = self.simulate(N=N, I0=max(1, int(obs[0])),
                               beta=beta_hat, gamma=gamma_hat,
                               n_days=n_days)

        return {
            'beta_hat': float(beta_hat),
            'gamma_hat': float(gamma_hat),
            'R0_hat': float(R0_hat),
            'fitted_curve': fitted['I'],
            'optimization_success': res.success,
            'optimization_message': res.message,
        }


# ===========================================================================
# 4. Innovation S-Curves / Technology Diffusion
# ===========================================================================

class InnovationSCurve:
    """Models of technology diffusion and innovation adoption.

    Implements the Bass / Rogers diffusion model, the Gompertz growth
    curve, and Moore's law projection, with automated model selection
    via the Bayesian Information Criterion (BIC).
    """

    def rogers_diffusion(self, t: np.ndarray, p_innovator: float = 0.025,
                         p_imitator_coeff: float = 0.5,
                         M: float = 1.0) -> Dict[str, Any]:
        """Rogers / Bass diffusion model.

        The Bass diffusion ODE:

            dF/dt = (p + q * F/M) * (M - F)

        where *p* is the coefficient of innovation, *q* is the
        coefficient of imitation, and *M* is the market potential.

        Parameters
        ----------
        t : array-like
            Time points at which to evaluate the diffusion curve.
        p_innovator : float
            Coefficient of innovation (external influence).
        p_imitator_coeff : float
            Coefficient of imitation *q* (internal influence).
        M : float
            Market potential (saturation level).

        Returns
        -------
        dict with ``adoption_curve``, ``peak_adoption_rate``, ``half_life``.
        """
        t = np.asarray(t, dtype=np.float64).ravel()
        p = p_innovator
        q = p_imitator_coeff

        def bass_ode(F, ti):
            return (p + q * F / M) * (M - F)

        # Solve via RK4 from F(0)=0
        dt_sim = 0.05
        t_sim = np.arange(0, np.max(t) + dt_sim, dt_sim)
        F_sim = np.zeros_like(t_sim)
        F_sim[0] = 0.0

        for i in range(len(t_sim) - 1):
            y = F_sim[i]
            ti = t_sim[i]
            k1 = bass_ode(y, ti)
            k2 = bass_ode(y + 0.5 * dt_sim * k1, ti + 0.5 * dt_sim)
            k3 = bass_ode(y + 0.5 * dt_sim * k2, ti + 0.5 * dt_sim)
            k4 = bass_ode(y + dt_sim * k3, ti + dt_sim)
            F_sim[i + 1] = y + (dt_sim / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            F_sim[i + 1] = np.clip(F_sim[i + 1], 0, M)

        # Interpolate to requested time points
        adoption_curve = np.interp(t, t_sim, F_sim)

        # Adoption rate = dF/dt
        adoption_rate = np.gradient(F_sim, t_sim)
        peak_adoption_rate = float(np.max(adoption_rate))

        # Half-life: time when F reaches M/2
        half_idx = np.where(F_sim >= 0.5 * M)[0]
        half_life = float(t_sim[half_idx[0]]) if len(half_idx) > 0 else None

        return {
            'adoption_curve': adoption_curve.tolist(),
            'peak_adoption_rate': peak_adoption_rate,
            'half_life': half_life,
        }

    # ------------------------------------------------------------------
    def gompertz_model(self, t: np.ndarray, a: float, b: float,
                       c: float) -> Dict[str, Any]:
        """Gompertz growth model with parameter fitting.

        Gompertz function:
            F(t) = a * exp(-b * exp(-c * t))

        As t -> inf, F -> a (saturation).  The parameter *b* controls the
        displacement along the time axis and *c* controls the growth rate.

        Parameters
        ----------
        t : array-like
            Time points.
        a : float
            Asymptote (carrying capacity / saturation level).
        b : float
            Displacement parameter (b > 0).
        c : float
            Growth rate parameter (c > 0).

        Returns
        -------
        dict with ``fitted_params``, ``adoption_curve``, ``saturation_level``.
        """
        t = np.asarray(t, dtype=np.float64).ravel()

        def gompertz(t_eval, a_, b_, c_):
            return a_ * np.exp(-b_ * np.exp(-c_ * t_eval))

        adoption_curve = gompertz(t, a, b, c)

        return {
            'fitted_params': {'a': a, 'b': b, 'c': c},
            'adoption_curve': adoption_curve.tolist(),
            'saturation_level': float(a),
        }

    # ------------------------------------------------------------------
    def moore_law(self, years_ahead: int = 10,
                  current_transistors: float = 1e9,
                  annual_doubling_rate: float = 2.0) -> Dict[str, Any]:
        """Moore's law projection for transistor count.

        Moore's law:
            transistors(t) = current * 2^((t - t0) / doubling_period)

        where ``doubling_period = annual_doubling_rate`` years.

        Parameters
        ----------
        years_ahead : int
            Number of years to project.
        current_transistors : float
            Current transistor count.
        annual_doubling_rate : float
            Number of years for transistor count to double (historically ~2).

        Returns
        -------
        dict with ``projection`` and ``year_of_1_trillion``.
        """
        years = np.arange(0, years_ahead + 1, dtype=np.float64)
        doubling_period = annual_doubling_rate
        projection = current_transistors * 2.0 ** (years / doubling_period)

        # Find when projection crosses 1 trillion (1e12)
        target = 1e12
        if projection[-1] >= target and projection[0] < target:
            # Linear interpolation in log-space for precision
            log_proj = np.log2(projection)
            log_target = np.log2(target)
            idx = np.where(log_proj >= log_target)[0][0]
            if idx > 0:
                frac = ((log_target - log_proj[idx - 1])
                        / (log_proj[idx] - log_proj[idx - 1]))
                year_of_1_trillion = float(years[idx - 1] + frac)
            else:
                year_of_1_trillion = float(years[0])
        elif projection[0] >= target:
            year_of_1_trillion = 0.0
        else:
            year_of_1_trillion = None

        return {
            'projection': projection.tolist(),
            'year_of_1_trillion': year_of_1_trillion,
        }

    # ------------------------------------------------------------------
    def technology_s_curve(self, adoption_data: np.ndarray,
                           model: str = 'bass') -> Dict[str, Any]:
        """Fit adoption data to Bass, Gompertz, or Logistic and select best.

        Model selection via BIC:
            BIC = n * ln(RSS/n) + k * ln(n)

        Parameters
        ----------
        adoption_data : array-like, shape (T,)
            Observed adoption (cumulative) at each time step.
        model : str
            Preferred model (``'bass'``, ``'gompertz'``, ``'logistic'``).
            If ``'auto'``, the best model is selected via BIC.

        Returns
        -------
        dict with ``best_model``, ``forecast``, ``market_saturation``.
        """
        data = np.asarray(adoption_data, dtype=np.float64).ravel()
        n = len(data)
        t = np.arange(n, dtype=np.float64)
        M = float(np.max(data) * 1.1)  # estimated market potential

        if M <= 0:
            M = 1.0

        results = {}

        # --- Logistic model: F(t) = M / (1 + exp(-k*(t - t0))) ---
        def logistic(t_eval, k, t0):
            return M / (1.0 + np.exp(-k * (t_eval - t0)))

        try:
            p0_log = [0.3, n / 2.0]
            popt_log, _ = curve_fit(logistic, t, data, p0=p0_log,
                                    maxfev=5000, bounds=([1e-6, 0], [10, 2 * n]))
            pred_log = logistic(t, *popt_log)
            rss_log = float(np.sum((pred_log - data) ** 2))
            bic_log = n * np.log(rss_log / n + 1e-30) + 2 * np.log(n)
            results['logistic'] = {
                'params': popt_log.tolist(), 'rss': rss_log, 'bic': bic_log,
                'fitted': pred_log.tolist(), 'saturation': float(M),
            }
        except Exception:
            pass

        # --- Gompertz model: F(t) = a*exp(-b*exp(-c*t)) ---
        def gompertz(t_eval, a, b, c):
            return a * np.exp(-b * np.exp(-c * t_eval))

        try:
            p0_gom = [M, 5.0, 0.1]
            popt_gom, _ = curve_fit(gompertz, t, data, p0=p0_gom,
                                    maxfev=5000,
                                    bounds=([0, 0.1, 1e-6], [M * 2, 50, 5]))
            pred_gom = gompertz(t, *popt_gom)
            rss_gom = float(np.sum((pred_gom - data) ** 2))
            bic_gom = n * np.log(rss_gom / n + 1e-30) + 3 * np.log(n)
            results['gompertz'] = {
                'params': popt_gom.tolist(), 'rss': rss_gom, 'bic': bic_gom,
                'fitted': pred_gom.tolist(),
                'saturation': float(popt_gom[0]),
            }
        except Exception:
            pass

        # --- Bass model (solve ODE, fit p and q) ---
        def _bass_residuals(params):
            p, q = params
            if p < 0 or q < 0:
                return 1e12
            dt_sim = 0.1
            t_sim = np.arange(0, n, dt_sim)
            F = np.zeros_like(t_sim)
            for i in range(len(t_sim) - 1):
                dFdt = (p + q * F[i] / M) * (M - F[i])
                F[i + 1] = F[i] + dt_sim * dFdt
                F[i + 1] = np.clip(F[i + 1], 0, M)
            F_daily = np.interp(t, t_sim, F)
            return float(np.sum((F_daily - data) ** 2))

        try:
            from scipy.optimize import minimize as _min
            res_bass = _min(_bass_residuals, [0.01, 0.3], method='Nelder-Mead',
                            options={'maxiter': 3000, 'xatol': 1e-8, 'fatol': 1e-8})
            p_bass, q_bass = res_bass.x
            rss_bass = res_bass.fun
            bic_bass = n * np.log(rss_bass / n + 1e-30) + 2 * np.log(n)
            # Generate fitted curve
            dt_sim = 0.1
            t_sim = np.arange(0, n, dt_sim)
            F = np.zeros_like(t_sim)
            for i in range(len(t_sim) - 1):
                dFdt = (p_bass + q_bass * F[i] / M) * (M - F[i])
                F[i + 1] = F[i] + dt_sim * dFdt
                F[i + 1] = np.clip(F[i + 1], 0, M)
            pred_bass = np.interp(t, t_sim, F)
            results['bass'] = {
                'params': [float(p_bass), float(q_bass)], 'rss': rss_bass,
                'bic': bic_bass, 'fitted': pred_bass.tolist(),
                'saturation': float(M),
            }
        except Exception:
            pass

        # --- Model selection ---
        if model.lower() == 'auto' and len(results) > 0:
            best_name = min(results, key=lambda k: results[k]['bic'])
        elif model.lower() in results:
            best_name = model.lower()
        elif len(results) > 0:
            best_name = min(results, key=lambda k: results[k]['bic'])
        else:
            best_name = None

        best = results.get(best_name, {})

        # Forecast: extend best model 20% beyond data
        forecast_horizon = int(n * 0.2)
        t_forecast = np.arange(n, n + forecast_horizon, dtype=np.float64)
        if best_name == 'logistic' and 'params' in best:
            forecast = logistic(t_forecast, *best['params']).tolist()
        elif best_name == 'gompertz' and 'params' in best:
            forecast = gompertz(t_forecast, *best['params']).tolist()
        elif best_name == 'bass' and 'params' in best:
            p_b, q_b = best['params']
            dt_s = 0.1
            t_all = np.arange(0, n + forecast_horizon, dt_s)
            F_all = np.zeros_like(t_all)
            for i in range(len(t_all) - 1):
                dFdt = (p_b + q_b * F_all[i] / M) * (M - F_all[i])
                F_all[i + 1] = F_all[i] + dt_s * dFdt
                F_all[i + 1] = np.clip(F_all[i + 1], 0, M)
            forecast = np.interp(t_forecast, t_all, F_all).tolist()
        else:
            forecast = [float(data[-1])] * forecast_horizon

        return {
            'best_model': best_name,
            'all_results': {k: {'bic': v['bic'], 'rss': v['rss']} for k, v in results.items()},
            'forecast': forecast,
            'market_saturation': best.get('saturation', None),
            'fitted_curve': best.get('fitted', None),
        }


# ===========================================================================
# 5. Epidemic-Finance Bridge
# ===========================================================================

class EpidemicFinance:
    """Bridge between epidemiological dynamics and financial market impact.

    Combines epidemic indicators (infection rates, mobility data) with
    market data (returns, volatility) to produce composite stress indices,
    sector-level impact estimates, and scenario-based recovery forecasts.
    """

    def market_stress_index(self, returns: np.ndarray, volatility: np.ndarray,
                            infection_rate: np.ndarray,
                            mobility_index: np.ndarray) -> Dict[str, Any]:
        """Combined market-epidemic stress index.

        The composite index is a weighted sum of normalised components:

            SI = w1 * z(returns) + w2 * z(vol) + w3 * z(inf) + w4 * z(1 - mobility)

        where z(x) standardises *x* to zero-mean, unit-variance.

        Parameters
        ----------
        returns : array-like, shape (T,)
            Asset or market returns.
        volatility : array-like, shape (T,)
            Realised volatility (e.g. rolling std of returns).
        infection_rate : array-like, shape (T,)
            Daily new infections per capita.
        mobility_index : array-like, shape (T,)
            Mobility index (0-100 or similar; higher = more mobility).

        Returns
        -------
        dict with ``index_value``, ``components``, ``stress_level``.
        """
        ret = np.asarray(returns, dtype=np.float64).ravel()
        vol = np.asarray(volatility, dtype=np.float64).ravel()
        inf = np.asarray(infection_rate, dtype=np.float64).ravel()
        mob = np.asarray(mobility_index, dtype=np.float64).ravel()

        n = min(len(ret), len(vol), len(inf), len(mob))
        ret, vol, inf, mob = ret[:n], vol[:n], inf[:n], mob[:n]

        def zscore(x):
            mu = np.mean(x)
            sd = np.std(x, ddof=0)
            if sd < 1e-12:
                return np.zeros_like(x)
            return (x - mu) / sd

        # Normalise: negative returns = stress, low mobility = stress
        z_ret = zscore(-ret)     # flip sign: losses are stressful
        z_vol = zscore(vol)      # high vol = stress
        z_inf = zscore(inf)      # high infection = stress
        z_mob = zscore(1.0 - mob / 100.0) if np.max(mob) > 1 else zscore(1.0 - mob)

        # Weights
        w = np.array([0.30, 0.25, 0.25, 0.20])

        composite = w[0] * z_ret + w[1] * z_vol + w[2] * z_inf + w[3] * z_mob
        index_value = float(np.mean(composite))

        components = {
            'return_stress': float(np.mean(z_ret)),
            'volatility_stress': float(np.mean(z_vol)),
            'infection_stress': float(np.mean(z_inf)),
            'mobility_stress': float(np.mean(z_mob)),
        }

        # Classify stress level
        if index_value < -1.0:
            stress_level = 'low'
        elif index_value < 0.5:
            stress_level = 'moderate'
        elif index_value < 1.5:
            stress_level = 'elevated'
        else:
            stress_level = 'severe'

        return {
            'index_value': index_value,
            'components': components,
            'stress_level': stress_level,
        }

    # ------------------------------------------------------------------
    def sector_impact(self, sector_returns: Dict[str, np.ndarray],
                      lockdown_intensity: np.ndarray,
                      contact_intensity_by_sector: Dict[str, float]
                      ) -> Dict[str, Any]:
        """Estimate sector-specific epidemic impact.

        Impact model:
            impact_s = contact_s * lockdown_intensity

        where *contact_s* captures how much sector *s* relies on
        face-to-face interaction (e.g. hospitality >> tech).

        Parameters
        ----------
        sector_returns : dict
            Mapping sector name -> returns array.
        lockdown_intensity : array-like, shape (T,)
            Time series of lockdown intensity (0 = none, 1 = full).
        contact_intensity_by_sector : dict
            Mapping sector name -> contact intensity score in [0, 1].

        Returns
        -------
        dict with ``sector_impacts``, ``most_affected``, ``least_affected``.
        """
        lockdown = np.asarray(lockdown_intensity, dtype=np.float64).ravel()

        sector_impacts = {}
        avg_impacts = {}

        for sector, ret in sector_returns.items():
            ret_arr = np.asarray(ret, dtype=np.float64).ravel()
            n = min(len(ret_arr), len(lockdown))
            ret_arr = ret_arr[:n]
            lock = lockdown[:n]

            contact = contact_intensity_by_sector.get(sector, 0.5)

            # Estimated impact: contact intensity x lockdown x mean return magnitude
            impact_series = contact * lock * np.abs(ret_arr)
            avg_impact = float(np.mean(impact_series))

            # Correlation between returns and lockdown (more negative = more affected)
            if len(ret_arr) > 2 and np.std(lock) > 1e-12:
                corr = float(np.corrcoef(ret_arr, lock)[0, 1])
            else:
                corr = 0.0

            sector_impacts[sector] = {
                'average_impact': avg_impact,
                'return_lockdown_correlation': corr,
                'contact_intensity': contact,
                'total_impact': float(np.sum(impact_series)),
            }
            avg_impacts[sector] = avg_impact

        most_affected = max(avg_impacts, key=avg_impacts.get) if avg_impacts else None
        least_affected = min(avg_impacts, key=avg_impacts.get) if avg_impacts else None

        return {
            'sector_impacts': sector_impacts,
            'most_affected': most_affected,
            'least_affected': least_affected,
        }

    # ------------------------------------------------------------------
    def recovery_forecast(self, pre_shock_trend: np.ndarray, shock_date: int,
                          recovery_shape: str = 'V',
                          shock_depth: float = 0.3) -> Dict[str, Any]:
        """Scenario-based recovery forecasting (V, U, W, L shapes).

        Each recovery shape is modelled as a different functional form
        for the path from the shock trough back to the pre-shock trend:

        * **V**: Linear recovery.  Fast, symmetric bounce-back.
        * **U**: Flat bottom then linear recovery.  Prolonged trough.
        * **W**: V-shaped recovery followed by a second dip and recovery.
        * **L**: No recovery; output remains depressed permanently.

        Parameters
        ----------
        pre_shock_trend : array-like
            Pre-shock output/GDP trend (used for baseline level).
        shock_date : int
            Index at which the shock occurs.
        recovery_shape : str
            One of ``'V'``, ``'U'``, ``'W'``, ``'L'``, or ``'all'``.
        shock_depth : float
            Maximum fractional decline from trend (e.g. 0.3 = 30 % drop).

        Returns
        -------
        dict with ``scenarios`` and ``expected_recovery_time``.
        """
        trend = np.asarray(pre_shock_trend, dtype=np.float64).ravel()
        n_pre = min(shock_date, len(trend))
        baseline_level = float(np.mean(trend[max(0, n_pre - 20):n_pre])) if n_pre > 0 else float(trend[0])

        recovery_len = max(len(trend) - shock_date, 50)
        t_recovery = np.arange(recovery_len, dtype=np.float64)

        scenarios = {}

        def _build_path(shape, t, depth, baseline):
            n_r = len(t)
            trough = baseline * (1.0 - depth)
            path = np.zeros(n_r)

            if shape == 'V':
                # Sharp drop then linear recovery over first half
                half = n_r // 3
                for i in range(n_r):
                    if i < 5:
                        path[i] = baseline - depth * baseline * (i / 5.0)
                    elif i < half:
                        frac = (i - 5) / max(half - 5, 1)
                        path[i] = trough + (baseline - trough) * frac
                    else:
                        path[i] = baseline + 0.01 * baseline * (i - half) / max(n_r - half, 1)

            elif shape == 'U':
                # Prolonged trough before recovery
                flat_len = n_r // 3
                for i in range(n_r):
                    if i < 5:
                        path[i] = baseline - depth * baseline * (i / 5.0)
                    elif i < flat_len:
                        path[i] = trough
                    else:
                        frac = (i - flat_len) / max(n_r - flat_len, 1)
                        path[i] = trough + (baseline - trough) * (frac ** 0.8)

            elif shape == 'W':
                # V recovery, second dip, then recovery
                q1 = n_r // 4
                q2 = n_r // 2
                q3 = 3 * n_r // 4
                dip2_depth = depth * 0.5  # second dip is shallower
                for i in range(n_r):
                    if i < 5:
                        path[i] = baseline - depth * baseline * (i / 5.0)
                    elif i < q1:
                        frac = (i - 5) / max(q1 - 5, 1)
                        path[i] = trough + (baseline - trough) * frac
                    elif i < q2:
                        frac = (i - q1) / max(q2 - q1, 1)
                        path[i] = baseline - dip2_depth * baseline * frac
                    elif i < q3:
                        trough2 = baseline * (1.0 - dip2_depth)
                        frac = (i - q2) / max(q3 - q2, 1)
                        path[i] = trough2 + (baseline - trough2) * frac
                    else:
                        path[i] = baseline + 0.005 * baseline * (i - q3) / max(n_r - q3, 1)

            elif shape == 'L':
                # No recovery
                for i in range(n_r):
                    if i < 5:
                        path[i] = baseline - depth * baseline * (i / 5.0)
                    else:
                        path[i] = trough + 0.005 * baseline * (i / n_r)
            else:
                path[:] = baseline

            return path

        shapes = [recovery_shape.upper()] if recovery_shape.upper() != 'ALL' else ['V', 'U', 'W', 'L']

        for shape in shapes:
            path = _build_path(shape, t_recovery, shock_depth, baseline_level)
            # Find recovery time: first index where path >= 0.98 * baseline
            above = np.where(path >= 0.98 * baseline_level)[0]
            recovery_time = int(above[0]) if len(above) > 0 else recovery_len

            scenarios[shape] = {
                'recovery_path': path.tolist(),
                'recovery_time_periods': recovery_time,
                'trough_level': float(np.min(path)),
                'terminal_level': float(path[-1]),
            }

        # Expected recovery time: equally weighted average across scenarios
        recovery_times = [v['recovery_time_periods'] for v in scenarios.values()]
        expected_recovery_time = float(np.mean(recovery_times)) if recovery_times else None

        return {
            'scenarios': scenarios,
            'expected_recovery_time': expected_recovery_time,
            'baseline_level': baseline_level,
            'shock_depth': shock_depth,
        }
