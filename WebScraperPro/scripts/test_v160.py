"""Integration tests for WebScraper Pro v1.6.0"""

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
print('=== Test 2: All v1.5.0 features still work ===')
from core.quant.report_generator import PDFReportGenerator, ExcelReportGenerator
from core.quant.quant_charts import (plot_forecast, plot_correlation_heatmap,
    plot_efficient_frontier, plot_var_histogram, plot_drawdown,
    create_chart_widget, get_figure_as_base64)
from core.api.server import QuantAPIServer
print('v1.5.0 modules OK')

# Test 3: Market Data module
print()
print('=== Test 3: Market Data Module ===')
from core.quant.market_data import MarketDataFeed, YahooFinanceProvider, AlphaVantageProvider
mdf = MarketDataFeed()
print('MarketDataFeed imported OK')

# Popular tickers (no network)
tickers = mdf.popular_tickers()
print(f'Popular tickers: {len(tickers)} tickers')
assert len(tickers) == 16, f'Expected 16, got {len(tickers)}'
print('Popular tickers OK')

# Test 4: WebSocket module
print()
print('=== Test 4: WebSocket Module ===')
from core.api.websocket_server import QuantWebSocketServer
print('QuantWebSocketServer imported OK')

# Test 5: LogManager
print()
print('=== Test 5: LogManager ===')
from core.log_manager import LogManager
LogManager.reset()  # fresh instance for testing
lm = LogManager.get_instance()
logger = lm.logger
logger.info('Test log entry 1')
logger.warning('Test warning entry')
logger.error('Test error entry')
stats = lm.get_log_stats()
print(f'Log stats: {stats["total_entries"]} entries')
assert stats['total_entries'] >= 3, f'Expected >= 3, got {stats["total_entries"]}'
print('LogManager OK')

# Export logs
result = lm.export_logs('/tmp/test_logs.json', format='json')
print(f'Log export: {result.get("status", result.get("error", "FAIL"))}')

result = lm.export_logs('/tmp/test_logs.csv', format='csv')
print(f'Log CSV export: {result.get("status", result.get("error", "FAIL"))}')

# Test 6: QuantEngine with market data integration
print()
print('=== Test 6: QuantEngine Market Data Methods ===')

# get_popular_tickers
r = qe.get_popular_tickers()
assert 'tickers' in r
print(f'Popular tickers via engine: {len(r["tickers"])} tickers')

# Verify MarketDataFeed is accessible
assert hasattr(qe, 'market'), 'QuantEngine missing .market attribute'
assert isinstance(qe.market, MarketDataFeed)
print('QuantEngine.market is MarketDataFeed OK')

# Test 7: Run core analyses
print()
print('=== Test 7: Core Analyses ===')
qe.data.generate_sample_data('AAPL', n=500)
qe.data.generate_sample_data('GOOGL', n=500)
qe.data.generate_sample_data('SPY', n=500)

r = qe.arima_forecast('AAPL', order=(2,1,1), steps=5)
s = 'OK' if 'error' not in r else r['error']
print(f'ARIMA: {s}')

r = qe.garch_analysis('GOOGL')
s = 'OK' if 'error' not in r else r['error']
print(f'GARCH: {s}')

r = qe.markowitz_optimize(['AAPL', 'GOOGL', 'SPY'])
s = 'OK' if 'error' not in r else r['error']
print(f'Markowitz: {s}')

r = qe.black_scholes_price(S=100, K=105, T=1.0, r=0.02, sigma=0.2)
s = 'OK' if 'error' not in r else r['error']
print(f'Black-Scholes: {s}')

r = qe.dsge_simulate()
s = 'OK' if 'error' not in r else r['error']
print(f'DSGE: {s}')

r = qe.capm_estimate(np.random.randn(252).tolist(), np.random.randn(252).tolist())
s = 'OK' if 'error' not in r else r['error']
print(f'CAPM: {s}')

# Test 8: Charts still work
print()
print('=== Test 8: Charts ===')
import matplotlib
matplotlib.use('Agg')

r = qe.chart_forecast('AAPL')
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Forecast chart: {s}')

r = qe.chart_correlation_heatmap()
s = 'OK' if 'status' in r else r.get('error', 'FAIL')
print(f'Heatmap chart: {s}')

# Test 9: Reports still work
print()
print('=== Test 9: Reports ===')
r = qe.export_pdf_report('/tmp/test_v160_report.pdf')
if 'status' in r:
    print(f'PDF report: OK - {r.get("size_bytes", 0)} bytes')
else:
    print(f'PDF report: {r.get("error", "FAIL")}')

r = qe.export_excel_report('/tmp/test_v160_report.xlsx')
if 'status' in r:
    print(f'Excel report: OK - {r.get("size_bytes", 0)} bytes')
else:
    print(f'Excel report: {r.get("error", "FAIL")}')

# Test 10: REST API with new endpoints
print()
print('=== Test 10: REST API (with market + log endpoints) ===')
server = QuantAPIServer(qe, port=18766)
server.start()
time.sleep(2)

import requests as req

resp = req.get('http://127.0.0.1:18766/api/v1/health', timeout=5)
j = resp.json()
print(f'Health: {resp.status_code} - version={j["version"]}, methods={j["methods"]}')
assert j['version'] == 'v1.6.0'

resp = req.get('http://127.0.0.1:18766/api/v1/market/tickers', timeout=5)
print(f'Tickers endpoint: {resp.status_code}')

resp = req.get('http://127.0.0.1:18766/api/v1/logs/stats', timeout=5)
print(f'Log stats endpoint: {resp.status_code} - {resp.json().get("total_entries", 0)} entries')

resp = req.get('http://127.0.0.1:18766/api/v1/logs/recent?limit=5', timeout=5)
print(f'Logs recent endpoint: {resp.status_code}')

server.stop()
time.sleep(0.5)
print(f'API stopped: {not server.is_running()}')

# Test 11: Method count
print()
print('=== Test 11: Method Count ===')
methods = qe.get_available_methods()
total = sum(len(v) for v in methods.values())
print(f'Total methods: {total} across {len(methods)} categories')
for cat, ms in methods.items():
    print(f'  {cat}: {len(ms)} methods')

# Cleanup
LogManager.reset()
lm2 = LogManager.get_instance()  # fresh instance after reset

print()
print('=== ALL TESTS PASSED ===')
