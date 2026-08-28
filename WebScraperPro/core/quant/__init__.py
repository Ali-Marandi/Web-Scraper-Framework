"""
WebScraper Pro - Quantitative Finance Engine
Comprehensive quantitative finance analytics layer that processes scraped data
through 30+ methodologies across time series, financial engineering, portfolio
optimization, machine learning, graph theory, fuzzy logic, and advanced methods.
"""

from .quant_engine import QuantEngine
from .data_manager import QuantDataManager, TimeSeriesData

__all__ = ["QuantEngine", "QuantDataManager", "TimeSeriesData"]
