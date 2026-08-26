"""
WebScraper Pro - Proxy Management Panel
Add, test, and manage proxy servers with rotation strategies.
v1.3.0: Enhanced with detailed testing, file import options, auto-remove, live stats.
"""

import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import theme, Typography, Spacing, Radius
from core.proxy_manager import ProxyConfig, ProxyType, ProxyStats


class ProxyPanel(ctk.CTkFrame):
    """Proxy pool management with add, test, remove, and rotation controls."""

    ROTATION_STRATEGIES = ["random", "round_robin", "least_used", "fastest"]
    PROXY_TYPE_OPTIONS = [t.value for t in ProxyType]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._test_thread: threading.Thread | None = None
        self._testing = False
        self._test_results: list = []
        self._auto_remove_var = ctk.BooleanVar(value=True)

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

        ctk.CTkButton(btn_frame, text="Import File", width=110, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._import_from_file
                       ).pack(side="left", padx=Spacing.SM)

        ctk.CTkButton(btn_frame, text="Export List", width=100, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._export_list
                       ).pack(side="left", padx=Spacing.SM)

    # ------------------------------------------------------------------
    # Stats Bar
    # ------------------------------------------------------------------

    def _build_stats_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self._stat_total = ctk.CTkLabel(bar, text="Total: 0",
                                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                         text_color=theme.colors.TEXT_SECONDARY)
        self._stat_total.grid(row=0, column=0, padx=Spacing.MD, pady=Spacing.SM, sticky="w")

        self._stat_healthy = ctk.CTkLabel(bar, text="Healthy: 0",
                                          font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                          text_color=theme.colors.TEXT_SUCCESS)
        self._stat_healthy.grid(row=0, column=1, padx=Spacing.MD, pady=Spacing.SM)

        self._stat_banned = ctk.CTkLabel(bar, text="Banned: 0",
                                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                         text_color=theme.colors.TEXT_ERROR)
        self._stat_banned.grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM)

        self._stat_rate = ctk.CTkLabel(bar, text="Success: --",
                                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                       text_color=theme.colors.TEXT_SECONDARY)
        self._stat_rate.grid(row=0, column=3, padx=Spacing.MD, pady=Spacing.SM)

        self._stat_avg_time = ctk.CTkLabel(bar, text="Avg Time: --",
                                           font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                           text_color=theme.colors.TEXT_SECONDARY)
        self._stat_avg_time.grid(row=0, column=4, padx=Spacing.MD, pady=Spacing.SM)

        self._stat_requests = ctk.CTkLabel(bar, text="Requests: 0",
                                           font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                           text_color=theme.colors.TEXT_SECONDARY)
        self._stat_requests.grid(row=0, column=5, padx=Spacing.MD, pady=Spacing.SM, sticky="e")

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
        bar.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(bar, text="Rotation", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM, sticky="w")

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
        self._rotation_menu.grid(row=0, column=1, padx=Spacing.XS, pady=Spacing.SM)

        ctk.CTkCheckBox(
            bar, text="Auto-remove dead", variable=self._auto_remove_var,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            command=self._on_auto_remove_toggle,
        ).grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM)

        self._progress_label = ctk.CTkLabel(bar, text="", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                             text_color=theme.colors.TEXT_SECONDARY)
        self._progress_label.grid(row=0, column=3, padx=Spacing.MD, pady=Spacing.SM, sticky="e")

        btns = [
            ("Test All", theme.colors.BRAND_PRIMARY, self._test_all),
            ("Remove Dead", theme.colors.WARNING, self._remove_dead),
            ("Remove Selected", theme.colors.BG_ELEVATED, self._remove_selected),
            ("Clear All", theme.colors.ERROR, self._clear_all),
        ]
        for i, (text, color, cmd) in enumerate(btns):
            is_last = (i == len(btns) - 1)
            ctk.CTkButton(bar, text=text, width=110 if "Remove Dead" in text else 100, height=28,
                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=color, hover_color=color,
                           text_color=theme.colors.TEXT_INVERSE if color in (theme.colors.BRAND_PRIMARY, theme.colors.ERROR, theme.colors.WARNING) else theme.colors.TEXT_PRIMARY,
                           corner_radius=Radius.MD, command=cmd
                           ).grid(row=1, column=0, columnspan=4, sticky="e", padx=(0, Spacing.MD if is_last else 2), pady=(0, Spacing.SM))

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
            if hasattr(engine, '_log_panel'):
                engine._log_panel.add_log(f"Proxy added: {host}:{port}", "success")

        self._host_entry.delete(0, "end")
        self._port_entry.delete(0, "end")
        self._user_entry.delete(0, "end")
        self._pass_entry.delete(0, "end")

    def _import_from_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"),
                      ("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        engine = self.winfo_toplevel().engine
        if not engine:
            return

        try:
            if path.endswith(".json"):
                import json
                count = self._import_json(path, engine)
            else:
                ptype = ProxyType(self._type_menu.get())
                count = engine.proxy_manager.add_proxies_from_file(path, ptype)

            messagebox.showinfo("Import", f"Imported {count} proxies from file.")
            self.update_ui(engine)
            if hasattr(engine, '_log_panel'):
                engine._log_panel.add_log(f"Imported {count} proxies from {path}", "success")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _import_json(self, path: str, engine) -> int:
        import json
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    try:
                        ptype = ProxyType(self._type_menu.get())
                        engine.proxy_manager.add_proxy_from_string(item, ptype)
                        count += 1
                    except ValueError:
                        continue
                elif isinstance(item, dict):
                    try:
                        host = item.get("host", "")
                        port = int(item.get("port", 0))
                        ptype = ProxyType(item.get("type", "http"))
                        config = ProxyConfig(
                            host=host, port=port, proxy_type=ptype,
                            username=item.get("username"),
                            password=item.get("password"),
                        )
                        engine.proxy_manager.add_proxy(config)
                        count += 1
                    except (ValueError, KeyError):
                        continue
        elif isinstance(data, dict):
            for key, val in data.items():
                try:
                    ptype = ProxyType(val.get("type", "http")) if isinstance(val, dict) else ProxyType.HTTP
                    if isinstance(val, str):
                        engine.proxy_manager.add_proxy_from_string(val, ptype)
                    elif isinstance(val, dict):
                        config = ProxyConfig(
                            host=val.get("host", key), port=int(val.get("port", 0)),
                            proxy_type=ptype, username=val.get("username"),
                            password=val.get("password"),
                        )
                        engine.proxy_manager.add_proxy(config)
                    count += 1
                except (ValueError, KeyError):
                    continue

        return count

    def _export_list(self):
        engine = self.winfo_toplevel().engine
        if not engine or engine.proxy_manager.proxy_count == 0:
            messagebox.showinfo("Export", "No proxies to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            stats = engine.proxy_manager.get_all_stats()
            if path.endswith(".json"):
                import json
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for s in stats:
                        f.write(s["proxy"] + "\n")

            messagebox.showinfo("Export", f"Exported {len(stats)} proxies.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _on_rotation_change(self, value):
        engine = self.winfo_toplevel().engine
        if engine:
            engine.proxy_manager.rotation_strategy = value

    def _on_auto_remove_toggle(self):
        engine = self.winfo_toplevel().engine
        if engine:
            engine.proxy_manager._auto_remove_banned = self._auto_remove_var.get()

    def _test_all(self):
        if self._testing:
            return
        engine = self.winfo_toplevel().engine
        if not engine or engine.proxy_manager.proxy_count == 0:
            return
        self._testing = True
        self._test_results.clear()
        self._progress_label.configure(text="Testing...")

        def _run():
            def _cb(done, total, result):
                self._test_results.append(result)
                self.after(0, lambda: self._progress_label.configure(
                    text=f"Testing {done}/{total}"))

            engine.proxy_manager.test_all_proxies(callback=_cb)
            self._testing = False
            self.after(0, lambda: self._progress_label.configure(text="Test complete"))
            self.after(0, lambda: self._update_test_results(engine))
            self.after(0, lambda: self.update_ui(engine))

            # Auto-remove dead if enabled
            if self._auto_remove_var.get():
                self._auto_remove_dead(engine)

            if hasattr(engine, '_log_panel'):
                self.after(0, lambda: engine._log_panel.add_log(
                    f"Proxy test complete: {len(self._test_results)} tested", "info"))

        self._test_thread = threading.Thread(target=_run, daemon=True)
        self._test_thread.start()

    def _update_test_results(self, engine):
        self._proxy_text.configure(state="normal")
        self._proxy_text.delete("0.0", "end")

        if not self._test_results:
            return

        for r in self._test_results:
            if r["success"]:
                ip = r.get("ip", "") or ""
                time_ms = r["response_time"] * 1000
                line = (f"  OK    {r['proxy']:<45}  |  {ip:<18}  |  "
                        f"{time_ms:.0f}ms")
            else:
                err = r.get("error", "Unknown")
                line = f"  FAIL  {r['proxy']:<45}  |  {err}"
            self._proxy_text.insert("end", line + "\n")

        self._proxy_text.configure(state="disabled")

    def _auto_remove_dead(self, engine):
        removed = 0
        for r in self._test_results:
            if not r["success"]:
                if engine.proxy_manager.remove_proxy(r["proxy"]):
                    removed += 1
        if removed > 0:
            self.after(0, lambda: engine._log_panel.add_log(
                f"Auto-removed {removed} dead proxies", "warning"))
            self.after(0, lambda: self.update_ui(engine))

    def _remove_dead(self):
        engine = self.winfo_toplevel().engine
        if not engine:
            return

        stats = engine.proxy_manager.get_all_stats()
        removed = 0
        for s in stats:
            if not s["healthy"] or s["banned"]:
                if engine.proxy_manager.remove_proxy(s["proxy"]):
                    removed += 1

        self.update_ui(engine)
        if hasattr(engine, '_log_panel'):
            engine._log_panel.add_log(f"Removed {removed} dead/banned proxies", "warning")
        messagebox.showinfo("Remove Dead", f"Removed {removed} dead proxies.")

    def _remove_selected(self):
        engine = self.winfo_toplevel().engine
        if not engine:
            return
        stats = engine.proxy_manager.get_all_stats()
        removed = 0
        for s in stats:
            if not s["healthy"] or s["banned"]:
                if engine.proxy_manager.remove_proxy(s["proxy"]):
                    removed += 1
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

        # Only update proxy list if not currently testing (to avoid overwriting test results)
        if not self._testing:
            self._proxy_text.configure(state="normal")
            self._proxy_text.delete("0.0", "end")
            if not stats:
                self._proxy_text.insert("end", "  No proxies added yet.\n")
                self._proxy_text.insert("end", "  \n")
                self._proxy_text.insert("end", "  Supported formats:\n")
                self._proxy_text.insert("end", "    host:port\n")
                self._proxy_text.insert("end", "    user:pass@host:port\n")
                self._proxy_text.insert("end", "    host:port\n")
            else:
                for s in stats:
                    if s["healthy"] and not s["banned"]:
                        status = "OK"
                        avg_ms = s['avg_time'] * 1000
                        line = (f"  {status:<6} {s['proxy']:<45}  |  "
                                f"reqs: {s['total_requests']:<4}  ok: {s['successful']:<4}  "
                                f"fail: {s['failed']:<4}  rate: {s['success_rate']:<5.1f}%  "
                                f"avg: {avg_ms:.0f}ms")
                    else:
                        status = "BANNED" if s["banned"] else "DEAD"
                        line = (f"  {status:<6} {s['proxy']:<45}  |  "
                                f"reqs: {s['total_requests']:<4}  ok: {s['successful']:<4}  "
                                f"fail: {s['failed']:<4}  rate: {s['success_rate']:<5.1f}%")
                    self._proxy_text.insert("end", line + "\n")
            self._proxy_text.configure(state="disabled")

        self._stat_total.configure(text=f"Total: {summary['total_proxies']}")
        self._stat_healthy.configure(text=f"Healthy: {summary['healthy_proxies']}")
        banned_count = summary['total_proxies'] - summary['healthy_proxies']
        self._stat_banned.configure(text=f"Dead: {banned_count}")
        self._stat_rate.configure(text=f"Success: {summary['overall_success_rate']:.1f}%")
        self._stat_requests.configure(text=f"Requests: {summary['total_requests']}")

        # Average response time across all proxies
        if stats:
            times = [s['avg_time'] * 1000 for s in stats if s['avg_time'] > 0]
            if times:
                avg = sum(times) / len(times)
                self._stat_avg_time.configure(text=f"Avg: {avg:.0f}ms")

        self._rotation_menu.set(summary.get("rotation_strategy", "random"))
