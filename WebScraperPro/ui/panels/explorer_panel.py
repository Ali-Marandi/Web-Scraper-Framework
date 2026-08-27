import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from urllib.parse import urlparse

from ui.styles import theme, Typography, Spacing, Radius
from core.url_explorer import URLExplorer, ExplorerResult, LinkInfo, LinkCategory


CATEGORY_ICONS = {
    LinkCategory.INTERNAL: "[page]",
    LinkCategory.EXTERNAL: "[ext]",
    LinkCategory.IMAGE: "[img]",
    LinkCategory.DOCUMENT: "[doc]",
    LinkCategory.VIDEO: "[vid]",
    LinkCategory.AUDIO: "[aud]",
    LinkCategory.EMAIL: "[@]",
    LinkCategory.SOCIAL: "[soc]",
    LinkCategory.FEED: "[rss]",
    LinkCategory.OTHER: "[?]",
}

STATUS_COLORS = {
    "success": theme.colors.TEXT_SUCCESS,
    "warning": theme.colors.TEXT_WARNING,
    "error": theme.colors.TEXT_ERROR,
    "muted": theme.colors.TEXT_MUTED,
}


class ExplorerPanel(ctk.CTkFrame):
    """URL Explorer panel with link extraction, categorization, and validation."""

    FILTER_OPTIONS = ["All", "Internal", "External", "Images", "Documents",
                      "Videos", "Audio", "Emails", "Social", "Feeds"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._explorer = URLExplorer()
        self._result: ExplorerResult | None = None
        self._exploring = False
        self._validating = False
        self._selected_category: str = "All"
        self._cached_html = ""

        self._build_url_bar()
        self._build_stats_bar()
        self._build_main_area()

    def _build_url_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))
        bar.grid_columnconfigure(0, weight=1)

        self._url_entry = ctk.CTkEntry(
            bar, placeholder_text="https://example.com  -  Enter URL to explore links",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY, height=34,
        )
        self._url_entry.grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="ew")

        opts_frame = ctk.CTkFrame(bar, fg_color="transparent")
        opts_frame.grid(row=0, column=1, padx=(0, Spacing.MD), pady=Spacing.SM)

        ctk.CTkLabel(opts_frame, text="Depth:", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).pack(side="left", padx=(0, 2))
        self._depth_menu = ctk.CTkOptionMenu(
            opts_frame, values=["0", "1", "2", "3"], width=50,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
        )
        self._depth_menu.set("1")
        self._depth_menu.pack(side="left", padx=2)

        self._validate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opts_frame, text="Validate", variable=self._validate_var,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
        ).pack(side="left", padx=(Spacing.SM, 0))

        self._explore_btn = ctk.CTkButton(
            opts_frame, text="Explore", width=80, height=28,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
            command=self._start_explore,
        )
        self._explore_btn.pack(side="left", padx=(Spacing.SM, 0))

        self._stop_btn = ctk.CTkButton(
            opts_frame, text="Stop", width=60, height=28,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
            text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
            command=self._stop_explore,
        )
        self._stop_btn.pack(side="left", padx=2)

    def _build_stats_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        self._stat_labels = {}
        stats = ["Links", "Pages", "Internal", "External", "Images", "Docs", "Broken", "Time"]
        for i, name in enumerate(stats):
            lbl = ctk.CTkLabel(bar, text=f"{name}: --",
                               font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                               text_color=theme.colors.TEXT_SECONDARY)
            lbl.grid(row=0, column=i, padx=Spacing.SM, pady=Spacing.XS)
            self._stat_labels[name.lower()] = lbl

    def _build_main_area(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        # Filter bar
        filter_bar = ctk.CTkFrame(container, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        filter_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Spacing.SM))
        filter_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(filter_bar, text="Filter:", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=0, column=0, padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM)

        self._filter_menu = ctk.CTkOptionMenu(
            filter_bar, values=self.FILTER_OPTIONS, width=110,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_filter_change,
        )
        self._filter_menu.set("All")
        self._filter_menu.grid(row=0, column=1, sticky="w", padx=Spacing.XS, pady=Spacing.SM)

        # Search in results
        self._search_entry = ctk.CTkEntry(
            filter_bar, placeholder_text="Search links...",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            width=250, height=28,
        )
        self._search_entry.grid(row=0, column=2, padx=Spacing.XS, pady=Spacing.SM, sticky="e")
        self._search_entry.bind("<KeyRelease>", self._on_search)

        # Action buttons on filter bar
        btn_frame = ctk.CTkFrame(filter_bar, fg_color="transparent")
        btn_frame.grid(row=0, column=3, padx=Spacing.MD, pady=Spacing.SM)

        ctk.CTkButton(btn_frame, text="Send to Scraper", width=120, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=self._send_to_scraper).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="Export Links", width=90, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                       border_width=1, border_color=theme.colors.BORDER,
                       command=self._export_links).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text="Copy All", width=75, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                       border_width=1, border_color=theme.colors.BORDER,
                       command=self._copy_all).pack(side="left", padx=2)

        # Left: Category Tree
        left_card = ctk.CTkFrame(container, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        left_card.grid_rowconfigure(1, weight=1)
        left_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_card, text="Categories",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._category_text = ctk.CTkTextbox(
            left_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled", width=300,
        )
        self._category_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Right: Links list
        right_card = ctk.CTkFrame(container, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        right_card.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        right_card.grid_rowconfigure(1, weight=1)
        right_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(right_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="Links",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        self._links_count_label = ctk.CTkLabel(header, text="",
                                                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                                text_color=theme.colors.TEXT_MUTED)
        self._links_count_label.grid(row=0, column=1, sticky="e")

        self._links_text = ctk.CTkTextbox(
            right_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._links_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start_explore(self):
        url = self._url_entry.get().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self._url_entry.delete(0, "end")
            self._url_entry.insert("0", url)

        if self._exploring:
            return

        self._exploring = True
        self._explore_btn.configure(state="disabled")
        max_depth = int(self._depth_menu.get())
        do_validate = self._validate_var.get()

        self._clear_display()
        self._set_links_text("  Exploring... please wait.\n")

        def _run():
            self._explorer.set_log_callback(self._on_explorer_log)
            try:
                result = self._explorer.explore(
                    url, max_depth=max_depth, max_pages=100,
                    validate=do_validate,
                )
                self._result = result
                self.after(0, lambda: self._display_result(result))
            except Exception as e:
                self.after(0, lambda: self._set_links_text(f"  Error: {e}"))
            finally:
                self._exploring = False
                self.after(0, lambda: self._explore_btn.configure(state="normal"))

        threading.Thread(target=_run, daemon=True).start()

    def _stop_explore(self):
        self._explorer.stop()
        self._set_links_text("  Stopping...\n")

    def _on_explorer_log(self, msg: str, level: str = "info"):
        app = self.winfo_toplevel()
        if hasattr(app, '_log_panel'):
            self.after(0, lambda: app._log_panel.add_log(f"[Explorer] {msg}", level))

    def _on_filter_change(self, value):
        self._selected_category = value
        if self._result:
            self._display_filtered_links()

    def _on_search(self, event=None):
        if self._result:
            self._display_filtered_links()

    def _clear_display(self):
        for txt in (self._category_text, self._links_text):
            txt.configure(state="normal")
            txt.delete("0.0", "end")
            txt.configure(state="disabled")

    def _set_links_text(self, text: str):
        self._links_text.configure(state="normal")
        self._links_text.delete("0.0", "end")
        self._links_text.insert("end", text)
        self._links_text.configure(state="disabled")

    def _display_result(self, result: ExplorerResult):
        self._display_categories(result)
        self._update_stats(result)
        self._display_filtered_links()

    def _display_categories(self, result: ExplorerResult):
        self._category_text.configure(state="normal")
        self._category_text.delete("0.0", "end")

        if not result.categories:
            self._category_text.insert("end", "  No categories found.")
        else:
            sorted_cats = sorted(result.categories.items(), key=lambda x: x[1], reverse=True)
            for cat_name, count in sorted_cats:
                icon = CATEGORY_ICONS.get(LinkCategory(cat_name), "[?]")
                bar_len = min(count, 30)
                bar = "" * bar_len
                line = f"  {icon} {cat_name:<12} {bar}  {count}\n"
                self._category_text.insert("end", line)

            self._category_text.insert("end", f"\n  {'':->40}\n")
            self._category_text.insert("end", f"  Total: {result.total_links} links\n")
            self._category_text.insert("end", f"  Pages crawled: {result.pages_crawled}\n")
            self._category_text.insert("end", f"  Max depth: {result.max_depth_reached}\n")
            self._category_text.insert("end", f"  Elapsed: {result.elapsed_time}s\n")
            if result.broken_count > 0:
                self._category_text.insert("end", f"  Broken: {result.broken_count}\n")

        self._category_text.configure(state="disabled")

    def _display_filtered_links(self):
        if not self._result:
            return

        filter_map = {
            "All": None, "Internal": LinkCategory.INTERNAL,
            "External": LinkCategory.EXTERNAL, "Images": LinkCategory.IMAGE,
            "Documents": LinkCategory.DOCUMENT, "Videos": LinkCategory.VIDEO,
            "Audio": LinkCategory.AUDIO, "Emails": LinkCategory.EMAIL,
            "Social": LinkCategory.SOCIAL, "Feeds": LinkCategory.FEED,
        }
        cat_filter = filter_map.get(self._selected_category)
        search = self._search_entry.get().strip().lower()

        filtered = self._result.links
        if cat_filter:
            filtered = [l for l in filtered if l.category == cat_filter]
        if search:
            filtered = [l for l in filtered if search in l.url.lower() or search in l.text.lower()]

        self._links_text.configure(state="normal")
        self._links_text.delete("0.0", "end")

        if not filtered:
            self._links_text.insert("end", "  No links match the current filter.")
        else:
            self._links_count_label.configure(text=f"{len(filtered)} links")
            for link in filtered:
                icon = CATEGORY_ICONS.get(link.category, "[?]")
                status = f" [{link.status_code}]" if link.validated else ""
                text_part = f" - {link.text[:50]}" if link.text else ""
                broken_tag = " !BROKEN" if link.is_broken else ""
                depth_tag = f" d{link.depth}" if link.depth > 0 else ""
                line = f"  {icon} {link.url[:90]}{text_part}{status}{broken_tag}{depth_tag}\n"
                self._links_text.insert("end", line)

        self._links_text.configure(state="disabled")

    def _update_stats(self, result: ExplorerResult):
        self._stat_labels["links"].configure(text=f"Links: {result.total_links}")
        self._stat_labels["pages"].configure(text=f"Pages: {result.pages_crawled}")
        self._stat_labels["internal"].configure(
            text=f"Internal: {result.categories.get('internal', 0)}")
        self._stat_labels["external"].configure(
            text=f"External: {result.categories.get('external', 0)}")
        self._stat_labels["images"].configure(
            text=f"Images: {result.categories.get('image', 0)}")
        self._stat_labels["docs"].configure(
            text=f"Docs: {result.categories.get('document', 0)}")
        broken_color = theme.colors.TEXT_ERROR if result.broken_count > 0 else theme.colors.TEXT_SUCCESS
        self._stat_labels["broken"].configure(
            text=f"Broken: {result.broken_count}", text_color=broken_color)
        self._stat_labels["time"].configure(text=f"Time: {result.elapsed_time}s")

    def _send_to_scraper(self):
        if not self._result or not self._result.links:
            messagebox.showinfo("Explorer", "No links to send. Explore a URL first.")
            return

        app = self.winfo_toplevel()
        if not hasattr(app, 'engine'):
            return

        urls = [l.url for l in self._result.links
                if l.category in (LinkCategory.INTERNAL, LinkCategory.EXTERNAL)
                and not l.is_broken]

        if not urls:
            messagebox.showinfo("Explorer", "No valid page URLs found.")
            return

        if messagebox.askyesno("Send to Scraper", f"Send {len(urls)} URLs to the Scraper panel?"):
            if hasattr(app, '_panels') and 'dashboard' in app._panels:
                panel = app._panels['dashboard']
                if hasattr(panel, '_url_entry'):
                    panel._url_entry.delete("0", "end")
                    panel._url_entry.insert("0", "\n".join(urls[:100]))
                if hasattr(app, '_switch_panel'):
                    app._switch_panel("dashboard")
                if hasattr(app, '_log_panel'):
                    app._log_panel.add_log(f"Sent {len(urls[:100])} URLs from Explorer to Scraper", "success")

    def _export_links(self):
        if not self._result or not self._result.links:
            messagebox.showinfo("Explorer", "No links to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("CSV", "*.csv"), ("JSON", "*.json"), ("All", "*.*")],
        )
        if not path:
            return

        try:
            ext = path.rsplit(".", 1)[-1].lower()
            links = self._result.links

            if ext == "json":
                import json
                data = [{
                    "url": l.url, "text": l.text, "category": l.category.value,
                    "status_code": l.status_code, "is_broken": l.is_broken,
                    "depth": l.depth,
                } for l in links]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif ext == "csv":
                with open(path, "w", encoding="utf-8") as f:
                    f.write("url,text,category,status_code,is_broken,depth\n")
                    for l in links:
                        f.write(f'"{l.url}","{l.text}","{l.category.value}","{l.status_code}","{l.is_broken}","{l.depth}"\n')
            else:
                with open(path, "w", encoding="utf-8") as f:
                    for l in links:
                        f.write(l.url + "\n")

            messagebox.showinfo("Export", f"Exported {len(links)} links to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _copy_all(self):
        if not self._result or not self._result.links:
            return
        urls = "\n".join(l.url for l in self._result.links)
        self.clipboard_clear()
        self.clipboard_append(urls)
        app = self.winfo_toplevel()
        if hasattr(app, '_log_panel'):
            app._log_panel.add_log(f"Copied {len(self._result.links)} links to clipboard", "success")

    def update_ui(self, engine):
        pass
