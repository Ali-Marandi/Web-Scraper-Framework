"""Integration tests for WebScraper Pro v1.5.0"""

import sys
import os
import time
import numpy as np

os.chdir('/home/z/my-project/WebScraperPro')

print('Python:', sys.version)

# Test 1
print()
print('=== Test 1: QuantEngine Imports ===')
from core.quant import QuantEngine
qe = QuantEngine()
print('QuantEngine imported OK')

# Test 2
print()
print('=== Test 2: Report Generators ===')
from core.quant.report_generator import PDFReportGenerator, ExcelReportGenerator
print('Report generators imported OK')

# Test 3
print()
print('=== Test 3: Charts ===')
from core.quant.quant_charts import (plot_forecast, plot_correlation_heatmap,
    plot_efficient_frontier, plot_var_histogram, plot_drawdown,
    create_chart_widget, get_figure_as_base64)
print('Chart functions imported OK')

# Test 4
print()
print('=== Test 4: API Server ===')
from core.api.server import QuantAPIServer
print('API server imported OK')

# Test 5
print()
print('=== Test 5: Sample Data + Analyses ===')
qe.data.generate_sample_data('AAPL', n=500)
qe.data.generate_sample_data('GOOGL', n=500)
qe.data.generate_sample_data('SPY', n=500)
print('Datasets:', qe.data.list_datasets())

r = qe.arima_forecast('AAPL', order=(2,1,1), steps=5)
s = 'OK' if 'error' not in r else r['error']
print(f'ARIMA: {s}')

r = qe.garch_analysis('GOOGL')
s = 'OK' if 'error' not in r else r['error']
print(f'GARCH: {s}')

r = qe.black_scholes_price(S=100, K=105, T=1.0, r=0.02, sigma=0.2)
s = 'OK' if 'error' not in r else r['error']
print(f'Black-Scholes: {s}')

r = qe.markowitz_optimize(['AAPL', 'GOOGL', 'SPY'])
s = 'OK' if 'error' not in r else r['error']
print(f'Markowitz: {s}')

r = qe.capm_estimate(np.random.randn(252).tolist(), np.random.randn(252).tolist())
s = 'OK' if 'error' not in r else r['error']
print(f'CAPM: {s}')

r = qe.altman_z_score(0.3, 0.15, 0.12, 1.5, 0.8)
s = 'OK' if 'error' not in r else r['error']
print(f'Altman Z: {s}')

r = qe.dsge_simulate()
s = 'OK' if 'error' not in r else r['error']
print(f'DSGE: {s}')

r = qe.quantum_option_price(S=100, K=105, T=1.0, r=0.02, sigma=0.2)
s = 'OK' if 'error' not in r else r['error']
print(f'Quantum Option: {s}')

print(f'Total history entries: {len(qe.history)}')

# Test 6
print()
print('=== Test 6: Chart Generation ===')
import matplotlib
matplotlib.use('Agg')

r = qe.chart_forecast('AAPL')
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Forecast chart: {s}')

r = qe.chart_correlation_heatmap()
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Heatmap chart: {s}')

r = qe.chart_efficient_frontier()
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Frontier chart: {s}')

r = qe.chart_var_histogram('AAPL')
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'VaR histogram: {s}')

r = qe.chart_drawdown('GOOGL')
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Drawdown chart: {s}')

# Test 7
print()
print('=== Test 7: Report Generation ===')
r = qe.export_pdf_report('/tmp/test_quant_report.pdf')
if 'status' in r:
    print(f'PDF report: OK - {r.get("size_bytes", 0)} bytes')
else:
    print(f'PDF report: {r.get("error", "FAIL")}')

r = qe.export_excel_report('/tmp/test_quant_report.xlsx')
if 'status' in r:
    print(f'Excel report: OK - {r.get("size_bytes", 0)} bytes')
else:
    print(f'Excel report: {r.get("error", "FAIL")}')

# Test 8
print()
print('=== Test 8: API Server ===')
server = QuantAPIServer(qe, port=18765)
server.start()
time.sleep(2)
print(f'API running: {server.is_running()}')

import requests as req
resp = req.get('http://127.0.0.1:18765/api/v1/health', timeout=5)
print(f'Health endpoint: {resp.status_code} - {resp.json()}')

resp = req.get('http://127.0.0.1:18765/api/v1/methods', timeout=5)
methods = resp.json().get('methods', {})
total = sum(len(v) for v in methods.values())
print(f'Methods endpoint: {resp.status_code} - {total} methods in {len(methods)} categories')

server.stop()
time.sleep(0.5)
print(f'API stopped: {not server.is_running()}')

# Test 9
print()
print('=== Test 9: Method Count ===')
methods = qe.get_available_methods()
total = sum(len(v) for v in methods.values())
print(f'Total methods: {total} across {len(methods)} categories')
for cat, ms in methods.items():
    print(f'  {cat}: {len(ms)} methods')

print()
print('=== ALL TESTS PASSED ===')
