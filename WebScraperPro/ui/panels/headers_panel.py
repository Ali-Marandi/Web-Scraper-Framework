import json
import customtkinter as ctk
from tkinter import messagebox

from ui.styles import theme, Typography, Spacing, Radius


class HeadersPanel(ctk.CTkFrame):
    """Manage custom HTTP headers and cookies for scraping requests."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_headers_section()
        self._build_cookies_section()

    def _build_headers_section(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Custom HTTP Headers",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        for text, cmd in [("+ Add", self._add_header_row), ("Reset Default", self._reset_headers),
                           ("Import", self._import_headers), ("Export", self._export_headers)]:
            ctk.CTkButton(btn_frame, text=text, width=75, height=24,
                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                           text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                           border_width=1, border_color=theme.colors.BORDER,
                           command=cmd).pack(side="left", padx=2)

        # Column headers
        ctk.CTkLabel(card, text="Header Name", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).grid(row=1, column=1, padx=Spacing.MD, sticky="w")
        ctk.CTkLabel(card, text="Value", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).grid(row=1, column=2, padx=Spacing.MD, sticky="w")

        self._headers_rows = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self._headers_rows.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        self._headers_rows.grid_columnconfigure(0, weight=3)
        self._headers_rows.grid_columnconfigure(1, weight=5)

        # Default headers
        defaults = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        for k, v in defaults.items():
            self._add_header_row(k, v)

    def _add_header_row(self, name: str = "", value: str = ""):
        row = len(self._headers_rows.winfo_children())
        name_entry = ctk.CTkEntry(self._headers_rows, placeholder_text="Header-Name",
                                   font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD,
                                   text_color=theme.colors.TEXT_PRIMARY, height=26)
        name_entry.grid(row=row, column=0, padx=(0, Spacing.XS), pady=1, sticky="ew")
        if name:
            name_entry.insert("0", name)

        val_entry = ctk.CTkEntry(self._headers_rows, placeholder_text="value",
                                  font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                  fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                  border_width=1, corner_radius=Radius.MD,
                                  text_color=theme.colors.TEXT_PRIMARY, height=26)
        val_entry.grid(row=row, column=1, padx=Spacing.XS, pady=1, sticky="ew")
        if value:
            val_entry.insert("0", value)

        def _remove():
            name_entry.destroy()
            val_entry.destroy()

        ctk.CTkButton(self._headers_rows, text="X", width=24, height=24,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=_remove).grid(row=row, column=2, padx=(Spacing.XS, 0), pady=1)

    def _reset_headers(self):
        for w in self._headers_rows.winfo_children():
            w.destroy()
        defaults = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        for k, v in defaults.items():
            self._add_header_row(k, v)

    def _get_headers(self) -> dict:
        headers = {}
        children = self._headers_rows.winfo_children()
        # Children come in groups of 3 (name_entry, val_entry, btn)
        for i in range(0, len(children), 3):
            if i + 1 < len(children):
                name = children[i].get().strip()
                val = children[i + 1].get().strip()
                if name:
                    headers[name] = val
        return headers

    def _import_headers(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for w in self._headers_rows.winfo_children():
                    w.destroy()
                for k, v in data.items():
                    self._add_header_row(k, str(v))
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _export_headers(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "w") as f:
                json.dump(self._get_headers(), f, indent=2)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _build_cookies_section(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.SM, Spacing.MD))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Cookies",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        for text, cmd in [("+ Add", self._add_cookie_row), ("Clear All", self._clear_cookies)]:
            ctk.CTkButton(btn_frame, text=text, width=75, height=24,
                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                           fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                           text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
                           border_width=1, border_color=theme.colors.BORDER,
                           command=cmd).pack(side="left", padx=2)

        ctk.CTkLabel(card, text="Name", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).grid(row=1, column=1, padx=Spacing.MD, sticky="w")
        ctk.CTkLabel(card, text="Value", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).grid(row=1, column=2, padx=Spacing.MD, sticky="w")

        self._cookies_rows = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self._cookies_rows.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        self._cookies_rows.grid_columnconfigure(0, weight=3)
        self._cookies_rows.grid_columnconfigure(1, weight=5)

    def _add_cookie_row(self, name: str = "", value: str = ""):
        row_count = len(self._cookies_rows.winfo_children()) // 3
        name_entry = ctk.CTkEntry(self._cookies_rows, placeholder_text="cookie_name",
                                   font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                   fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                   border_width=1, corner_radius=Radius.MD,
                                   text_color=theme.colors.TEXT_PRIMARY, height=26)
        name_entry.grid(row=row_count, column=0, padx=(0, Spacing.XS), pady=1, sticky="ew")
        if name:
            name_entry.insert("0", name)

        val_entry = ctk.CTkEntry(self._cookies_rows, placeholder_text="value",
                                  font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                                  fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
                                  border_width=1, corner_radius=Radius.MD,
                                  text_color=theme.colors.TEXT_PRIMARY, height=26)
        val_entry.grid(row=row_count, column=1, padx=Spacing.XS, pady=1, sticky="ew")
        if value:
            val_entry.insert("0", value)

        def _remove():
            name_entry.destroy()
            val_entry.destroy()

        ctk.CTkButton(self._cookies_rows, text="X", width=24, height=24,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
                       text_color=theme.colors.TEXT_INVERSE, corner_radius=Radius.MD,
                       command=_remove).grid(row=row_count, column=2, padx=(Spacing.XS, 0), pady=1)

    def _clear_cookies(self):
        for w in self._cookies_rows.winfo_children():
            w.destroy()

    def _get_cookies(self) -> dict:
        cookies = {}
        children = self._cookies_rows.winfo_children()
        for i in range(0, len(children), 3):
            if i + 1 < len(children):
                name = children[i].get().strip()
                val = children[i + 1].get().strip()
                if name:
                    cookies[name] = val
        return cookies

    def update_ui(self, engine):
        pass
