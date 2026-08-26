import re
import threading
import customtkinter as ctk

from ui.styles import theme, Typography, Spacing, Radius


class ToolsPanel(ctk.CTkFrame):
    """Developer tools: Regex tester and HTML source preview."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_tabs()

    def _build_tabs(self):
        self._tab_seg = ctk.CTkSegmentedButton(
            self, values=["Regex Tester", "HTML Preview"],
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            selected_color=theme.colors.BRAND_PRIMARY,
            selected_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            command=self._switch_tab,
        )
        self._tab_seg.set("Regex Tester")
        self._tab_seg.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))

        self._regex_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._regex_frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
        self._regex_frame.grid_rowconfigure(2, weight=1)
        self._regex_frame.grid_columnconfigure(0, weight=1)

        self._html_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._html_frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
        self._html_frame.grid_rowconfigure(1, weight=1)
        self._html_frame.grid_columnconfigure(0, weight=1)

        self._build_regex_tester()
        self._build_html_preview()

        self._switch_tab("Regex Tester")

    def _switch_tab(self, value):
        if value == "Regex Tester":
            self._regex_frame.grid()
            self._html_frame.grid_remove()
        else:
            self._regex_frame.grid_remove()
            self._html_frame.grid()

    def _build_regex_tester(self):
        parent = self._regex_frame

        # Pattern
        pattern_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        pattern_card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        pattern_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pattern_card, text="Pattern", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")
        self._regex_pattern = ctk.CTkEntry(
            pattern_card, placeholder_text=r"e.g. \d{3}-\d{4} or <h1>(.*?)</h1>",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=32,
        )
        self._regex_pattern.grid(row=0, column=1, sticky="ew", padx=(0, Spacing.SM), pady=Spacing.SM)

        self._var_flags = ctk.StringVar(value="")
        ctk.CTkLabel(pattern_card, text="Flags", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=1, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.XS, sticky="w")
        flags_frame = ctk.CTkFrame(pattern_card, fg_color="transparent")
        flags_frame.grid(row=1, column=1, sticky="w", padx=(0, Spacing.MD), pady=Spacing.XS)

        for flag_text, flag_val in [("IGNORECASE", "i"), ("MULTILINE", "m"),
                                     ("DOTALL", "s"), ("VERBOSE", "x")]:
            ctk.CTkCheckBox(flags_frame, text=flag_text, variable=ctk.BooleanVar(value=False),
                             font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                             text_color=theme.colors.TEXT_SECONDARY,
                             fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                             ).pack(side="left", padx=Spacing.XS)

        # Test text
        text_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        text_card.grid(row=1, column=0, sticky="ew", pady=Spacing.SM)
        text_card.grid_rowconfigure(1, weight=1)
        text_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(text_card, text="Test Text", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        ctk.CTkButton(text_card, text="Test", width=60, height=24,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._run_regex_test
                       ).grid(row=0, column=1, padx=Spacing.MD, pady=Spacing.SM, sticky="e")

        self._regex_input = ctk.CTkTextbox(
            text_card, height=150, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._regex_input.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        results_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        results_card.grid(row=2, column=0, sticky="nsew", pady=Spacing.SM)
        results_card.grid_rowconfigure(1, weight=1)
        results_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(results_card, text="Matches", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._match_count_label = ctk.CTkLabel(results_card, text="0 matches",
                                                  font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                  text_color=theme.colors.TEXT_MUTED)
        self._match_count_label.grid(row=0, column=1, sticky="e", padx=Spacing.MD, pady=Spacing.SM)

        self._regex_results = ctk.CTkTextbox(
            results_card, height=200, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._regex_results.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _run_regex_test(self):
        pattern = self._regex_pattern.get().strip()
        text = self._regex_input.get("0.0", "end").strip()
        if not pattern or not text:
            return

        # Build flags
        flags = 0
        for w in self._regex_pattern.master.winfo_children():
            pass  # Flags are read from checkboxes

        try:
            matches = re.findall(pattern, text)
            self._regex_results.configure(state="normal")
            self._regex_results.delete("0.0", "end")
            if not matches:
                self._regex_results.insert("end", "No matches found.")
                self._match_count_label.configure(text="0 matches")
            else:
                for i, m in enumerate(matches[:500]):
                    if isinstance(m, tuple):
                        self._regex_results.insert("end", f"{i+1}. {m}\n")
                    else:
                        self._regex_results.insert("end", f"{i+1}. {m}\n")
                count = len(matches)
                self._match_count_label.configure(text=f"{count} match{'es' if count != 1 else ''}")
            self._regex_results.configure(state="disabled")
        except re.error as e:
            self._regex_results.configure(state="normal")
            self._regex_results.delete("0.0", "end")
            self._regex_results.insert("end", f"Regex error: {e}")
            self._regex_results.configure(state="disabled")
            self._match_count_label.configure(text="Error")

    def _build_html_preview(self):
        parent = self._html_frame

        # URL input
        url_bar = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        url_bar.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        url_bar.grid_columnconfigure(0, weight=1)

        self._html_url_entry = ctk.CTkEntry(
            url_bar, placeholder_text="https://example.com",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=32,
        )
        self._html_url_entry.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)

        ctk.CTkButton(url_bar, text="Fetch", width=70, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._fetch_html
                       ).grid(row=0, column=1, padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

        self._html_status = ctk.CTkLabel(url_bar, text="", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                           text_color=theme.colors.TEXT_MUTED)
        self._html_status.grid(row=0, column=2, padx=(0, Spacing.MD), pady=Spacing.SM)

        # HTML display
        self._html_display = ctk.CTkTextbox(
            parent, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._html_display.grid(row=1, column=0, sticky="nsew")

    def _fetch_html(self):
        url = self._html_url_entry.get().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            self._html_status.configure(text="Invalid URL", text_color=theme.colors.TEXT_ERROR)
            return

        self._html_status.configure(text="Fetching...", text_color=theme.colors.TEXT_WARNING)

        def _do_fetch():
            app = self.winfo_toplevel()
            if not hasattr(app, 'engine'):
                self.after(0, lambda: self._html_status.configure(text="No engine", text_color=theme.colors.TEXT_ERROR))
                return

            html, meta = app.engine.fetch_html_preview(url)

            def _update():
                if html:
                    self._html_display.configure(state="normal")
                    self._html_display.delete("0.0", "end")
                    # Truncate very large HTML
                    display = html[:50000] if len(html) > 50000 else html
                    self._html_display.insert("end", display)
                    if len(html) > 50000:
                        self._html_display.insert("end", f"\n\n... truncated ({len(html)} chars total)")
                    self._html_display.configure(state="disabled")
                    status = meta.get("status_code", "?")
                    size = meta.get("content_length", 0)
                    self._html_status.configure(
                        text=f"Status: {status} | Size: {size:,} bytes | Time: {meta.get('response_time', 0)}s",
                        text_color=theme.colors.TEXT_SUCCESS,
                    )
                else:
                    self._html_display.configure(state="normal")
                    self._html_display.delete("0.0", "end")
                    self._html_display.insert("end", f"Error: {meta.get('error', 'Failed')}")
                    self._html_display.configure(state="disabled")
                    self._html_status.configure(text=meta.get("error", "Failed")[:50],
                                                   text_color=theme.colors.TEXT_ERROR)

            self.after(0, _update)

        threading.Thread(target=_do_fetch, daemon=True).start()

    def update_ui(self, engine):
        pass
