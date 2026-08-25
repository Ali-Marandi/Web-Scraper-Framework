"""
WebScraper Pro - Dashboard / Scraper Panel
Main scraping interface with URL input, extraction rules, page actions, and results preview.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import (
    theme, Colors, Typography, Spacing, Radius,
)
from core.data_parser import ExtractionRule, ExtractionMethod
from core.scraper_engine import ScrapingMode


class DashboardPanel(ctk.CTkFrame):
    """Main scraper panel with URL input, rules manager, and results display."""

    METHOD_OPTIONS = [m.value for m in ExtractionMethod]
    ACTION_TYPES = ["click", "type", "scroll", "wait", "select", "hover"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._extraction_rules: list[ExtractionRule] = []
        self._page_actions: list[dict] = []
        self._build_toolbar()
        self._build_main_area()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="Scraping Mode", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.XS))
        self._mode_seg = ctk.CTkSegmentedButton(
            bar, values=[m.value.capitalize() for m in ScrapingMode],
            command=self._on_mode_change, font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            selected_color=theme.colors.BRAND_PRIMARY, selected_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
        )
        self._mode_seg.set("Static")
        self._mode_seg.grid(row=0, column=1, padx=Spacing.XS, pady=Spacing.SM, sticky="w")

        self._btn_start = ctk.CTkButton(
            bar, text=">>  Start", width=100, font=(Typography.FONT_FAMILY, Typography.BODY_SIZE, "bold"),
            fg_color=theme.colors.SUCCESS, hover_color=theme.colors.SUCCESS, corner_radius=Radius.MD,
            command=self._on_start,
        )
        self._btn_start.grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM)

        self._btn_stop = ctk.CTkButton(
            bar, text="Stop", width=80, font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR, corner_radius=Radius.MD,
            command=self._on_stop, state="disabled",
        )
        self._btn_stop.grid(row=0, column=3, padx=(0, Spacing.MD), pady=Spacing.SM)

    def _build_main_area(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(Spacing.MD, Spacing.XS / 2), pady=Spacing.MD)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(Spacing.XS / 2, Spacing.MD), pady=Spacing.MD)
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_url_section(left)
        self._build_options_section(left)
        self._build_rules_section(left)
        self._build_actions_section(left)
        self._build_results_section(right)
        self._build_export_section(right)

    # ------------------------------------------------------------------
    # URL Section
    # ------------------------------------------------------------------

    def _build_url_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Target URLs (one per line)",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._url_text = ctk.CTkTextbox(
            card, height=80, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._url_text.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    # ------------------------------------------------------------------
    # Options Section
    # ------------------------------------------------------------------

    def _build_options_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="ew", pady=Spacing.SM)
        card.grid_columnconfigure(2, weight=1)

        self._var_auto_scroll = ctk.BooleanVar(value=False)
        self._var_follow_links = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(card, text="Auto-scroll", variable=self._var_auto_scroll,
                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                         text_color=theme.colors.TEXT_SECONDARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM)

        ctk.CTkCheckBox(card, text="Follow links", variable=self._var_follow_links,
                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                         text_color=theme.colors.TEXT_SECONDARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=0, column=1, padx=Spacing.SM, pady=Spacing.SM)

        ctk.CTkLabel(card, text="Max Pages", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM, sticky="e")
        self._max_pages_entry = ctk.CTkEntry(
            card, width=70, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._max_pages_entry.insert("0", "100")
        self._max_pages_entry.grid(row=0, column=3, padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

    # ------------------------------------------------------------------
    # Extraction Rules Section
    # ------------------------------------------------------------------

    def _build_rules_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=2, column=0, sticky="nsew", pady=Spacing.SM)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Extraction Rules", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        for col, (text, cmd) in enumerate([
            ("+ Add", self._add_rule), ("Edit", self._edit_rule), ("Remove", self._remove_rule)
        ]):
            ctk.CTkButton(btn_frame, text=text, width=65, height=26, font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                           text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                           border_color=theme.colors.BORDER, command=cmd).grid(row=0, column=col, padx=2)

        self._rules_listbox = ctk.CTkTextbox(
            card, height=140, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._rules_listbox.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _refresh_rules_list(self):
        self._rules_listbox.configure(state="normal")
        self._rules_listbox.delete("0.0", "end")
        for i, rule in enumerate(self._extraction_rules):
            list_flag = " [LIST]" if rule.is_list else ""
            attr = f" attr={rule.attribute}" if rule.attribute else ""
            default = f" default=\"{rule.default}\"" if rule.default else ""
            line = f"{i + 1}. {rule.name}  |  {rule.method.value}  |  {rule.selector}{attr}{default}{list_flag}\n"
            self._rules_listbox.insert("end", line)
        self._rules_listbox.configure(state="disabled")

    def _add_rule(self):
        self._show_rule_dialog()

    def _edit_rule(self):
        sel = self._rules_listbox.get("1.0", "end").strip().split("\n")
        if not sel:
            return
        idx = int(self._rules_listbox.index("insert").split(".")[0]) - 1
        if 0 <= idx < len(self._extraction_rules):
            self._show_rule_dialog(edit_index=idx)

    def _remove_rule(self):
        if self._extraction_rules:
            self._extraction_rules.pop()
            self._refresh_rules_list()

    def _show_rule_dialog(self, edit_index: int = -1):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Extraction Rule" if edit_index >= 0 else "Add Extraction Rule")
        dialog.geometry("460x380")
        dialog.configure(fg_color=theme.colors.BG_MAIN)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.grid_columnconfigure(1, weight=1)

        existing = self._extraction_rules[edit_index] if edit_index >= 0 else None

        labels = ["Name", "Method", "Selector", "Attribute", "Default Value"]
        row = 0
        for lbl_text in labels:
            ctk.CTkLabel(dialog, text=lbl_text, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                          text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=0, sticky="w",
                                                                        padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM)
            row += 1

        name_entry = ctk.CTkEntry(dialog, font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY)
        name_entry.grid(row=0, column=1, sticky="ew", padx=(0, Spacing.MD), pady=Spacing.SM)

        method_menu = ctk.CTkOptionMenu(dialog, values=self.METHOD_OPTIONS,
                                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                                         fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
                                         button_hover_color=theme.colors.BG_HOVER,
                                         dropdown_fg_color=theme.colors.BG_ELEVATED,
                                         text_color=theme.colors.TEXT_PRIMARY,
                                         corner_radius=Radius.MD)
        method_menu.grid(row=1, column=1, sticky="ew", padx=(0, Spacing.MD), pady=Spacing.SM)

        selector_entry = ctk.CTkEntry(dialog, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
                                       fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                       border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY)
        selector_entry.grid(row=2, column=1, sticky="ew", padx=(0, Spacing.MD), pady=Spacing.SM)

        attr_entry = ctk.CTkEntry(dialog, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY)
        attr_entry.grid(row=3, column=1, sticky="ew", padx=(0, Spacing.MD), pady=Spacing.SM)

        default_entry = ctk.CTkEntry(dialog, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
                                      fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                      border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY)
        default_entry.grid(row=4, column=1, sticky="ew", padx=(0, Spacing.MD), pady=Spacing.SM)

        var_is_list = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(dialog, text="Extract as list", variable=var_is_list,
                         font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                         text_color=theme.colors.TEXT_SECONDARY,
                         fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                         ).grid(row=5, column=0, columnspan=2, sticky="w", padx=Spacing.MD, pady=Spacing.SM)

        if existing:
            name_entry.insert("0", existing.name)
            method_menu.set(existing.method.value)
            selector_entry.insert("0", existing.selector)
            if existing.attribute:
                attr_entry.insert("0", existing.attribute)
            if existing.default:
                default_entry.insert("0", existing.default)
            var_is_list.set(existing.is_list)

        def _save():
            name = name_entry.get().strip()
            selector = selector_entry.get().strip()
            if not name or not selector:
                messagebox.showwarning("Validation", "Name and selector are required.", parent=dialog)
                return
            rule = ExtractionRule(
                name=name,
                method=ExtractionMethod(method_menu.get()),
                selector=selector,
                attribute=attr_entry.get().strip() or None,
                default=default_entry.get().strip() or None,
                is_list=var_is_list.get(),
            )
            if edit_index >= 0:
                self._extraction_rules[edit_index] = rule
            else:
                self._extraction_rules.append(rule)
            self._refresh_rules_list()
            dialog.destroy()

        ctk.CTkButton(dialog, text="Save Rule", command=_save, width=140,
                       font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD).grid(row=6, column=0, columnspan=2, pady=Spacing.MD)

    # ------------------------------------------------------------------
    # Page Actions Section (Dynamic mode)
    # ------------------------------------------------------------------

    def _build_actions_section(self, parent):
        self._actions_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        self._actions_card.grid(row=3, column=0, sticky="ew", pady=Spacing.SM)
        self._actions_card.grid_columnconfigure(1, weight=1)

        header = ctk.CTkFrame(self._actions_card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=4, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Page Actions (Dynamic Mode)",
                      font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(header, text="+ Add Action", width=90, height=24,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._add_action_row).grid(row=0, column=1)

        self._action_rows_frame = ctk.CTkFrame(self._actions_card, fg_color="transparent")
        self._action_rows_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _add_action_row(self):
        row_idx = len(self._action_rows_frame.winfo_children())
        row_frame = ctk.CTkFrame(self._action_rows_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=1)

        type_menu = ctk.CTkOptionMenu(row_frame, values=self.ACTION_TYPES, width=80,
                                        font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                        fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
                                        button_hover_color=theme.colors.BG_HOVER,
                                        dropdown_fg_color=theme.colors.BG_ELEVATED,
                                        text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD)
        type_menu.grid(row=0, column=0, padx=(0, Spacing.XS))

        sel_entry = ctk.CTkEntry(row_frame, placeholder_text="Selector", font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=26)
        sel_entry.grid(row=0, column=1, padx=Spacing.XS, sticky="ew")

        val_entry = ctk.CTkEntry(row_frame, placeholder_text="Value", font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=26)
        val_entry.grid(row=0, column=2, padx=Spacing.XS, sticky="ew")

        def _remove_row():
            row_frame.destroy()
            self._rebuild_action_rows()

        ctk.CTkButton(row_frame, text="X", width=26, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=_remove_row).grid(row=0, column=3, padx=(Spacing.XS, 0))

    def _rebuild_action_rows(self):
        pass

    def _collect_page_actions(self) -> list[dict]:
        actions = []
        for row in self._action_rows_frame.winfo_children():
            if isinstance(row, ctk.CTkFrame):
                widgets = row.winfo_children()
                if len(widgets) >= 3:
                    action_type = widgets[0].get()
                    selector = widgets[1].get().strip()
                    value = widgets[2].get().strip()
                    actions.append({
                        "action_type": action_type,
                        "selector": selector,
                        "value": value,
                        "delay": 0.5,
                    })
        return actions

    # ------------------------------------------------------------------
    # Results Section
    # ------------------------------------------------------------------

    def _build_results_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, Spacing.SM))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Results Preview",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._results_text = ctk.CTkTextbox(
            card, height=400, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._results_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _display_results(self, results: list[dict]):
        self._results_text.configure(state="normal")
        self._results_text.delete("0.0", "end")
        if not results:
            self._results_text.insert("end", "No results yet. Configure rules and start scraping.")
        else:
            headers = list(results[0].keys())
            col_widths = {h: max(len(str(h)), max((len(str(r.get(h, ""))) for r in results), default=0)) for h in headers}
            col_widths = {h: min(w, 40) for h, w in col_widths.items()}

            header_line = "  |  ".join(str(h).ljust(col_widths.get(h, 12)) for h in headers)
            sep_line = "-+-".join("-" * col_widths.get(h, 12) for h in headers)
            self._results_text.insert("end", header_line + "\n")
            self._results_text.insert("end", sep_line + "\n")
            for row in results:
                line = "  |  ".join(str(row.get(h, ""))[:col_widths.get(h, 12)].ljust(col_widths.get(h, 12)) for h in headers)
                self._results_text.insert("end", line + "\n")
        self._results_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Export Section
    # ------------------------------------------------------------------

    def _build_export_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="ew", pady=Spacing.SM)

        ctk.CTkLabel(card, text="Export", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, columnspan=5,
                                                                     sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        formats = [("CSV", "csv"), ("JSON", "json"), ("Excel", "xlsx"), ("XML", "xml"), ("HTML", "html")]
        for col, (label, fmt) in enumerate(formats):
            ctk.CTkButton(
                card, text=label, width=65, height=28,
                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                border_color=theme.colors.BORDER,
                command=lambda f=fmt: self._on_export(f),
            ).grid(row=1, column=col, padx=(Spacing.MD if col == 0 else 2, Spacing.MD if col == 4 else 2),
                   pady=(Spacing.XS, Spacing.MD))

    def _on_export(self, fmt: str):
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} files", f"*.{fmt}"), ("All files", "*.*")],
        )
        if path:
            engine = self.winfo_toplevel().engine
            if engine and engine.results:
                try:
                    engine.export_results(fmt, path)
                    messagebox.showinfo("Export", f"Results exported to:\n{path}")
                except Exception as e:
                    messagebox.showerror("Export Error", str(e))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_mode_change(self, value):
        pass

    def _on_start(self):
        engine = self.winfo_toplevel().engine
        if not engine:
            return
        urls_text = self._url_text.get("0.0", "end").strip()
        if not urls_text:
            return
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        mode_map = {"Static": ScrapingMode.STATIC, "Dynamic": ScrapingMode.DYNAMIC, "Auto": ScrapingMode.AUTO}
        mode = mode_map.get(self._mode_seg.get(), ScrapingMode.STATIC)

        for rule in self._extraction_rules:
            engine.data_parser.add_rule(rule)

        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        engine.scrape_urls(urls, mode, callback=self._on_progress)

    def _on_stop(self):
        engine = self.winfo_toplevel().engine
        if engine:
            engine.stop()
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")

    def _on_progress(self, current, total, records):
        engine = self.winfo_toplevel().engine
        if engine:
            self._display_results(engine.results)
        if engine and engine.state.value == "idle":
            self._btn_start.configure(state="normal")
            self._btn_stop.configure(state="disabled")
            self._display_results(engine.results)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_ui(self, engine):
        if engine:
            self._display_results(engine.results)
            if engine.state.value == "idle":
                self._btn_start.configure(state="normal")
                self._btn_stop.configure(state="disabled")
            else:
                self._btn_start.configure(state="disabled")
                self._btn_stop.configure(state="normal")
            for rule in engine.data_parser.rules:
                if rule not in self._extraction_rules:
                    self._extraction_rules.append(rule)
            self._refresh_rules_list()
