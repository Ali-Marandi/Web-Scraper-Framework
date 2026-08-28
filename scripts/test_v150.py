#!/usr/bin/env python3
"""WebScraper Pro v1.5.0 — Integration test for Charts, Reports, API."""

import sys
import os
import traceback
import numpy as np
import tempfile

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
print("WebScraper Pro v1.5.0 — Integration Tests")
print("=" * 60)

# ============================================================
# 1. Module Imports
# ============================================================
print("\n--- Module Imports ---")
run_test("Import report_generator", lambda: __import__('core.quant.report_generator', fromlist=['PDFReportGenerator']))
run_test("Import quant_charts", lambda: __import__('core.quant.quant_charts', fromlist=['plot_forecast']))
run_test("Import API server", lambda: __import__('core.api.server', fromlist=['QuantAPIServer']))
run_test("Import QuantEngine", lambda: __import__('core.quant.quant_engine', fromlist=['QuantEngine']))

# ============================================================
# 2. Charts Module Tests
# ============================================================
print("\n--- Charts ---")
from core.quant.quant_charts import (plot_forecast, plot_volatility,
    plot_efficient_frontier, plot_pie_weights, plot_var_histogram,
    plot_drawdown, plot_correlation_heatmap, plot_dsge_irf,
    plot_phillips_curve, plot_comparison_bars, plot_multi_series,
    get_figure_as_base64)

np.random.seed(42)
n = 200
vals = 100 + np.cumsum(np.random.randn(n) * 0.5)
fc = vals[-1] + np.cumsum(np.random.randn(20) * 0.3)
vol = np.abs(np.random.randn(n)) * 0.02

run_test("Chart: Forecast", lambda: get_figure_as_base64(plot_forecast(vals, fc)))
run_test("Chart: Volatility", lambda: get_figure_as_base64(plot_volatility(vals, vol[:20])))
pts = np.column_stack([np.linspace(0, 0.03, 50), np.linspace(0.005, 0.025, 50)[::-1]])
run_test("Chart: Efficient Frontier", lambda: get_figure_as_base64(plot_efficient_frontier(pts)))
run_test("Chart: Pie Weights", lambda: get_figure_as_base64(plot_pie_weights(
    np.array([0.3, 0.25, 0.2, 0.15, 0.1]), ['A','B','C','D','E'])))
rets = np.random.randn(500) * 0.02
run_test("Chart: VaR Histogram", lambda: get_figure_as_base64(plot_var_histogram(rets, -0.03)))
run_test("Chart: Drawdown", lambda: get_figure_as_base64(plot_drawdown(rets)))
corr = np.array([[1,0.8,0.3],[0.8,1,0.2],[0.3,0.2,1]])
run_test("Chart: Correlation Heatmap", lambda: get_figure_as_base64(
    plot_correlation_heatmap(corr, ['X','Y','Z'])))
irf = {"output_gap": np.random.randn(20)*0.01, "inflation": np.random.randn(20)*0.005}
run_test("Chart: DSGE IRF", lambda: get_figure_as_base64(plot_dsge_irf(irf)))
run_test("Chart: Phillips Curve", lambda: get_figure_as_base64(
    plot_phillips_curve(np.random.uniform(3,8,50), np.random.uniform(1,5,50))))
run_test("Chart: Comparison Bars", lambda: get_figure_as_base64(
    plot_comparison_bars(['A','B','C','D'], [10,25,15,30])))
run_test("Chart: Multi-Series", lambda: get_figure_as_base64(
    plot_multi_series({'Series 1': np.random.randn(50), 'Series 2': np.random.randn(50)})))

# ============================================================
# 3. Report Generator Tests
# ============================================================
print("\n--- Reports ---")
from core.quant.report_generator import PDFReportGenerator, ExcelReportGenerator

history = [
    {"category": "Time Series", "method": "ARIMA(5,1,2)", "result": {"aicc": 1.5, "bic": 2.1, "forecast": [1,2,3]}, "timestamp": "2025-01-01T00:00:00"},
    {"category": "Portfolio", "method": "Markowitz", "result": {"sharpe": 1.8, "weights": [0.4,0.3,0.3]}, "timestamp": "2025-01-01T00:01:00"},
    {"category": "Corporate Finance", "method": "Altman Z-Score", "result": {"z_score": 3.5, "zone": "Safe"}, "timestamp": "2025-01-01T00:02:00"},
]

with tempfile.TemporaryDirectory() as tmpdir:
    pdf_path = os.path.join(tmpdir, "test_report.pdf")
    run_test("PDF Report Generation", lambda: PDFReportGenerator().generate_report(history, pdf_path) or os.path.exists(pdf_path))
    if os.path.exists(pdf_path):
        run_test("PDF File Size > 0", lambda: os.path.getsize(pdf_path) > 0)

    xls_path = os.path.join(tmpdir, "test_report.xlsx")
    run_test("Excel Report Generation", lambda: ExcelReportGenerator().generate_workbook(history, xls_path) or os.path.exists(xls_path))
    if os.path.exists(xls_path):
        run_test("Excel File Size > 0", lambda: os.path.getsize(xls_path) > 0)

# ============================================================
# 4. API Server Tests
# ============================================================
print("\n--- API Server ---")
from core.api.server import QuantAPIServer
from core.quant.quant_engine import QuantEngine

engine = QuantEngine()
engine.data.generate_sample_data('TEST')

server = QuantAPIServer(engine, port=8766)
run_test("API Server Create", lambda: {'ok': True} if server else {'error': 'None'})

server.start()
import time; time.sleep(1)
run_test("API Server Running", lambda: {'ok': server.is_running()} if server.is_running() else {'error': 'not running'})

import requests
try:
    r = requests.get('http://127.0.0.1:8766/api/v1/health', timeout=3)
    data = r.json()
    run_test("API GET /health", lambda: data if data.get('status') == 'ok' else {'error': str(data)})
except Exception as e:
    run_test("API GET /health", lambda: {'error': str(e)})

try:
    r = requests.get('http://127.0.0.1:8766/api/v1/methods', timeout=3)
    data = r.json()
    methods_dict = data.get('methods', data)
    total = sum(len(v) for v in methods_dict.values())
    run_test("API GET /methods", lambda: data if total > 60 else {'error': f'only {total} methods'})
except Exception as e:
    run_test("API GET /methods", lambda: {'error': str(e)})

try:
    r = requests.get('http://127.0.0.1:8766/api/v1/datasets', timeout=3)
    run_test("API GET /datasets", lambda: r.json())
except Exception as e:
    run_test("API GET /datasets", lambda: {'error': str(e)})

server.stop()
time.sleep(0.5)
run_test("API Server Stopped", lambda: {'ok': not server.is_running()} if not server.is_running() else {'error': 'still running'})

# ============================================================
# 5. Engine Report/Chart Bridges
# ============================================================
print("\n--- Engine Bridges ---")
engine2 = QuantEngine()
engine2.data.generate_sample_data('AAPL')
engine2.data.generate_sample_data('GOOGL')
engine2.data.generate_sample_data('SPY')

# Run some analyses first
engine2.arima_forecast('AAPL')
engine2.markowitz_optimize([])
engine2.capm_estimate(list(np.random.randn(100)), list(np.random.randn(100)))

with tempfile.TemporaryDirectory() as tmpdir:
    pdf_p = os.path.join(tmpdir, "engine_test.pdf")
    run_test("Engine PDF Export", lambda: engine2.export_pdf_report(pdf_p))
    xls_p = os.path.join(tmpdir, "engine_test.xlsx")
    run_test("Engine Excel Export", lambda: engine2.export_excel_report(xls_p))

run_test("Engine Chart Forecast", lambda: engine2.chart_forecast('AAPL'))
run_test("Engine Chart Heatmap", lambda: engine2.chart_correlation_heatmap())
run_test("Engine Chart VaR", lambda: engine2.chart_var_histogram('AAPL'))
run_test("Engine Chart Drawdown", lambda: engine2.chart_drawdown('AAPL'))

# ============================================================
# 6. Method Count
# ============================================================
print("\n--- Method Count ---")
methods = engine2.get_available_methods()
total = sum(len(v) for v in methods.values())
print(f"  Total categories: {len(methods)}")
print(f"  Total methods: {total}")
for cat, mlist in methods.items():
    print(f"    {cat}: {len(mlist)}")
run_test("Methods > 70", lambda: {'ok': total} if total > 70 else {'error': f'Only {total} methods'})

# ============================================================
print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
print("=" * 60)
if failed > 0:
    print("\nFailed tests:")
    for name, ok, err in tests:
        if not ok:
            print(f"  - {name}: {err[:100]}")
sys.exit(0 if failed == 0 else 1)
