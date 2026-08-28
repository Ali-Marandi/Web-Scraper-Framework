r"""
Quantitative Finance Engine - Main Orchestrator
Unified interface to all 30+ quantitative finance methodologies.
Bridges scraped data from the web scraper to quantitative analytics.
"""

import threading
import numpy as np
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .data_manager import QuantDataManager, TimeSeriesData
from .time_series import ARIMA, SARIMA, GARCH, VAR, Cointegration, VaR as VaRAnalyzer
from .financial_engineering import (BlackScholes, MonteCarloSimulator,
                                    InterestRateModels, OptionStrategyAnalyzer)
from .portfolio import (MarkowitzOptimizer, BlackLittermanModel,
                        FuzzyPortfolioOptimizer, FactorModel)
from .machine_learning import (LSTMForecaster, TransformerForecaster,
                               NLPSentimentAnalyzer, AnomalyDetector, BehavioralFinance)
from .graph_analysis import CorrelationNetwork, ContagionModel, CausalGraph
from .advanced_methods import (CausalInference, TransferEntropy,
                                TopologicalDataAnalysis, ReinforcementLearning, GameTheory)
from .fuzzy_logic import (FuzzyNumber, FuzzyInferenceSystem, FuzzyCreditScoring,
                          FuzzyTradingSystem, FuzzyAHP, FuzzyTOPSIS, ANFIS)


class QuantEngine:
    """Main quantitative finance engine. Orchestrates all analysis modules."""

    def __init__(self):
        self.data = QuantDataManager()
        self._log_callback: Optional[Callable] = None
        self._progress_callback: Optional[Callable] = None
        self._analysis_history: List[Dict] = []
        self._lock = threading.RLock()

    def set_log_callback(self, cb: Callable) -> None:
        self._log_callback = cb

    def set_progress_callback(self, cb: Callable) -> None:
        self._progress_callback = cb

    def _log(self, msg: str, level: str = 'info') -> None:
        if self._log_callback:
            self._log_callback(msg, level)

    def _record(self, category: str, method: str, result: Dict) -> Dict:
        record = {"category": category, "method": method, "result": result,
                  "timestamp": datetime.now().isoformat()}
        with self._lock:
            self._analysis_history.append(record)
        return record

    @property
    def history(self) -> List[Dict]:
        return list(self._analysis_history)

    # =================================================================
    # TIME SERIES
    # =================================================================

    def arima_forecast(self, dataset_name: str, order=(5,1,2), steps=10) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"ARIMA({order[0]},{order[1]},{order[2]}) forecast on {dataset_name}")
        model = ARIMA()
        result = model.fit(tsd.values, order=order)
        if 'error' not in result:
            fc = model.forecast(steps=steps)
            result['forecast'] = fc
        return self._record('Time Series', f'ARIMA{order}', result)

    def sarima_forecast(self, dataset_name: str, order=(2,1,2),
                        seasonal_order=(1,1,1,12), steps=10) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"SARIMA forecast on {dataset_name}")
        model = SARIMA()
        result = model.fit(tsd.values, order=order, seasonal_order=seasonal_order)
        if 'error' not in result:
            fc = model.forecast(steps=steps)
            result['forecast'] = fc
        return self._record('Time Series', f'SARIMA', result)

    def garch_analysis(self, dataset_name: str, p=1, q=1, forecast_steps=10) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        rets = tsd.returns
        if len(rets) < 10: return {"error": "Insufficient data for GARCH"}
        self._log(f"GARCH({p},{q}) volatility analysis on {dataset_name}")
        model = GARCH()
        result = model.fit(rets, p=p, q=q)
        if 'error' not in result:
            fc = model.forecast_volatility(steps=forecast_steps)
            result['volatility_forecast'] = fc
        return self._record('Time Series', f'GARCH({p},{q})', result)

    def var_analysis(self, dataset_names: List[str], max_lags=5) -> Dict:
        data = {}
        for name in dataset_names:
            tsd = self.data.get_dataset(name)
            if tsd and len(tsd.returns) > 10:
                data[name] = tsd.returns
        if len(data) < 2: return {"error": "Need at least 2 datasets with returns"}
        self._log(f"VAR analysis on {list(data.keys())}")
        model = VAR()
        result = model.fit(data, max_lags=max_lags)
        return self._record('Time Series', 'VAR', result)

    def cointegration_test(self, name1: str, name2: str, lags=2) -> Dict:
        t1 = self.data.get_dataset(name1)
        t2 = self.data.get_dataset(name2)
        if not t1 or not t2: return {"error": "Dataset not found"}
        min_len = min(len(t1.values), len(t2.values))
        self._log(f"Engle-Granger cointegration test: {name1} vs {name2}")
        model = Cointegration()
        result = model.engle_granger_test(t1.values[-min_len:], t2.values[-min_len:])
        result['ecm'] = model.error_correction_model(
            t1.values[-min_len:], t2.values[-min_len:], lags=lags)
        return self._record('Time Series', 'Cointegration', result)

    def var_risk(self, dataset_name: str, confidence=0.95) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        rets = tsd.returns
        if len(rets) < 20: return {"error": "Insufficient data for VaR"}
        self._log(f"VaR analysis on {dataset_name} at {confidence*100}%")
        analyzer = VaRAnalyzer()
        result = analyzer.all_methods(rets, confidence=confidence)
        return self._record('Risk', 'VaR/CVaR', result)

    # =================================================================
    # FINANCIAL ENGINEERING
    # =================================================================

    def black_scholes_price(self, S, K, T, r, sigma, option_type='call') -> Dict:
        self._log(f"Black-Scholes pricing: {option_type} S={S} K={K} T={T}")
        bs = BlackScholes()
        if option_type in ('call', 'both'):
            call = bs.european_call(S, K, T, r, sigma)
            call_greeks = bs.greeks(S, K, T, r, sigma)
        if option_type in ('put', 'both'):
            put = bs.european_put(S, K, T, r, sigma)
        result = {}
        if option_type in ('call', 'both'):
            result['call'] = call; result['greeks'] = call_greeks
        if option_type in ('put', 'both'):
            result['put'] = put
        return self._record('Financial Engineering', 'Black-Scholes', result)

    def implied_vol(self, market_price, S, K, T, r, option_type='call') -> Dict:
        bs = BlackScholes()
        result = bs.implied_volatility(market_price, S, K, T, r, option_type)
        return self._record('Financial Engineering', 'Implied Volatility', result)

    def binomial_tree_price(self, S, K, T, r, sigma, steps=100,
                            option_type='call', american=False) -> Dict:
        bs = BlackScholes()
        result = bs.binomial_tree(S, K, T, r, sigma, steps, option_type, american)
        return self._record('Financial Engineering', 'Binomial Tree', result)

    def monte_carlo_simulation(self, S0, mu, sigma, T=1.0,
                                n_paths=1000, n_steps=252) -> Dict:
        self._log(f"Monte Carlo GBM: S0={S0} mu={mu} sigma={sigma}")
        mc = MonteCarloSimulator()
        result = mc.geometric_brownian_motion(S0, mu, sigma, T, n_paths, n_steps)
        return self._record('Financial Engineering', 'Monte Carlo GBM', result)

    def interest_rate_model(self, model_type, r0, kappa, theta, sigma,
                             T=1.0, n_steps=252, n_paths=1000) -> Dict:
        self._log(f"Interest rate model: {model_type}")
        irm = InterestRateModels()
        if model_type == 'vasicek':
            result = irm.vasicek(r0, kappa, theta, sigma, T, n_steps, n_paths)
        elif model_type == 'cir':
            result = irm.cir(r0, kappa, theta, sigma, T, n_steps, n_paths)
        elif model_type == 'hull_white':
            result = irm.hull_white(r0, kappa, theta, sigma, T, n_steps, n_paths)
        else:
            result = {"error": f"Unknown model: {model_type}"}
        return self._record('Financial Engineering', f'IR {model_type}', result)

    def option_strategy(self, strategy, S, **kwargs) -> Dict:
        self._log(f"Option strategy: {strategy}")
        osa = OptionStrategyAnalyzer()
        if strategy == 'bull_call_spread':
            result = osa.bull_call_spread(S, kwargs['K1'], kwargs['K2'],
                                         kwargs['T'], kwargs['r'], kwargs['sigma'])
        elif strategy == 'straddle':
            result = osa.straddle(S, kwargs['K'], kwargs['T'], kwargs['r'], kwargs['sigma'])
        elif strategy == 'iron_condor':
            result = osa.iron_condor(S, kwargs['K1'], kwargs['K2'],
                                     kwargs['K3'], kwargs['K4'],
                                     kwargs['T'], kwargs['r'], kwargs['sigma'])
        elif strategy == 'butterfly':
            result = osa.butterfly_spread(S, kwargs['K1'], kwargs['K2'],
                                          kwargs['K3'], kwargs['T'], kwargs['r'], kwargs['sigma'])
        else:
            result = {"error": f"Unknown strategy: {strategy}"}
        return self._record('Financial Engineering', strategy, result)

    # =================================================================
    # PORTFOLIO OPTIMIZATION
    # =================================================================

    def markowitz_optimize(self, dataset_names: List[str], method='sharpe',
                           risk_free_rate=0.02) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty or len(names) < 2:
            return {"error": "Need at least 2 datasets with returns"}
        self._log(f"Markowitz {method} optimization on {len(names)} assets")
        opt = MarkowitzOptimizer()
        result = opt.optimize(rets_df.values, method=method, risk_free_rate=risk_free_rate)
        result['optimal_weights'] = result.get('weights', [])
        result['asset_names'] = names
        return self._record('Portfolio', f'Markowitz {method}', result)

    def efficient_frontier(self, dataset_names: List[str],
                           n_points=50, risk_free_rate=0.02) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No returns data"}
        self._log("Computing efficient frontier")
        opt = MarkowitzOptimizer()
        result = opt.efficient_frontier(rets_df.values, n_points, risk_free_rate)
        result['asset_names'] = names
        return self._record('Portfolio', 'Efficient Frontier', result)

    def black_litterman(self, dataset_names: List[str], views: List[Dict],
                        risk_aversion=2.5, tau=0.05) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No returns data"}
        cov = np.cov(rets_df.values.T)
        if cov.ndim == 0: cov = np.array([[float(cov)]])
        n = len(names)
        market_weights = np.ones(n) / n
        self._log(f"Black-Litterman with {len(views)} views")
        bl = BlackLittermanModel(market_weights, cov, risk_aversion, tau)
        for v in views:
            idx = names.index(v['asset']) if v['asset'] in names else 0
            bl.add_view(idx, v['return'], v.get('confidence', 0.5))
        result = bl.compute()
        if 'error' not in result:
            opt = bl.optimize_portfolio(risk_free_rate=0.02)
            result['optimal_weights'] = opt.get('optimal_weights', [])
        result['asset_names'] = names
        return self._record('Portfolio', 'Black-Litterman', result)

    def fuzzy_portfolio(self, dataset_names: List[str], target_return=None,
                        membership='triangular') -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No returns data"}
        self._log(f"Fuzzy portfolio optimization on {len(names)} assets")
        opt = FuzzyPortfolioOptimizer()
        if target_return is not None:
            result = opt.fuzzy_mean_variance(rets_df.values, target_return, membership)
        else:
            result = opt.fuzzy_sharpe_optimization(rets_df.values, membership)
        result['asset_names'] = names
        return self._record('Portfolio', 'Fuzzy Portfolio', result)

    def pca_factors(self, dataset_names: List[str], n_factors=5) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No returns data"}
        self._log(f"PCA factor extraction: {n_factors} factors")
        fm = FactorModel()
        result = fm.pca_factors(rets_df.values, n_factors)
        result['asset_names'] = names
        return self._record('Portfolio', 'PCA Factors', result)

    # =================================================================
    # MACHINE LEARNING
    # =================================================================

    def lstm_forecast(self, dataset_name: str, n_steps=10, epochs=50,
                       seq_length=20) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"LSTM forecast on {dataset_name}")
        model = LSTMForecaster(hidden_size=32)
        train = model.fit(tsd.values, epochs=epochs, seq_length=seq_length, verbose=False)
        pred = model.predict(tsd.values, n_steps=n_steps)
        result = {**train, **pred}
        return self._record('Machine Learning', 'LSTM', result)

    def transformer_forecast(self, dataset_name: str, n_steps=10,
                             epochs=50) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Transformer forecast on {dataset_name}")
        model = TransformerForecaster(d_model=32, n_heads=4, n_layers=2)
        train = model.fit(tsd.values, epochs=epochs, verbose=False)
        pred = model.predict(tsd.values, n_steps=n_steps)
        result = {**train, **pred}
        return self._record('Machine Learning', 'Transformer', result)

    def sentiment_analysis(self, text: str) -> Dict:
        sa = NLPSentimentAnalyzer()
        result = sa.analyze(text)
        return self._record('NLP', 'Sentiment Analysis', result)

    def anomaly_detection(self, dataset_name: str, method='zscore',
                          threshold=3.0) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Anomaly detection ({method}) on {dataset_name}")
        det = AnomalyDetector(method=method)
        result = det.detect(tsd.values, threshold=threshold)
        breaks = det.detect_structural_breaks(tsd.values)
        result['structural_breaks'] = breaks
        return self._record('Machine Learning', f'Anomaly ({method})', result)

    def behavioral_analysis(self, returns) -> Dict:
        bf = BehavioralFinance()
        pt = bf.prospect_theory_value(returns)
        la = bf.loss_aversion_ratio(returns)
        return self._record('Behavioral', 'Prospect Theory', {
            'prospect_theory': pt, 'loss_aversion': la})

    # =================================================================
    # GRAPH ANALYSIS
    # =================================================================

    def correlation_network(self, dataset_names: List[str],
                            threshold=0.3) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty or len(names) < 3:
            return {"error": "Need at least 3 datasets"}
        self._log(f"Correlation network on {len(names)} assets")
        cn = CorrelationNetwork()
        result = cn.build_correlation_network(rets_df.values, threshold)
        result['node_names'] = names
        mst = cn.minimum_spanning_tree(rets_df.values)
        result['mst'] = mst
        comm = cn.community_detection(rets_df.values)
        result['communities'] = comm
        cent = cn.centrality_measures(
            np.abs(np.corrcoef(rets_df.values.T)) > threshold)
        result['centrality'] = cent
        return self._record('Graph', 'Correlation Network', result)

    def contagion_analysis(self, dataset_names: List[str],
                           shock_asset=None, threshold=0.5) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        self._log("Contagion analysis")
        cm = ContagionModel()
        corr = np.abs(np.corrcoef(rets_df.values.T))
        adj = (corr > threshold).astype(float)
        np.fill_diagonal(adj, 0)
        shock_idx = 0
        if shock_asset and shock_asset in names:
            shock_idx = names.index(shock_asset)
        result = cm.threshold_model(adj, [shock_idx], threshold=0.3)
        result['node_names'] = names
        return self._record('Graph', 'Contagion', result)

    # =================================================================
    # FUZZY LOGIC
    # =================================================================

    def fuzzy_credit_score(self, income, debt_ratio, credit_history,
                           employment_years) -> Dict:
        self._log("Fuzzy credit scoring")
        fcs = FuzzyCreditScoring()
        result = fcs.score(income, debt_ratio, credit_history, employment_years)
        return self._record('Fuzzy', 'Credit Scoring', result)

    def fuzzy_trading_signal(self, rsi, volume_norm, price_trend_pct,
                             volatility) -> Dict:
        self._log("Fuzzy trading signal")
        fts = FuzzyTradingSystem()
        result = fts.evaluate_signal(rsi, volume_norm, price_trend_pct, volatility)
        return self._record('Fuzzy', 'Trading Signal', result)

    def fuzzy_ahp(self, criteria: List[str]) -> Dict:
        self._log(f"Fuzzy AHP: {len(criteria)} criteria")
        fahp = FuzzyAHP(criteria)
        n = len(criteria)
        for i in range(n):
            for j in range(i+1, n):
                fahp.set_pairwise_comparison(i, j, 1.0)
        result = fahp.compute_weights()
        result['criteria'] = criteria
        return self._record('Fuzzy', 'AHP', result)

    # =================================================================
    # ADVANCED METHODS
    # =================================================================

    def transfer_entropy_analysis(self, dataset_names: List[str],
                                  lag=1, n_bins=10) -> Dict:
        results = {}
        te = TransferEntropy()
        pairs = []
        for i, n1 in enumerate(dataset_names):
            t1 = self.data.get_dataset(n1)
            if not t1: continue
            for j, n2 in enumerate(dataset_names):
                if i == j: continue
                t2 = self.data.get_dataset(n2)
                if not t2: continue
                min_l = min(len(t1.values), len(t2.values))
                r = te.compute(t1.values[-min_l:], t2.values[-min_l:], lag, n_bins=n_bins)
                r['source'] = n1; r['target'] = n2
                pairs.append(r)
        results['pairs'] = pairs
        results['summary'] = f"Analyzed {len(pairs)} directed pairs"
        self._log(f"Transfer entropy: {len(pairs)} pairs")
        return self._record('Advanced', 'Transfer Entropy', results)

    def tda_analysis(self, dataset_name: str, window=50) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Topological Data Analysis on {dataset_name}")
        tda = TopologicalDataAnalysis()
        diag = tda.persistent_homology_1d(tsd.values)
        betti = tda.betti_numbers(diag['diagram'])
        regime = tda.detect_regime_changes(tsd.values, window=window)
        result = {**diag, 'betti_numbers': betti, 'regime_changes': regime}
        return self._record('Advanced', 'TDA', result)

    def causal_analysis(self, dataset_names: List[str]) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        self._log("Causal analysis")
        ci = CausalInference()
        te = TransferEntropy()
        gc = te.granger_causality_matrix(rets_df.values, max_lag=3)
        result = {'granger_matrix': gc, 'asset_names': names}
        return self._record('Advanced', 'Causal', result)

    def game_theory_analysis(self, payoff_a, payoff_b) -> Dict:
        self._log("Game theory Nash equilibrium")
        gt = GameTheory()
        result = gt.nash_equilibrium_2x2(
            np.array(payoff_a), np.array(payoff_b))
        mixed = gt.mixed_nash_2x2(
            np.array(payoff_a), np.array(payoff_b))
        result['mixed_equilibrium'] = mixed
        return self._record('Advanced', 'Game Theory', result)

    def rl_trading(self, dataset_name: str, n_episodes=500) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"RL trading agent on {dataset_name}")
        rl = ReinforcementLearning(n_states=20, n_actions=3)
        env_fn = rl.trading_env(tsd.values)
        result = rl.train_q_learning(env_fn, n_episodes=n_episodes, max_steps=100)
        return self._record('Advanced', 'RL Trading', result)

    # =================================================================
    # CONVENIENCE
    # =================================================================

    def get_available_methods(self) -> Dict[str, List[str]]:
        return {
            'Time Series': ['ARIMA', 'SARIMA', 'GARCH', 'VAR', 'Cointegration', 'VaR/CVaR'],
            'Financial Engineering': ['Black-Scholes', 'Implied Volatility', 'Binomial Tree',
                                     'Monte Carlo', 'Interest Rate Models', 'Option Strategies'],
            'Portfolio': ['Markowitz', 'Black-Litterman', 'Fuzzy Portfolio',
                         'PCA Factors', 'Fama-French'],
            'Machine Learning': ['LSTM', 'Transformer', 'Sentiment Analysis',
                                'Anomaly Detection', 'Behavioral Finance'],
            'Graph Analysis': ['Correlation Network', 'Contagion', 'Causal Graph'],
            'Fuzzy Logic': ['Credit Scoring', 'Trading Signal', 'AHP', 'TOPSIS', 'ANFIS'],
            'Advanced': ['Transfer Entropy', 'TDA', 'Causal Inference',
                        'Game Theory', 'Reinforcement Learning'],
        }

    def full_analysis_report(self, dataset_names: List[str]) -> Dict:
        """Run comprehensive analysis on given datasets."""
        self._log(f"Starting full analysis on {dataset_names}")
        report = {'datasets': {}, 'analyses': {}}
        for name in dataset_names:
            tsd = self.data.get_dataset(name)
            if tsd:
                report['datasets'][name] = tsd.summary()
        if len(dataset_names) >= 2:
            report['analyses']['var'] = self.var_analysis(dataset_names)
            report['analyses']['network'] = self.correlation_network(dataset_names)
        if len(dataset_names) >= 1:
            report['analyses']['arima'] = self.arima_forecast(dataset_names[0])
            report['analyses']['garch'] = self.garch_analysis(dataset_names[0])
            report['analyses']['anomaly'] = self.anomaly_detection(dataset_names[0])
            report['analyses']['var_risk'] = self.var_risk(dataset_names[0])
        self._log("Full analysis complete")
        return report
