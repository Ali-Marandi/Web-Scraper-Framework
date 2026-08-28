#!/usr/bin/env python3
"""WebScraper Pro v1.4.0 — Integration test for all new quant modules."""

import sys
import traceback
import numpy as np

passed = 0
failed = 0
tests = []

def run_test(name, fn):
    global passed, failed
    try:
        result = fn()
        if isinstance(result, dict) and 'error' in result:
            tests.append((name, False, result['error']))
            failed += 1
            print(f"  FAIL {name}: {result['error']}")
        else:
            tests.append((name, True, None))
            passed += 1
            print(f"  PASS {name}")
    except Exception as e:
        tests.append((name, False, str(e)))
        failed += 1
        print(f"  FAIL {name}: {e}")
        traceback.print_exc()

print("=" * 60)
print("WebScraper Pro v1.4.0 — Integration Tests")
print("=" * 60)

# ============================================================
# 1. Import all modules
# ============================================================
print("\n--- Module Imports ---")

run_test("Import corporate_finance", lambda: __import__('core.quant.corporate_finance', fromlist=['CAPMModel']))
run_test("Import frontier_models", lambda: __import__('core.quant.frontier_models', fromlist=['FrontierAnalytics']))
run_test("Import quantum_synthetic", lambda: __import__('core.quant.quantum_synthetic', fromlist=['QuantumMonteCarlo']))
run_test("Import QuantEngine", lambda: __import__('core.quant.quant_engine', fromlist=['QuantEngine']))

# ============================================================
# 2. Corporate Finance Tests
# ============================================================
print("\n--- Corporate Finance ---")
from core.quant.corporate_finance import CAPMModel, APTModel, EMHTester, AltmanZScore, BeneishMScore

np.random.seed(42)
n = 252
asset_rets = np.random.normal(0.001, 0.02, n)
mkt_rets = np.random.normal(0.0005, 0.015, n)
prices = 100 * np.cumprod(1 + asset_rets)

run_test("CAPM Estimate", lambda: CAPMModel().estimate(asset_rets, mkt_rets, 0.02))
run_test("CAPM Rolling Beta", lambda: CAPMModel().rolling_beta(asset_rets, mkt_rets, 60))
run_test("CAPM Fama-French 3", lambda: CAPMModel().fama_french_3factor(asset_rets, np.random.randn(n), np.random.randn(n), mkt_rets, 0.02))

factors = np.random.randn(n, 3)
run_test("APT Estimate", lambda: APTModel().estimate(asset_rets, factors))
# APT factor_analysis needs 2D array (multi-asset)
multi_asset = np.random.randn(n, 5)
run_test("APT Factor Analysis", lambda: APTModel().factor_analysis(multi_asset, 3))

run_test("EMH Runs Test", lambda: EMHTester().runs_test(asset_rets))
run_test("EMH Autocorrelation", lambda: EMHTester().autocorrelation_test(asset_rets))
run_test("EMH Variance Ratio", lambda: EMHTester().variance_ratio_test(asset_rets))
run_test("EMH ADF", lambda: EMHTester().engle_granger_adf(prices))
run_test("EMH Summary", lambda: EMHTester().summary(asset_rets, prices))

run_test("Altman Z Manufacturing", lambda: AltmanZScore().manufacturing(0.3, 0.4, 0.15, 1.2, 2.0))
run_test("Altman Z Private", lambda: AltmanZScore().private_non_manufacturing(0.3, 0.4, 0.15, 1.2, 2.0))
run_test("Altman Z Emerging", lambda: AltmanZScore().emerging_markets(0.3, 0.4, 0.15, 1.2, 2.0))
run_test("Altman Interpret", lambda: AltmanZScore().interpret(3.5, 'manufacturing'))
run_test("Altman Bond Equiv", lambda: AltmanZScore().bond_equivalent(1.8, 'manufacturing'))

run_test("Beneish M-Score", lambda: BeneishMScore().m_score(1.0, 1.1, 1.0, 1.2, 0.9, 1.05, 0.95, 1.1, -0.04))
run_test("Beneish Probability", lambda: BeneishMScore().probability_of_manipulation(-1.5))

# ============================================================
# 3. Frontier Portfolio Tests
# ============================================================
print("\n--- Frontier Portfolio ---")
from core.quant.frontier_models import (FrontierAnalytics, RiskParityOptimizer,
                                        KellyCriterion, CVaROptimizer,
                                        HierarchicalRiskParity)

np.random.seed(123)
n_assets = 5
n_obs = 500
rets_matrix = np.random.randn(n_obs, n_assets) * 0.02 + 0.0005
names = [f"Asset_{i}" for i in range(n_assets)]

run_test("Frontier Full Analysis", lambda: FrontierAnalytics().full_analysis(rets_matrix))
run_test("Risk Parity", lambda: RiskParityOptimizer().compute(rets_matrix))
run_test("Kelly Criterion (portfolio)", lambda: KellyCriterion().compute(rets_matrix))
run_test("CVaR Optimize", lambda: CVaROptimizer().compute(rets_matrix))
run_test("HRP Portfolio", lambda: HierarchicalRiskParity().compute(rets_matrix))

# ============================================================
# 4. Quantum & Synthetic Tests
# ============================================================
print("\n--- Quantum & Synthetic ---")
from core.quant.quantum_synthetic import (QuantumMonteCarlo, DiffusionSyntheticData,
                                           FederatedLearningSim, QuantumGameTheory)

run_test("Quantum Option Pricing", lambda: QuantumMonteCarlo().quantum_option_pricing(100, 105, 1.0, 0.02, 0.2))
run_test("Quantum Walk Option", lambda: QuantumMonteCarlo().quantum_walk_option(100, 105, 1.0, 0.02, 0.2))
run_test("VQE Eigenvalue", lambda: QuantumMonteCarlo().variational_eigenvalue(5, 3, 50))

run_test("Diffusion OU", lambda: DiffusionSyntheticData().univariate_diffusion(100, 50, 0.1, 'OU'))
run_test("Diffusion GBM", lambda: DiffusionSyntheticData().univariate_diffusion(100, 50, 0.2, 'GBM'))
run_test("Diffusion CIR", lambda: DiffusionSyntheticData().univariate_diffusion(100, 50, 0.1, 'CIR'))
run_test("Correlated Diffusion", lambda: DiffusionSyntheticData().correlated_diffusion(5, 100))
run_test("Score Matching", lambda: DiffusionSyntheticData().score_matching(np.random.randn(200)))
run_test("Generate Realistic Prices", lambda: DiffusionSyntheticData().generate_realistic_prices(5, 252))

run_test("Federated OLS", lambda: FederatedLearningSim().federated_ols(
    [np.random.randn(100,3) for _ in range(5)],
    [np.random.randn(100) for _ in range(5)], 5))
run_test("Federated PCA", lambda: FederatedLearningSim().federated_pca(
    [np.random.randn(100,5) for _ in range(5)], 3, 5))
run_test("Differential Privacy", lambda: FederatedLearningSim().differential_privacy_mechanism(np.random.randn(100), 1.0))
run_test("Secure Aggregation", lambda: FederatedLearningSim().secure_aggregation([np.random.randn(5) for _ in range(5)]))
run_test("Cross-Silo Sim", lambda: FederatedLearningSim().cross_silo_simulation(3, 100, 5, 5))

run_test("Quantum Prisoners Dilemma", lambda: QuantumGameTheory().quantum_prisoners_dilemma(0.5))
run_test("Quantum Auction", lambda: QuantumGameTheory().quantum_auction([100, 90, 85]))

# ============================================================
# 5. QuantEngine Bridge Tests
# ============================================================
print("\n--- QuantEngine Bridges ---")
from core.quant.quant_engine import QuantEngine

engine = QuantEngine()

# Load sample data
engine.data.generate_sample_data('AAPL')
engine.data.generate_sample_data('GOOGL')
engine.data.generate_sample_data('SPY')

run_test("Engine CAPM", lambda: engine.capm_estimate(list(asset_rets), list(mkt_rets), 0.02))
run_test("Engine EMH", lambda: engine.emh_test(list(asset_rets), list(prices)))
run_test("Engine Altman Z", lambda: engine.altman_z_score(0.3, 0.4, 0.15, 1.2, 2.0))
run_test("Engine Beneish M", lambda: engine.beneish_m_score(1.0, 1.1, 1.0, 1.2, 0.9, 1.05, 0.95, 1.1, -0.04))
run_test("Engine Frontier Analysis", lambda: engine.frontier_analysis())
run_test("Engine Risk Parity", lambda: engine.risk_parity())
run_test("Engine Kelly", lambda: engine.kelly_criterion(0.55, 2.0, 0.5))
run_test("Engine CVaR Optimize", lambda: engine.cvar_optimize(confidence=0.95))
run_test("Engine HRP", lambda: engine.hrp_portfolio())
run_test("Engine Quantum Option", lambda: engine.quantum_option_price(100, 105, 1.0, 0.02, 0.2))
run_test("Engine Diffusion", lambda: engine.diffusion_generate(n_assets=3, n_days=100))
run_test("Engine Federated", lambda: engine.federated_learning_sim(n_silos=3, n_samples=50, n_features=5))
run_test("Engine Quantum Game", lambda: engine.quantum_game('prisoners_dilemma', 0.5))
run_test("Engine Epidemic Stress", lambda: engine.epidemic_market_stress(list(asset_rets), list(np.abs(np.random.randn(n)))))

# ============================================================
# 6. get_available_methods
# ============================================================
print("\n--- Available Methods ---")
methods = engine.get_available_methods()
total = sum(len(v) for v in methods.values())
print(f"  Total categories: {len(methods)}")
print(f"  Total methods: {total}")
for cat, mlist in methods.items():
    print(f"    {cat}: {len(mlist)} methods")
run_test("Methods > 50", lambda: {'ok': total} if total > 50 else {'error': f'Only {total} methods'})

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
print("=" * 60)

if failed > 0:
    print("\nFailed tests:")
    for name, ok, err in tests:
        if not ok:
            print(f"  - {name}: {err[:80]}")

sys.exit(0 if failed == 0 else 1)
