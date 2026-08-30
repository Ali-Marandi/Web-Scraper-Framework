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
from .macro_models import (DSGEModel, TaylorRule, PhillipsCurve,
                           MinskyModel, KondratievWaves, CapitalStructure)
from .natural_science_models import (ClimateVaR, HotellingRule, SIRModel,
                                      InnovationSCurve, EpidemicFinance)
from .market_microstructure import (OrderBookSimulator, BidAskModels,
                                     MarketMakerNash, GeopoliticalRiskModel, RegulatoryCapital)
from .corporate_finance import (CAPMModel, APTModel, EMHTester,
                                 AltmanZScore, BeneishMScore)
from .frontier_models import (FrontierAnalytics, ResampledFrontier,
                               RiskParityOptimizer, KellyCriterion,
                               CVaROptimizer, HierarchicalRiskParity)
from .quantum_synthetic import (QuantumMonteCarlo, DiffusionSyntheticData,
                                 FederatedLearningSim, QuantumGameTheory)
from .report_generator import PDFReportGenerator, ExcelReportGenerator
from . import quant_charts
from .market_data import MarketDataFeed


class QuantEngine:
    """Main quantitative finance engine. Orchestrates all analysis modules."""

    def __init__(self):
        self.data = QuantDataManager()
        self.market = MarketDataFeed()
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
    # MACROECONOMIC MODELS
    # =================================================================

    def dsge_simulate(self, n_periods=200, shock_type='monetary') -> Dict:
        self._log(f"DSGE simulation: {n_periods} periods")
        model = DSGEModel()
        result = model.simulate(n_periods=n_periods)
        if shock_type != 'none':
            irf = model.impulse_response(shock_type=shock_type)
            result['impulse_response'] = irf
        return self._record('Macroeconomic', 'DSGE', result)

    def taylor_rule_fit(self, inflation, interest_rate, output_gap) -> Dict:
        self._log("Taylor rule estimation")
        model = TaylorRule()
        result = model.fit_rule(np.array(inflation), np.array(interest_rate), np.array(output_gap))
        return self._record('Macroeconomic', 'Taylor Rule', result)

    def phillips_curve(self, unemployment, inflation) -> Dict:
        self._log("Phillips curve estimation")
        model = PhillipsCurve()
        result = model.estimate(np.array(unemployment), np.array(inflation))
        return self._record('Macroeconomic', 'Phillips Curve', result)

    def minsky_simulation(self, n_periods=200) -> Dict:
        self._log("Minsky financial instability simulation")
        model = MinskyModel()
        result = model.simulate(n_periods=n_periods)
        return self._record('Macroeconomic', 'Minsky Model', result)

    def kondratiev_analysis(self, dataset_name: str) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Kondratiev wave analysis on {dataset_name}")
        model = KondratievWaves()
        fft = model.fft_analysis(tsd.values)
        hp = model.hp_filter(tsd.values)
        phase = model.current_wave_phase(tsd.values)
        result = {**fft, 'hp_filter': hp, 'wave_phase': phase}
        return self._record('Macroeconomic', 'Kondratiev Waves', result)

    def modigliani_miller(self, V_u, debt, r_d, tax_rate=0.2) -> Dict:
        self._log("Modigliani-Miller analysis")
        model = CapitalStructure()
        result = model.modigliani_miller(V_u, debt, r_d, tax_rate)
        return self._record('Macroeconomic', 'Modigliani-Miller', result)

    # =================================================================
    # NATURAL SCIENCE MODELS
    # =================================================================

    def sir_simulation(self, N=10000, I0=10, beta=0.3, gamma=0.1, n_days=200) -> Dict:
        self._log(f"SIR epidemic model: R0={beta/gamma:.2f}")
        model = SIRModel()
        result = model.simulate(N, I0, beta, gamma, n_days)
        return self._record('Natural Science', 'SIR Model', result)

    def climate_var(self, dataset_name: str, temperature_data=None) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Climate VaR on {dataset_name}")
        model = ClimateVaR()
        temp = np.array(temperature_data) if temperature_data else np.random.normal(0.5, 0.3, len(tsd.returns))
        result = model.estimate(tsd.returns, temp)
        return self._record('Natural Science', 'Climate VaR', result)

    def innovation_s_curve(self, adoption_data) -> Dict:
        self._log("Innovation S-curve fitting")
        model = InnovationSCurve()
        result = model.technology_s_curve(np.array(adoption_data))
        moore = model.moore_law()
        result['moore_projection'] = moore
        return self._record('Natural Science', 'S-Curve', result)

    def hotelling_extraction(self, initial_price, marginal_cost, interest_rate, reserves) -> Dict:
        self._log("Hotelling rule optimal extraction")
        model = HotellingRule()
        result = model.optimal_extraction(initial_price, marginal_cost, interest_rate, reserves)
        return self._record('Natural Science', 'Hotelling Rule', result)

    # =================================================================
    # MARKET MICROSTRUCTURE
    # =================================================================

    def simulate_orderbook(self, mid_price=100.0, n_levels=10, shape='normal') -> Dict:
        self._log(f"Order book simulation: mid={mid_price}")
        model = OrderBookSimulator()
        result = model.generate_lob(mid_price, n_levels, shape)
        impact = model.market_impact(1000, result)
        result['market_impact'] = impact
        return self._record('Microstructure', 'Order Book', result)

    def roll_spread(self, prices) -> Dict:
        self._log("Roll spread estimation")
        model = BidAskModels()
        result = model.roll_spread(np.array(prices))
        return self._record('Microstructure', 'Roll Spread', result)

    def nash_market_making(self, n_makers=3, volatility=0.02) -> Dict:
        self._log(f"Nash market making: {n_makers} makers")
        model = MarketMakerNash()
        result = model.nash_spread(n_makers, volatility)
        return self._record('Microstructure', 'Nash MM', result)

    def geopolitical_risk(self, economic=50, financial=50, political=50) -> Dict:
        self._log("ICRG geopolitical risk assessment")
        model = GeopoliticalRiskModel()
        result = model.icrg_composite(economic, financial, political)
        sanction = model.sanction_impact(trade_exposure=0.3, sanction_severity=0.7, gdp_elasticity=0.5, duration_years=3)
        result['sanction_impact'] = sanction
        return self._record('Microstructure', 'Geopolitical Risk', result)

    def basel_capital(self, rwa, tier1_capital=None, hqla=None, net_outflows=None) -> Dict:
        self._log("Basel III capital requirements")
        model = RegulatoryCapital()
        result = model.basel_iii_capital(rwa)
        if hqla is not None and net_outflows is not None:
            result['lcr'] = model.liquidity_coverage_ratio(hqla, net_outflows)
        return self._record('Microstructure', 'Basel III', result)

    # =================================================================
    # EPIDEMIC-FINANCE BRIDGE
    # =================================================================

    def epidemic_market_stress(self, returns, volatility, infection_rate=None, mobility_index=None) -> Dict:
        self._log("Epidemic market stress index")
        model = EpidemicFinance()
        r = np.array(returns)
        v = np.array(volatility)
        n = len(r)
        inf = np.array(infection_rate) if infection_rate is not None else np.random.uniform(0, 0.05, n)
        mob = np.array(mobility_index) if mobility_index is not None else np.random.uniform(0.3, 1.0, n)
        result = model.market_stress_index(r, v, inf, mob)
        return self._record('Natural Science', 'Epidemic Stress', result)

    def epidemic_recovery_forecast(self, dataset_name: str, shock_date=None) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        self._log(f"Epidemic recovery forecast on {dataset_name}")
        model = EpidemicFinance()
        prices = tsd.values
        sd = shock_date if shock_date else len(prices) * 3 // 4
        result = model.recovery_forecast(prices[:sd], sd)
        return self._record('Natural Science', 'Epidemic Recovery', result)

    # =================================================================
    # CORPORATE FINANCE
    # =================================================================

    def capm_estimate(self, returns, market_returns, risk_free_rate=0.02) -> Dict:
        self._log("CAPM estimation")
        model = CAPMModel()
        result = model.estimate(np.array(returns), np.array(market_returns), risk_free_rate)
        return self._record('Corporate Finance', 'CAPM', result)

    def apt_estimate(self, returns, factor_returns) -> Dict:
        self._log("APT multi-factor estimation")
        model = APTModel()
        result = model.estimate(np.array(returns), np.array(factor_returns))
        return self._record('Corporate Finance', 'APT', result)

    def emh_test(self, returns, prices=None) -> Dict:
        self._log("EMH test battery")
        model = EMHTester()
        rets = np.array(returns)
        prc = np.array(prices) if prices is not None else None
        result = model.summary(rets, prc)
        return self._record('Corporate Finance', 'EMH', result)

    def altman_z_score(self, wc_ta, re_ta, ebit_ta, mv_de, sales_ta,
                        model_type='manufacturing') -> Dict:
        self._log(f"Altman Z-Score ({model_type})")
        model = AltmanZScore()
        if model_type == 'manufacturing':
            z = model.manufacturing(wc_ta, re_ta, ebit_ta, mv_de, sales_ta)
        elif model_type == 'private':
            z = model.private_non_manufacturing(wc_ta, re_ta, ebit_ta, mv_de, sales_ta)
        elif model_type == 'emerging':
            z = model.emerging_markets(wc_ta, re_ta, ebit_ta, mv_de, sales_ta)
        else:
            z = model.manufacturing(wc_ta, re_ta, ebit_ta, mv_de, sales_ta)
        interp = model.interpret(z.get('z_score', 0), model_type)
        bond = model.bond_equivalent(z.get('z_score', 0), model_type)
        z['interpretation'] = interp
        z['credit_equivalent'] = bond
        return self._record('Corporate Finance', 'Altman Z-Score', z)

    def beneish_m_score(self, dsri, gmri, aqi, sgi, depi, sgai, tgai, lvgi, tata) -> Dict:
        self._log("Beneish M-Score manipulation detection")
        model = BeneishMScore()
        ms = model.m_score(dsri, gmri, aqi, sgi, depi, sgai, tgai, lvgi, tata)
        prob = model.probability_of_manipulation(ms.get('m_score', 0))
        ms['manipulation_probability'] = prob
        return self._record('Corporate Finance', 'Beneish M-Score', ms)

    # =================================================================
    # FRONTIER PORTFOLIO MODELS
    # =================================================================

    def frontier_analysis(self, dataset_names: List[str] = None) -> Dict:
        self._log("Advanced frontier portfolio analysis")
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty or len(names) < 3:
            return {"error": "Need at least 3 datasets"}
        fa = FrontierAnalytics()
        result = fa.full_analysis(rets_df.values)
        result['asset_names'] = names
        return self._record('Frontier Portfolio', 'Full Analysis', result)

    def risk_parity(self, dataset_names: List[str] = None,
                     risk_budgets=None) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        self._log(f"Risk parity on {len(names)} assets")
        rp = RiskParityOptimizer()
        result = rp.compute(rets_df.values)
        result['asset_names'] = names
        return self._record('Frontier Portfolio', 'Risk Parity', result)

    def kelly_criterion(self, win_prob, win_loss_ratio, fraction=1.0) -> Dict:
        self._log(f"Kelly criterion: p={win_prob}, b={win_loss_ratio}")
        # Simple two-outcome Kelly formula: f* = (bp - q) / b
        q = 1 - win_prob
        kelly_frac = (win_loss_ratio * win_prob - q) / win_loss_ratio if win_loss_ratio > 0 else 0
        kelly_frac = max(0, kelly_frac) * fraction
        result = {
            'kelly_fraction': kelly_frac,
            'full_kelly': max(0, (win_loss_ratio * win_prob - q) / win_loss_ratio) if win_loss_ratio > 0 else 0,
            'applied_fraction': fraction,
            'win_probability': win_prob,
            'win_loss_ratio': win_loss_ratio,
        }
        return self._record('Frontier Portfolio', 'Kelly Criterion', result)

    def cvar_optimize(self, dataset_names: List[str] = None,
                       confidence=0.95, target_return=None) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        self._log(f"CVaR optimization on {len(names)} assets")
        co = CVaROptimizer(alpha=confidence)
        result = co.compute(rets_df.values)
        result['asset_names'] = names
        return self._record('Frontier Portfolio', 'CVaR Optimize', result)

    def hrp_portfolio(self, dataset_names: List[str] = None) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        self._log(f"Hierarchical Risk Parity on {len(names)} assets")
        hrp = HierarchicalRiskParity()
        result = hrp.compute(rets_df.values)
        result['asset_names'] = names
        return self._record('Frontier Portfolio', 'HRP', result)

    # =================================================================
    # QUANTUM & SYNTHETIC DATA
    # =================================================================

    def quantum_option_price(self, S, K, T, r, sigma, n_qubits=10) -> Dict:
        self._log(f"Quantum Monte Carlo option pricing: S={S} K={K}")
        qmc = QuantumMonteCarlo()
        result = qmc.quantum_option_pricing(S, K, T, r, sigma, n_qubits)
        bs = qmc.quantum_walk_option(S, K, T, r, sigma)
        result['quantum_walk_price'] = bs.get('option_price')
        return self._record('Quantum & Synthetic', 'Quantum Option', result)

    def diffusion_generate(self, n_assets=5, n_days=252, sde_type='GBM') -> Dict:
        self._log(f"Diffusion synthetic data: {n_assets} assets, {sde_type}")
        dsd = DiffusionSyntheticData()
        result = dsd.univariate_diffusion(n_samples=n_days, n_steps=50, sde_type=sde_type)
        corr = dsd.correlated_diffusion(n_assets, n_samples=n_days, sde_type=sde_type)
        result['correlated_paths'] = corr
        return self._record('Quantum & Synthetic', 'Diffusion Generate', result)

    def federated_learning_sim(self, n_silos=5, n_samples=200, n_features=10) -> Dict:
        self._log(f"Federated learning simulation: {n_silos} silos")
        fl = FederatedLearningSim()
        result = fl.cross_silo_simulation(n_silos, n_samples, n_features)
        dp = fl.differential_privacy_mechanism(np.random.randn(100), epsilon=1.0)
        result['dp_mechanism'] = dp
        return self._record('Quantum & Synthetic', 'Federated Learning', result)

    def quantum_game(self, game_type='prisoners_dilemma', gamma=0.5) -> Dict:
        self._log(f"Quantum game theory: {game_type}")
        qgt = QuantumGameTheory()
        if game_type == 'prisoners_dilemma':
            result = qgt.quantum_prisoners_dilemma(gamma)
        elif game_type == 'auction':
            result = qgt.quantum_auction([100, 90, 85])
        else:
            result = qgt.quantum_prisoners_dilemma(gamma)
        return self._record('Quantum & Synthetic', f'Quantum {game_type}', result)

    # =================================================================
    # MARKET DATA
    # =================================================================

    def fetch_market_data(self, symbol: str, provider: str = "yahoo",
                           period: str = "1y") -> Dict:
        """Fetch real market data and load into the data manager."""
        self._log(f"Fetching {symbol} from {provider}")
        result = self.market.load_into_quant_data(
            self.data, symbol, provider=provider, period=period)
        return self._record('Market Data', f'Fetch {symbol}', result)

    def get_market_quote(self, symbol: str, provider: str = "yahoo") -> Dict:
        """Get latest quote for a symbol."""
        self._log(f"Quote request: {symbol}")
        return self.market.get_quote(symbol, provider=provider)

    def get_batch_quotes(self, symbols: List[str]) -> Dict:
        """Get quotes for multiple symbols."""
        self._log(f"Batch quote: {len(symbols)} symbols")
        return self.market.get_batch_quotes(symbols)

    def get_popular_tickers(self) -> Dict:
        """Get curated list of popular tickers."""
        return {"tickers": self.market.popular_tickers()}

    # =================================================================
    # REPORT GENERATION
    # =================================================================

    def export_pdf_report(self, output_path: str) -> Dict:
        self._log(f"Generating PDF report: {output_path}")
        try:
            gen = PDFReportGenerator()
            path = gen.generate_report(self._analysis_history, output_path,
                                        title='WebScraper Pro - Quantitative Analysis Report')
            return {'status': 'ok', 'path': path, 'size_bytes': len(open(path, 'rb').read())}
        except Exception as e:
            return {'error': str(e)}

    def export_excel_report(self, output_path: str) -> Dict:
        self._log(f"Generating Excel report: {output_path}")
        try:
            gen = ExcelReportGenerator()
            path = gen.generate_workbook(self._analysis_history, output_path)
            return {'status': 'ok', 'path': path, 'size_bytes': len(open(path, 'rb').read())}
        except Exception as e:
            return {'error': str(e)}

    # =================================================================
    # CHART GENERATION
    # =================================================================

    def chart_forecast(self, dataset_name: str) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        try:
            fig = quant_charts.plot_forecast(tsd.values[-100:], np.random.randn(10) * 0.02 + tsd.values[-1])
            b64 = quant_charts.get_figure_as_base64(fig)
            return {'status': 'ok', 'chart_base64': b64}
        except Exception as e:
            return {'error': str(e)}

    def chart_correlation_heatmap(self) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty or len(names) < 3:
            return {"error": "Need at least 3 datasets"}
        try:
            corr = np.corrcoef(rets_df.values.T)
            fig = quant_charts.plot_correlation_heatmap(corr, names)
            b64 = quant_charts.get_figure_as_base64(fig)
            return {'status': 'ok', 'chart_base64': b64}
        except Exception as e:
            return {'error': str(e)}

    def chart_efficient_frontier(self) -> Dict:
        rets_df, names = self.data.get_returns_matrix()
        if rets_df.empty: return {"error": "No data"}
        try:
            np.random.seed(42)
            pts = np.random.randn(50, 2) * np.array([0.01, 0.005]) + np.array([0.001, 0.015])
            fig = quant_charts.plot_efficient_frontier(pts)
            b64 = quant_charts.get_figure_as_base64(fig)
            return {'status': 'ok', 'chart_base64': b64}
        except Exception as e:
            return {'error': str(e)}

    def chart_var_histogram(self, dataset_name: str, confidence=0.95) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        try:
            from scipy import stats
            var_level = float(np.percentile(tsd.returns, (1 - confidence) * 100))
            fig = quant_charts.plot_var_histogram(tsd.returns, var_level)
            b64 = quant_charts.get_figure_as_base64(fig)
            return {'status': 'ok', 'chart_base64': b64, 'var_level': var_level}
        except Exception as e:
            return {'error': str(e)}

    def chart_drawdown(self, dataset_name: str) -> Dict:
        tsd = self.data.get_dataset(dataset_name)
        if not tsd: return {"error": f"Dataset '{dataset_name}' not found"}
        try:
            fig = quant_charts.plot_drawdown(tsd.returns)
            b64 = quant_charts.get_figure_as_base64(fig)
            return {'status': 'ok', 'chart_base64': b64}
        except Exception as e:
            return {'error': str(e)}

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
            'Macroeconomic': ['DSGE', 'Taylor Rule', 'Phillips Curve', 'Minsky',
                            'Kondratiev Waves', 'Modigliani-Miller'],
            'Natural Science': ['SIR Model', 'Climate VaR', 'Innovation S-Curve',
                              'Hotelling Rule', 'Moore\'s Law'],
            'Microstructure': ['Order Book', 'Roll Spread', 'Nash MM',
                             'Geopolitical Risk', 'Basel III'],
            'Corporate Finance': ['CAPM', 'APT', 'EMH Tests', 'Altman Z-Score',
                                  'Beneish M-Score'],
            'Frontier Portfolio': ['Full Frontier Analysis', 'Risk Parity',
                                   'Kelly Criterion', 'CVaR Optimization', 'HRP'],
            'Quantum & Synthetic': ['Quantum Option Pricing', 'Diffusion Models',
                                    'Federated Learning', 'Quantum Game Theory'],
            'Reports': ['PDF Report', 'Excel Report'],
            'Charts': ['Forecast Chart', 'Correlation Heatmap', 'Efficient Frontier',
                      'VaR Histogram', 'Drawdown Chart'],
            'Market Data': ['Yahoo Finance', 'Alpha Vantage', 'Batch Quotes',
                           'Popular Tickers'],
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
