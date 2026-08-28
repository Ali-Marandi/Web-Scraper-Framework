"""
WebScraper Pro - Main Application Window
Professional desktop UI with sidebar navigation, header, content panels, and status bar.
"""

import customtkinter as ctk

from ui.styles import theme, Typography, Spacing, Radius, apply_custom_styles
from core.scraper_engine import ScraperEngine
from ui.panels.dashboard_panel import DashboardPanel
from ui.panels.proxy_panel import ProxyPanel
from ui.panels.scheduler_panel import SchedulerPanel
from ui.panels.settings_panel import SettingsPanel
from ui.panels.log_panel import LogPanel
from ui.panels.tools_panel import ToolsPanel
from ui.panels.headers_panel import HeadersPanel
from ui.panels.quant_panel import QuantPanel


class MainWindow(ctk.CTk):
    """Main application window for WebScraper Pro."""

    NAV_ICONS = {
        "dashboard": "⬡",
        "scraper": "◈",
        "proxies": "⊕",
        "tools": "✦",
        "quant": "◈",
        "headers": "☰",
        "logs": "≡",
        "scheduler": "⏲",
        "settings": "⚙",
    }
    NAV_LABELS = ["Scraper", "Proxies", "Tools", "Quant", "Headers", "Logs", "Scheduler", "Settings"]
    NAV_KEYS = ["dashboard", "scraper", "proxies", "tools", "quant", "headers", "logs", "scheduler", "settings"]

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("WebScraper Pro")
        self.geometry("1400x800")
        self.minsize(1200, 700)
        self.configure(fg_color=theme.colors.BG_MAIN)

        # Set window icon
        try:
            icon_path = self._resolve_icon_path()
            if icon_path:
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # Log startup
        self._log_buffer: list[tuple[str, str]] = []

        # Apply theme
        apply_custom_styles()

        # Engine
        self.engine = ScraperEngine()
        self.engine.set_progress_callback(self._on_progress)
        self.engine.set_log_callback(self._on_log)

        # State
        self._current_panel_key = "dashboard"
        self._panels: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        # Layout
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_header()
        self._build_content_area()
        self._build_status_bar()

        # Switch to default panel
        self._switch_panel("dashboard")

        # Periodic UI update
        self.after(1000, self._periodic_update)

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=180, corner_radius=0,
                               fg_color=theme.colors.BG_SIDEBAR)
        sidebar.grid(row=0, column=0, rowspan=3, sticky="ns")
        sidebar.grid_rowconfigure(4, weight=1)
        sidebar.grid_propagate(False)

        # Logo
        ctk.CTkLabel(sidebar, text=self.NAV_ICONS["dashboard"],
                      font=(Typography.FONT_FAMILY, 28),
                      text_color=theme.colors.BRAND_PRIMARY
                      ).grid(row=0, column=0, padx=Spacing.LG, pady=(Spacing.XL, Spacing.XS))
        ctk.CTkLabel(sidebar, text="WebScraper",
                      font=(Typography.HEADING_FONT, Typography.H3_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY
                      ).grid(row=1, column=0, padx=Spacing.LG, pady=(0, Spacing.XS))
        ctk.CTkLabel(sidebar, text="Pro",
                      font=(Typography.HEADING_FONT, Typography.H3_SIZE),
                      text_color=theme.colors.TEXT_MUTED
                      ).grid(row=2, column=0, padx=Spacing.LG, pady=(0, Spacing.LG))

        # Separator
        sep = ctk.CTkFrame(sidebar, height=1, fg_color=theme.colors.BORDER)
        sep.grid(row=3, column=0, sticky="ew", padx=Spacing.MD)

        # Nav buttons
        for i, (key, label) in enumerate(zip(self.NAV_KEYS, self.NAV_LABELS)):
            btn = ctk.CTkButton(
                sidebar, text=f"  {self.NAV_ICONS[key]}  {label}",
                font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                fg_color="transparent", hover_color=theme.colors.BG_HOVER,
                text_color=theme.colors.TEXT_SECONDARY,
                anchor="w", height=38, corner_radius=Radius.MD,
                command=lambda k=key: self._switch_panel(k),
            )
            btn.grid(row=4 + i, column=0, sticky="ew", padx=Spacing.SM, pady=1)
            self._nav_buttons[key] = btn

        # Bottom version label
        self._version_label = ctk.CTkLabel(sidebar, text="v1.3.0",
                      font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED
                      )
        self._version_label.grid(row=14, column=0, sticky="s", padx=Spacing.LG, pady=Spacing.MD)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, height=48, corner_radius=0,
                              fg_color=theme.colors.BG_CARD)
        header.grid(row=0, column=1, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)

        self._header_title = ctk.CTkLabel(
            header, text="WebScraper Pro",
            font=(Typography.HEADING_FONT, Typography.H2_SIZE),
            text_color=theme.colors.TEXT_PRIMARY,
        )
        self._header_title.pack(side="left", padx=Spacing.LG)

        # Right side: theme toggle + status indicators
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=Spacing.LG, fill="y")

        self._indicator_label = ctk.CTkLabel(
            right, text="* Idle",
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            text_color=theme.colors.TEXT_MUTED,
        )
        self._indicator_label.pack(side="right", padx=Spacing.SM, pady=Spacing.SM)

        self._theme_btn = ctk.CTkButton(
            right, text=":", width=34, height=30,
            font=(Typography.FONT_FAMILY, Typography.H2_SIZE),
            fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
            text_color=theme.colors.TEXT_SECONDARY, corner_radius=Radius.MD,
            command=self.toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=(Spacing.SM, 0), pady=Spacing.SM)

    # ------------------------------------------------------------------
    # Content Area
    # ------------------------------------------------------------------

    def _build_content_area(self):
        self._content_frame = ctk.CTkFrame(self, corner_radius=0,
                                           fg_color=theme.colors.BG_MAIN)
        self._content_frame.grid(row=1, column=1, sticky="nsew")
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

        # Create all panels (only one visible at a time)
        self._panels["dashboard"] = DashboardPanel(self._content_frame)
        self._panels["scraper"] = self._panels["dashboard"]  # alias
        self._panels["explorer"] = ExplorerPanel(self._content_frame)
        self._panels["analytics"] = AnalyticsPanel(self._content_frame)
        self._panels["proxies"] = ProxyPanel(self._content_frame)
        self._panels["tools"] = ToolsPanel(self._content_frame)
        self._panels["headers"] = HeadersPanel(self._content_frame)
        self._panels["quant"] = QuantPanel(self._content_frame)
        self._panels["scheduler"] = SchedulerPanel(self._content_frame)
        self._panels["settings"] = SettingsPanel(self._content_frame)
        self._panels["logs"] = LogPanel(self._content_frame)
        self._panels["history"] = HistoryPanel(self._content_frame)
        self._log_panel = self._panels["logs"]

        # Flush buffered logs
        for msg, lvl in self._log_buffer:
            self._log_panel.add_log(msg, lvl)
        self._log_buffer.clear()

    # ------------------------------------------------------------------
    # Status Bar
    # ------------------------------------------------------------------

    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, height=32, corner_radius=0,
                           fg_color=theme.colors.BG_CARD)
        bar.grid(row=2, column=1, sticky="ew")
        bar.grid_propagate(False)

        self._status_state = ctk.CTkLabel(
            bar, text="State: Idle", width=140,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED, anchor="w",
        )
        self._status_state.pack(side="left", padx=(Spacing.LG, Spacing.SM), pady=Spacing.SM, fill="y")

        self._status_results = ctk.CTkLabel(
            bar, text="Results: 0", width=120,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED, anchor="w",
        )
        self._status_results.pack(side="left", padx=Spacing.SM, pady=Spacing.SM, fill="y")

        self._status_proxies = ctk.CTkLabel(
            bar, text="Proxies: 0", width=120,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED, anchor="w",
        )
        self._status_proxies.pack(side="left", padx=Spacing.SM, pady=Spacing.SM, fill="y")

        self._status_engine = ctk.CTkLabel(
            bar, text="Engine: Ready", width=130,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED, anchor="w",
        )
        self._status_engine.pack(side="left", padx=Spacing.SM, pady=Spacing.SM, fill="y")

        # Progress bar (right side)
        self._progress_bar = ctk.CTkProgressBar(
            bar, width=200, height=12,
            fg_color=theme.colors.BG_INPUT,
            progress_color=theme.colors.BRAND_PRIMARY,
            corner_radius=Radius.FULL,
        )
        self._progress_bar.pack(side="right", padx=(Spacing.SM, Spacing.LG), pady=Spacing.SM)
        self._progress_bar.set(0)

        self._progress_label = ctk.CTkLabel(
            bar, text="0 / 0", width=60,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED, anchor="e",
        )
        self._progress_label.pack(side="right", padx=Spacing.SM, pady=Spacing.SM, fill="y")

    # ------------------------------------------------------------------
    # Panel Switching
    # ------------------------------------------------------------------

    def _switch_panel(self, key: str):
        # Hide all panels
        for panel in self._panels.values():
            if panel is not self._panels["scraper"]:  # skip alias
                panel.grid_remove()
        self._panels["dashboard"].grid_remove()

        # Show selected
        panel = self._panels.get(key, self._panels["dashboard"])
        panel.grid(row=0, column=0, sticky="nsew")
        self._current_panel_key = key

        # Update nav button styles
        for k, btn in self._nav_buttons.items():
            if k == key or (key == "dashboard" and k == "dashboard"):
                btn.configure(fg_color=theme.colors.BG_ACTIVE,
                              text_color=theme.colors.TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent",
                              text_color=theme.colors.TEXT_SECONDARY)

        # Update panel with engine data
        panel.update_ui(self.engine)

        # Update header title
        title_map = {
            "dashboard": "Scraper",
            "scraper": "Scraper",
            "explorer": "URL Explorer",
            "analytics": "Analytics (Quantitative)",
            "proxies": "Proxy Manager",
            "tools": "Developer Tools",
            "quant": "Quantitative Finance",
            "headers": "Headers & Cookies",
            "logs": "Logs",
            "scheduler": "Task Scheduler",
            "settings": "Settings",
            "history": "Scrape History",
        }
        self._header_title.configure(text=title_map.get(key, "WebScraper Pro"))

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def toggle_theme(self):
        theme.toggle()
        apply_custom_styles()
        self.configure(fg_color=theme.colors.BG_MAIN)
        icon = "\u2600" if theme.is_dark else "\u263d"
        self._theme_btn.configure(text=icon)
        self._reapply_theme_colors()
        # Refresh current panel
        panel = self._panels.get(self._current_panel_key, self._panels["dashboard"])
        panel.update_ui(self.engine)

    def _reapply_theme_colors(self):
        c = theme.colors
        # Sidebar
        self._sidebar_ref = self.grid_slaves(row=0, column=0)
        for w in self._sidebar_ref:
            if isinstance(w, ctk.CTkFrame):
                w.configure(fg_color=c.BG_SIDEBAR)
                break
        # Header
        for w in self.grid_slaves(row=0, column=1):
            if isinstance(w, ctk.CTkFrame):
                w.configure(fg_color=c.BG_CARD)
                break
        # Status bar
        for w in self.grid_slaves(row=2, column=1):
            if isinstance(w, ctk.CTkFrame):
                w.configure(fg_color=c.BG_CARD)
                break
        # Content
        self._content_frame.configure(fg_color=c.BG_MAIN)
        # Nav buttons
        for k, btn in self._nav_buttons.items():
            if k == self._current_panel_key:
                btn.configure(fg_color=c.BG_ACTIVE, text_color=c.TEXT_PRIMARY,
                              hover_color=c.BG_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=c.TEXT_SECONDARY,
                              hover_color=c.BG_HOVER)
        # Progress bar
        self._progress_bar.configure(fg_color=c.BG_INPUT, progress_color=c.BRAND_PRIMARY)
        # Theme button
        self._theme_btn.configure(fg_color=c.BG_ELEVATED, hover_color=c.BG_HOVER,
                                    text_color=c.TEXT_SECONDARY)
        # Status labels
        for lbl in [self._status_state, self._status_results,
                     self._status_proxies, self._status_engine, self._progress_label]:
            lbl.configure(text_color=c.TEXT_MUTED)
        self._indicator_label.configure(text_color=c.TEXT_MUTED)
        self._header_title.configure(text_color=c.TEXT_PRIMARY)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_progress(self, progress: dict):
        current = progress.get("current", 0)
        total = progress.get("total", 0)
        if total > 0:
            self.after(0, lambda: self._progress_bar.set(current / total))
            self.after(0, lambda: self._progress_label.configure(text=f"{current}/{total}"))
        status = progress.get("status", "idle")
        color_map = {
            "running": theme.colors.TEXT_SUCCESS,
            "completed": theme.colors.TEXT_SUCCESS,
            "stopping": theme.colors.TEXT_WARNING,
            "error": theme.colors.TEXT_ERROR,
            "idle": theme.colors.TEXT_MUTED,
        }
        self.after(0, lambda: self._indicator_label.configure(
            text=f"* {status.capitalize()}",
            text_color=color_map.get(status, theme.colors.TEXT_MUTED)))

    def _resolve_icon_path(self) -> str | None:
        """Resolve icon path for both dev and PyInstaller frozen environments."""
        import os, sys
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icons", "app.ico"),
            os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "icons", "app.ico"),
            "assets\\icons\\app.ico",
        ]
        for p in candidates:
            if os.path.isfile(p):
                return os.path.normpath(p)
        return None

    def _on_log(self, message: str, level: str = "info"):
        # Buffer logs before log panel is ready
        if hasattr(self, '_log_panel') and self._log_panel:
            self.after(0, lambda: self._log_panel.add_log(message, level))
        else:
            self._log_buffer.append((message, level))

    # ------------------------------------------------------------------
    # Periodic Update
    # ------------------------------------------------------------------

    def _periodic_update(self):
        if self.engine:
            state_text = self.engine.state.value.capitalize()
            self._status_state.configure(text=f"State: {state_text}")
            self._status_results.configure(text=f"Results: {self.engine.result_count}")
            proxy_count = self.engine.proxy_manager.proxy_count
            self._status_proxies.configure(text=f"Proxies: {proxy_count}")
            self._status_engine.configure(text=f"Engine: {state_text}")

            # Update current panel
            panel = self._panels.get(self._current_panel_key, self._panels["dashboard"])
            panel.update_ui(self.engine)

        self.after(2000, self._periodic_update)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self):
        self.mainloop()
