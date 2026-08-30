"""
QuantEngine REST API Server

Lightweight Flask-based HTTP API exposing the QuantEngine as a local service.
All analysis endpoints accept JSON, return JSON, and are wrapped in
try/except for safe error handling.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, Response

logger = logging.getLogger(__name__)


class QuantAPIServer:
    """Flask REST API wrapper around a QuantEngine instance.

    Parameters
    ----------
    quant_engine : object
        A QuantEngine instance that provides ``get_available_methods()``,
        ``history``, dataset loading / generation, and per-method analysis
        calls (``analyze_arima``, ``analyze_garch``, etc.).
    host : str, default ``'127.0.0.1'``
        Bind address for the Flask server.
    port : int, default ``8765``
        Bind port for the Flask server.
    """

    VERSION = "v1.6.0"
    METHOD_COUNT = 76

    def __init__(
        self,
        quant_engine: Any,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self._engine = quant_engine
        self._host = host
        self._port = port
        self._flask_app: Optional[Flask] = None
        self._thread: Optional[threading.Thread] = None
        self._shutdown_flag = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _create_app(self) -> Flask:
        """Build and configure the Flask application (deferred)."""
        app = Flask(__name__)
        app.config["JSON_SORT_KEYS"] = False

        # ----- CORS helper --------------------------------------------
        @app.after_request
        def _add_cors_headers(response: Response) -> Response:
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )
            return response

        # Handle preflight OPTIONS for every route
        @app.before_request
        def _handle_options() -> Optional[Response]:
            if request.method == "OPTIONS":
                resp = Response(status=204)
                resp.headers["Access-Control-Allow-Origin"] = "*"
                resp.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, OPTIONS"
                )
                resp.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization"
                )
                return resp
            return None

        # --------------------------------------------------------------
        # System endpoints
        # --------------------------------------------------------------
        @app.route("/api/v1/health", methods=["GET"])
        def health() -> tuple[Response, int]:
            return jsonify({
                "status": "ok",
                "version": self.VERSION,
                "methods": self.METHOD_COUNT,
            }), 200

        @app.route("/api/v1/methods", methods=["GET"])
        def list_methods() -> tuple[Response, int]:
            methods = self._engine.get_available_methods()
            return jsonify({"methods": methods}), 200

        # --------------------------------------------------------------
        # Data Management endpoints
        # --------------------------------------------------------------
        @app.route("/api/v1/datasets", methods=["GET"])
        def list_datasets() -> tuple[Response, int]:
            try:
                datasets = getattr(self._engine, "list_datasets", lambda: [])()
                if not datasets:
                    datasets = list(getattr(self._engine, "datasets", {}).keys())
                return jsonify({"datasets": datasets}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/datasets/generate", methods=["POST"])
        def generate_dataset() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                name = data.get("name", "SAMPLE")
                n = int(data.get("n", 500))
                result = self._engine.generate_sample_data(name=name, n=n)
                return jsonify({
                    "status": "generated",
                    "dataset": name,
                    "rows": n,
                    "result": result,
                }), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        # --------------------------------------------------------------
        # Analysis endpoints
        # --------------------------------------------------------------
        @app.route("/api/v1/analyze/arima", methods=["POST"])
        def analyze_arima() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                dataset = data.get("dataset")
                order = tuple(data.get("order", [5, 1, 2]))
                steps = int(data.get("steps", 10))
                result = self._engine.analyze_arima(
                    dataset=dataset, order=order, steps=steps
                )
                return jsonify({"method": "arima", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/garch", methods=["POST"])
        def analyze_garch() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                dataset = data.get("dataset")
                p = int(data.get("p", 1))
                q = int(data.get("q", 1))
                result = self._engine.analyze_garch(
                    dataset=dataset, p=p, q=q
                )
                return jsonify({"method": "garch", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/black-scholes", methods=["POST"])
        def analyze_black_scholes() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                S = float(data["S"])
                K = float(data["K"])
                T = float(data["T"])
                r = float(data["r"])
                sigma = float(data["sigma"])
                result = self._engine.analyze_black_scholes(
                    S=S, K=K, T=T, r=r, sigma=sigma
                )
                return jsonify({"method": "black-scholes", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/markowitz", methods=["POST"])
        def analyze_markowitz() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                method = data.get("method", "sharpe")
                result = self._engine.analyze_markowitz(method=method)
                return jsonify({"method": "markowitz", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/capm", methods=["POST"])
        def analyze_capm() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                returns = list(data["returns"])
                market_returns = list(data["market_returns"])
                rf = float(data.get("rf", 0.02))
                result = self._engine.analyze_capm(
                    returns=returns,
                    market_returns=market_returns,
                    rf=rf,
                )
                return jsonify({"method": "capm", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/altman-z", methods=["POST"])
        def analyze_altman_z() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                wc_ta = float(data["wc_ta"])
                re_ta = float(data["re_ta"])
                ebit_ta = float(data["ebit_ta"])
                mv_de = float(data["mv_de"])
                sales_ta = float(data["sales_ta"])
                result = self._engine.analyze_altman_z(
                    wc_ta=wc_ta,
                    re_ta=re_ta,
                    ebit_ta=ebit_ta,
                    mv_de=mv_de,
                    sales_ta=sales_ta,
                )
                return jsonify({"method": "altman-z", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/emh", methods=["POST"])
        def analyze_emh() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                returns = list(data["returns"])
                prices = list(data["prices"])
                result = self._engine.analyze_emh(
                    returns=returns, prices=prices
                )
                return jsonify({"method": "emh", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/frontier", methods=["POST"])
        def analyze_frontier() -> tuple[Response, int]:
            try:
                result = self._engine.analyze_frontier()
                return jsonify({"method": "frontier", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/quantum-option", methods=["POST"])
        def analyze_quantum_option() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                S = float(data["S"])
                K = float(data["K"])
                T = float(data["T"])
                r = float(data["r"])
                sigma = float(data["sigma"])
                result = self._engine.analyze_quantum_option(
                    S=S, K=K, T=T, r=r, sigma=sigma
                )
                return jsonify({"method": "quantum-option", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/analyze/dsge", methods=["POST"])
        def analyze_dsge() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                n_periods = int(data.get("n_periods", 200))
                shock_type = data.get("shock_type", "monetary")
                result = self._engine.analyze_dsge(
                    n_periods=n_periods, shock_type=shock_type
                )
                return jsonify({"method": "dsge", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        # --------------------------------------------------------------
        # History
        # --------------------------------------------------------------
        @app.route("/api/v1/history", methods=["GET"])
        def get_history() -> tuple[Response, int]:
            try:
                history = getattr(self._engine, "history", [])
                return jsonify({"history": history}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        # --------------------------------------------------------------
        # Market Data
        # --------------------------------------------------------------
        @app.route("/api/v1/market/quote/<symbol>", methods=["GET"])
        def market_quote(symbol: str) -> tuple[Response, int]:
            try:
                provider = request.args.get("provider", "yahoo")
                result = self._engine.get_market_quote(symbol, provider=provider)
                return jsonify({"symbol": symbol, "data": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/market/fetch", methods=["POST"])
        def market_fetch() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                symbol = data.get("symbol", "AAPL")
                provider = data.get("provider", "yahoo")
                period = data.get("period", "1y")
                result = self._engine.fetch_market_data(symbol, provider=provider, period=period)
                return jsonify({"status": "fetched", "result": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/market/batch-quotes", methods=["POST"])
        def market_batch() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                symbols = data.get("symbols", ["AAPL", "GOOGL", "MSFT"])
                result = self._engine.get_batch_quotes(symbols)
                return jsonify({"quotes": result}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/market/tickers", methods=["GET"])
        def popular_tickers() -> tuple[Response, int]:
            try:
                result = self._engine.get_popular_tickers()
                return jsonify(result), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        # --------------------------------------------------------------
        # Log Management
        # --------------------------------------------------------------
        @app.route("/api/v1/logs/recent", methods=["GET"])
        def logs_recent() -> tuple[Response, int]:
            try:
                from core.log_manager import LogManager
                lm = LogManager.get_instance()
                limit = int(request.args.get("limit", 50))
                level = request.args.get("level", None)
                entries = lm.get_recent(limit=limit, level=level)
                return jsonify({"entries": entries, "count": len(entries)}), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/logs/stats", methods=["GET"])
        def logs_stats() -> tuple[Response, int]:
            try:
                from core.log_manager import LogManager
                lm = LogManager.get_instance()
                return jsonify(lm.get_log_stats()), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/logs/export", methods=["POST"])
        def logs_export() -> tuple[Response, int]:
            try:
                from core.log_manager import LogManager
                lm = LogManager.get_instance()
                data = request.get_json(force=True)
                output_path = data.get("output_path", "logs_export.json")
                fmt = data.get("format", "json")
                result = lm.export_logs(output_path, format=fmt)
                return jsonify(result), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        # --------------------------------------------------------------
        # Report generation
        # --------------------------------------------------------------
        @app.route("/api/v1/report/pdf", methods=["POST"])
        def report_pdf() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                output_path = data.get("output_path", "report.pdf")
                result = self._engine.generate_pdf_report(
                    output_path=output_path
                )
                return jsonify({
                    "status": "generated",
                    "format": "pdf",
                    "path": result if isinstance(result, str) else output_path,
                }), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        @app.route("/api/v1/report/excel", methods=["POST"])
        def report_excel() -> tuple[Response, int]:
            try:
                data = request.get_json(force=True)
                output_path = data.get("output_path", "report.xlsx")
                result = self._engine.generate_excel_report(
                    output_path=output_path
                )
                return jsonify({
                    "status": "generated",
                    "format": "excel",
                    "path": result if isinstance(result, str) else output_path,
                }), 200
            except Exception as exc:
                return jsonify({"error": str(exc)}), 400

        return app

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the Flask server in a background daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("API server is already running.")
            return

        self._shutdown_flag = False
        self._flask_app = self._create_app()

        def _run() -> None:
            logger.info(
                "QuantAPI server starting on %s:%d", self._host, self._port
            )
            self._flask_app.run(
                host=self._host,
                port=self._port,
                threaded=True,
                use_reloader=False,
            )

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info("QuantAPI server thread launched.")

    def stop(self) -> None:
        """Signal the server to stop."""
        self._shutdown_flag = True
        logger.info("QuantAPI server shutdown requested.")

    def is_running(self) -> bool:
        """Return ``True`` if the background thread is alive."""
        if self._thread is None:
            return False
        return self._thread.is_alive() and not self._shutdown_flag
