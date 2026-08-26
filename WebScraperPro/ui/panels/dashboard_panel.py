"""
WebScraper Pro - Dashboard / Scraper Panel
Main scraping interface with URL input, extraction rules, page actions, results table, and project management.
"""

import json
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import theme, Typography, Spacing, Radius
from core.data_parser import ExtractionRule, ExtractionMethod
from core.scraper_engine import ScrapingMode
from core.templates import TEMPLATES, get_template_names
from ui.components.table_widget import DataTable


class DashboardPanel(ctk.CTkFrame):
    """Main scraper panel with URL input, rules manager, results table, and project controls."""

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
        bar.grid_columnconfigure(3, weight=1)

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
        self._btn_stop.grid(row=0, column=3, padx=Spacing.SM, pady=Spacing.SM)

        # Templates dropdown
        ctk.CTkLabel(bar, text="Templates", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=4, padx=(Spacing.LG, Spacing.XS))
        self._template_menu = ctk.CTkOptionMenu(
            bar, values=get_template_names(), width=160,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_template_selected,
        )
        self._template_menu.grid(row=0, column=5, padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

    def _build_main_area(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(Spacing.MD, 4), pady=Spacing.MD)
        left.grid_rowconfigure(3, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(4, Spacing.MD), pady=Spacing.MD)
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_project_bar(left)
        self._build_url_section(left)
        self._build_options_section(left)
        self._build_rules_section(left)
        self._build_actions_section(left)
        self._build_results_section(right)
        self._build_export_section(right)

    # ------------------------------------------------------------------
    # Project Bar
    # ------------------------------------------------------------------

    def _build_project_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))

        ctk.CTkLabel(bar, text="Project", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM)

        for text, cmd in [("New", self._new_project), ("Save", self._save_project),
                           ("Load", self._load_project), ("Import Rules", self._import_rules),
                           ("Export Rules", self._export_rules)]:
            ctk.CTkButton(bar, text=text, width=80, height=24,
                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                           text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                           border_width=1, border_color=theme.colors.BORDER,
                           command=cmd).pack(side="left", padx=2, pady=Spacing.SM)

    def _new_project(self):
        app = self.winfo_toplevel()
        if hasattr(app, 'engine'):
            app.engine.create_project("New Project")
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log("New project created", "info")

    def _save_project(self):
        app = self.winfo_toplevel()
        if not hasattr(app, 'engine'):
            return
        engine = app.engine
        # Gather current UI state into the project
        if not engine.current_project:
            engine.create_project("Untitled")
        proj = engine.current_project
        proj.urls = [u.strip() for u in self._url_text.get("0.0", "end").strip().splitlines() if u.strip()]
        proj.mode = ScrapingMode(self._mode_seg.get().lower())
        proj.extraction_rules = [self._rule_to_dict(r) for r in self._extraction_rules]
        proj.page_actions = self._collect_page_actions()
        proj.auto_scroll = self._var_auto_scroll.get()
        proj.follow_links = self._var_follow_links.get()
        try:
            proj.max_pages = int(self._max_pages_entry.get().strip() or "100")
        except ValueError:
            proj.max_pages = 100
        try:
            proj.max_depth = int(self._depth_entry.get().strip() or "1")
        except ValueError:
            proj.max_depth = 1
        engine.save_current_project()
        if hasattr(app, '_log_panel'):
            app._log_panel.add_log(f"Project saved: {proj.name}", "success")

    def _load_project(self):
        app = self.winfo_toplevel()
        if not hasattr(app, 'engine'):
            return
        engine = app.engine
        projects = engine.projects
        if not projects:
            messagebox.showinfo("Projects", "No saved projects found.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Load Project")
        dialog.geometry("500x350")
        dialog.configure(fg_color=theme.colors.BG_MAIN)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        listbox = ctk.CTkTextbox(dialog, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
                                  fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                  border_width=1, corner_radius=Radius.MD,
                                  text_color=theme.colors.TEXT_PRIMARY)
        listbox.pack(fill="both", expand=True, padx=Spacing.MD, pady=Spacing.MD)

        for p in projects:
            rules_count = len(p.extraction_rules)
            listbox.insert("end", f"{p.name}  |  URLs: {len(p.urls)}  |  Rules: {rules_count}  |  Mode: {p.mode.value}  |  Updated: {p.updated_at[:16]}\n")

        def _do_load():
            content = listbox.get("1.0", "end").strip()
            if content:
                # Get first project name
                first_line = content.split("\n")[0]
                name = first_line.split("|")[0].strip()
                for p in projects:
                    if p.name == name:
                        engine.load_project(p.id)
                        self._apply_project_to_ui(p)
                        if hasattr(app, '_log_panel'):
                            app._log_panel.add_log(f"Project loaded: {p.name}", "success")
                        break
            dialog.destroy()

        ctk.CTkButton(dialog, text="Load Selected", width=140,
                       font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=_do_load).pack(pady=(0, Spacing.MD))

    def _apply_project_to_ui(self, proj):
        self._url_text.configure(state="normal")
        self._url_text.delete("0.0", "end")
        for url in proj.urls:
            self._url_text.insert("end", url + "\n")

        self._mode_seg.set(proj.mode.value.capitalize())
        self._var_auto_scroll.set(proj.auto_scroll)
        self._var_follow_links.set(proj.follow_links)
        self._max_pages_entry.delete("0", "end")
        self._max_pages_entry.insert("0", str(proj.max_pages))
        self._depth_entry.delete("0", "end")
        self._depth_entry.insert("0", str(proj.max_depth))

        self._extraction_rules.clear()
        for rd in proj.extraction_rules:
            self._extraction_rules.append(ExtractionRule(
                name=rd["name"], method=ExtractionMethod(rd["method"]),
                selector=rd["selector"], attribute=rd.get("attribute"),
                default=rd.get("default"), is_list=rd.get("is_list", False),
            ))
        self._refresh_rules_list()

    def _import_rules(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                rules_data = json.load(f)
            count = 0
            for rd in rules_data if isinstance(rules_data, list) else [rules_data]:
                if "name" in rd and "method" in rd and "selector" in rd:
                    self._extraction_rules.append(ExtractionRule(
                        name=rd["name"], method=ExtractionMethod(rd["method"]),
                        selector=rd["selector"], attribute=rd.get("attribute"),
                        default=rd.get("default"), is_list=rd.get("is_list", False),
                    ))
                    count += 1
            self._refresh_rules_list()
            app = self.winfo_toplevel()
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log(f"Imported {count} rules from {path}", "info")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _export_rules(self):
        if not self._extraction_rules:
            messagebox.showinfo("Export", "No rules to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = [self._rule_to_dict(r) for r in self._extraction_rules]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            app = self.winfo_toplevel()
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log(f"Exported {len(data)} rules to {path}", "success")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _rule_to_dict(self, rule: ExtractionRule) -> dict:
        return {
            "name": rule.name, "method": rule.method.value,
            "selector": rule.selector, "attribute": rule.attribute,
            "default": rule.default, "is_list": rule.is_list,
        }

    # ------------------------------------------------------------------
    # URL Section
    # ------------------------------------------------------------------

    def _build_url_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="ew", pady=Spacing.SM)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Target URLs (one per line)",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._url_text = ctk.CTkTextbox(
            card, height=70, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._url_text.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    # ------------------------------------------------------------------
    # Options Section
    # ------------------------------------------------------------------

    def _build_options_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=2, column=0, sticky="ew", pady=Spacing.SM)
        card.grid_columnconfigure(4, weight=1)

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

        ctk.CTkLabel(bar, text="Max Pages", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=2, padx=Spacing.SM, pady=Spacing.SM, sticky="e")
        self._max_pages_entry = ctk.CTkEntry(
            card, width=60, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=28,
        )
        self._max_pages_entry.insert("0", "100")
        self._max_pages_entry.grid(row=0, column=3, padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)

        ctk.CTkLabel(card, text="Depth", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=4, padx=Spacing.SM, pady=Spacing.SM, sticky="e")
        self._depth_entry = ctk.CTkEntry(
            card, width=50, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=28,
        )
        self._depth_entry.insert("0", "1")
        self._depth_entry.grid(row=0, column=5, padx=(Spacing.XS, Spacing.SM), pady=Spacing.SM)

        ctk.CTkLabel(card, text="Workers", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=6, padx=Spacing.SM, pady=Spacing.SM, sticky="e")
        self._workers_entry = ctk.CTkEntry(
            card, width=40, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=28,
        )
        self._workers_entry.insert("0", "1")
        self._workers_entry.grid(row=0, column=7, padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

    # ------------------------------------------------------------------
    # Extraction Rules Section
    # ------------------------------------------------------------------

    def _build_rules_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=3, column=0, sticky="nsew", pady=Spacing.SM)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Extraction Rules", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1)

        for col, (text, cmd) in enumerate([("+ Add", self._add_rule), ("Edit", self._edit_rule),
                                            ("Remove", self._remove_rule), ("Clear", self._clear_rules)]):
            ctk.CTkButton(btn_frame, text=text, width=60, height=24,
                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                           text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                           border_color=theme.colors.BORDER, command=cmd).grid(row=0, column=col, padx=2)

        self._rules_listbox = ctk.CTkTextbox(
            card, height=120, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
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

    def _clear_rules(self):
        self._extraction_rules.clear()
        self._refresh_rules_list()

    def _show_rule_dialog(self, edit_index: int = -1):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Extraction Rule" if edit_index >= 0 else "Add Extraction Rule")
        dialog.geometry("480x420")
        dialog.configure(fg_color=theme.colors.BG_MAIN)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.grid_columnconfigure(1, weight=1)

        existing = self._extraction_rules[edit_index] if edit_index >= 0 else None

        labels = ["Name", "Method", "Selector", "Attribute", "Default Value"]
        for row, lbl_text in enumerate(labels):
            ctk.CTkLabel(dialog, text=lbl_text, font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                          text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=0, sticky="w",
                                                                        padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM)

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
                name=name, method=ExtractionMethod(method_menu.get()), selector=selector,
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
        self._actions_card.grid(row=4, column=0, sticky="ew", pady=Spacing.SM)
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

        ctk.CTkButton(row_frame, text="X", width=26, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=_remove_row).grid(row=0, column=3, padx=(Spacing.XS, 0))

    def _collect_page_actions(self) -> list[dict]:
        actions = []
        for row in self._action_rows_frame.winfo_children():
            if isinstance(row, ctk.CTkFrame):
                widgets = row.winfo_children()
                if len(widgets) >= 3:
                    actions.append({
                        "action_type": widgets[0].get(),
                        "selector": widgets[1].get().strip(),
                        "value": widgets[2].get().strip(),
                        "delay": 0.5,
                    })
        return actions

    # ------------------------------------------------------------------
    # Results Section (with search/filter and data table)
    # ------------------------------------------------------------------

    def _build_results_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, Spacing.SM))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(1, weight=1)

        # Header with search
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Results Preview",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        self._result_count_label = ctk.CTkLabel(header, text="0 records",
                                                  font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                  text_color=theme.colors.TEXT_MUTED)
        self._result_count_label.grid(row=0, column=1, sticky="e")

        # Search bar
        search_frame = ctk.CTkFrame(card, fg_color="transparent")
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=Spacing.MD, pady=(Spacing.XS, 0))
        search_frame.grid_columnconfigure(0, weight=1)

        self._search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Search results...",
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=28,
        )
        self._search_entry.grid(row=0, column=0, sticky="ew", padx=(0, Spacing.SM))
        self._search_entry.bind("<KeyRelease>", self._on_search)

        # Data table
        self._data_table = DataTable(card)
        self._data_table.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Fallback textbox (for when table has issues)
        self._results_text = ctk.CTkTextbox(
            card, height=400, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )

    def _on_search(self, event=None):
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and app.engine.results:
            search_text = self._search_entry.get().strip()
            filtered = self._data_table.get_filtered_data(search_text)
            self._data_table.set_data(filtered)
            self._result_count_label.configure(text=f"{len(filtered)} records")

    def _display_results(self, results: list[dict]):
        if not results:
            self._data_table.set_data([])
            self._result_count_label.configure(text="0 records")
            return
        # Filter out internal fields
        display = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
        self._data_table.set_data(display)
        self._result_count_label.configure(text=f"{len(display)} records")

    # ------------------------------------------------------------------
    # Export Section
    # ------------------------------------------------------------------

    def _build_export_section(self, parent):
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="ew", pady=Spacing.SM)

        ctk.CTkLabel(card, text="Export", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, columnspan=6,
                                                                     sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        formats = [("CSV", "csv"), ("JSON", "json"), ("Excel", "xlsx"),
                   ("XML", "xml"), ("HTML", "html"), ("SQLite", "sqlite")]
        for col, (label, fmt) in enumerate(formats):
            ctk.CTkButton(
                card, text=label, width=60, height=28,
                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                border_color=theme.colors.BORDER,
                command=lambda f=fmt: self._on_export(f),
            ).grid(row=1, column=col, padx=(Spacing.MD if col == 0 else 2, Spacing.MD if col == len(formats)-1 else 2),
                   pady=(Spacing.XS, Spacing.MD))

    def _on_export(self, fmt: str):
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} files", f"*.{fmt}"), ("All files", "*.*")],
        )
        if path:
            try:
                app = self.winfo_toplevel()
                if hasattr(app, 'engine') and app.engine.results:
                    app.engine.export_results(fmt, path)
                    messagebox.showinfo("Export", f"Exported {len(app.engine.results)} records to:\n{path}")
                    if hasattr(app, '_log_panel'):
                        app._log_panel.add_log(f"Exported {len(app.engine.results)} records to {path} ({fmt})", "success")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_mode_change(self, value):
        pass

    def _on_template_selected(self, name):
        from core.templates import get_template_by_name
        t = get_template_by_name(name)
        if not t:
            return
        self._url_text.configure(state="normal")
        self._url_text.delete("0.0", "end")
        for url in t.urls:
            self._url_text.insert("end", url + "\n")
        mode_map = {"static": "Static", "dynamic": "Dynamic", "auto": "Auto"}
        self._mode_seg.set(mode_map.get(t.mode, "Static"))
        self._var_auto_scroll.set(t.options.get("auto_scroll", False))
        self._var_follow_links.set(t.options.get("follow_links", False))
        max_p = t.options.get("max_pages", 100)
        self._max_pages_entry.delete("0", "end")
        self._max_pages_entry.insert("0", str(max_p))
        self._extraction_rules.clear()
        for rd in t.extraction_rules:
            self._extraction_rules.append(ExtractionRule(
                name=rd["name"], method=ExtractionMethod(rd["method"]),
                selector=rd["selector"], attribute=rd.get("attribute"),
                default=rd.get("default"), is_list=rd.get("is_list", False),
            ))
        self._refresh_rules_list()
        app = self.winfo_toplevel()
        if hasattr(app, '_log_panel'):
            app._log_panel.add_log(f"Template loaded: {t.name}", "info")

    def _on_start(self):
        app = self.winfo_toplevel()
        if not hasattr(app, 'engine'):
            return
        engine = app.engine
        urls_text = self._url_text.get("0.0", "end").strip()
        if not urls_text:
            messagebox.showwarning("Warning", "Please enter at least one URL.")
            return
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        valid_urls = []
        for u in urls:
            if u.startswith(("http://", "https://")):
                valid_urls.append(u)
            else:
                messagebox.showwarning("Invalid URL", f"URL must start with http:// or https://:\n{u}")
                return
        if not valid_urls:
            return
        mode_map = {"Static": ScrapingMode.STATIC, "Dynamic": ScrapingMode.DYNAMIC, "Auto": ScrapingMode.AUTO}
        mode = mode_map.get(self._mode_seg.get(), ScrapingMode.STATIC)
        engine.data_parser.clear_rules()
        for rule in self._extraction_rules:
            engine.data_parser.add_rule(rule)
        engine.clear_results()
        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        if hasattr(app, '_log_panel'):
            app._log_panel.add_log(f"Starting {mode.value} scrape of {len(valid_urls)} URL(s)", "info")
        engine.scrape_urls(valid_urls, mode, callback=self._on_progress)

    def _on_stop(self):
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and app.engine:
            app.engine.stop()
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log("Scraping stopped by user", "warning")
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
