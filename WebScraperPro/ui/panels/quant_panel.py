"""
WebScraper Pro - Quantitative Finance Panel
Comprehensive UI for time series analysis, financial engineering, portfolio optimization,
ML/NLP, network analysis, fuzzy logic, and advanced quant methods.
"""

import json
import threading
import customtkinter as ctk

from ui.styles import theme, Typography, Spacing, Radius


# Lazy import — QuantEngine may not exist yet at import time
def _get_quant_engine(engine):
    """Safely retrieve the QuantEngine from the scraper engine."""
    qe = getattr(engine, "_quant_engine", None)
    if qe is None:
        try:
            from core.quant import QuantEngine
            qe = QuantEngine()
            engine._quant_engine = qe
        except Exception:
            qe = None
    return qe


# ====================================================================
# Shared widget helpers
# ====================================================================

def _entry_opts(**overrides):
    """Standard CTkEntry styling options."""
    opts = dict(
        font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
        fg_color=theme.colors.BG_INPUT,
        border_color=theme.colors.BORDER,
        border_width=1,
        corner_radius=Radius.MD,
        text_color=theme.colors.TEXT_PRIMARY,
        height=30,
    )
    opts.update(overrides)
    return opts


def _option_menu_opts(**overrides):
    """Standard CTkOptionMenu styling options."""
    opts = dict(
        font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
        fg_color=theme.colors.BG_INPUT,
        button_color=theme.colors.BG_ELEVATED,
        button_hover_color=theme.colors.BG_HOVER,
        dropdown_fg_color=theme.colors.BG_ELEVATED,
        text_color=theme.colors.TEXT_PRIMARY,
        corner_radius=Radius.MD,
    )
    opts.update(overrides)
    return opts


def _primary_btn(master, text, command, **overrides):
    """Create a brand-primary styled button."""
    return ctk.CTkButton(
        master, text=text, command=command,
        font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
        fg_color=theme.colors.BRAND_PRIMARY,
        hover_color=theme.colors.BRAND_PRIMARY_HOVER,
        text_color="white",
        corner_radius=Radius.MD,
        height=30,
        **overrides,
    )


def _secondary_btn(master, text, command, **overrides):
    """Create a secondary / ghost-style button."""
    return ctk.CTkButton(
        master, text=text, command=command,
        font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
        fg_color=theme.colors.BG_ELEVATED,
        hover_color=theme.colors.BG_HOVER,
        text_color=theme.colors.TEXT_PRIMARY,
        corner_radius=Radius.MD,
        border_width=1,
        border_color=theme.colors.BORDER,
        height=28,
        **overrides,
    )


def _make_card(parent, **grid_opts):
    """Create a card-style CTkFrame and return it."""
    card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
    card.grid(**grid_opts, sticky="nsew")
    return card


def _make_label(parent, text, header=False):
    """Create a CTkLabel, optionally as a section header."""
    if header:
        return ctk.CTkLabel(
            parent, text=text,
            font=(Typography.HEADING_FONT, Typography.H3_SIZE),
            text_color=theme.colors.TEXT_PRIMARY,
        )
    return ctk.CTkLabel(
        parent, text=text,
        font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
        text_color=theme.colors.TEXT_SECONDARY,
    )


def _make_results_box(parent, height=220):
    """Create a read-only CTkTextbox for JSON results."""
    box = ctk.CTkTextbox(
        parent, height=height,
        font=(Typography.MONO_FONT, Typography.TINY_SIZE),
        fg_color=theme.colors.BG_INPUT,
        border_color=theme.colors.BORDER,
        border_width=1,
        corner_radius=Radius.MD,
        text_color=theme.colors.TEXT_SECONDARY,
        state="disabled",
        wrap="none",
    )
    return box


def _set_results(textbox, data):
    """Write JSON-formatted data into a results textbox."""
    textbox.configure(state="normal")
    textbox.delete("0.0", "end")
    if isinstance(data, (dict, list)):
        textbox.insert("0.0", json.dumps(data, indent=2, default=str))
    else:
        textbox.insert("0.0", str(data))
    textbox.configure(state="disabled")


def _form_row(parent, row, label_text, widget_factory, col_label=0, col_widget=1,
              padx_l=Spacing.MD, padx_r=Spacing.SM):
    """Place a label + widget pair on a grid row inside *parent*."""
    _make_label(parent, label_text).grid(
        row=row, column=col_label, padx=(padx_l, Spacing.XS), pady=(Spacing.SM, 0), sticky="w",
    )
    widget = widget_factory()
    widget.grid(
        row=row, column=col_widget, columnspan=2, sticky="ew",
        padx=Spacing.XS, pady=(Spacing.SM, 0),
    )
    return widget


class QuantPanel(ctk.CTkFrame):
    """Comprehensive quantitative finance panel for WebScraper Pro."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._analysis_running = False

        self._build_data_management()
        self._build_tabview()
        self._build_shared_results()

    # ==================================================================
    # DATA MANAGEMENT (top section)
    # ==================================================================

    def _build_data_management(self):
        card = _make_card(
            self,
            row=0, column=0, sticky="ew",
            padx=Spacing.MD, pady=(Spacing.MD, 0),
        )
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS))
        header.grid_columnconfigure(1, weight=1)

        _make_label(header, "Data Management", header=True).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        _primary_btn(btn_frame, "Load Sample Data", self._load_sample_data, width=150).pack(
            side="left", padx=(0, Spacing.SM),
        )
        _primary_btn(btn_frame, "Load from Scraped Results", self._load_from_scraped, width=210).pack(
            side="left",
        )

        # Dataset list
        list_frame = ctk.CTkFrame(card, fg_color="transparent")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        list_frame.grid_columnconfigure(0, weight=1)

        _make_label(list_frame, "Loaded Datasets").grid(row=0, column=0, sticky="w", pady=(0, Spacing.XS))

        self._dataset_listbox = ctk.CTkTextbox(
            list_frame, height=60,
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT,
            border_color=theme.colors.BORDER,
            border_width=1,
            corner_radius=Radius.MD,
            text_color=theme.colors.TEXT_SECONDARY,
            state="disabled",
        )
        self._dataset_listbox.grid(row=1, column=0, sticky="nsew")

    # ==================================================================
    # TABVIEW
    # ==================================================================

    def _build_tabview(self):
        self._tabview = ctk.CTkTabview(
            self,
            fg_color=theme.colors.BG_CARD,
            segmented_button_fg_color=theme.colors.BG_ELEVATED,
            segmented_button_selected_color=theme.colors.BRAND_PRIMARY,
            segmented_button_selected_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            segmented_button_unselected_color=theme.colors.BG_ELEVATED,
            segmented_button_unselected_hover_color=theme.colors.BG_HOVER,
            text_color=theme.colors.TEXT_MUTED,
            command=self._on_tab_change,
        )
        self._tabview.grid(
            row=1, column=0, sticky="ew",
            padx=Spacing.MD, pady=Spacing.SM,
        )
        self._tabview.grid_columnconfigure(0, weight=1)

        tab_names = [
            "Time Series", "Financial Eng.", "Portfolio",
            "ML & NLP", "Network", "Fuzzy", "Advanced",
        ]
        for name in tab_names:
            self._tabview.add(name)

        self._build_timeseries_tab()
        self._build_fineng_tab()
        self._build_portfolio_tab()
        self._build_ml_nlp_tab()
        self._build_network_tab()
        self._build_fuzzy_tab()
        self._build_advanced_tab()

    # ------------------------------------------------------------------
    # Tab 1: Time Series
    # ------------------------------------------------------------------

    def _build_timeseries_tab(self):
        tab = self._tabview.tab("Time Series")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        # Left: inputs
        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        _make_label(left, "Time Series Analysis", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        # Dataset selector
        self._ts_dataset_var = ctk.StringVar(value="(none)")
        self._ts_dataset_menu = ctk.CTkOptionMenu(
            left, variable=self._ts_dataset_var,
            values=["(none)"], width=180, **_option_menu_opts(),
        )
        _form_row(left, 1, "Dataset", lambda: self._ts_dataset_menu)

        # Method selector
        self._ts_method_var = ctk.StringVar(value="ARIMA")
        self._ts_method_menu = ctk.CTkOptionMenu(
            left, variable=self._ts_method_var,
            values=["ARIMA", "SARIMA", "GARCH", "VAR", "Cointegration", "VaR/CVaR"],
            width=180, **_option_menu_opts(), command=self._on_ts_method_change,
        )
        _form_row(left, 2, "Method", lambda: self._ts_method_menu)

        # Dynamic parameter frame
        self._ts_param_frame = ctk.CTkFrame(left, fg_color="transparent")
        self._ts_param_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        self._ts_param_frame.grid_columnconfigure(1, weight=1)
        self._ts_entries: dict[str, ctk.CTkEntry] = {}
        self._ts_sliders: dict[str, ctk.CTkSlider] = {}
        self._on_ts_method_change("ARIMA")

        # Run button
        _primary_btn(left, "Run Analysis", self._run_timeseries, width=160).grid(
            row=4, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Results", header=True).grid(
            row=0, column=0, sticky="w", pady=(0, Spacing.XS),
        )
        self._ts_results = _make_results_box(right, height=280)
        self._ts_results.grid(row=1, column=0, sticky="nsew")

    def _on_ts_method_change(self, method: str):
        # Clear existing params
        for w in self._ts_param_frame.winfo_children():
            w.destroy()
        self._ts_entries.clear()
        self._ts_sliders.clear()

        row = 0
        params: list[tuple[str, str, str]] = []

        if method == "ARIMA":
            params = [("p", "0", "entry"), ("d", "0", "entry"), ("q", "0", "entry"),
                      ("forecast_steps", "10", "slider")]
        elif method == "SARIMA":
            params = [("p", "0", "entry"), ("d", "0", "entry"), ("q", "0", "entry"),
                      ("P", "0", "entry"), ("D", "0", "entry"), ("Q", "0", "entry"),
                      ("m", "12", "entry"), ("forecast_steps", "10", "slider")]
        elif method == "GARCH":
            params = [("p", "1", "entry"), ("q", "1", "entry"),
                      ("forecast_steps", "10", "slider")]
        elif method == "VAR":
            params = [("maxlag", "4", "entry"), ("forecast_steps", "10", "slider")]
        elif method == "Cointegration":
            params = [("det_order", "-1", "entry")]
        elif method == "VaR/CVaR":
            params = [("confidence", "0.95", "entry"), ("method", "historical", "entry")]

        for name, default, kind in params:
            if kind == "entry":
                lbl = _make_label(self._ts_param_frame, name)
                lbl.grid(row=row, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.XS, 0), sticky="w")
                entry = ctk.CTkEntry(self._ts_param_frame, placeholder_text=default, width=100, **_entry_opts())
                entry.insert("0", default)
                entry.grid(row=row, column=1, sticky="ew", padx=Spacing.XS, pady=(Spacing.XS, 0))
                self._ts_entries[name] = entry
            elif kind == "slider":
                lbl = _make_label(self._ts_param_frame, name)
                lbl.grid(row=row, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.XS, 0), sticky="w")
                slider = ctk.CTkSlider(
                    self._ts_param_frame, from_=1, to=100,
                    number_of_steps=99,
                    font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                    fg_color=theme.colors.BG_ELEVATED,
                    button_color=theme.colors.BRAND_PRIMARY,
                    button_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                    progress_color=theme.colors.BRAND_PRIMARY,
                )
                slider.set(int(default))
                slider.grid(row=row, column=1, sticky="ew", padx=Spacing.XS, pady=(Spacing.XS, 0))
                self._ts_sliders[name] = slider
            row += 1

    def _run_timeseries(self):
        threading.Thread(target=self._run_timeseries_bg, daemon=True).start()

    def _run_timeseries_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            if qe is None:
                _set_results(self._ts_results, {"error": "QuantEngine not available"})
                return

            dataset = self._ts_dataset_var.get()
            method = self._ts_method_var.get()

            params = {}
            for name, entry in self._ts_entries.items():
                val = entry.get().strip()
                try:
                    params[name] = int(val)
                except ValueError:
                    try:
                        params[name] = float(val)
                    except ValueError:
                        params[name] = val
            for name, slider in self._ts_sliders.items():
                params[name] = int(slider.get())

            if hasattr(qe, "time_series"):
                result = qe.time_series.run(dataset, method, **params)
            else:
                result = {
                    "status": "engine_stub",
                    "dataset": dataset,
                    "method": method,
                    "params": params,
                    "note": "QuantEngine.time_series.run() not yet implemented",
                }
            _set_results(self._ts_results, result)
        except Exception as exc:
            _set_results(self._ts_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 2: Financial Engineering
    # ------------------------------------------------------------------

    def _build_fineng_tab(self):
        tab = self._tabview.tab("Financial Eng.")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        _make_label(left, "Black-Scholes Pricing", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        self._bs_entries: dict[str, ctk.CTkEntry] = {}
        bs_fields = [("S", "100"), ("K", "105"), ("T", "1.0"), ("r", "0.05"), ("sigma", "0.2")]
        for i, (name, default) in enumerate(bs_fields, start=1):
            e = ctk.CTkEntry(left, placeholder_text=name, width=100, **_entry_opts())
            e.insert("0", default)
            self._bs_entries[name] = e
            _form_row(left, i, name, lambda _e=e: _e)

        # Call / Put radio
        radio_frame = ctk.CTkFrame(left, fg_color="transparent")
        radio_frame.grid(row=len(bs_fields) + 1, column=0, columnspan=2, sticky="w", padx=Spacing.MD)
        self._bs_option_type = ctk.StringVar(value="call")
        for val in ("call", "put"):
            ctk.CTkRadioButton(
                radio_frame, text=val.capitalize(), variable=self._bs_option_type, value=val,
                font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                fg_color=theme.colors.BRAND_PRIMARY,
                hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                text_color=theme.colors.TEXT_PRIMARY,
            ).pack(side="left", padx=(0, Spacing.MD))

        _primary_btn(left, "Price", self._run_bs, width=120).grid(
            row=len(bs_fields) + 2, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Monte Carlo
        mc_start = len(bs_fields) + 3
        _make_label(left, "Monte Carlo Simulation", header=True).grid(
            row=mc_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )
        self._mc_entries: dict[str, ctk.CTkEntry] = {}
        mc_fields = [("S0", "100"), ("mu", "0.05"), ("sigma", "0.2"), ("T", "1.0"), ("n_paths", "10000")]
        for i, (name, default) in enumerate(mc_fields, start=mc_start + 1):
            e = ctk.CTkEntry(left, placeholder_text=name, width=100, **_entry_opts())
            e.insert("0", default)
            self._mc_entries[name] = e
            _form_row(left, i, name, lambda _e=e: _e)

        _primary_btn(left, "Simulate", self._run_mc, width=120).grid(
            row=mc_start + 1 + len(mc_fields), column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Interest Rate
        ir_start = mc_start + 1 + len(mc_fields) + 1
        _make_label(left, "Interest Rate Models", header=True).grid(
            row=ir_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        self._ir_model_var = ctk.StringVar(value="Vasicek")
        self._ir_model_menu = ctk.CTkOptionMenu(
            left, variable=self._ir_model_var,
            values=["Vasicek", "CIR", "Hull-White"],
            width=160, **_option_menu_opts(),
        )
        _form_row(left, ir_start + 1, "Model", lambda: self._ir_model_menu)

        self._ir_entries: dict[str, ctk.CTkEntry] = {}
        for i, (name, default) in enumerate([("a", "0.1"), ("b", "0.05"), ("sigma", "0.01")], start=ir_start + 2):
            e = ctk.CTkEntry(left, placeholder_text=name, width=100, **_entry_opts())
            e.insert("0", default)
            self._ir_entries[name] = e
            _form_row(left, i, name, lambda _e=e: _e)

        _primary_btn(left, "Simulate Rates", self._run_ir, width=140).grid(
            row=ir_start + 2 + 3, column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Option Strategy
        os_start = ir_start + 2 + 3 + 1
        _make_label(left, "Option Strategy", header=True).grid(
            row=os_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )
        self._os_strategy_var = ctk.StringVar(value="Long Straddle")
        self._os_strategy_menu = ctk.CTkOptionMenu(
            left, variable=self._os_strategy_var,
            values=["Long Straddle", "Short Straddle", "Bull Call Spread",
                    "Bear Put Spread", "Iron Condor", "Butterfly", "Covered Call"],
            width=180, **_option_menu_opts(),
        )
        _form_row(left, os_start + 1, "Strategy", lambda: self._os_strategy_menu)

        _primary_btn(left, "Analyze Strategy", self._run_os, width=160).grid(
            row=os_start + 2, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Results", header=True).grid(row=0, column=0, sticky="w", pady=(0, Spacing.XS))
        self._fe_results = _make_results_box(right, height=400)
        self._fe_results.grid(row=1, column=0, sticky="nsew")

    def _run_bs(self):
        threading.Thread(target=self._run_bs_bg, daemon=True).start()

    def _run_bs_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            params = {k: float(e.get()) for k, e in self._bs_entries.items()}
            params["option_type"] = self._bs_option_type.get()
            if qe and hasattr(qe, "financial_engineering"):
                result = qe.financial_engineering.black_scholes(**params)
            else:
                result = {"status": "engine_stub", "method": "Black-Scholes", "params": params}
            _set_results(self._fe_results, result)
        except Exception as exc:
            _set_results(self._fe_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_mc(self):
        threading.Thread(target=self._run_mc_bg, daemon=True).start()

    def _run_mc_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            params = {}
            for k, e in self._mc_entries.items():
                try:
                    params[k] = int(e.get())
                except ValueError:
                    params[k] = float(e.get())
            if qe and hasattr(qe, "financial_engineering"):
                result = qe.financial_engineering.monte_carlo(**params)
            else:
                result = {"status": "engine_stub", "method": "Monte Carlo", "params": params}
            _set_results(self._fe_results, result)
        except Exception as exc:
            _set_results(self._fe_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_ir(self):
        threading.Thread(target=self._run_ir_bg, daemon=True).start()

    def _run_ir_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            params = {k: float(e.get()) for k, e in self._ir_entries.items()}
            params["model"] = self._ir_model_var.get()
            if qe and hasattr(qe, "financial_engineering"):
                result = qe.financial_engineering.interest_rate_model(**params)
            else:
                result = {"status": "engine_stub", "method": "Interest Rate", "params": params}
            _set_results(self._fe_results, result)
        except Exception as exc:
            _set_results(self._fe_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_os(self):
        threading.Thread(target=self._run_os_bg, daemon=True).start()

    def _run_os_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            bs_params = {k: float(e.get()) for k, e in self._bs_entries.items()}
            strategy = self._os_strategy_var.get()
            if qe and hasattr(qe, "financial_engineering"):
                result = qe.financial_engineering.option_strategy(strategy, **bs_params)
            else:
                result = {"status": "engine_stub", "method": "Option Strategy", "strategy": strategy, "bs_params": bs_params}
            _set_results(self._fe_results, result)
        except Exception as exc:
            _set_results(self._fe_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 3: Portfolio
    # ------------------------------------------------------------------

    def _build_portfolio_tab(self):
        tab = self._tabview.tab("Portfolio")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        _make_label(left, "Portfolio Optimization", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        # Asset checkboxes
        _make_label(left, "Select Assets").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS),
        )
        self._portfolio_check_frame = ctk.CTkScrollableFrame(left, fg_color="transparent", height=80)
        self._portfolio_check_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", padx=Spacing.MD,
        )
        self._portfolio_checks: dict[str, ctk.CTkCheckBox] = {}

        # Method selector
        self._pf_method_var = ctk.StringVar(value="Markowitz Sharpe")
        self._pf_method_menu = ctk.CTkOptionMenu(
            left, variable=self._pf_method_var,
            values=["Markowitz Sharpe", "Min Variance", "Black-Litterman", "Fuzzy"],
            width=180, **_option_menu_opts(),
        )
        _form_row(left, 3, "Method", lambda: self._pf_method_menu)

        # Risk-free rate slider
        _make_label(left, "Risk-Free Rate").grid(
            row=4, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.SM, 0), sticky="w",
        )
        self._pf_rf_slider = ctk.CTkSlider(
            left, from_=0.0, to=0.10, number_of_steps=100,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED,
            button_color=theme.colors.BRAND_PRIMARY,
            button_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            progress_color=theme.colors.BRAND_PRIMARY,
        )
        self._pf_rf_slider.set(0.02)
        self._pf_rf_slider.grid(row=4, column=1, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))
        self._pf_rf_label = ctk.CTkLabel(
            left, text="2.0%",
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED,
        )
        self._pf_rf_label.grid(row=4, column=2, padx=(Spacing.XS, Spacing.MD), pady=(Spacing.SM, 0))
        self._pf_rf_slider.configure(command=self._on_rf_change)

        _primary_btn(left, "Optimize", self._run_portfolio, width=140).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Optimal Weights", header=True).grid(
            row=0, column=0, sticky="w", pady=(0, Spacing.XS),
        )
        self._pf_results = _make_results_box(right, height=280)
        self._pf_results.grid(row=1, column=0, sticky="nsew")

    def _on_rf_change(self, value):
        self._pf_rf_label.configure(text=f"{value * 100:.1f}%")

    def _run_portfolio(self):
        threading.Thread(target=self._run_portfolio_bg, daemon=True).start()

    def _run_portfolio_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            if qe is None:
                _set_results(self._pf_results, {"error": "QuantEngine not available"})
                return

            selected = [name for name, cb in self._portfolio_checks.items() if cb.get() == 1]
            method = self._pf_method_var.get()
            rf = float(self._pf_rf_slider.get())

            if hasattr(qe, "portfolio"):
                result = qe.portfolio.optimize(selected, method=method, risk_free_rate=rf)
            else:
                result = {
                    "status": "engine_stub",
                    "method": method,
                    "assets": selected,
                    "risk_free_rate": rf,
                    "note": "QuantEngine.portfolio.optimize() not yet implemented",
                }
            _set_results(self._pf_results, result)
        except Exception as exc:
            _set_results(self._pf_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 4: ML & NLP
    # ------------------------------------------------------------------

    def _build_ml_nlp_tab(self):
        tab = self._tabview.tab("ML & NLP")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        # --- LSTM / Transformer Forecast ---
        _make_label(left, "Deep Learning Forecast", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        self._ml_dataset_var = ctk.StringVar(value="(none)")
        self._ml_dataset_menu = ctk.CTkOptionMenu(
            left, variable=self._ml_dataset_var,
            values=["(none)"], width=180, **_option_menu_opts(),
        )
        _form_row(left, 1, "Dataset", lambda: self._ml_dataset_menu)

        self._ml_model_var = ctk.StringVar(value="LSTM")
        self._ml_model_menu = ctk.CTkOptionMenu(
            left, variable=self._ml_model_var,
            values=["LSTM", "Transformer"], width=180, **_option_menu_opts(),
        )
        _form_row(left, 2, "Model", lambda: self._ml_model_menu)

        _make_label(left, "Epochs").grid(
            row=3, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.SM, 0), sticky="w",
        )
        self._ml_epochs_slider = ctk.CTkSlider(
            left, from_=1, to=200, number_of_steps=199,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED,
            button_color=theme.colors.BRAND_PRIMARY,
            button_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            progress_color=theme.colors.BRAND_PRIMARY,
        )
        self._ml_epochs_slider.set(50)
        self._ml_epochs_slider.grid(row=3, column=1, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))
        self._ml_epochs_label = ctk.CTkLabel(
            left, text="50",
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED,
        )
        self._ml_epochs_label.grid(row=3, column=2, padx=(Spacing.XS, Spacing.MD))
        self._ml_epochs_slider.configure(command=lambda v: self._ml_epochs_label.configure(text=str(int(v))))

        self._ml_steps_entry = ctk.CTkEntry(left, placeholder_text="10", width=100, **_entry_opts())
        self._ml_steps_entry.insert("0", "10")
        _form_row(left, 4, "Forecast Steps", lambda: self._ml_steps_entry)

        _primary_btn(left, "Forecast", self._run_ml_forecast, width=140).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # --- Sentiment ---
        _make_label(left, "Sentiment Analysis (NLP)", header=True).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        _make_label(left, "Text").grid(
            row=7, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.SM, 0), sticky="nw",
        )
        self._nlp_text = ctk.CTkTextbox(
            left, height=80, width=240,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT,
            border_color=theme.colors.BORDER,
            border_width=1,
            corner_radius=Radius.MD,
            text_color=theme.colors.TEXT_PRIMARY,
        )
        self._nlp_text.grid(row=7, column=1, columnspan=2, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))

        _primary_btn(left, "Analyze Sentiment", self._run_sentiment, width=160).grid(
            row=8, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # --- Anomaly Detection ---
        _make_label(left, "Anomaly Detection", header=True).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        self._anom_dataset_var = ctk.StringVar(value="(none)")
        self._anom_dataset_menu = ctk.CTkOptionMenu(
            left, variable=self._anom_dataset_var,
            values=["(none)"], width=180, **_option_menu_opts(),
        )
        _form_row(left, 10, "Dataset", lambda: self._anom_dataset_menu)

        self._anom_method_var = ctk.StringVar(value="Isolation Forest")
        self._anom_method_menu = ctk.CTkOptionMenu(
            left, variable=self._anom_method_var,
            values=["Isolation Forest", "Z-Score", "IQR", "DBSCAN", "Autoencoder"],
            width=180, **_option_menu_opts(),
        )
        _form_row(left, 11, "Method", lambda: self._anom_method_menu)

        _primary_btn(left, "Detect Anomalies", self._run_anomaly, width=170).grid(
            row=12, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Results", header=True).grid(row=0, column=0, sticky="w", pady=(0, Spacing.XS))
        self._ml_results = _make_results_box(right, height=400)
        self._ml_results.grid(row=1, column=0, sticky="nsew")

    def _run_ml_forecast(self):
        threading.Thread(target=self._run_ml_forecast_bg, daemon=True).start()

    def _run_ml_forecast_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            dataset = self._ml_dataset_var.get()
            model = self._ml_model_var.get()
            epochs = int(self._ml_epochs_slider.get())
            steps = int(self._ml_steps_entry.get())
            if qe and hasattr(qe, "ml_nlp"):
                result = qe.ml_nlp.forecast(dataset, model=model, epochs=epochs, steps=steps)
            else:
                result = {"status": "engine_stub", "model": model, "dataset": dataset,
                          "epochs": epochs, "steps": steps}
            _set_results(self._ml_results, result)
        except Exception as exc:
            _set_results(self._ml_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_sentiment(self):
        threading.Thread(target=self._run_sentiment_bg, daemon=True).start()

    def _run_sentiment_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            text = self._nlp_text.get("0.0", "end").strip()
            if qe and hasattr(qe, "ml_nlp"):
                result = qe.ml_nlp.sentiment(text)
            else:
                result = {"status": "engine_stub", "method": "sentiment", "text": text}
            _set_results(self._ml_results, result)
        except Exception as exc:
            _set_results(self._ml_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_anomaly(self):
        threading.Thread(target=self._run_anomaly_bg, daemon=True).start()

    def _run_anomaly_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            dataset = self._anom_dataset_var.get()
            method = self._anom_method_var.get()
            if qe and hasattr(qe, "ml_nlp"):
                result = qe.ml_nlp.anomaly_detection(dataset, method=method)
            else:
                result = {"status": "engine_stub", "method": "anomaly_detection",
                          "dataset": dataset, "algorithm": method}
            _set_results(self._ml_results, result)
        except Exception as exc:
            _set_results(self._ml_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 5: Network
    # ------------------------------------------------------------------

    def _build_network_tab(self):
        tab = self._tabview.tab("Network")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        _make_label(left, "Network Analysis", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        # Correlation threshold
        _make_label(left, "Correlation Threshold").grid(
            row=1, column=0, padx=(Spacing.MD, Spacing.XS), pady=(Spacing.SM, 0), sticky="w",
        )
        self._net_thresh_slider = ctk.CTkSlider(
            left, from_=0.0, to=1.0, number_of_steps=100,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED,
            button_color=theme.colors.BRAND_PRIMARY,
            button_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            progress_color=theme.colors.BRAND_PRIMARY,
        )
        self._net_thresh_slider.set(0.5)
        self._net_thresh_slider.grid(row=1, column=1, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))
        self._net_thresh_label = ctk.CTkLabel(
            left, text="0.50",
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_MUTED,
        )
        self._net_thresh_label.grid(row=1, column=2, padx=(Spacing.XS, Spacing.MD))
        self._net_thresh_slider.configure(
            command=lambda v: self._net_thresh_label.configure(text=f"{v:.2f}"),
        )

        # Contagion shock
        self._net_shock_var = ctk.StringVar(value="None")
        self._net_shock_menu = ctk.CTkOptionMenu(
            left, variable=self._net_shock_var,
            values=["None", "-5% Market Crash", "-10% Market Crash",
                    "+10% Rally", "Sector Shock"],
            width=200, **_option_menu_opts(),
        )
        _form_row(left, 2, "Contagion Shock", lambda: self._net_shock_menu)

        _primary_btn(left, "Build Network", self._run_network, width=160).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Network Results", header=True).grid(
            row=0, column=0, sticky="w", pady=(0, Spacing.XS),
        )
        self._net_results = _make_results_box(right, height=280)
        self._net_results.grid(row=1, column=0, sticky="nsew")

    def _run_network(self):
        threading.Thread(target=self._run_network_bg, daemon=True).start()

    def _run_network_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            threshold = float(self._net_thresh_slider.get())
            shock = self._net_shock_var.get()
            if qe and hasattr(qe, "network"):
                result = qe.network.build(threshold=threshold, shock=shock)
            else:
                result = {"status": "engine_stub", "threshold": threshold, "shock": shock}
            _set_results(self._net_results, result)
        except Exception as exc:
            _set_results(self._net_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 6: Fuzzy
    # ------------------------------------------------------------------

    def _build_fuzzy_tab(self):
        tab = self._tabview.tab("Fuzzy")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        # --- Credit Scoring ---
        _make_label(left, "Credit Scoring", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        self._fz_credit_entries: dict[str, ctk.CTkEntry] = {}
        credit_fields = [
            ("income", "50000"), ("debt_ratio", "0.3"),
            ("credit_history", "5"), ("employment_years", "3"),
        ]
        for i, (name, default) in enumerate(credit_fields, start=1):
            e = ctk.CTkEntry(left, placeholder_text=name, width=120, **_entry_opts())
            e.insert("0", default)
            self._fz_credit_entries[name] = e
            _form_row(left, i, name.replace("_", " ").title(), lambda _e=e: _e)

        _primary_btn(left, "Score Credit", self._run_fuzzy_credit, width=140).grid(
            row=len(credit_fields) + 1, column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # --- Trading Signal ---
        ts_start = len(credit_fields) + 2
        _make_label(left, "Trading Signal", header=True).grid(
            row=ts_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        self._fz_trade_entries: dict[str, ctk.CTkEntry] = {}
        trade_fields = [
            ("rsi", "50"), ("volume_ratio", "1.0"),
            ("trend_strength", "0.5"), ("volatility", "0.15"),
        ]
        for i, (name, default) in enumerate(trade_fields, start=ts_start + 1):
            e = ctk.CTkEntry(left, placeholder_text=name, width=120, **_entry_opts())
            e.insert("0", default)
            self._fz_trade_entries[name] = e
            _form_row(left, i, name.replace("_", " ").title(), lambda _e=e: _e)

        _primary_btn(left, "Generate Signal", self._run_fuzzy_trade, width=160).grid(
            row=ts_start + 1 + len(trade_fields), column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Results", header=True).grid(row=0, column=0, sticky="w", pady=(0, Spacing.XS))
        self._fz_results = _make_results_box(right, height=320)
        self._fz_results.grid(row=1, column=0, sticky="nsew")

    def _run_fuzzy_credit(self):
        threading.Thread(target=self._run_fuzzy_credit_bg, daemon=True).start()

    def _run_fuzzy_credit_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            params = {k: float(e.get()) for k, e in self._fz_credit_entries.items()}
            if qe and hasattr(qe, "fuzzy"):
                result = qe.fuzzy.credit_score(**params)
            else:
                result = {"status": "engine_stub", "method": "credit_scoring", "params": params}
            _set_results(self._fz_results, result)
        except Exception as exc:
            _set_results(self._fz_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_fuzzy_trade(self):
        threading.Thread(target=self._run_fuzzy_trade_bg, daemon=True).start()

    def _run_fuzzy_trade_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            params = {k: float(e.get()) for k, e in self._fz_trade_entries.items()}
            if qe and hasattr(qe, "fuzzy"):
                result = qe.fuzzy.trading_signal(**params)
            else:
                result = {"status": "engine_stub", "method": "trading_signal", "params": params}
            _set_results(self._fz_results, result)
        except Exception as exc:
            _set_results(self._fz_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ------------------------------------------------------------------
    # Tab 7: Advanced
    # ------------------------------------------------------------------

    def _build_advanced_tab(self):
        tab = self._tabview.tab("Advanced")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)

        left = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(Spacing.SM, Spacing.XS), pady=Spacing.SM)
        left.grid_columnconfigure(1, weight=1)

        # --- Transfer Entropy ---
        _make_label(left, "Transfer Entropy", header=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, Spacing.SM),
        )

        _make_label(left, "Select Datasets").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS),
        )
        self._te_check_frame = ctk.CTkScrollableFrame(left, fg_color="transparent", height=60)
        self._te_check_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=Spacing.MD)
        self._te_checks: dict[str, ctk.CTkCheckBox] = {}

        _primary_btn(left, "Compute Transfer Entropy", self._run_te, width=210).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # --- TDA ---
        tda_start = 4
        _make_label(left, "Topological Data Analysis", header=True).grid(
            row=tda_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        self._tda_dataset_var = ctk.StringVar(value="(none)")
        self._tda_dataset_menu = ctk.CTkOptionMenu(
            left, variable=self._tda_dataset_var,
            values=["(none)"], width=180, **_option_menu_opts(),
        )
        _form_row(left, tda_start + 1, "Dataset", lambda: self._tda_dataset_menu)

        _primary_btn(left, "Run TDA", self._run_tda, width=140).grid(
            row=tda_start + 2, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # --- Game Theory ---
        gt_start = tda_start + 3
        _make_label(left, "Game Theory (2x2)", header=True).grid(
            row=gt_start, column=0, columnspan=2, sticky="w", pady=(Spacing.LG, Spacing.SM),
        )

        _make_label(left, "Player 1 Payoffs").grid(
            row=gt_start + 1, column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS),
        )
        self._gt_p1_entries: list[ctk.CTkEntry] = []
        p1_grid = ctk.CTkFrame(left, fg_color="transparent")
        p1_grid.grid(row=gt_start + 2, column=0, columnspan=2, padx=Spacing.MD, sticky="w")
        for i, val in enumerate(["3, 0", "0, 2"]):
            e = ctk.CTkEntry(p1_grid, placeholder_text=f"Row {i+1}", width=100, **_entry_opts())
            e.insert("0", val)
            e.grid(row=i, column=0, padx=Spacing.XS, pady=Spacing.XS)
            self._gt_p1_entries.append(e)

        _make_label(left, "Player 2 Payoffs").grid(
            row=gt_start + 3, column=0, columnspan=2,
            sticky="w", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS),
        )
        self._gt_p2_entries: list[ctk.CTkEntry] = []
        p2_grid = ctk.CTkFrame(left, fg_color="transparent")
        p2_grid.grid(row=gt_start + 4, column=0, columnspan=2, padx=Spacing.MD, sticky="w")
        for i, val in enumerate(["3, 0", "0, 2"]):
            e = ctk.CTkEntry(p2_grid, placeholder_text=f"Row {i+1}", width=100, **_entry_opts())
            e.insert("0", val)
            e.grid(row=i, column=0, padx=Spacing.XS, pady=Spacing.XS)
            self._gt_p2_entries.append(e)

        _primary_btn(left, "Solve Game", self._run_game_theory, width=140).grid(
            row=gt_start + 5, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.MD,
        )

        # Right: results
        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        _make_label(right, "Results", header=True).grid(row=0, column=0, sticky="w", pady=(0, Spacing.XS))
        self._adv_results = _make_results_box(right, height=400)
        self._adv_results.grid(row=1, column=0, sticky="nsew")

    def _run_te(self):
        threading.Thread(target=self._run_te_bg, daemon=True).start()

    def _run_te_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            selected = [name for name, cb in self._te_checks.items() if cb.get() == 1]
            if qe and hasattr(qe, "advanced"):
                result = qe.advanced.transfer_entropy(selected)
            else:
                result = {"status": "engine_stub", "method": "transfer_entropy", "datasets": selected}
            _set_results(self._adv_results, result)
        except Exception as exc:
            _set_results(self._adv_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_tda(self):
        threading.Thread(target=self._run_tda_bg, daemon=True).start()

    def _run_tda_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            dataset = self._tda_dataset_var.get()
            if qe and hasattr(qe, "advanced"):
                result = qe.advanced.tda(dataset)
            else:
                result = {"status": "engine_stub", "method": "TDA", "dataset": dataset}
            _set_results(self._adv_results, result)
        except Exception as exc:
            _set_results(self._adv_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    def _run_game_theory(self):
        threading.Thread(target=self._run_game_theory_bg, daemon=True).start()

    def _run_game_theory_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)

            def _parse_payoffs(entries):
                matrix = []
                for e in entries:
                    row = [float(x.strip()) for x in e.get().split(",")]
                    matrix.append(row)
                return matrix

            p1 = _parse_payoffs(self._gt_p1_entries)
            p2 = _parse_payoffs(self._gt_p2_entries)

            if qe and hasattr(qe, "advanced"):
                result = qe.advanced.game_theory(p1, p2)
            else:
                result = {"status": "engine_stub", "method": "game_theory",
                          "player1_payoffs": p1, "player2_payoffs": p2}
            _set_results(self._adv_results, result)
        except Exception as exc:
            _set_results(self._adv_results, {"error": str(exc)})
        finally:
            self._set_analysis_running(False)

    # ==================================================================
    # SHARED RESULTS (bottom)
    # ==================================================================

    def _build_shared_results(self):
        card = _make_card(
            self,
            row=2, column=0, sticky="nsew",
            padx=Spacing.MD, pady=(0, Spacing.MD),
        )
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, Spacing.XS))

        _make_label(header, "Analysis Log", header=True).pack(side="left")
        _secondary_btn(header, "Clear", self._clear_shared_results, width=60).pack(side="right")

        self._shared_results = _make_results_box(card, height=120)
        self._shared_results.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.SM))

    def _clear_shared_results(self):
        self._shared_results.configure(state="normal")
        self._shared_results.delete("0.0", "end")
        self._shared_results.configure(state="disabled")

    # ==================================================================
    # TAB CHANGE HANDLER
    # ==================================================================

    def _on_tab_change(self):
        """Called whenever the user switches tabs."""
        pass

    # ==================================================================
    # DATA MANAGEMENT ACTIONS
    # ==================================================================

    def _load_sample_data(self):
        """Generate 3 sample financial datasets using QuantEngine."""
        threading.Thread(target=self._load_sample_data_bg, daemon=True).start()

    def _load_sample_data_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            if qe is None:
                self._append_log({"error": "QuantEngine not available"})
                return

            if hasattr(qe, "data") and hasattr(qe.data, "generate_sample"):
                qe.data.generate_sample()
            else:
                # Fallback: create minimal sample data
                import numpy as np
                np.random.seed(42)
                names = ["AAPL", "GOOGL", "SPY"]
                if not hasattr(qe, "data"):
                    from types import SimpleNamespace
                    qe.data = SimpleNamespace()
                if not hasattr(qe.data, "_datasets"):
                    qe.data._datasets = {}
                for name in names:
                    returns = np.random.normal(0.0005, 0.015, 252).tolist()
                    qe.data._datasets[name] = {"returns": returns, "length": 252}

            result = {"status": "ok", "message": "3 sample datasets loaded (AAPL, GOOGL, SPY)"}
            self._append_log(result)
        except Exception as exc:
            self._append_log({"error": str(exc)})
        finally:
            self._set_analysis_running(False)
            self.after(0, self._refresh_dataset_lists)

    def _load_from_scraped(self):
        """Convert engine._results to quant datasets."""
        threading.Thread(target=self._load_from_scraped_bg, daemon=True).start()

    def _load_from_scraped_bg(self):
        self._set_analysis_running(True)
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            results = getattr(engine, "_results", [])

            if qe is None:
                self._append_log({"error": "QuantEngine not available"})
                return

            if hasattr(qe, "data") and hasattr(qe.data, "from_scraper_results"):
                count = qe.data.from_scraper_results(results)
                result = {"status": "ok", "datasets_created": count}
            else:
                result = {"status": "engine_stub", "note": "data.from_scraper_results() not yet implemented",
                          "results_count": len(results) if results else 0}
            self._append_log(result)
        except Exception as exc:
            self._append_log({"error": str(exc)})
        finally:
            self._set_analysis_running(False)
            self.after(0, self._refresh_dataset_lists)

    # ==================================================================
    # HELPERS
    # ==================================================================

    def _set_analysis_running(self, running: bool):
        self._analysis_running = running

    def _append_log(self, data):
        """Append a JSON line to the shared results log."""
        try:
            self._shared_results.configure(state="normal")
            line = json.dumps(data, indent=2, default=str) if isinstance(data, (dict, list)) else str(data)
            self._shared_results.insert("end", line + "\n" + "─" * 60 + "\n")
            self._shared_results.see("end")
            self._shared_results.configure(state="disabled")
        except Exception:
            pass

    def _refresh_dataset_lists(self):
        """Refresh all dataset selectors with current QuantEngine datasets."""
        try:
            engine = self.winfo_toplevel().engine
            qe = _get_quant_engine(engine)
            if qe is None:
                return

            # Get dataset names
            if hasattr(qe, "data") and hasattr(qe.data, "list_datasets"):
                names = qe.data.list_datasets()
            elif hasattr(qe, "data") and hasattr(qe.data, "_datasets"):
                names = list(qe.data._datasets.keys())
            else:
                names = []

            if not names:
                names = ["(none)"]

            # Update all option menus
            for menu in [self._ts_dataset_menu, self._ml_dataset_menu,
                         self._anom_dataset_menu, self._tda_dataset_menu]:
                current = menu.get()
                menu.configure(values=names)
                if current in names:
                    menu.set(current)
                elif names:
                    menu.set(names[0])

            # Update dataset listbox
            self._dataset_listbox.configure(state="normal")
            self._dataset_listbox.delete("0.0", "end")
            if names and names != ["(none)"]:
                for name in names:
                    self._dataset_listbox.insert("end", f"  ■  {name}\n")
            else:
                self._dataset_listbox.insert("end", "  No datasets loaded. Click 'Load Sample Data'.\n")
            self._dataset_listbox.configure(state="disabled")

            # Update portfolio checkboxes
            for w in self._portfolio_check_frame.winfo_children():
                w.destroy()
            self._portfolio_checks.clear()
            for name in names:
                if name == "(none)":
                    continue
                cb = ctk.CTkCheckBox(
                    self._portfolio_check_frame, text=name,
                    font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                    fg_color=theme.colors.BRAND_PRIMARY,
                    hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                    text_color=theme.colors.TEXT_PRIMARY,
                    corner_radius=Radius.SM,
                )
                cb.pack(anchor="w", pady=1)
                self._portfolio_checks[name] = cb

            # Update TE checkboxes
            for w in self._te_check_frame.winfo_children():
                w.destroy()
            self._te_checks.clear()
            for name in names:
                if name == "(none)":
                    continue
                cb = ctk.CTkCheckBox(
                    self._te_check_frame, text=name,
                    font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                    fg_color=theme.colors.BRAND_PRIMARY,
                    hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                    text_color=theme.colors.TEXT_PRIMARY,
                    corner_radius=Radius.SM,
                )
                cb.pack(anchor="w", pady=1)
                self._te_checks[name] = cb

        except Exception:
            pass

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def update_ui(self, engine):
        """Called by MainWindow to refresh the panel state."""
        if not engine:
            return
        self._refresh_dataset_lists()
