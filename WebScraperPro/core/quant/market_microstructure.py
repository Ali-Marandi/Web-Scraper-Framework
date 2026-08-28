"""
Market Microstructure and Political-Economic Models.

Implements order book simulation, bid-ask spread estimation, market maker
game theory, geopolitical risk modeling, and regulatory capital frameworks.
Uses only numpy, pandas, and scipy.
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize, linalg


class OrderBookSimulator:
    """Simulate and analyze limit order books, auctions, and market impact."""

    def __init__(self, tick_size=0.01):
        """
        Initialize the order book simulator.

        Parameters
        ----------
        tick_size : float
            Minimum price increment for the instrument.
        """
        self.tick_size = tick_size

    def generate_lob(
        self,
        mid_price=100.0,
        n_levels=10,
        shape="normal",
        spread=0.05,
        imbalance=0.0,
    ):
        """
        Generate a synthetic limit order book around a mid price.

        Parameters
        ----------
        mid_price : float
            Center price for the order book.
        n_levels : int
            Number of price levels on each side.
        shape : str
            Quantity distribution shape: 'normal', 'uniform', 'exponential'.
        spread : float
            Initial half-spread separating best bid and best ask.
        imbalance : float
            Order imbalance parameter. Positive means more buy-side liquidity.
            Range roughly -1 to 1.

        Returns
        -------
        dict with keys: bids, asks, mid, spread, imbalance_ratio
            bids/asks are lists of (price, quantity) tuples sorted by price.
        """
        half_spread = spread
        best_bid = mid_price - half_spread
        best_ask = mid_price + half_spread

        # Snap to tick grid
        best_bid = np.floor(best_bid / self.tick_size) * self.tick_size
        best_ask = np.ceil(best_ask / self.tick_size) * self.tick_size

        # Generate base quantities for each level
        rng = np.random.default_rng()
        level_indices = np.arange(1, n_levels + 1, dtype=float)

        if shape == "normal":
            # Peak quantity near best level, declining outward
            base_qty = np.exp(-0.5 * ((level_indices - 1) / (n_levels / 3)) ** 2) * 1000
            noise = rng.normal(1.0, 0.1, n_levels)
            qty = np.maximum(base_qty * noise, 10)
        elif shape == "uniform":
            qty = rng.uniform(500, 1500, n_levels)
        elif shape == "exponential":
            # Declining quantity away from best level
            decay_rate = 0.2
            base_qty = 1000 * np.exp(-decay_rate * (level_indices - 1))
            noise = rng.normal(1.0, 0.1, n_levels)
            qty = np.maximum(base_qty * noise, 10)
        else:
            raise ValueError(f"Unknown shape: {shape}")

        # Apply imbalance: scale bid/ask quantities
        # imbalance > 0 => more buy orders (higher bid quantities)
        bid_scale = 1.0 + imbalance * 0.5
        ask_scale = 1.0 - imbalance * 0.5
        bid_scale = max(bid_scale, 0.1)
        ask_scale = max(ask_scale, 0.1)

        # Build bid levels (descending price)
        bid_prices = best_bid - (level_indices - 1) * self.tick_size
        bid_prices = np.floor(bid_prices / self.tick_size) * self.tick_size
        bid_qty = qty * bid_scale
        bids = list(zip(bid_prices.tolist(), bid_qty.tolist()))
        bids.sort(key=lambda x: -x[0])  # highest bid first

        # Build ask levels (ascending price)
        ask_prices = best_ask + (level_indices - 1) * self.tick_size
        ask_prices = np.ceil(ask_prices / self.tick_size) * self.tick_size
        ask_qty = qty * ask_scale
        asks = list(zip(ask_prices.tolist(), ask_qty.tolist()))
        asks.sort(key=lambda x: x[0])  # lowest ask first

        # Compute actual imbalance ratio
        total_bid_qty = sum(q for _, q in bids)
        total_ask_qty = sum(q for _, q in asks)
        imbalance_ratio = (total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty + 1e-12)

        return {
            "bids": bids,
            "asks": asks,
            "mid": (best_bid + best_ask) / 2,
            "spread": best_ask - best_bid,
            "imbalance_ratio": imbalance_ratio,
        }

    def simulate_auction(self, buy_orders, sell_orders, auction_type="continuous"):
        """
        Clear orders in an auction mechanism.

        Parameters
        ----------
        buy_orders : list of (price, quantity)
            Buy limit orders.
        sell_orders : list of (price, quantity)
            Sell limit orders.
        auction_type : str
            'continuous' for simple crossing, 'batch' for uniform-price auction.

        Returns
        -------
        dict with keys: clearing_price, executed_qty, remaining_bids, remaining_asks
        """
        buy_orders = sorted(buy_orders, key=lambda x: -x[0])  # highest bid first
        sell_orders = sorted(sell_orders, key=lambda x: x[0])  # lowest ask first

        if auction_type == "continuous":
            # Simple crossing: match highest bid with lowest ask
            cum_buy = 0.0
            cum_sell = 0.0
            clearing_price = None
            executed_qty = 0.0

            for bp, bq in buy_orders:
                if bp < (sell_orders[0][0] if sell_orders else np.inf):
                    break
                # This buy can potentially match
                for sp, sq in sell_orders:
                    if bp >= sp:
                        match_qty = min(bq, sq - cum_sell) if cum_sell < sq else 0
                        if match_qty > 0:
                            cum_sell += match_qty
                            executed_qty += match_qty
                            clearing_price = sp  # price-taker model
                            bq -= match_qty
                        if bq <= 0:
                            break
                if bq > 0:
                    cum_buy += bq

            # Build remaining orders
            # (simplified: remove fully filled orders)
            remaining_bids = [(p, q) for p, q in buy_orders if q > 0]
            remaining_asks = [(p, q) for p, q in sell_orders if q > 0]

            if clearing_price is None:
                clearing_price = 0.0

            return {
                "clearing_price": clearing_price,
                "executed_qty": executed_qty,
                "remaining_bids": remaining_bids,
                "remaining_asks": remaining_asks,
            }

        elif auction_type == "batch":
            # Uniform-price auction: maximize executable quantity
            # Build step function for buy and sell cumulative quantities
            # Collect all candidate prices
            all_prices = []
            for p, q in buy_orders:
                all_prices.append(p)
            for p, q in sell_orders:
                all_prices.append(p)

            if not all_prices:
                return {
                    "clearing_price": 0.0,
                    "executed_qty": 0.0,
                    "remaining_bids": buy_orders,
                    "remaining_asks": sell_orders,
                }

            candidate_prices = sorted(set(all_prices))
            best_qty = 0.0
            best_price = candidate_prices[0]

            for price in candidate_prices:
                # Cumulative buy volume willing to pay >= price
                buy_vol = sum(q for p, q in buy_orders if p >= price)
                # Cumulative sell volume willing to sell at <= price
                sell_vol = sum(q for p, q in sell_orders if p <= price)
                executable = min(buy_vol, sell_vol)
                if executable > best_qty:
                    best_qty = executable
                    best_price = price

            # Fill orders at uniform price
            remaining_bids = []
            remaining_asks = []
            buy_filled = 0.0

            for p, q in buy_orders:
                if p >= best_price:
                    fill = min(q, best_qty - buy_filled)
                    buy_filled += fill
                    leftover = q - fill
                    if leftover > 0:
                        remaining_bids.append((p, leftover))
                else:
                    remaining_bids.append((p, q))

            sell_filled = 0.0
            for p, q in sell_orders:
                if p <= best_price:
                    fill = min(q, best_qty - sell_filled)
                    sell_filled += fill
                    leftover = q - fill
                    if leftover > 0:
                        remaining_asks.append((p, leftover))
                else:
                    remaining_asks.append((p, q))

            return {
                "clearing_price": best_price,
                "executed_qty": best_qty,
                "remaining_bids": remaining_bids,
                "remaining_asks": remaining_asks,
            }

        else:
            raise ValueError(f"Unknown auction_type: {auction_type}")

    def market_impact(self, order_size, lob, side="buy"):
        """
        Estimate market impact by walking the book.

        Parameters
        ----------
        order_size : float
            Size of the order to execute.
        lob : dict
            Order book as returned by generate_lob.
        side : str
            'buy' or 'sell'.

        Returns
        -------
        dict with keys: avg_execution_price, impact_bps, slippage, levels_consumed
        """
        if side == "buy":
            levels = lob["asks"]  # (price, qty) sorted ascending
            levels.sort(key=lambda x: x[0])
        else:
            levels = lob["bids"]  # (price, qty) sorted descending
            levels.sort(key=lambda x: -x[0])

        if not levels:
            return {
                "avg_execution_price": 0.0,
                "impact_bps": 0.0,
                "slippage": 0.0,
                "levels_consumed": 0,
            }

        remaining = order_size
        total_cost = 0.0
        total_filled = 0.0
        levels_consumed = 0

        for price, qty in levels:
            if remaining <= 0:
                break
            fill_qty = min(remaining, qty)
            total_cost += fill_qty * price
            total_filled += fill_qty
            remaining -= fill_qty
            levels_consumed += 1

        if total_filled < 1e-12:
            avg_exec_price = lob["mid"]
        else:
            avg_exec_price = total_cost / total_filled

        mid = lob["mid"]
        if side == "buy":
            slippage = avg_exec_price - mid
        else:
            slippage = mid - avg_exec_price

        impact_bps = (slippage / mid) * 10000

        # Permanent vs temporary impact estimate (Almgren-Chriss style)
        # Temporary impact grows with levels consumed
        # Permanent impact proportional to sqrt of total order fraction
        total_lob_qty = sum(q for _, q in lob["asks"]) + sum(q for _, q in lob["bids"])
        order_fraction = order_size / (total_lob_qty + 1e-12)

        return {
            "avg_execution_price": round(avg_exec_price, 6),
            "impact_bps": round(impact_bps, 4),
            "slippage": round(slippage, 6),
            "levels_consumed": levels_consumed,
        }

    def kyle_lambda(self, order_flow, price_changes):
        """
        Estimate Kyle's lambda (price impact coefficient) via OLS regression.

        Model: ΔP_t = λ * OrderFlow_t + ε_t

        Parameters
        ----------
        order_flow : array-like
            Net order flow (signed quantity: buys positive, sells negative).
        price_changes : array-like
            Mid-price changes corresponding to each order flow observation.

        Returns
        -------
        dict with keys: lambda, R_squared, permanent_impact, temporary_impact
        """
        x = np.asarray(order_flow, dtype=float)
        y = np.asarray(price_changes, dtype=float)

        n = len(x)
        if n < 3:
            return {
                "lambda": 0.0,
                "R_squared": 0.0,
                "permanent_impact": 0.0,
                "temporary_impact": 0.0,
            }

        # OLS regression: y = lambda * x + epsilon
        # Using numpy for robustness
        x_mean = np.mean(x)
        y_mean = np.mean(y)

        ss_xy = np.sum((x - x_mean) * (y - y_mean))
        ss_xx = np.sum((x - x_mean) ** 2)
        ss_yy = np.sum((y - y_mean) ** 2)

        if abs(ss_xx) < 1e-15:
            return {
                "lambda": 0.0,
                "R_squared": 0.0,
                "permanent_impact": 0.0,
                "temporary_impact": 0.0,
            }

        lam = ss_xy / ss_xx
        y_pred = lam * x
        residuals = y - y_pred
        ss_res = np.sum(residuals ** 2)

        r_squared = 1.0 - ss_res / (ss_yy + 1e-15)
        r_squared = max(0.0, min(1.0, r_squared))

        # Standard error of lambda
        n_params = 1
        if n > n_params + 1:
            mse = ss_res / (n - n_params - 1)
            se_lambda = np.sqrt(mse / ss_xx)
        else:
            se_lambda = 0.0

        # Permanent impact: long-run price change per unit of order flow
        # Approximate via cumulative price change vs cumulative order flow
        cum_flow = np.cumsum(x)
        cum_price = np.cumsum(y)
        if np.std(cum_flow) > 1e-12:
            permanent_impact = np.cov(cum_flow, cum_price)[0, 1] / np.var(cum_flow)
        else:
            permanent_impact = lam

        # Temporary impact: difference between total and permanent
        temporary_impact = lam - permanent_impact

        return {
            "lambda": round(lam, 8),
            "R_squared": round(r_squared, 6),
            "permanent_impact": round(permanent_impact, 8),
            "temporary_impact": round(temporary_impact, 8),
        }


class BidAskModels:
    """Bid-ask spread estimation and decomposition models."""

    def roll_spread(self, prices):
        """
        Roll's implied spread estimator.

        The effective spread is estimated as:
            S = -cov(ΔP_t, ΔP_{t-1}) / var(ΔP)

        Which simplifies to: S = 2 * sqrt(-cov(ΔP_t, ΔP_{t-1}))
        when using the standard Roll (1984) formulation.

        Parameters
        ----------
        prices : array-like
            Sequence of transaction prices.

        Returns
        -------
        dict with keys: spread_estimate, effective_spread
        """
        p = np.asarray(prices, dtype=float)
        if len(p) < 3:
            return {"spread_estimate": 0.0, "effective_spread": 0.0}

        # Price changes
        dp = np.diff(p)
        if len(dp) < 2:
            return {"spread_estimate": 0.0, "effective_spread": 0.0}

        # Roll's estimator using serial covariance
        dp_t = dp[1:]      # ΔP_t
        dp_t1 = dp[:-1]    # ΔP_{t-1}

        cov_serial = np.cov(dp_t, dp_t1, ddof=1)[0, 1]
        var_dp = np.var(dp, ddof=1)

        # Spread estimate: -cov / var
        if abs(var_dp) < 1e-15:
            spread_estimate = 0.0
        else:
            spread_estimate = -cov_serial / var_dp

        # Standard Roll effective spread (constrained to be non-negative)
        if cov_serial < 0:
            effective_spread = 2.0 * np.sqrt(-cov_serial)
        else:
            # If positive autocovariance, no reliable estimate
            effective_spread = 0.0

        return {
            "spread_estimate": round(spread_estimate, 8),
            "effective_spread": round(effective_spread, 8),
        }

    def beck_stoll(self, transaction_prices, trade_directions):
        """
        Beech-Stoll (Stoll 1989) spread decomposition into components.

        Decomposes the spread into:
            - Adverse selection component (information-driven)
            - Inventory holding component (risk management)
            - Order processing component (operational cost)

        Uses regression of mid-price changes and trade returns on trade
        direction indicators.

        Parameters
        ----------
        transaction_prices : array-like
            Sequence of transaction prices.
        trade_directions : array-like
            Trade direction indicators: +1 for buy-initiated, -1 for sell-initiated.

        Returns
        -------
        dict with keys: adverse_selection, inventory_holding, order_processing, total_spread
        """
        prices = np.asarray(transaction_prices, dtype=float)
        directions = np.asarray(trade_directions, dtype=float)

        n = len(prices)
        if n < 10:
            return {
                "adverse_selection": 0.0,
                "inventory_holding": 0.0,
                "order_processing": 0.0,
                "total_spread": 0.0,
            }

        # Mid-price proxy: use weighted mid or simple mid of consecutive trades
        # Compute trade returns
        trade_returns = np.diff(prices) / prices[:-1]

        # Compute mid-price changes (proxy via consecutive trade average)
        mid_proxy = np.zeros(n - 1)
        for i in range(n - 1):
            mid_proxy[i] = (prices[i] + prices[i + 1]) / 2
        mid_changes = np.diff(mid_proxy) / mid_proxy[:-1]

        # Align directions with returns
        d = directions[1 : len(trade_returns) + 1]
        if len(d) != len(trade_returns):
            min_len = min(len(d), len(trade_returns))
            d = d[:min_len]
            trade_returns = trade_returns[:min_len]
            mid_changes = mid_changes[: min(len(mid_changes), min_len)]

        if len(d) < 10:
            return {
                "adverse_selection": 0.0,
                "inventory_holding": 0.0,
                "order_processing": 0.0,
                "total_spread": 0.0,
            }

        # Regression 1: Trade return on direction (captures total spread)
        # r_t = c + s/2 * D_t + error
        d_mean = np.mean(d)
        r_mean = np.mean(trade_returns)
        ss_dd = np.sum((d - d_mean) ** 2)
        ss_dr = np.sum((d - d_mean) * (trade_returns - r_mean))

        if abs(ss_dd) < 1e-15:
            return {
                "adverse_selection": 0.0,
                "inventory_holding": 0.0,
                "order_processing": 0.0,
                "total_spread": 0.0,
            }

        half_spread = ss_dr / ss_dd  # s/2
        total_spread = abs(2 * half_spread)

        # Regression 2: Mid-price change on direction (adverse selection)
        mc_mean = np.mean(mid_changes)
        ss_dmc = np.sum((d - d_mean) * (mid_changes - mc_mean))
        adverse_selection_coeff = ss_dmc / ss_dd
        adverse_selection = abs(2 * adverse_selection_coeff)

        # Regression 3: Inventory component via autocorrelation of spread returns
        # Inventory holding cost captured by serial dependence
        spread_return = trade_returns - half_spread * d
        if len(spread_return) > 1:
            inv_cov = np.cov(spread_return[:-1], spread_return[1:], ddof=1)[0, 1]
            inventory_holding = abs(inv_cov) * 2
        else:
            inventory_holding = 0.0

        # Order processing: residual
        order_processing = max(total_spread - adverse_selection - inventory_holding, 0.0)

        return {
            "adverse_selection": round(adverse_selection, 8),
            "inventory_holding": round(inventory_holding, 8),
            "order_processing": round(order_processing, 8),
            "total_spread": round(total_spread, 8),
        }

    def hasbrouck_informative_share(self, order_flow, mid_price_changes, trade_directions):
        """
        Hasbrouck's information share from a VAR on mid-price and order flow.

        Estimates the fraction of price variance attributable to
        informational (private information) shocks vs order flow
        (non-informational) shocks via variance decomposition of a
        bivariate VAR.

        Parameters
        ----------
        order_flow : array-like
            Signed order flow (buys positive, sells negative).
        mid_price_changes : array-like
            Changes in the mid-price.
        trade_directions : array-like
            Trade direction indicators: +1 for buy, -1 for sell.

        Returns
        -------
        dict with keys: information_share, variance_decomposition
        """
        of = np.asarray(order_flow, dtype=float)
        mp = np.asarray(mid_price_changes, dtype=float)
        td = np.asarray(trade_directions, dtype=float)

        min_len = min(len(of), len(mp), len(td))
        of = of[:min_len]
        mp = mp[:min_len]
        td = td[:min_len]

        n = len(mp)
        if n < 20:
            return {
                "information_share": 0.0,
                "variance_decomposition": {
                    "information_shock": 0.0,
                    "order_flow_shock": 0.0,
                },
            }

        # Construct VAR system: [Δmid_t, OF_t]
        # VAR(1): Y_t = A * Y_{t-1} + e_t
        # Y = [Δmid, order_flow]
        Y = np.column_stack([mp, of])
        T = len(Y)

        # Lag and difference
        Y_lag = Y[:-1]
        Y_curr = Y[1:]
        n_obs = len(Y_curr)

        # OLS for each equation
        # A: 2x2 matrix, estimate via multivariate OLS
        # Y_curr = Y_lag @ A.T + E
        # A = (Y_lag.T @ Y_lag)^{-1} @ Y_lag.T @ Y_curr
        try:
            XtX = Y_lag.T @ Y_lag
            XtY = Y_lag.T @ Y_curr
            A = np.linalg.solve(XtX, XtY)  # 2x2

            residuals = Y_curr - Y_lag @ A
            Sigma = (residuals.T @ residuals) / (n_obs - 2)

            # Cholesky decomposition for identification
            # Order: mid-price first, then order flow
            # This gives upper bound on information share
            L = np.linalg.cholesky(Sigma + np.eye(2) * 1e-10)
            L_inv = np.linalg.inv(L)

            # Compute VMA representation and accumulate impulse responses
            # For horizon H, compute sum of impulse response coefficients
            H = 20
            # Ψ_0 = L_inv (impact response in structural form)
            Psi = np.zeros((H, 2, 2))
            Psi[0] = L_inv

            for h in range(1, H):
                Psi[h] = Psi[h - 1] @ A.T

            # Variance decomposition for price (first variable)
            # Contribution of each shock to price forecast error variance
            total_var = np.zeros(2)
            for h in range(H):
                for s in range(2):
                    total_var[s] += (Psi[h][0, s]) ** 2

            grand_total = np.sum(total_var)
            if grand_total > 1e-15:
                info_share_price = total_var[0] / grand_total
                of_share_price = total_var[1] / grand_total
            else:
                info_share_price = 0.5
                of_share_price = 0.5

        except (np.linalg.LinAlgError, ValueError):
            # Fallback: use simple correlation-based estimate
            corr = np.corrcoef(mp, of)[0, 1] if np.std(mp) > 1e-12 and np.std(of) > 1e-12 else 0.0
            info_share_price = max(0.0, min(1.0, (1 + corr) / 2))
            of_share_price = 1.0 - info_share_price

        return {
            "information_share": round(info_share_price, 6),
            "variance_decomposition": {
                "information_shock": round(info_share_price, 6),
                "order_flow_shock": round(of_share_price, 6),
            },
        }


class MarketMakerNash:
    """Game-theoretic models of market maker competition and quoting."""

    def nash_spread(self, n_market_makers=3, volatility=0.02, competition_intensity=0.5):
        """
        Compute Nash equilibrium bid-ask spread among competing market makers.

        Each market maker chooses spread s_i to maximize profit given
        competitors' spreads. Profit = (s_i / 2) * share_i - adverse_selection_cost.
        Market share is allocated proportionally (tighter spread = more share).

        Solved via best-response iteration until convergence.

        Parameters
        ----------
        n_market_makers : int
            Number of competing market makers.
        volatility : float
            Underlying asset volatility (annualized).
        competition_intensity : float
            Intensity of competition on market share (0=s monopolist, 1=perfect).

        Returns
        -------
        dict with keys: equilibrium_spread, profits_per_mm, convergence
        """
        n_mm = max(n_market_makers, 1)

        # Adverse selection cost per trade (proportional to volatility)
        adverse_cost = 0.5 * volatility * np.sqrt(1 / 252)  # daily adverse selection

        # Fixed order processing cost
        order_cost = 0.0001

        # Initialize spreads (symmetric assumption)
        spreads = np.full(n_mm, 2 * (adverse_cost + order_cost) * 1.5)

        # Best-response iteration
        max_iter = 500
        tol = 1e-10
        converged = False

        for iteration in range(max_iter):
            old_spreads = spreads.copy()
            total_inv_spread = np.sum(1.0 / (spreads + 1e-12))

            new_spreads = np.zeros(n_mm)
            for i in range(n_mm):
                # Competitor spread (equal weight)
                if n_mm > 1:
                    competitor_spread = np.mean(np.delete(spreads, i))
                else:
                    competitor_spread = spreads[i]

                # Market share function: share_i = (1/s_i)^alpha / sum_j (1/s_j)^alpha
                # alpha = competition_intensity controls elasticity
                alpha = 1.0 + 3.0 * competition_intensity

                # Best response: maximize (s/2) * share - adverse_cost - order_cost
                # With share proportional to s^(-alpha), optimal s = alpha/(alpha-1) * 2*(adv+op)
                if alpha > 1:
                    optimal_s = (alpha / (alpha - 1)) * 2 * (adverse_cost + order_cost)
                else:
                    optimal_s = 2 * (adverse_cost + order_cost) * 5

                # Blend with competitor spread (strategic interaction)
                blended = (1 - competition_intensity) * optimal_s + competition_intensity * competitor_spread
                new_spreads[i] = max(blended, 2 * (adverse_cost + order_cost))

            spreads = new_spreads

            # Check convergence
            if np.max(np.abs(spreads - old_spreads)) < tol:
                converged = True
                break

        # Compute equilibrium profits
        alpha = 1.0 + 3.0 * competition_intensity
        weights = (1.0 / (spreads + 1e-12)) ** alpha
        total_weight = np.sum(weights)
        shares = weights / (total_weight + 1e-12)

        # Assume daily volume
        daily_volume = 1_000_000  # shares
        profits = (spreads / 2) * shares * daily_volume - (adverse_cost + order_cost) * shares * daily_volume

        return {
            "equilibrium_spread": round(float(np.mean(spreads)), 8),
            "profits_per_mm": [round(float(p), 4) for p in profits],
            "convergence": converged,
        }

    def payment_for_order_flow(
        self,
        retail_fraction,
        informed_fraction,
        adverse_selection_cost,
        tick_size=0.01,
    ):
        """
        Model payment for order flow (PFOF) economics.

        The exchange/internalizer pays the broker for retail order flow.
        Retail traders are assumed uninformed, so the internalizer earns
        the spread. The PFOF payment splits this surplus.

        Parameters
        ----------
        retail_fraction : float
            Fraction of total volume that is retail (0 to 1).
        informed_fraction : float
            Fraction of non-retail flow that is informed (0 to 1).
        adverse_selection_cost : float
            Cost per share of adverse selection from informed traders.
        tick_size : float
            Minimum tick size.

        Returns
        -------
        dict with keys: pofp_per_share, broker_profit, exchange_profit
        """
        # Effective half-spread earned on retail flow
        # Retail is uninformed, so full spread can be captured
        half_spread = tick_size  # minimum profitable spread
        retail_spread = 2 * half_spread

        # Cost of handling informed flow (only affects non-retail)
        informed_cost = informed_fraction * adverse_selection_cost

        # Net profit to internalizer per retail share
        internalizer_profit_per_share = retail_spread / 2 - 0.0  # no adverse selection on retail

        # PFOF payment: split the surplus between broker and exchange
        # Broker has bargaining power proportional to retail fraction
        broker_bargaining = retail_fraction / (retail_fraction + 0.5)
        pofp_per_share = internalizer_profit_per_share * broker_bargaining

        # Assume total daily volume
        daily_volume = 1_000_000
        retail_volume = retail_fraction * daily_volume

        # Broker profit from PFOF
        broker_profit = pofp_per_share * retail_volume

        # Exchange/internalizer profit (keeps the remainder)
        exchange_profit = (internalizer_profit_per_share - pofp_per_share) * retail_volume
        # Subtract cost of informed flow on wholesale side
        wholesale_volume = (1 - retail_fraction) * daily_volume
        exchange_profit -= informed_cost * wholesale_volume

        return {
            "pofp_per_share": round(float(pofp_per_share), 6),
            "broker_profit": round(float(broker_profit), 4),
            "exchange_profit": round(float(exchange_profit), 4),
        }

    def optimal_inventory(
        self,
        arrival_rate_bid,
        arrival_rate_ask,
        holding_cost,
        risk_aversion,
        volatility,
    ):
        """
        Optimal inventory management for a market maker (Avellaneda-Stoikov style).

        The market maker sets bid and ask quotes to attract order flow
        toward a target inventory (typically zero). The optimal quotes
        depend on current inventory, risk aversion, volatility, and order
        arrival rates.

        Parameters
        ----------
        arrival_rate_bid : float
            Rate at which buy orders arrive (Poisson intensity).
        arrival_rate_ask : float
            Rate at which sell orders arrive (Poisson intensity).
        holding_cost : float
            Cost per unit of inventory per period.
        risk_aversion : float
            Coefficient of risk aversion (gamma).
        volatility : float
            Underlying asset volatility (per period).

        Returns
        -------
        dict with keys: optimal_quotes, inventory_target, expected_profit
        """
        # Avellaneda-Stoikov (2008) optimal market making quotes
        # Optimal ask: S_a = S + 1/gamma * ln(1 + gamma/k_a) + (q - q_bar) * adjustment
        # Optimal bid: S_b = S - 1/gamma * ln(1 + gamma/k_b) + (q - q_bar) * adjustment
        # where k_a, k_b are intensity parameters

        gamma = risk_aversion
        q = 0  # assume starting at zero inventory for baseline quotes
        q_target = 0  # target inventory
        T = 1.0  # time horizon (normalized)

        kappa_a = arrival_rate_ask  # arrival rate of sell orders (fill our bid)
        kappa_b = arrival_rate_bid  # arrival rate of buy orders (fill our ask)

        # Base spread component (risk premium)
        if gamma > 0 and kappa_a > 0 and kappa_b > 0:
            delta_a = (1.0 / gamma) * np.log(1.0 + gamma / kappa_a)
            delta_b = (1.0 / gamma) * np.log(1.0 + gamma / kappa_b)
        else:
            delta_a = 0.01
            delta_b = 0.01

        # Inventory adjustment: skew quotes away from inventory buildup
        # Higher inventory => lower bid, lower ask to attract sells
        sigma2 = volatility ** 2
        inventory_skew = (q - q_target) * gamma * sigma2 * T

        # Holding cost adjustment
        holding_adjustment = holding_cost / (kappa_a + kappa_b + 1e-12)

        # Optimal half-spreads
        optimal_ask = delta_a + inventory_skew + holding_adjustment
        optimal_bid = delta_b - inventory_skew + holding_adjustment

        # Ensure non-negative spreads
        optimal_ask = max(optimal_ask, 0.001)
        optimal_bid = max(optimal_bid, 0.001)

        # Expected profit per unit time
        # E[profit] = (delta_a + delta_b) * (kappa_a + kappa_b) / 2 - inventory_cost
        fill_rate = kappa_a + kappa_b
        spread_revenue = (optimal_ask + optimal_bid) * fill_rate / 2
        inventory_cost = holding_cost * abs(q - q_target)
        risk_cost = 0.5 * gamma * sigma2 * (q - q_target) ** 2
        expected_profit = spread_revenue - inventory_cost - risk_cost

        return {
            "optimal_quotes": {
                "ask_half_spread": round(float(optimal_ask), 8),
                "bid_half_spread": round(float(optimal_bid), 8),
                "full_spread": round(float(optimal_ask + optimal_bid), 8),
            },
            "inventory_target": int(q_target),
            "expected_profit": round(float(expected_profit), 8),
        }


class GeopoliticalRiskModel:
    """Geopolitical and political-economic risk quantification models."""

    def icrg_composite(self, economic_risk, financial_risk, political_risk):
        """
        Compute ICRG-style composite risk score.

        The International Country Risk Guide methodology combines economic,
        financial, and political risk into a composite score. Lower scores
        indicate higher risk.

        Weights (ICRG standard):
            Economic: 25%
            Financial: 25%
            Political: 50%

        Parameters
        ----------
        economic_risk : float or array-like
            Economic risk indicator (0-100, higher = safer).
        financial_risk : float or array-like
            Financial risk indicator (0-100, higher = safer).
        political_risk : float or array-like
            Political risk indicator (0-100, higher = safer).

        Returns
        -------
        dict with keys: composite_score, rating, risk_level
        """
        e = np.asarray(economic_risk, dtype=float)
        f = np.asarray(financial_risk, dtype=float)
        p = np.asarray(political_risk, dtype=float)

        # ICRG standard weights
        w_econ = 0.25
        w_fin = 0.25
        w_pol = 0.50

        composite = w_econ * e + w_fin * f + w_pol * p

        # Rating assignment
        def _get_rating(score):
            if score >= 80:
                return "AAA", "Very Low Risk"
            elif score >= 70:
                return "AA", "Low Risk"
            elif score >= 60:
                return "A", "Moderate-Low Risk"
            elif score >= 50:
                return "BBB", "Moderate Risk"
            elif score >= 40:
                return "BB", "Moderate-High Risk"
            elif score >= 30:
                return "B", "High Risk"
            elif score >= 20:
                return "CCC", "Very High Risk"
            else:
                return "D", "Default / Extreme Risk"

        if composite.ndim == 0:
            rating, risk_level = _get_rating(float(composite))
        else:
            ratings = []
            risk_levels = []
            for s in composite:
                r, rl = _get_rating(float(s))
                ratings.append(r)
                risk_levels.append(rl)
            rating = ratings
            risk_level = risk_levels

        return {
            "composite_score": round(float(composite) if composite.ndim == 0 else composite.tolist(), 4),
            "rating": rating,
            "risk_level": risk_level,
        }

    def sanction_impact(
        self, trade_exposure, sanction_severity, gdp_elasticity, duration_years
    ):
        """
        Estimate GDP impact of economic sanctions.

        Model: ΔGDP = exposure × severity × elasticity × √duration

        The square root of duration captures diminishing marginal impact
        as economies adapt over time.

        Parameters
        ----------
        trade_exposure : float
            Bilateral trade as fraction of GDP (0 to 1).
        sanction_severity : float
            Severity index (0=none, 1=comprehensive embargo).
        gdp_elasticity : float
            Elasticity of GDP to trade disruption (typically 0.1-0.5).
        duration_years : float
            Expected duration of sanctions in years.

        Returns
        -------
        dict with keys: gdp_impact, sector_impacts, recovery_timeline
        """
        # Core impact formula
        gdp_impact = (
            trade_exposure * sanction_severity * gdp_elasticity * np.sqrt(duration_years)
        )

        # Sector-level impact estimates
        # Different sectors have different sensitivities to sanctions
        sector_sensitivities = {
            "energy": 1.5,
            "manufacturing": 1.2,
            "agriculture": 1.0,
            "technology": 1.3,
            "financial_services": 1.4,
            "consumer_goods": 0.8,
            "pharmaceuticals": 0.6,
            "defense": 1.8,
        }

        sector_impacts = {}
        for sector, sensitivity in sector_sensitivities.items():
            sector_impacts[sector] = round(
                gdp_impact * sensitivity * trade_exposure, 6
            )

        # Recovery timeline based on severity and duration
        # Higher severity and longer duration => longer recovery
        if sanction_severity < 0.3:
            recovery_years = duration_years * 0.5
        elif sanction_severity < 0.6:
            recovery_years = duration_years * 1.0
        else:
            recovery_years = duration_years * 1.5

        # Recovery follows logistic curve: 50% recovery at recovery_years
        recovery_timeline = {
            "years_to_50pct_recovery": round(recovery_years, 2),
            "years_to_90pct_recovery": round(recovery_years * np.log(9), 2),
            "permanent_gdp_loss": round(
                gdp_impact * 0.1 * sanction_severity, 6
            ),
        }

        return {
            "gdp_impact": round(gdp_impact, 6),
            "sector_impacts": sector_impacts,
            "recovery_timeline": recovery_timeline,
        }

    def trade_war_game(
        self,
        country_a_tariff_power,
        country_b_retaliation_power,
        trade_volume,
        n_rounds=10,
    ):
        """
        Iterative tariff escalation game between two countries.

        Each round, each country chooses a tariff level. Payoff incorporates:
            - Domestic industry protection (GDP gain)
            - Trade volume reduction (GDP loss)
            - Consumer welfare loss (deadweight cost)

        Nash equilibrium found via best-response iteration.

        Parameters
        ----------
        country_a_tariff_power : float
            Country A's ability to impose tariffs (0 to 1).
        country_b_retaliation_power : float
            Country B's ability to retaliate (0 to 1).
        trade_volume : float
            Bilateral trade volume in value terms.
        n_rounds : int
            Number of game iterations.

        Returns
        -------
        dict with keys: equilibrium_tariffs, welfare_impact, nash_converged
        """
        # Model parameters
        # Tariff revenue function: T * t * (1 - t/t_max)  -- Laffer curve
        # Consumer cost: 0.5 * t^2 * elasticity * trade_volume
        # Trade loss: trade_volume * (1 - (1-t_a)(1-t_b))

        t_max = 1.0  # maximum tariff rate (100%)
        elasticity = 2.0  # trade elasticity

        # Initialize tariff levels
        t_a = 0.05  # Country A tariff
        t_b = 0.05  # Country B tariff

        # Convergence tracking
        tariff_history_a = [t_a]
        tariff_history_b = [t_b]
        converged = False

        for round_idx in range(n_rounds):
            old_a, old_b = t_a, t_b

            # Country A's best response to t_b
            # Maximize: t_a * (1 - t_a) * trade_volume * country_a_tariff_power
            #        - 0.5 * t_a^2 * elasticity * trade_volume
            #        - trade_volume * (1 - (1-t_a)(1-t_b)) * 0.5
            # FOC: (1 - 2*t_a) * tp - t_a * e - 0.5 * (1-t_b) = 0
            tp_a = country_a_tariff_power
            denom_a = 2 * tp_a + elasticity
            if abs(denom_a) > 1e-12:
                best_a = (tp_a - 0.5 * (1 - t_b)) / denom_a
            else:
                best_a = 0.0
            t_a = np.clip(best_a, 0.0, t_max)

            # Country B's best response to t_a
            tp_b = country_b_retaliation_power
            denom_b = 2 * tp_b + elasticity
            if abs(denom_b) > 1e-12:
                best_b = (tp_b - 0.5 * (1 - t_a)) / denom_b
            else:
                best_b = 0.0
            t_b = np.clip(best_b, 0.0, t_max)

            tariff_history_a.append(t_a)
            tariff_history_b.append(t_b)

            if abs(t_a - old_a) < 1e-8 and abs(t_b - old_b) < 1e-8:
                converged = True
                break

        # Compute welfare impacts at equilibrium
        # Trade remaining after tariffs
        trade_remaining = trade_volume * (1 - t_a) * (1 - t_b)
        trade_loss = trade_volume - trade_remaining

        # Tariff revenue
        revenue_a = t_a * trade_remaining
        revenue_b = t_b * trade_remaining

        # Consumer deadweight loss
        dwl_a = 0.5 * elasticity * t_a ** 2 * trade_volume
        dwl_b = 0.5 * elasticity * t_b ** 2 * trade_volume

        # Net welfare impact for each country
        welfare_a = revenue_a - dwl_a - trade_loss * 0.5
        welfare_b = revenue_b - dwl_b - trade_loss * 0.5

        welfare_impact = {
            "country_a": {
                "tariff_rate": round(t_a, 6),
                "tariff_revenue": round(revenue_a, 4),
                "consumer_loss": round(dwl_a, 4),
                "net_welfare": round(welfare_a, 4),
            },
            "country_b": {
                "tariff_rate": round(t_b, 6),
                "tariff_revenue": round(revenue_b, 4),
                "consumer_loss": round(dwl_b, 4),
                "net_welfare": round(welfare_b, 4),
            },
            "joint_trade_loss": round(trade_loss, 4),
            "trade_remaining_pct": round(100 * trade_remaining / (trade_volume + 1e-12), 2),
        }

        return {
            "equilibrium_tariffs": {
                "country_a": round(t_a, 6),
                "country_b": round(t_b, 6),
            },
            "welfare_impact": welfare_impact,
            "nash_converged": converged,
        }

    def election_cycle_effect(self, monthly_returns, election_months):
        """
        Analyze pre/post-election return patterns.

        Compares mean returns in months before and after elections.
        Tests for statistical significance using a two-sample t-test.

        Parameters
        ----------
        monthly_returns : array-like
            Monthly returns for the asset/market.
        election_months : array-like of int
            Zero-indexed months in which elections occur.

        Returns
        -------
        dict with keys: pre_election_mean, post_election_mean,
                        statistical_significance, effect_size
        """
        returns = np.asarray(monthly_returns, dtype=float)
        elections = np.asarray(election_months, dtype=int)
        n = len(returns)

        if n < 12 or len(elections) == 0:
            return {
                "pre_election_mean": 0.0,
                "post_election_mean": 0.0,
                "statistical_significance": {"t_statistic": 0.0, "p_value": 1.0},
                "effect_size": 0.0,
            }

        # Define pre-election window: 6 months before each election
        # Post-election window: 6 months after each election
        pre_window = 6
        post_window = 6

        pre_returns = []
        post_returns = []

        for em in elections:
            if em >= 0 and em < n:
                # Pre-election returns
                start_pre = max(0, em - pre_window)
                for i in range(start_pre, em):
                    if i >= 0 and i < n:
                        pre_returns.append(returns[i])

                # Post-election returns
                end_post = min(n, em + post_window + 1)
                for i in range(em + 1, end_post):
                    if i >= 0 and i < n:
                        post_returns.append(returns[i])

        pre_returns = np.array(pre_returns)
        post_returns = np.array(post_returns)

        pre_mean = float(np.mean(pre_returns)) if len(pre_returns) > 0 else 0.0
        post_mean = float(np.mean(post_returns)) if len(post_returns) > 0 else 0.0

        # Two-sample t-test
        if len(pre_returns) > 1 and len(post_returns) > 1:
            t_stat, p_value = stats.ttest_ind(pre_returns, post_returns, equal_var=False)
            t_stat = float(t_stat)
            p_value = float(p_value)
        else:
            t_stat = 0.0
            p_value = 1.0

        # Cohen's d effect size
        pre_std = np.std(pre_returns, ddof=1) if len(pre_returns) > 1 else 1.0
        post_std = np.std(post_returns, ddof=1) if len(post_returns) > 1 else 1.0
        pooled_std = np.sqrt(
            (len(pre_returns) * pre_std ** 2 + len(post_returns) * post_std ** 2)
            / (len(pre_returns) + len(post_returns) + 1e-12)
        )
        if pooled_std > 1e-12:
            cohens_d = (post_mean - pre_mean) / pooled_std
        else:
            cohens_d = 0.0

        return {
            "pre_election_mean": round(pre_mean, 8),
            "post_election_mean": round(post_mean, 8),
            "statistical_significance": {
                "t_statistic": round(t_stat, 6),
                "p_value": round(p_value, 6),
            },
            "effect_size": round(float(cohens_d), 6),
        }


class RegulatoryCapital:
    """Regulatory capital requirement models (Basel III framework)."""

    def basel_iii_capital(self, risk_weighted_assets, capital_ratios=None):
        """
        Compute Basel III capital requirements.

        Minimum ratios:
            - CET1 (Common Equity Tier 1) >= 4.5%
            - Tier 1 Capital >= 6.0%
            - Total Capital >= 8.0%

        Plus buffers:
            - Capital Conservation Buffer: 2.5%
            - Countercyclical Buffer: 0-2.5%

        Parameters
        ----------
        risk_weighted_assets : float
            Total risk-weighted assets (RWA).
        capital_ratios : dict or None
            Current capital ratios: {cet1, tier1, total}.
            If None, assumes minimum ratios.

        Returns
        -------
        dict with keys: required_capital, buffers, total_requirement, surplus_deficit
        """
        rwa = float(risk_weighted_assets)

        # Minimum capital ratios
        min_cet1 = 0.045   # 4.5%
        min_tier1 = 0.060   # 6.0%
        min_total = 0.080   # 8.0%

        # Buffers
        ccb_rate = 0.025  # Capital Conservation Buffer: 2.5%
        cyb_rate = 0.0125  # Countercyclical Buffer: 1.25% (midpoint)

        # G-SIB surcharge (not always applicable, assume 0 for standard)
        gsib_surcharge = 0.0

        # Minimum + buffers
        cet1_with_buffer = min_cet1 + ccb_rate + cyb_rate + gsib_surcharge
        tier1_with_buffer = min_tier1 + ccb_rate + cyb_rate + gsib_surcharge
        total_with_buffer = min_total + ccb_rate + cyb_rate + gsib_surcharge

        # Required capital amounts
        required_cet1 = cet1_with_buffer * rwa
        required_tier1 = tier1_with_buffer * rwa
        required_total = total_with_buffer * rwa

        buffers = {
            "capital_conservation_buffer_pct": 0.025,
            "capital_conservation_buffer_amount": round(0.025 * rwa, 4),
            "countercyclical_buffer_pct": 0.0125,
            "countercyclical_buffer_amount": round(0.0125 * rwa, 4),
            "gsib_surcharge_pct": 0.0,
            "gsib_surcharge_amount": 0.0,
            "total_buffer_pct": round(ccb_rate + cyb_rate + gsib_surcharge, 4),
            "total_buffer_amount": round((ccb_rate + cyb_rate + gsib_surcharge) * rwa, 4),
        }

        required_capital = {
            "cet1_minimum_pct": 0.045,
            "cet1_minimum_amount": round(0.045 * rwa, 4),
            "cet1_with_buffer_pct": round(cet1_with_buffer, 4),
            "cet1_with_buffer_amount": round(required_cet1, 4),
            "tier1_minimum_pct": 0.060,
            "tier1_minimum_amount": round(0.060 * rwa, 4),
            "tier1_with_buffer_pct": round(tier1_with_buffer, 4),
            "tier1_with_buffer_amount": round(required_tier1, 4),
            "total_minimum_pct": 0.080,
            "total_minimum_amount": round(0.080 * rwa, 4),
            "total_with_buffer_pct": round(total_with_buffer, 4),
            "total_with_buffer_amount": round(required_total, 4),
        }

        # Surplus/deficit analysis if current ratios provided
        surplus_deficit = None
        if capital_ratios is not None:
            current_cet1 = capital_ratios.get("cet1", 0.0)
            current_tier1 = capital_ratios.get("tier1", 0.0)
            current_total = capital_ratios.get("total", 0.0)

            surplus_deficit = {
                "cet1_surplus_deficit": round((current_cet1 - cet1_with_buffer) * rwa, 4),
                "tier1_surplus_deficit": round((current_tier1 - tier1_with_buffer) * rwa, 4),
                "total_surplus_deficit": round((current_total - total_with_buffer) * rwa, 4),
                "cet1_ratio_current": current_cet1,
                "tier1_ratio_current": current_tier1,
                "total_ratio_current": current_total,
                "cet1_compliant": current_cet1 >= cet1_with_buffer,
                "tier1_compliant": current_tier1 >= tier1_with_buffer,
                "total_compliant": current_total >= total_with_buffer,
            }

        return {
            "required_capital": required_capital,
            "buffers": buffers,
            "total_requirement": round(required_total, 4),
            "surplus_deficit": surplus_deficit,
        }

    def var_based_capital(self, var_99, holding_period=10, n_days=250):
        """
        Compute capital charge based on Value-at-Risk (Basel 2.5/III).

        Capital charge = max(VaR_{t-1}, m_c * avg_VaR_{last_60_days}) * sqrt(10)/sqrt(hp)

        where m_c is the multiplier based on backtesting zones:
            Green zone:   multiplier = 3
            Yellow zone: multiplier = 3-4
            Red zone:    multiplier = 4+

        Parameters
        ----------
        var_99 : float or array-like
            Daily 99% VaR. If scalar, treated as constant.
            If array, uses last 60 observations for average.
        holding_period : int
            Current VaR holding period in days.
        n_days : int
            Number of trading days per year.

        Returns
        -------
        dict with keys: capital_charge, backtesting_zones, multiplier
        """
        var_99 = np.asarray(var_99, dtype=float)

        # Scaling factor to 10-day holding period
        if holding_period > 0:
            scaling_factor = np.sqrt(10.0 / holding_period)
        else:
            scaling_factor = 1.0

        if var_99.ndim == 0:
            # Single VaR value
            var_current = float(var_99) * scaling_factor
            var_avg = var_current
            # Assume green zone
            multiplier = 3.0
            exceptions = 0
        else:
            # Time series of VaR
            var_scaled = var_99 * scaling_factor
            var_current = var_scaled[-1]
            # Average of last 60 days
            n_avg = min(60, len(var_scaled))
            var_avg = np.mean(var_scaled[-n_avg:])

            # Estimate backtesting exceptions based on VaR level
            # With 99% VaR, expect ~1% exceptions over n_days
            # Simulate exceptions count (model-based estimate)
            n_backtest = min(n_days, len(var_99))
            expected_exceptions = n_backtest * 0.01
            # Assume slight model risk: multiply expected by 1.5
            exceptions = int(np.ceil(expected_exceptions * 1.5))

        # Determine multiplier based on exception zones
        # Basel traffic light approach (250 trading days)
        green_threshold = 4
        yellow_threshold = 9

        if exceptions <= green_threshold:
            multiplier = 3.0
            zone = "Green"
        elif exceptions <= yellow_threshold:
            # Linear interpolation between 3 and 4
            multiplier = 3.0 + (exceptions - green_threshold) * (1.0 / (yellow_threshold - green_threshold))
            zone = "Yellow"
        else:
            multiplier = 4.0
            zone = "Red"

        # Capital charge = max(current VaR, multiplier * average VaR)
        capital_charge = max(var_current, multiplier * var_avg)

        # Plus stressed VaR component (Basel 2.5)
        stressed_var_addon = var_avg * 0.5  # simplified
        total_capital = capital_charge + stressed_var_addon

        return {
            "capital_charge": round(float(total_capital), 6),
            "backtesting_zones": {
                "zone": zone,
                "exceptions": exceptions,
                "green_threshold": green_threshold,
                "yellow_threshold": yellow_threshold,
                "multiplier": round(multiplier, 2),
            },
            "multiplier": round(multiplier, 2),
            "scaling_factor": round(scaling_factor, 4),
            "var_current_10d": round(float(var_current), 6),
            "var_avg_10d": round(float(var_avg), 6),
        }

    def liquidity_coverage_ratio(self, hqla, net_cash_outflows_30d):
        """
        Compute the Liquidity Coverage Ratio (LCR).

        LCR = High Quality Liquid Assets / Net Cash Outflows (30-day)

        Requirement: LCR >= 100%

        Parameters
        ----------
        hqla : float
            Total High Quality Liquid Assets.
        net_cash_outflows_30d : float
            Total net cash outflows over 30 days.

        Returns
        -------
        dict with keys: lcr, compliant, surplus
        """
        if abs(net_cash_outflows_30d) < 1e-12:
            lcr = float("inf")
        else:
            lcr = hqla / net_cash_outflows_30d

        compliant = lcr >= 1.0
        surplus = hqla - net_cash_outflows_30d

        # HQLA composition breakdown (regulatory classification)
        # Level 1 assets: cash, central bank reserves, sovereign securities (0% haircut)
        # Level 2A assets: corporate bonds (15% haircut), covered bonds (15%)
        # Level 2B assets: lower-rated corporate bonds (25-50% haircut)
        # Level 2 assets capped at 40% of total HQLA

        # Assume breakdown for analysis
        level1_min = 0.60  # at least 60% of HQLA should be Level 1
        level2_max = 0.40

        return {
            "lcr": round(lcr, 6),
            "lcr_pct": round(lcr * 100, 2),
            "compliant": compliant,
            "surplus": round(surplus, 4),
            "hqla": round(hqla, 4),
            "net_cash_outflows": round(net_cash_outflows_30d, 4),
            "minimum_hqla_required": round(net_cash_outflows_30d * 1.0, 4),
            "shortfall": round(max(0, net_cash_outflows_30d - hqla), 4),
            "regulatory_notes": {
                "minimum_ratio": "100%",
                "level1_minimum_pct": f"{level1_min * 100:.0f}%",
                "level2_maximum_pct": f"{level2_max * 100:.0f}%",
            },
        }

    def leverage_ratio(self, tier1_capital, total_exposure):
        """
        Compute the Basel III leverage ratio.

        Leverage Ratio = Tier 1 Capital / Total Exposure

        Requirement: Leverage Ratio >= 3%

        Parameters
        ----------
        tier1_capital : float
            Tier 1 capital.
        total_exposure : float
            Total exposure measure (on- and off-balance sheet).

        Returns
        -------
        dict with keys: leverage_ratio, compliant, buffer
        """
        if abs(total_exposure) < 1e-12:
            lr = float("inf")
        else:
            lr = tier1_capital / total_exposure

        minimum_ratio = 0.03  # 3%
        compliant = lr >= minimum_ratio

        # Supplementary leverage ratio buffer (G-SIBs: 50% of G-SIB surcharge)
        # For non-G-SIB, buffer is 0
        buffer = 0.0
        effective_minimum = minimum_ratio + buffer

        surplus = tier1_capital - effective_minimum * total_exposure
        buffer_amount = buffer * total_exposure

        # Capital needed to meet minimum
        capital_needed = max(0, effective_minimum * total_exposure - tier1_capital)

        return {
            "leverage_ratio": round(lr, 6),
            "leverage_ratio_pct": round(lr * 100, 4),
            "compliant": compliant,
            "buffer": {
                "buffer_rate": round(buffer, 4),
                "buffer_amount": round(buffer_amount, 4),
                "effective_minimum_pct": round(effective_minimum * 100, 2),
            },
            "surplus": round(surplus, 4),
            "capital_shortfall": round(capital_needed, 4),
            "tier1_capital": round(tier1_capital, 4),
            "total_exposure": round(total_exposure, 4),
            "minimum_ratio_pct": "3.0%",
        }
