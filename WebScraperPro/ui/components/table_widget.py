"""
WebScraper Pro - Custom Data Table Widget
A scrollable, sortable table built with CustomTkinter Canvas for displaying scraped data.
"""

import customtkinter as ctk
from ui.styles import theme, Typography, Spacing, Radius


class DataTable(ctk.CTkFrame):
    """A custom table widget for displaying scraped data in columns and rows.

    Features:
    - Sortable column headers (click to sort)
    - Row striping for readability
    - Horizontal and vertical scrolling
    - Column auto-sizing
    """

    def __init__(self, master, data: list[dict] | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._headers: list[str] = []
        self._rows: list[dict] = []
        self._sort_col: int = -1
        self._sort_asc: bool = True
        self._col_widths: dict[str, int] = {}
        self._row_height = 28
        self._header_height = 32
        self._min_col_width = 80
        self._max_col_width = 300

        self._build_canvas()

        if data:
            self.set_data(data)

    def _build_canvas(self):
        # Header frame
        self._header_frame = ctk.CTkFrame(self, fg_color=theme.colors.BG_ELEVATED,
                                           corner_radius=0, height=self._header_height)
        self._header_frame.grid(row=0, column=0, sticky="ew")
        self._header_frame.grid_propagate(False)
        self._header_canvas = ctk.Canvas(self._header_frame, bg=theme.colors.BG_ELEVATED,
                                           highlight_thickness=0, height=self._header_height)
        self._header_canvas.pack(fill="x", expand=True)
        self._header_canvas.bind("<Configure>", lambda e: self._draw_headers())

        # Data area
        self._canvas = ctk.CTkCanvas(self, fg_color=theme.colors.BG_INPUT,
                                       highlight_thickness=0)
        self._canvas.grid(row=1, column=0, sticky="nsew")

        self._scrollbar_v = ctk.CTkScrollbar(self, orientation="vertical", command=self._canvas.yview)
        self._scrollbar_v.grid(row=1, column=1, sticky="ns")

        self._scrollbar_h = ctk.CTkScrollbar(self, orientation="horizontal", command=self._canvas.xview)
        self._scrollbar_h.grid(row=2, column=0, sticky="ew")

        self._canvas.configure(yscrollcommand=self._scrollbar_v.set,
                                xscrollcommand=self._scrollbar_h.set)

        self._inner_frame = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._canvas.create_window((0, 0), window=self._inner_frame, anchor="nw")
        self._inner_frame.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

    def set_data(self, data: list[dict]):
        self._rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in data]
        self._headers = list(self._rows[0].keys()) if self._rows else []
        self._compute_col_widths()
        self._draw_headers()
        self._draw_rows()

    def _compute_col_widths(self):
        self._col_widths = {}
        if not self._headers:
            return
        for h in self._headers:
            w = max(len(str(h)) * 8 + 24, self._min_col_width)
            for row in self._rows:
                val = row.get(h, "")
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                w = max(w, min(len(str(val)) * 8 + 24, self._max_col_width))
            self._col_widths[h] = w

    def _draw_headers(self):
        c = self._header_canvas
        c.delete("all")
        if not self._headers:
            return

        w = max(c.winfo_width(), 800)
        x = 0
        for i, h in enumerate(self._headers):
            cw = self._col_widths.get(h, self._min_col_width)
            c.create_rectangle(x, 0, x + cw, self._header_height,
                               fill=theme.colors.BG_ELEVATED, outline="")
            c.create_line(x + cw, 0, x + cw, self._header_height,
                          fill=theme.colors.BORDER)
            sort_ind = "" if self._sort_col != i else (" ^" if self._sort_asc else " v")
            c.create_text(x + 10, self._header_height // 2,
                          text=str(h) + sort_ind, anchor="w",
                          fill=theme.colors.TEXT_PRIMARY,
                          font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE, "bold"))
            # Invisible rect for click binding
            rect = c.create_rectangle(x, 0, x + cw, self._header_height, fill="", outline="")
            c.tag_bind(rect, "<Button-1>", lambda e, col=i: self._on_header_click(col))
            x += cw

        total_w = sum(self._col_widths.get(h, self._min_col_width) for h in self._headers)
        self._scrollbar_h.configure(command=self._canvas.xview)
        self._canvas.configure(scrollregion=(0, 0, max(total_w, w), self._canvas.winfo_height()))

    def _draw_rows(self):
        for child in self._inner_frame.winfo_children():
            child.destroy()

        if not self._rows:
            ctk.CTkLabel(self._inner_frame,
                          text="No results yet. Add extraction rules and start scraping.",
                          font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                          text_color=theme.colors.TEXT_MUTED).pack(pady=40)
            return

        total_w = sum(self._col_widths.get(h, self._min_col_width) for h in self._headers)

        for row_idx, row_data in enumerate(self._rows):
            is_even = row_idx % 2 == 0
            bg = theme.colors.BG_MAIN if is_even else theme.colors.BG_CARD

            row_frame = ctk.CTkFrame(self._inner_frame, fg_color=bg,
                                       height=self._row_height, corner_radius=0)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)

            x = 0
            for col_idx, h in enumerate(self._headers):
                cw = self._col_widths.get(h, self._min_col_width)
                val = row_data.get(h, "")
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                display_val = str(val)[:int(cw / 7)]

                ctk.CTkLabel(row_frame, text=display_val,
                              font=(Typography.MONO_FONT, Typography.TINY_SIZE),
                              text_color=theme.colors.TEXT_PRIMARY,
                              anchor="w", width=cw).place(x=x, y=0, relheight=1.0)
                x += cw

    def _on_header_click(self, col_idx):
        if self._sort_col == col_idx:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_idx
            self._sort_asc = True
        if 0 <= col_idx < len(self._headers):
            h = self._headers[col_idx]
            self._rows.sort(key=lambda r: str(r.get(h, "")), reverse=not self._sort_asc)
            self._draw_rows()

    def get_filtered_data(self, search_text: str = "") -> list[dict]:
        if not search_text:
            return list(self._rows)
        s = search_text.lower()
        return [r for r in self._rows if any(s in str(v).lower() for v in r.values())]

    def update_ui(self, engine):
        pass
