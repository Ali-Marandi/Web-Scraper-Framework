"""
WebScraper Pro - Proxy Management Panel
Add, test, and manage proxy servers with rotation strategies.
"""

import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import theme, Typography, Spacing, Radius
from core.proxy_manager import ProxyConfig, ProxyType


class ProxyPanel(ctk.CTkFrame):
    """Proxy pool management with add, test, remove, and rotation controls."""

    ROTATION_STRATEGIES = ["random", "round_robin", "least_used", "fastest"]
    PROXY_TYPE_OPTIONS = [t.value for t in ProxyType]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._test_thread: threading.Thread | None = None
        self._testing = False

        self._build_add_form()
        self._build_stats_bar()
        self._build_proxy_list()
        self._build_controls()

    # ------------------------------------------------------------------
    # Add Proxy Form
    # ------------------------------------------------------------------

    def _build_add_form(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(3, weight=1)
        card.grid_columnconfigure(5, weight=1)

        row = 0
        labels = ["Host", "Port", "Type", "Username", "Password"]
        for col_offset, lbl in enumerate(labels):
            ctk.CTkLabel(card, text=lbl, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                          text_color=theme.colors.TEXT_SECONDARY
                          ).grid(row=row, column=col_offset * 2, padx=(Spacing.MD if col_offset == 0 else 0, Spacing.XS),
                                 pady=(Spacing.SM, 0), sticky="w")

        entry_opts = dict(
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=30,
        )

        self._host_entry = ctk.CTkEntry(card, placeholder_text="192.168.1.1", width=160, **entry_opts)
        self._host_entry.grid(row=1, column=0, padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM, sticky="ew")

        self._port_entry = ctk.CTkEntry(card, placeholder_text="8080", width=80, **entry_opts)
        self._port_entry.grid(row=1, column=2, padx=Spacing.XS, pady=Spacing.SM)

        self._type_menu = ctk.CTkOptionMenu(
            card, values=self.PROXY_TYPE_OPTIONS, width=90,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
        )
        self._type_menu.set("http")
        self._type_menu.grid(row=1, column=4, padx=Spacing.XS, pady=Spacing.SM)

        self._user_entry = ctk.CTkEntry(card, placeholder_text="user", width=120, **entry_opts)
        self._user_entry.grid(row=1, column=6, padx=Spacing.XS, pady=Spacing.SM, sticky="ew")

        self._pass_entry = ctk.CTkEntry(card, placeholder_text="pass", width=120, show="*", **entry_opts)
        self._pass_entry.grid(row=1, column=8, padx=(Spacing.XS, Spacing.XS), pady=Spacing.SM, sticky="ew")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=9, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))

        ctk.CTkButton(btn_frame, text="Add Proxy", width=110, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._add_proxy
                       ).pack(side="left", padx=(0, Spacing.SM))

        ctk.CTkButton(btn_frame, text="Import from File", width=130, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._import_from_file
                       ).pack(side="left", padx=Spacing.SM)

    # ------------------------------------------------------------------
    # Stats Bar
    # ------------------------------------------------------------------

    def _build_stats_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure((0, 1, 2), weight=1)

        self._stat_total = ctk.CTkLabel(bar, text="Total: 0",
                                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                         text_color=theme.colors.TEXT_SECONDARY)
        self._stat_total.grid(row=0, column=0, padx=Spacing.MD, pady=Spacing.SM, sticky="w")

        self._stat_healthy = ctk.CTkLabel(bar, text="Healthy: 0",
                                          font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                          text_color=theme.colors.TEXT_SUCCESS)
        self._stat_healthy.grid(row=0, column=1, padx=Spacing.MD, pady=Spacing.SM)

        self._stat_rate = ctk.CTkLabel(bar, text="Success Rate: --",
                                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                       text_color=theme.colors.TEXT_SECONDARY)
        self._stat_rate.grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM, sticky="e")

    # ------------------------------------------------------------------
    # Proxy List
    # ------------------------------------------------------------------

    def _build_proxy_list(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.SM)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self._proxy_text = ctk.CTkTextbox(
            card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._proxy_text.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _build_controls(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=3, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))

        ctk.CTkLabel(bar, text="Rotation", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM)

        self._rotation_menu = ctk.CTkOptionMenu(
            bar, values=self.ROTATION_STRATEGIES, width=120,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_rotation_change,
        )
        self._rotation_menu.set("random")
        self._rotation_menu.pack(side="left", padx=Spacing.XS, pady=Spacing.SM)

        self._progress_label = ctk.CTkLabel(bar, text="", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                             text_color=theme.colors.TEXT_SECONDARY)
        self._progress_label.pack(side="left", padx=Spacing.MD, pady=Spacing.SM)

        btns = [
            ("Test All", theme.colors.BRAND_PRIMARY, self._test_all),
            ("Remove Selected", theme.colors.WARNING, self._remove_selected),
            ("Clear All", theme.colors.ERROR, self._clear_all),
        ]
        for text, color, cmd in btns:
            ctk.CTkButton(bar, text=text, width=120, height=28,
                           font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                           fg_color=color, hover_color=color,
                           corner_radius=Radius.MD, command=cmd
                           ).pack(side="right", padx=(0, Spacing.SM if text != "Clear All" else Spacing.MD), pady=Spacing.SM)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_proxy(self):
        host = self._host_entry.get().strip()
        port_str = self._port_entry.get().strip()
        if not host or not port_str:
            messagebox.showwarning("Validation", "Host and port are required.")
            return
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning("Validation", "Port must be a number.")
            return

        ptype = ProxyType(self._type_menu.get())
        username = self._user_entry.get().strip() or None
        password = self._pass_entry.get().strip() or None

        config = ProxyConfig(host=host, port=port, proxy_type=ptype,
                              username=username, password=password)
        engine = self.winfo_toplevel().engine
        if engine:
            engine.proxy_manager.add_proxy(config)
            self.update_ui(engine)

        self._host_entry.delete(0, "end")
        self._port_entry.delete(0, "end")
        self._user_entry.delete(0, "end")
        self._pass_entry.delete(0, "end")

    def _import_from_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        engine = self.winfo_toplevel().engine
        if engine:
            try:
                count = engine.proxy_manager.add_proxies_from_file(path)
                messagebox.showinfo("Import", f"Imported {count} proxies from file.")
                self.update_ui(engine)
            except Exception as e:
                messagebox.showerror("Import Error", str(e))

    def _on_rotation_change(self, value):
        engine = self.winfo_toplevel().engine
        if engine:
            engine.proxy_manager.rotation_strategy = value

    def _test_all(self):
        if self._testing:
            return
        engine = self.winfo_toplevel().engine
        if not engine or engine.proxy_manager.proxy_count == 0:
            return
        self._testing = True
        self._progress_label.configure(text="Testing...")

        def _run():
            def _cb(done, total, result):
                self.after(0, lambda: self._progress_label.configure(
                    text=f"Testing {done}/{total}"))

            engine.proxy_manager.test_all_proxies(callback=_cb)
            self._testing = False
            self.after(0, lambda: self._progress_label.configure(text="Done"))
            self.after(0, lambda: self.update_ui(engine))

        self._test_thread = threading.Thread(target=_run, daemon=True)
        self._test_thread.start()

    def _remove_selected(self):
        content = self._proxy_text.get("1.0", "end").strip()
        if not content:
            return
        engine = self.winfo_toplevel().engine
        if engine:
            lines = content.split("\n")
            for line in lines:
                parts = line.split("  ", 1)
                if parts:
                    proxy_name = parts[0].strip()
                    engine.proxy_manager.remove_proxy(proxy_name)
            self.update_ui(engine)

    def _clear_all(self):
        engine = self.winfo_toplevel().engine
        if engine:
            engine.proxy_manager.clear_all()
            self.update_ui(engine)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_ui(self, engine):
        if not engine:
            return
        pm = engine.proxy_manager
        stats = pm.get_all_stats()
        summary = pm.get_summary()

        self._proxy_text.configure(state="normal")
        self._proxy_text.delete("0.0", "end")
        if not stats:
            self._proxy_text.insert("end", "No proxies added yet.")
        else:
            for s in stats:
                status = "OK" if s["healthy"] and not s["banned"] else "BANNED"
                line = (f"{s['proxy']:<40}  |  reqs: {s['total_requests']:<5}  "
                        f"ok: {s['successful']:<5}  fail: {s['failed']:<5}  "
                        f"rate: {s['success_rate']:.0f}%  |  {status}")
                self._proxy_text.insert("end", line + "\n")
        self._proxy_text.configure(state="disabled")

        self._stat_total.configure(text=f"Total: {summary['total_proxies']}")
        self._stat_healthy.configure(text=f"Healthy: {summary['healthy_proxies']}")
        self._stat_rate.configure(text=f"Success Rate: {summary['overall_success_rate']:.1f}%")

        self._rotation_menu.set(summary.get("rotation_strategy", "random"))
