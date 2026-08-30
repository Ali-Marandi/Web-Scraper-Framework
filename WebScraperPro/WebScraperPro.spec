# -*- mode: python ; coding: utf-8 -*-
"""
WebScraper Pro v1.6.0 — PyInstaller build specification
Optimized for Windows desktop EXE with full quant finance engine.
"""

import os
import sys

block_cipher = None

# Quant engine sub-modules (explicit hidden imports for reliable packaging)
_quant_modules = [
    'core.quant',
    'core.quant.data_manager',
    'core.quant.time_series',
    'core.quant.financial_engineering',
    'core.quant.portfolio',
    'core.quant.machine_learning',
    'core.quant.graph_analysis',
    'core.quant.fuzzy_logic',
    'core.quant.advanced_methods',
    'core.quant.quant_engine',
    'core.quant.macro_models',
    'core.quant.natural_science_models',
    'core.quant.market_microstructure',
    'core.quant.corporate_finance',
    'core.quant.frontier_models',
    'core.quant.quantum_synthetic',
    'core.quant.report_generator',
    'core.quant.quant_charts',
    'core.api',
    'core.api.server',
    'core.api.websocket_server',
    'core.quant.market_data',
    'core.log_manager',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('/usr/share/fonts/truetype/chinese', 'fonts/chinese'),
    ],
    hiddenimports=[
        # Core UI
        'customtkinter',
        # Web scraping
        'requests',
        'bs4',
        'lxml',
        'lxml.etree',
        'openpyxl',
        'playwright',
        'playwright.async_api',
        # Quant engine dependencies
        'numpy',
        'pandas',
        'scipy',
        'scipy.linalg',
        'scipy.stats',
        'scipy.optimize',
        'scipy.signal',
        'scipy.sparse',
        'scipy.sparse.linalg',
        'scipy.integrate',
        'scipy.cluster',
        'scipy.cluster.hierarchy',
        # Charts & Reports
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        # REST API
        'flask',
        'flask.json',
        'jinja2',
        'markupsafe',
        # Market Data
        'yfinance',
        'yfinance.base',
        'yfinance.ticker',
        # WebSocket
        'websockets',
        'websockets.server',
        'websockets.legacy',
        'websockets.legacy.server',
        'asyncio',
    ] + _quant_modules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test/doc modules
        'tkinter.test',
        'unittest',
        'pydoc',
        'doctest',
        'pdb',
        # Heavy unused ML frameworks (not needed — we use pure numpy)
        'torch',
        'tensorflow',
        'sklearn',
        'statsmodels',
        'arch',
        'pmdarima',
        'prophet',
        'xgboost',
        'lightgbm',
        'catboost',
        # Jupyter/IPython
        'IPython',
        'jupyter',
        'notebook',
        'nbconvert',
        # Other unnecessary packages
        'pylint',
        'flake8',
        'pytest',
        'sphinx',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WebScraperPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # Exclude UPX compression for scipy DLLs (causes issues on Windows)
        'libscipy*.dll',
        'numpy*.dll',
    ],
    console=False,
    icon='assets/icons/app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'libscipy*.dll',
        'numpy*.dll',
    ],
    name='WebScraperPro',
)
