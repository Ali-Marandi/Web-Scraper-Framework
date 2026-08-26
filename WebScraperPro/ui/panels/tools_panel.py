"""
WebScraper Pro - Developer Tools Panel
Regex tester, CSS/XPath/JSON Path testers, and Response Inspector.
v1.3.0: Added CSS Selector, XPath, JSON Path testers, and Response Inspector.
"""

import re
import json
import threading
import time
import customtkinter as ctk
from bs4 import BeautifulSoup
from lxml import html as lhtml

from ui.styles import theme, Typography, Spacing, Radius


class ToolsPanel(ctk.CTkFrame):
    """Developer tools with multiple testing and inspection utilities."""

    TAB_VALUES = ["Regex Tester", "CSS Selector", "XPath", "JSON Path", "Response Inspector"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._cached_html = ""
        self._cached_url = ""
        self._cached_response_headers = {}

        self._build_tabs()

    def _build_tabs(self):
        self._tab_seg = ctk.CTkSegmentedButton(
            self, values=self.TAB_VALUES,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            selected_color=theme.colors.BRAND_PRIMARY,
            selected_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            command=self._switch_tab,
        )
        self._tab_seg.set("Regex Tester")
        self._tab_seg.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))

        self._frames = {}
        for tab_name in self.TAB_VALUES:
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
            frame.grid_rowconfigure(1, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            self._frames[tab_name] = frame

        self._build_regex_tester(self._frames["Regex Tester"])
        self._build_css_tester(self._frames["CSS Selector"])
        self._build_xpath_tester(self._frames["XPath"])
        self._build_jsonpath_tester(self._frames["JSON Path"])
        self._build_response_inspector(self._frames["Response Inspector"])

        self._switch_tab("Regex Tester")

    def _switch_tab(self, value):
        for name, frame in self._frames.items():
            if name == value:
                frame.grid()
            else:
                frame.grid_remove()

    # ==================================================================
    # Regex Tester
    # ==================================================================

    def _build_regex_tester(self, parent):
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

        ctk.CTkButton(pattern_card, text="Test", width=60, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._run_regex_test
                       ).grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM)

        flags_frame = ctk.CTkFrame(pattern_card, fg_color="transparent")
        flags_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=(Spacing.MD, 0), pady=(0, Spacing.SM))

        self._regex_flags = {}
        for flag_text, flag_val in [("IGNORECASE", "i"), ("MULTILINE", "m"),
                                     ("DOTALL", "s"), ("VERBOSE", "x")]:
            var = ctk.BooleanVar(value=False)
            self._regex_flags[flag_val] = var
            ctk.CTkCheckBox(flags_frame, text=flag_text, variable=var,
                             font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                             text_color=theme.colors.TEXT_SECONDARY,
                             fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                             ).pack(side="left", padx=Spacing.XS)

        # Test text
        text_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        text_card.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        text_card.grid_rowconfigure(1, weight=1)
        text_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(text_card, text="Test Text", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._regex_input = ctk.CTkTextbox(
            text_card, height=120, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._regex_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        results_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        results_card.grid(row=2, column=0, sticky="nsew", pady=Spacing.SM)
        results_card.grid_rowconfigure(1, weight=1)
        results_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(results_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Matches", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self._match_count_label = ctk.CTkLabel(header, text="0 matches",
                                                  font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                  text_color=theme.colors.TEXT_MUTED)
        self._match_count_label.grid(row=0, column=1, sticky="e")

        self._regex_results = ctk.CTkTextbox(
            results_card, height=200, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._regex_results.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _run_regex_test(self):
        pattern = self._regex_pattern.get().strip()
        text = self._regex_input.get("0.0", "end").strip()
        if not pattern or not text:
            return

        flags = 0
        if self._regex_flags.get("i") and self._regex_flags["i"].get(): flags |= re.IGNORECASE
        if self._regex_flags.get("m") and self._regex_flags["m"].get(): flags |= re.MULTILINE
        if self._regex_flags.get("s") and self._regex_flags["s"].get(): flags |= re.DOTALL
        if self._regex_flags.get("x") and self._regex_flags["x"].get(): flags |= re.VERBOSE

        try:
            matches = re.findall(pattern, text, flags)
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

    # ==================================================================
    # CSS Selector Tester
    # ==================================================================

    def _build_css_tester(self, parent):
        # HTML source input
        html_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        html_card.grid(row=0, column=0, sticky="nsew", pady=(0, Spacing.SM))
        html_card.grid_rowconfigure(1, weight=1)
        html_card.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(html_card, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="HTML Source", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(top_bar, text="Load from URL", width=110, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                       border_width=1, border_color=theme.colors.BORDER,
                       command=self._load_html_for_css).grid(row=0, column=1, padx=Spacing.SM)

        self._css_html_input = ctk.CTkTextbox(
            html_card, height=150, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._css_html_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Selector + Results
        bottom = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bottom.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        bottom.grid_rowconfigure(2, weight=1)
        bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bottom, text="Selector", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")

        self._css_selector = ctk.CTkEntry(
            bottom, placeholder_text="e.g. h1.title, div.article > p, a[href]",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=32,
        )
        self._css_selector.grid(row=0, column=1, sticky="ew", padx=(0, Spacing.XS), pady=Spacing.SM)

        attr_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        attr_frame.grid(row=0, column=2, padx=(0, Spacing.MD), pady=Spacing.SM)

        ctk.CTkLabel(attr_frame, text="Attr:", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).pack(side="left")
        self._css_attr = ctk.CTkEntry(attr_frame, placeholder_text="href", width=60, height=28,
                                        font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                        fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                        border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY)
        self._css_attr.pack(side="left", padx=2)

        ctk.CTkButton(attr_frame, text="Run", width=50, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=self._run_css_test).pack(side="left", padx=2)

        header = ctk.CTkFrame(bottom, fg_color="transparent")
        header.grid(row=1, column=0, columnspan=3, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Results", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self._css_count_label = ctk.CTkLabel(header, text="0 elements",
                                                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                text_color=theme.colors.TEXT_MUTED)
        self._css_count_label.grid(row=0, column=1, sticky="e")

        self._css_results = ctk.CTkTextbox(
            bottom, height=200, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._css_results.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _load_html_for_css(self):
        url = self._css_html_input.get("0.0", "end").strip()[:200]
        if url.startswith(("http://", "https://")):
            self._fetch_url_html(url, "css")
        else:
            from tkinter import filedialog
            path = filedialog.askopenfilename(filetypes=[("HTML", "*.html"), ("All", "*.*")])
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    self._css_html_input.delete("0.0", "end")
                    self._css_html_input.insert("0.0", content[:100000])
                    self._cached_html = content
                except Exception as e:
                    messagebox = __import__("tkinter").messagebox
                    messagebox.showerror("Error", str(e))

    def _run_css_test(self):
        selector = self._css_selector.get().strip()
        html_text = self._css_html_input.get("0.0", "end").strip()
        attr = self._css_attr.get().strip() or None

        if not selector or not html_text:
            return

        try:
            soup = BeautifulSoup(html_text, "lxml")
            elements = soup.select(selector)

            self._css_results.configure(state="normal")
            self._css_results.delete("0.0", "end")

            if not elements:
                self._css_results.insert("end", "No elements matched.")
            else:
                for i, el in enumerate(elements[:200]):
                    if attr:
                        val = el.get(attr, "")
                        self._css_results.insert("end", f"{i+1}. [{attr}] {str(val)[:200]}\n")
                    else:
                        text = el.get_text(strip=True)
                        tag = el.name
                        classes = el.get("class", [])
                        cls_str = "." + ".".join(classes) if classes else ""
                        self._css_results.insert("end", f"{i+1}. <{tag}{cls_str}> {text[:200]}\n")

            self._css_count_label.configure(text=f"{len(elements)} elements")
            self._css_results.configure(state="disabled")
        except Exception as e:
            self._css_results.configure(state="normal")
            self._css_results.delete("0.0", "end")
            self._css_results.insert("end", f"Error: {e}")
            self._css_results.configure(state="disabled")
            self._css_count_label.configure(text="Error")

    # ==================================================================
    # XPath Tester
    # ==================================================================

    def _build_xpath_tester(self, parent):
        html_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        html_card.grid(row=0, column=0, sticky="nsew", pady=(0, Spacing.SM))
        html_card.grid_rowconfigure(1, weight=1)
        html_card.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(html_card, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        top_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_bar, text="HTML Source", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(top_bar, text="Load from URL", width=110, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                       border_width=1, border_color=theme.colors.BORDER,
                       command=self._load_html_for_xpath).grid(row=0, column=1, padx=Spacing.SM)

        self._xpath_html_input = ctk.CTkTextbox(
            html_card, height=150, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._xpath_html_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # XPath + Results
        bottom = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bottom.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        bottom.grid_rowconfigure(2, weight=1)
        bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bottom, text="XPath", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")

        self._xpath_expr = ctk.CTkEntry(
            bottom, placeholder_text='e.g. //h1/text(), //div[@class="content"]/p',
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=32,
        )
        self._xpath_expr.grid(row=0, column=1, sticky="ew", padx=(0, Spacing.SM), pady=Spacing.SM)

        ctk.CTkButton(bottom, text="Run", width=50, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=self._run_xpath_test).grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM)

        header = ctk.CTkFrame(bottom, fg_color="transparent")
        header.grid(row=1, column=0, columnspan=3, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Results", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self._xpath_count_label = ctk.CTkLabel(header, text="0 results",
                                                  font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                  text_color=theme.colors.TEXT_MUTED)
        self._xpath_count_label.grid(row=0, column=1, sticky="e")

        self._xpath_results = ctk.CTkTextbox(
            bottom, height=200, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._xpath_results.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _load_html_for_xpath(self):
        url = self._xpath_html_input.get("0.0", "end").strip()[:200]
        if url.startswith(("http://", "https://")):
            self._fetch_url_html(url, "xpath")
        else:
            from tkinter import filedialog
            path = filedialog.askopenfilename(filetypes=[("HTML", "*.html"), ("All", "*.*")])
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    self._xpath_html_input.delete("0.0", "end")
                    self._xpath_html_input.insert("0.0", content[:100000])
                    self._cached_html = content
                except Exception as e:
                    messagebox = __import__("tkinter").messagebox
                    messagebox.showerror("Error", str(e))

    def _run_xpath_test(self):
        expr = self._xpath_expr.get().strip()
        html_text = self._xpath_html_input.get("0.0", "end").strip()
        if not expr or not html_text:
            return

        try:
            tree = lhtml.fromstring(html_text)
            results = tree.xpath(expr)

            self._xpath_results.configure(state="normal")
            self._xpath_results.delete("0.0", "end")

            if not results:
                self._xpath_results.insert("end", "No results matched.")
            else:
                for i, r in enumerate(results[:200]):
                    if isinstance(r, str):
                        self._xpath_results.insert("end", f"{i+1}. {r.strip()[:300]}\n")
                    elif hasattr(r, 'text_content'):
                        text = " ".join(r.itertext()).strip()[:300]
                        tag = r.tag if hasattr(r, 'tag') else "?"
                        self._xpath_results.insert("end", f"{i+1}. <{tag}> {text}\n")
                    elif isinstance(r, float):
                        self._xpath_results.insert("end", f"{i+1}. {r}\n")
                    else:
                        self._xpath_results.insert("end", f"{i+1}. {str(r)[:300]}\n")

            self._xpath_count_label.configure(text=f"{len(results)} results")
            self._xpath_results.configure(state="disabled")
        except Exception as e:
            self._xpath_results.configure(state="normal")
            self._xpath_results.delete("0.0", "end")
            self._xpath_results.insert("end", f"XPath error: {e}")
            self._xpath_results.configure(state="disabled")
            self._xpath_count_label.configure(text="Error")

    # ==================================================================
    # JSON Path Tester
    # ==================================================================

    def _build_jsonpath_tester(self, parent):
        json_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        json_card.grid(row=0, column=0, sticky="nsew", pady=(0, Spacing.SM))
        json_card.grid_rowconfigure(1, weight=1)
        json_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(json_card, text="JSON Data", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._json_input = ctk.CTkTextbox(
            json_card, height=180, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._json_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Path + Results
        bottom = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bottom.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        bottom.grid_rowconfigure(2, weight=1)
        bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bottom, text="JSON Path", font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")

        self._jsonpath_expr = ctk.CTkEntry(
            bottom, placeholder_text='e.g. data.items[0].name, results[0:3]',
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=32,
        )
        self._jsonpath_expr.grid(row=0, column=1, sticky="ew", padx=(0, Spacing.SM), pady=Spacing.SM)

        ctk.CTkButton(bottom, text="Run", width=50, height=28,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=self._run_jsonpath_test).grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.SM)

        self._jsonpath_results = ctk.CTkTextbox(
            bottom, height=200, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._jsonpath_results.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=Spacing.MD, pady=(Spacing.SM, Spacing.MD))

    def _run_jsonpath_test(self):
        path_expr = self._jsonpath_expr.get().strip()
        json_text = self._json_input.get("0.0", "end").strip()
        if not path_expr or not json_text:
            return

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            self._jsonpath_results.configure(state="normal")
            self._jsonpath_results.delete("0.0", "end")
            self._jsonpath_results.insert("end", f"JSON parse error: {e}")
            self._jsonpath_results.configure(state="disabled")
            return

        try:
            # Simple JSON path resolver (dotted + bracket notation)
            result = self._resolve_json_path(data, path_expr)

            self._jsonpath_results.configure(state="normal")
            self._jsonpath_results.delete("0.0", "end")

            if result is None:
                self._jsonpath_results.insert("end", "Path not found.")
            else:
                output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
                if len(output) > 50000:
                    output = output[:50000] + "\n\n... (truncated)"
                self._jsonpath_results.insert("end", output)

            self._jsonpath_results.configure(state="disabled")
        except Exception as e:
            self._jsonpath_results.configure(state="normal")
            self._jsonpath_results.delete("0.0", "end")
            self._jsonpath_results.insert("end", f"Path error: {e}")
            self._jsonpath_results.configure(state="disabled")

    def _resolve_json_path(self, data, path: str):
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]
        current = data
        for part in parts:
            if not part:
                continue
            # Handle slice notation like [0:3]
            slice_match = re.match(r'^(\d+):(\d*)$', part)
            if slice_match and isinstance(current, list):
                start = int(slice_match.group(1))
                end = int(slice_match.group(2)) if slice_match.group(2) else len(current)
                current = current[start:end]
                continue
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    # ==================================================================
    # Response Inspector
    # ==================================================================

    def _build_response_inspector(self, parent):
        # URL bar
        url_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        url_card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        url_card.grid_columnconfigure(0, weight=1)

        self._resp_url = ctk.CTkEntry(
            url_card, placeholder_text="https://example.com  -  Enter URL to inspect response",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=34,
        )
        self._resp_url.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)

        ctk.CTkButton(url_card, text="Inspect", width=80, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=self._fetch_response).grid(row=0, column=1, padx=(Spacing.SM, Spacing.MD), pady=Spacing.SM)

        self._resp_status = ctk.CTkLabel(url_card, text="", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                           text_color=theme.colors.TEXT_MUTED)
        self._resp_status.grid(row=0, column=2, padx=(0, Spacing.MD), pady=Spacing.SM)

        # Content area
        content_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        content_card.grid(row=1, column=0, sticky="nsew")
        content_card.grid_rowconfigure(1, weight=1)
        content_card.grid_columnconfigure(0, weight=1)

        tab_bar = ctk.CTkFrame(content_card, fg_color="transparent")
        tab_bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._resp_tab_var = ctk.StringVar(value="headers")
        for text, val in [("Headers", "headers"), ("Body", "body"), ("Raw Headers", "raw_headers")]:
            ctk.CTkRadioButton(
                tab_bar, text=text, variable=self._resp_tab_var, value=val,
                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                text_color=theme.colors.TEXT_SECONDARY,
                fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                command=self._switch_resp_tab,
            ).pack(side="left", padx=Spacing.SM)

        self._resp_headers_text = ctk.CTkTextbox(
            content_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._resp_headers_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        self._resp_body_text = ctk.CTkTextbox(
            content_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._resp_body_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        self._resp_body_text.grid_remove()

        self._resp_raw_text = ctk.CTkTextbox(
            content_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._resp_raw_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        self._resp_raw_text.grid_remove()

    def _switch_resp_tab(self):
        val = self._resp_tab_var.get()
        if val == "headers":
            self._resp_headers_text.grid()
            self._resp_body_text.grid_remove()
            self._resp_raw_text.grid_remove()
        elif val == "body":
            self._resp_headers_text.grid_remove()
            self._resp_body_text.grid()
            self._resp_raw_text.grid_remove()
        else:
            self._resp_headers_text.grid_remove()
            self._resp_body_text.grid_remove()
            self._resp_raw_text.grid()

    def _fetch_response(self):
        url = self._resp_url.get().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            self._resp_status.configure(text="Invalid URL", text_color=theme.colors.TEXT_ERROR)
            return

        self._resp_status.configure(text="Fetching...", text_color=theme.colors.TEXT_WARNING)

        def _do():
            import requests
            try:
                start = time.time()
                resp = requests.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                elapsed = time.time() - start

                def _update():
                    # Status line
                    size = len(resp.content)
                    size_str = f"{size:,} B" if size < 1024 else f"{size/1024:.1f} KB"
                    self._resp_status.configure(
                        text=f"{resp.status_code} | {elapsed:.2f}s | {size_str} | {resp.headers.get('Content-Type', '')[:40]}",
                        text_color=theme.colors.TEXT_SUCCESS if resp.status_code < 400 else theme.colors.TEXT_ERROR,
                    )

                    # Formatted headers
                    self._resp_headers_text.configure(state="normal")
                    self._resp_headers_text.delete("0.0", "end")
                    self._resp_headers_text.insert("end", f"  Status:     {resp.status_code} {resp.reason}\n")
                    self._resp_headers_text.insert("end", f"  URL:        {resp.url}\n")
                    self._resp_headers_text.insert("end", f"  Time:       {elapsed:.3f}s\n")
                    self._resp_headers_text.insert("end", f"  Size:       {size_str}\n")
                    self._resp_headers_text.insert("end", f"  Encoding:   {resp.encoding or 'unknown'}\n")
                    self._resp_headers_text.insert("end", f"\n  Response Headers:\n")
                    self._resp_headers_text.insert("end", f"  {'':-<50}\n")
                    for key, val in resp.headers.items():
                        self._resp_headers_text.insert("end", f"  {key}: {val}\n")
                    self._resp_headers_text.configure(state="disabled")

                    # Raw headers
                    self._resp_raw_text.configure(state="normal")
                    self._resp_raw_text.delete("0.0", "end")
                    self._resp_raw_text.insert("end", f"  Request Headers:\n")
                    self._resp_raw_text.insert("end", f"  {'':-<50}\n")
                    for key, val in resp.request.headers.items():
                        self._resp_raw_text.insert("end", f"  {key}: {val}\n")
                    self._resp_raw_text.insert("end", f"\n  Response Headers:\n")
                    self._resp_raw_text.insert("end", f"  {'':-<50}\n")
                    for key, val in resp.headers.items():
                        self._resp_raw_text.insert("end", f"  {key}: {val}\n")
                    self._resp_raw_text.configure(state="disabled")

                    # Body
                    self._resp_body_text.configure(state="normal")
                    self._resp_body_text.delete("0.0", "end")
                    body = resp.text[:50000] if resp.text else "(empty body)"
                    self._resp_body_text.insert("0.0", body)
                    if len(resp.text or "") > 50000:
                        self._resp_body_text.insert("end", f"\n\n... truncated ({len(resp.text or '')} chars total)")
                    self._resp_body_text.configure(state="disabled")

                    # Cache for other tools
                    self._cached_html = resp.text or ""
                    self._cached_url = url

                self.after(0, _update)

            except Exception as e:
                self.after(0, lambda: self._resp_status.configure(
                    text=f"Error: {str(e)[:60]}", text_color=theme.colors.TEXT_ERROR))

        threading.Thread(target=_do, daemon=True).start()

    # ==================================================================
    # Shared: Fetch URL HTML for testers
    # ==================================================================

    def _fetch_url_html(self, url: str, target: str = "css"):
        import requests
        self._resp_status_text = "Fetching..." if hasattr(self, '_resp_status_text') else None

        def _do():
            try:
                resp = requests.get(url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                html = resp.text[:100000]
                self._cached_html = html
                self._cached_url = url

                def _update():
                    if target == "css":
                        self._css_html_input.delete("0.0", "end")
                        self._css_html_input.insert("0.0", html)
                    elif target == "xpath":
                        self._xpath_html_input.delete("0.0", "end")
                        self._xpath_html_input.insert("0.0", html)

                    app = self.winfo_toplevel()
                    if hasattr(app, '_log_panel'):
                        app._log_panel.add_log(f"Loaded HTML from {url} ({len(html)} chars)", "success")

                self.after(0, _update)
            except Exception as e:
                app = self.winfo_toplevel()
                if hasattr(app, '_log_panel'):
                    self.after(0, lambda: app._log_panel.add_log(f"Failed to fetch: {e}", "error"))

        threading.Thread(target=_do, daemon=True).start()

    def update_ui(self, engine):
        pass
