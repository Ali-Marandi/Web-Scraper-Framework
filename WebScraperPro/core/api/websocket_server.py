r"""
WebSocket Server for QuantEngine Real-Time Streaming
=====================================================
Provides a WebSocket endpoint that streams analysis results, market data
updates, and log events to connected clients.

Uses the ``websockets`` library for async WebSocket handling.
Run via ``QuantWebSocketServer.start()`` in a background thread.
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class QuantWebSocketServer:
    """WebSocket server that broadcasts QuantEngine events.

    Parameters
    ----------
    quant_engine : object
        A QuantEngine instance with ``history``, ``data``, and analysis methods.
    host : str
        Bind address.
    port : int
        Bind port (default 8766, adjacent to REST API on 8765).
    """

    VERSION = "v1.6.0"

    def __init__(
        self,
        quant_engine: Any,
        host: str = "127.0.0.1",
        port: int = 8766,
    ) -> None:
        self._engine = quant_engine
        self._host = host
        self._port = port
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event = asyncio.Event()
        self._clients: Set[Any] = set()
        self._message_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._running = False
        self._last_event_id = 0

    def _get_ws_module(self):
        """Lazy import websockets."""
        try:
            import websockets
            return websockets
        except ImportError:
            raise RuntimeError(
                "websockets is not installed. Install it with: pip install websockets"
            )

    def broadcast(self, event_type: str, data: Any) -> None:
        """Queue an event for broadcasting to all connected WebSocket clients.

        Thread-safe — can be called from any thread.

        Parameters
        ----------
        event_type : str
            Event type identifier (e.g. ``"analysis_result"``, ``"log"``,
            ``"data_update"``).
        data : Any
            Event payload (will be JSON-serialized).
        """
        self._last_event_id += 1
        event = {
            "id": self._last_event_id,
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        try:
            self._message_queue.put_nowait(event)
        except queue.Full:
            logger.warning("WebSocket event queue full, dropping event: %s", event_type)

    async def _handler(self, websocket) -> None:
        """Handle a single WebSocket connection."""
        self._clients.add(websocket)
        addr = websocket.remote_address if hasattr(websocket, 'remote_address') else 'unknown'
        logger.info("WebSocket client connected from %s", addr)
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "version": self.VERSION,
                "server_time": time.time(),
                "available_events": [
                    "analysis_result", "log", "data_update",
                    "market_quote", "progress", "heartbeat"
                ],
            }))

            async for message in websocket:
                try:
                    msg = json.loads(message)
                    await self._handle_client_message(websocket, msg)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error", "message": "Invalid JSON"
                    }))
        except Exception as exc:
            logger.debug("WebSocket client disconnected: %s", exc)
        finally:
            self._clients.discard(websocket)
            logger.info("WebSocket client disconnected. Active clients: %d", len(self._clients))

    async def _handle_client_message(self, websocket, msg: Dict) -> None:
        """Process an incoming message from a WebSocket client."""
        msg_type = msg.get("type", "")

        if msg_type == "subscribe":
            await websocket.send(json.dumps({
                "type": "subscribed",
                "channels": msg.get("channels", ["*"]),
            }))

        elif msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong", "ts": time.time()}))

        elif msg_type == "get_methods":
            methods = self._engine.get_available_methods()
            await websocket.send(json.dumps({
                "type": "methods_list",
                "data": methods,
            }))

        elif msg_type == "get_datasets":
            if hasattr(self._engine, 'data'):
                names = self._engine.data.list_datasets()
                summaries = {}
                for n in names:
                    tsd = self._engine.data.get_dataset(n)
                    if tsd:
                        summaries[n] = tsd.summary()
                await websocket.send(json.dumps({
                    "type": "datasets_list",
                    "data": {"names": names, "summaries": summaries},
                }, default=str))

        elif msg_type == "get_history":
            history = getattr(self._engine, 'history', [])
            last_n = min(int(msg.get("limit", 20)), len(history))
            await websocket.send(json.dumps({
                "type": "history_snapshot",
                "data": history[-last_n:],
            }, default=str))

        elif msg_type == "run_analysis":
            method = msg.get("method", "")
            params = msg.get("params", {})
            try:
                result = self._dispatch_analysis(method, params)
                self.broadcast("analysis_result", {
                    "method": method,
                    "result": result,
                })
            except Exception as e:
                self.broadcast("analysis_result", {
                    "method": method,
                    "error": str(e),
                })

        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            }))

    def _dispatch_analysis(self, method: str, params: Dict) -> Any:
        """Dispatch an analysis method call from WebSocket to the QuantEngine."""
        engine = self._engine
        dispatch = {
            "arima": lambda: engine.arima_forecast(params.get("dataset", "AAPL"),
                                                      tuple(params.get("order", [2,1,1])),
                                                      params.get("steps", 10)),
            "garch": lambda: engine.garch_analysis(params.get("dataset", "AAPL")),
            "var": lambda: engine.var_risk(params.get("dataset", "AAPL")),
            "markowitz": lambda: engine.markowitz_optimize(
                params.get("datasets", engine.data.list_datasets())),
            "black_scholes": lambda: engine.black_scholes_price(
                S=params.get("S", 100), K=params.get("K", 105),
                T=params.get("T", 1.0), r=params.get("r", 0.02),
                sigma=params.get("sigma", 0.2)),
            "dsge": lambda: engine.dsge_simulate(
                n_periods=params.get("n_periods", 200)),
        }
        fn = dispatch.get(method)
        if fn:
            return fn()
        return {"error": f"Unknown method: {method}"}

    async def _broadcast_loop(self) -> None:
        """Continuously drain the message queue and send to all clients."""
        while not self._shutdown_event.is_set():
            try:
                event = self._message_queue.get(timeout=0.5)
                payload = json.dumps(event, default=str)
                dead = []
                for client in self._clients:
                    try:
                        await client.send(payload)
                    except Exception:
                        dead.append(client)
                for c in dead:
                    self._clients.discard(c)
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as exc:
                logger.debug("Broadcast error: %s", exc)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to keep connections alive."""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(30)
            if self._clients:
                self.broadcast("heartbeat", {"active_clients": len(self._clients)})

    async def _server_main(self) -> None:
        """Main async server coroutine."""
        websockets = self._get_ws_module()
        self._shutdown_event.clear()
        async with websockets.serve(
            self._handler,
            self._host,
            self._port,
            ping_interval=20,
            ping_timeout=60,
        ):
            logger.info("WebSocket server listening on ws://%s:%d", self._host, self._port)
            await asyncio.gather(
                self._broadcast_loop(),
                self._heartbeat_loop(),
                self._shutdown_event.wait(),
            )

    def _run_in_thread(self) -> None:
        """Entry point for the background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._server_main())
        except Exception as exc:
            logger.error("WebSocket server error: %s", exc)
        finally:
            self._loop.close()
            self._running = False

    def start(self) -> None:
        """Start the WebSocket server in a background daemon thread."""
        if self._running:
            logger.warning("WebSocket server is already running.")
            return
        self._running = True
        self._shutdown_event = asyncio.Event()
        self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._thread.start()
        logger.info("WebSocket server thread launched.")

    def stop(self) -> None:
        """Signal the server to stop."""
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._shutdown_event.set)
        self._running = False
        logger.info("WebSocket server shutdown requested.")

    def is_running(self) -> bool:
        """Return True if the server is active."""
        return self._running and self._thread is not None and self._thread.is_alive()

    @property
    def client_count(self) -> int:
        return len(self._clients)
