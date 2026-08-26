"""
WebScraper Pro - Settings Panel
Application settings: theme, request config, browser config, rate limiter, export defaults, about.
"""

import customtkinter as ctk
from tkinter import filedialog

from ui.styles import theme, Typography, Spacing, Radius
from core.rate_limiter import LimitStrategy


class SettingsPanel(ctk.CTkScrollableFrame):
    """Settings panel with scrollable sections for all configuration."""

    STRATEGY_OPTIONS = [s.value for s in LimitStrategy]
    BROWSER_OPTIONS = ["chromium", "firefox", "webkit"]
    EXPORT_FORMATS = ["csv", "json", "xlsx", "xml", "html"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._build_theme_section()
        self._build_request_section()
        self._build_browser_section()
        self._build_rate_limiter_section()
        self._build_export_section()
        self._build_about_section()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section_card(self, title: str, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=row, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text=title, font=(Typography.FONT_FAMILY, Typography.H3_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, columnspan=2,
                                                                     sticky="w", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM))
        return card

    def _make_entry(self, parent, placeholder: str = "", width: int = 100) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent, placeholder_text=placeholder, width=width,
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=30,
        )

    def _make_option_menu(self, parent, values: list[str], width: int = 140) -> ctk.CTkOptionMenu:
        return ctk.CTkOptionMenu(
            parent, values=values, width=width,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
        )

    def _add_row(self, card, row, label, widget, sticky="w"):
        ctk.CTkLabel(card, text=label, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=0,
                                                                     padx=(Spacing.MD, Spacing.SM), pady=Spacing.XS, sticky="w")
        widget.grid(row=row, column=1, padx=(0, Spacing.MD), pady=Spacing.XS, sticky=sticky)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _build_theme_section(self):
        card = self._section_card("Appearance", 0)

        self._theme_var = ctk.StringVar(value="dark")
        ctk.CTkRadioButton(card, text="Dark", variable=self._theme_var, value="dark",
                            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                            text_color=theme.colors.TEXT_PRIMARY,
                            command=self._apply_theme).grid(row=1, column=0, padx=(Spacing.MD, Spacing.SM),
                                                              pady=Spacing.SM, sticky="w")
        ctk.CTkRadioButton(card, text="Light", variable=self._theme_var, value="light",
                            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                            text_color=theme.colors.TEXT_PRIMARY,
                            command=self._apply_theme).grid(row=1, column=1, padx=Spacing.SM,
                                                              pady=Spacing.SM, sticky="w")

    def _apply_theme(self):
        root = self.winfo_toplevel()
        if hasattr(root, "toggle_theme"):
            root.toggle_theme()

    # ------------------------------------------------------------------
    # Request Settings
    # ------------------------------------------------------------------

    def _build_request_section(self):
        card = self._section_card("Request Settings", 1)

        self._timeout_entry = self._make_entry(card, "30", 80)
        self._timeout_entry.insert("0", "30")
        self._add_row(card, 1, "Timeout (sec)", self._timeout_entry)

        self._retries_entry = self._make_entry(card, "3", 80)
        self._retries_entry.insert("0", "3")
        self._add_row(card, 2, "Max Retries", self._retries_entry)

        self._retry_delay_entry = self._make_entry(card, "2.0", 80)
        self._retry_delay_entry.insert("0", "2.0")
        self._add_row(card, 3, "Retry Delay (sec)", self._retry_delay_entry)

        self._var_verify_ssl = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Verify SSL", variable=self._var_verify_ssl,
                         font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                         text_color=theme.colors.TEXT_PRIMARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=4, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")

        self._var_follow_redirects = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Follow Redirects", variable=self._var_follow_redirects,
                         font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                         text_color=theme.colors.TEXT_PRIMARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=4, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky="w")

        # User-Agent
        ua_frame = ctk.CTkFrame(card, fg_color="transparent")
        ua_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        ua_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ua_frame, text="User-Agent", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=Spacing.XS)

        self._ua_entry = ctk.CTkEntry(ua_frame, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                       fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                       border_width=1, corner_radius=Radius.MD,
                                       text_color=theme.colors.TEXT_PRIMARY, height=28)
        self._ua_entry.grid(row=0, column=1, sticky="ew", padx=Spacing.SM, pady=Spacing.XS)
        self._ua_entry.insert("0", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    # ------------------------------------------------------------------
    # Browser Settings
    # ------------------------------------------------------------------

    def _build_browser_section(self):
        card = self._section_card("Browser Settings (Dynamic Mode)", 2)

        self._var_headless = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Headless Mode", variable=self._var_headless,
                         font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                         text_color=theme.colors.TEXT_PRIMARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=1, column=0, columnspan=2, padx=(Spacing.MD, Spacing.SM),
                                pady=Spacing.SM, sticky="w")

        self._browser_menu = self._make_option_menu(card, self.BROWSER_OPTIONS, 120)
        self._browser_menu.set("chromium")
        self._add_row(card, 2, "Browser Type", self._browser_menu, "w")

        vp_frame = ctk.CTkFrame(card, fg_color="transparent")
        vp_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=Spacing.XS)
        ctk.CTkLabel(vp_frame, text="Viewport", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=(0, Spacing.SM))
        self._vp_w_entry = self._make_entry(vp_frame, "1920", 70)
        self._vp_w_entry.insert("0", "1920")
        self._vp_w_entry.pack(side="left")
        ctk.CTkLabel(vp_frame, text="x", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=Spacing.XS)
        self._vp_h_entry = self._make_entry(vp_frame, "1080", 70)
        self._vp_h_entry.insert("0", "1080")
        self._vp_h_entry.pack(side="left")

        self._var_stealth = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Stealth Mode", variable=self._var_stealth,
                         font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                         text_color=theme.colors.TEXT_PRIMARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=4, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")

        self._var_block_images = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(card, text="Block Images/Media", variable=self._var_block_images,
                         font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                         text_color=theme.colors.TEXT_PRIMARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=4, column=1, padx=Spacing.SM, pady=Spacing.SM, sticky="w")

    # ------------------------------------------------------------------
    # Rate Limiter
    # ------------------------------------------------------------------

    def _build_rate_limiter_section(self):
        card = self._section_card("Rate Limiter", 3)

        self._strategy_menu = self._make_option_menu(card, self.STRATEGY_OPTIONS, 160)
        self._strategy_menu.set("token_bucket")
        self._add_row(card, 1, "Strategy", self._strategy_menu, "w")

        rps_frame = ctk.CTkFrame(card, fg_color="transparent")
        rps_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        rps_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(rps_frame, text="Global RPS", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, padx=(0, Spacing.SM), sticky="w")

        self._rps_slider = ctk.CTkSlider(
            rps_frame, from_=0.5, to=50, number_of_steps=99,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, button_color=theme.colors.BRAND_PRIMARY_HOVER,
            button_hover_color=theme.colors.BRAND_PRIMARY_DARK,
            progress_color=theme.colors.BRAND_PRIMARY,
        )
        self._rps_slider.set(10.0)
        self._rps_slider.grid(row=0, column=1, sticky="ew")

        self._rps_label = ctk.CTkLabel(rps_frame, text="10.0", width=40,
                                        font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                        text_color=theme.colors.TEXT_PRIMARY)
        self._rps_label.grid(row=0, column=2, padx=(Spacing.SM, 0))
        self._rps_slider.configure(command=self._on_rps_change)

        domain_frame = ctk.CTkFrame(card, fg_color="transparent")
        domain_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        domain_frame.grid_columnconfigure(0, weight=1)

        self._domain_entry = self._make_entry(domain_frame, "example.com", 200)
        self._domain_entry.grid(row=0, column=0, sticky="ew", padx=(0, Spacing.SM))
        self._domain_rps_entry = self._make_entry(domain_frame, "2.0", 70)
        self._domain_rps_entry.insert("0", "2.0")
        self._domain_rps_entry.grid(row=0, column=1, padx=Spacing.SM)

        ctk.CTkButton(domain_frame, text="Set", width=50, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._set_domain_limit
                       ).grid(row=0, column=2, padx=(Spacing.SM, 0))

    def _on_rps_change(self, value):
        self._rps_label.configure(text=f"{value:.1f}")
        engine = self.winfo_toplevel().engine
        if engine:
            engine.rate_limiter.global_rps = value

    def _set_domain_limit(self):
        domain = self._domain_entry.get().strip()
        rps = self._domain_rps_entry.get().strip()
        if not domain:
            return
        try:
            rps_val = float(rps)
        except ValueError:
            return
        engine = self.winfo_toplevel().engine
        if engine:
            from core.rate_limiter import DomainLimits
            engine.rate_limiter.set_domain_limits(domain, DomainLimits(requests_per_second=rps_val))

    # ------------------------------------------------------------------
    # Export Defaults
    # ------------------------------------------------------------------

    def _build_export_section(self):
        card = self._section_card("Export Defaults", 4)

        self._export_format_menu = self._make_option_menu(card, self.EXPORT_FORMATS, 120)
        self._export_format_menu.set("json")
        self._add_row(card, 1, "Default Format", self._export_format_menu, "w")

        path_frame = ctk.CTkFrame(card, fg_color="transparent")
        path_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(path_frame, text="Default Path", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, padx=(0, Spacing.SM), sticky="w")

        self._export_path_entry = self._make_entry(path_frame, "", 0)
        self._export_path_entry.grid(row=0, column=1, sticky="ew", padx=Spacing.SM)

        ctk.CTkButton(path_frame, text="Browse", width=70, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._browse_export_path
                       ).grid(row=0, column=2, padx=(Spacing.SM, 0))

    def _browse_export_path(self):
        path = filedialog.askdirectory()
        if path:
            self._export_path_entry.delete(0, "end")
            self._export_path_entry.insert("0", path)

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------

    def _build_about_section(self):
        card = self._section_card("About", 6)

        info_text = (
            "WebScraper Pro  v1.3.0\n"
            "A commercial-grade web scraping application.\n"
            "Built with Python, CustomTkinter, and Playwright.\n\n"
            "Features:\n"
            "  - Static & dynamic (JS) page scraping\n"
            "  - CSS, XPath, Regex, JSON Path extraction\n"
            "  - Proxy rotation with health monitoring\n"
            "  - Adaptive rate limiting (4 strategies)\n"
            "  - Multi-format data export (6 formats)\n"
            "  - Task scheduling (5 schedule types)\n"
            "  - Pre-built scraping templates (11 templates)\n"
            "  - Project save/load with persistence\n"
            "  - Real-time log viewer with filtering\n"
            "  - Sortable data table with search\n"
            "  - Import/export extraction rules as JSON\n"
            "  - Data transform pipeline (15 operations)\n"
            "  - Captcha detection (reCAPTCHA, hCaptcha, Cloudflare)\n"
            "  - Scrape history with session replay & re-export\n"
            "  - URL Explorer with link categorization & validation\n"
            "  - CSS/XPath/JSON Path testers & Response Inspector\n"
            "  - Enhanced proxy panel: file import, auto-remove dead\n"
        )

        ctk.CTkLabel(card, text=info_text, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY, justify="left"
                      ).grid(row=1, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=(0, Spacing.MD))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_ui(self, engine):
        if not engine:
            return
        stats = engine.rate_limiter.get_stats()
        self._rps_slider.set(stats.get("global_rps", 10.0))
        self._strategy_menu.set(stats.get("strategy", "token_bucket"))
        self._theme_var.set("dark" if theme.is_dark else "light")
