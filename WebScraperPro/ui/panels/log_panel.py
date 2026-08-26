import customtkinter as ctk
import datetime
from ui.styles import theme, Typography, Spacing, Radius


class LogPanel(ctk.CTkFrame):
    """Real-time log viewer with color-coded levels, filtering, and auto-scroll."""

    LEVEL_COLORS = {
        "debug": None,
        "info": None,
        "success": "TEXT_SUCCESS",
        "warning": "TEXT_WARNING",
        "error": "TEXT_ERROR",
    }
    LEVEL_ICONS = {
        "debug": "  ",
        "info": "i  ",
        "success": "+  ",
        "warning": "!  ",
        "error": "X  ",
    }

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._max_lines = 500
        self._auto_scroll = True
        self._filter_level = "all"
        self._all_logs: list[tuple[str, str, str]] = []  # (timestamp, message, level)

        self._build_toolbar()
        self._build_log_area()

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))

        ctk.CTkLabel(bar, text="Log Level", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM)

        self._filter_menu = ctk.CTkOptionMenu(
            bar, values=["all", "info", "success", "warning", "error"], width=100,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_filter_change,
        )
        self._filter_menu.set("all")
        self._filter_menu.pack(side="left", padx=Spacing.XS, pady=Spacing.SM)

        self._var_auto_scroll = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(bar, text="Auto-scroll", variable=self._var_auto_scroll,
                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                         text_color=theme.colors.TEXT_SECONDARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         command=self._on_auto_scroll_toggle,
                         ).pack(side="left", padx=Spacing.LG, pady=Spacing.SM)

        self._count_label = ctk.CTkLabel(bar, text="0 entries",
                                          font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                          text_color=theme.colors.TEXT_MUTED)
        self._count_label.pack(side="right", padx=Spacing.MD, pady=Spacing.SM)

        # Clear button
        ctk.CTkButton(bar, text="Clear", width=60, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._clear_logs
                       ).pack(side="right", padx=(0, Spacing.XS), pady=Spacing.SM)

        # Copy All button
        ctk.CTkButton(bar, text="Copy All", width=70, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._copy_all
                       ).pack(side="right", padx=(0, Spacing.XS), pady=Spacing.SM)

    def _build_log_area(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self._log_text = ctk.CTkTextbox(
            card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            activate_scrollbars=True,
        )
        self._log_text.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    def add_log(self, message: str, level: str = "info"):
        """Add a log entry (thread-safe via after)."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._all_logs.append((timestamp, message, level.lower()))

        # Trim to max
        if len(self._all_logs) > self._max_lines:
            self._all_logs = self._all_logs[-self._max_lines:]

        # Only refresh if visible
        try:
            if self.winfo_viewable():
                self.after(0, self._refresh_display)
        except Exception:
            pass

    def _refresh_display(self):
        self._log_text.configure(state="normal")
        self._log_text.delete("0.0", "end")

        filtered = self._all_logs
        if self._filter_level != "all":
            filtered = [log for log in self._all_logs if log[2] == self._filter_level]

        c = theme.colors
        for ts, msg, lvl in filtered:
            color_key = self.LEVEL_COLORS.get(lvl)
            icon = self.LEVEL_ICONS.get(lvl, "  ")
            color = getattr(c, color_key, None) if color_key else None

            tag_name = f"log_{lvl}_{ts}"
            self._log_text.insert("end", f"[{ts}] ", "timestamp")
            self._log_text.insert("end", f"{icon}", tag_name)
            self._log_text.insert("end", f"{msg}\n", tag_name)

            if color:
                self._log_text.tag_config(tag_name, text_color=color)
            else:
                self._log_text.tag_config(tag_name, text_color=c.TEXT_SECONDARY)

        self._log_text.tag_config("timestamp", text_color=c.TEXT_MUTED)

        if self._var_auto_scroll.get():
            self._log_text.see("end")

        self._log_text.configure(state="disabled")
        self._count_label.configure(text=f"{len(filtered)} entries")

    def _on_filter_change(self, value):
        self._filter_level = value
        self._refresh_display()

    def _on_auto_scroll_toggle(self):
        self._auto_scroll = self._var_auto_scroll.get()

    def _clear_logs(self):
        self._all_logs.clear()
        self._log_text.configure(state="normal")
        self._log_text.delete("0.0", "end")
        self._log_text.configure(state="disabled")
        self._count_label.configure(text="0 entries")

    def _copy_all(self):
        try:
            text = "\n".join(f"[{ts}] [{lvl.upper()}] {msg}" for ts, msg, lvl in self._all_logs)
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass

    def update_ui(self, engine):
        pass  # Logs are pushed, not polled
