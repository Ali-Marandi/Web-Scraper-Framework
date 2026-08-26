"""
WebScraper Pro - History Panel
Displays past scraping sessions with stats, search, detail view, and re-export capability.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import theme, Typography, Spacing, Radius
from core.history import HistoryManager, HistoryEntry, HistorySortField, SortOrder


class HistoryPanel(ctk.CTkFrame):
    """History panel showing past scraping sessions with stats and actions."""

    SORT_OPTIONS = {"Date": HistorySortField.DATE, "Name": HistorySortField.NAME,
                    "Records": HistorySortField.RECORDS, "Duration": HistorySortField.DURATION}
    ORDER_OPTIONS = ["Newest First", "Oldest First"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._history_manager = HistoryManager()
        self._selected_entry_id: str | None = None
        self._current_sort = HistorySortField.DATE
        self._current_order = SortOrder.DESC

        self._build_toolbar()
        self._build_stats_bar()
        self._build_main_area()

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))
        bar.grid_columnconfigure(1, weight=1)

        # Search
        self._search_entry = ctk.CTkEntry(
            bar, placeholder_text="Search history...",
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            width=250, height=30,
        )
        self._search_entry.grid(row=0, column=0, padx=(Spacing.MD, Spacing.SM), pady=Spacing.SM, sticky="w")
        self._search_entry.bind("<KeyRelease>", self._on_search)

        # Sort controls
        ctk.CTkLabel(bar, text="Sort:", font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                      text_color=theme.colors.TEXT_MUTED).grid(row=0, column=2, padx=(Spacing.LG, Spacing.XS))

        self._sort_menu = ctk.CTkOptionMenu(
            bar, values=list(self.SORT_OPTIONS.keys()), width=100,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_sort_change,
        )
        self._sort_menu.set("Date")
        self._sort_menu.grid(row=0, column=3, padx=Spacing.XS)

        self._order_menu = ctk.CTkOptionMenu(
            bar, values=self.ORDER_OPTIONS, width=120,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_order_change,
        )
        self._order_menu.set("Newest First")
        self._order_menu.grid(row=0, column=4, padx=Spacing.XS)

        # Action buttons
        btns_frame = ctk.CTkFrame(bar, fg_color="transparent")
        btns_frame.grid(row=0, column=5, padx=Spacing.MD, pady=Spacing.SM)

        for text, color, cmd in [
            ("View", theme.colors.BRAND_PRIMARY, self._view_selected),
            ("Export", theme.colors.BG_ELEVATED, self._export_selected),
            ("Delete", theme.colors.ERROR, self._delete_selected),
            ("Clear All", theme.colors.ERROR, self._clear_all),
        ]:
            ctk.CTkButton(
                btns_frame, text=text, width=70, height=28,
                font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                fg_color=color, hover_color=color,
                text_color=theme.colors.TEXT_PRIMARY if color != theme.colors.BRAND_PRIMARY else theme.colors.TEXT_INVERSE,
                corner_radius=Radius.MD, command=cmd,
            ).pack(side="left", padx=2)

    # ------------------------------------------------------------------
    # Stats Bar
    # ------------------------------------------------------------------

    def _build_stats_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        bar.grid(row=1, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._stat_sessions = ctk.CTkLabel(bar, text="Sessions: 0",
                                            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                            text_color=theme.colors.TEXT_SECONDARY)
        self._stat_sessions.grid(row=0, column=0, padx=Spacing.MD, pady=Spacing.XS, sticky="w")

        self._stat_records = ctk.CTkLabel(bar, text="Records: 0",
                                           font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                           text_color=theme.colors.TEXT_SECONDARY)
        self._stat_records.grid(row=0, column=1, padx=Spacing.MD, pady=Spacing.XS)

        self._stat_success = ctk.CTkLabel(bar, text="Success: --",
                                          font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                          text_color=theme.colors.TEXT_SUCCESS)
        self._stat_success.grid(row=0, column=2, padx=Spacing.MD, pady=Spacing.XS)

        self._stat_avg = ctk.CTkLabel(bar, text="Avg Records: --",
                                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                       text_color=theme.colors.TEXT_SECONDARY)
        self._stat_avg.grid(row=0, column=3, padx=Spacing.MD, pady=Spacing.XS)

        self._stat_duration = ctk.CTkLabel(bar, text="Total Time: --",
                                            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                                            text_color=theme.colors.TEXT_SECONDARY)
        self._stat_duration.grid(row=0, column=4, padx=Spacing.MD, pady=Spacing.XS, sticky="e")

    # ------------------------------------------------------------------
    # Main Area (Session List + Detail)
    # ------------------------------------------------------------------

    def _build_main_area(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=2)

        # Left: Session list
        list_card = ctk.CTkFrame(container, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(list_card, text="Sessions",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._session_text = ctk.CTkTextbox(
            list_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._session_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))
        self._session_text.bind("<Button-1>", self._on_session_click)

        # Right: Detail view
        detail_card = ctk.CTkFrame(container, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        detail_card.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        detail_card.grid_rowconfigure(1, weight=1)
        detail_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(detail_card, text="Session Details",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._detail_text = ctk.CTkTextbox(
            detail_card, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._detail_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_search(self, event=None):
        query = self._search_entry.get().strip()
        entries = self._history_manager.search(query)
        self._display_entries(entries)

    def _on_sort_change(self, value):
        self._current_sort = self.SORT_OPTIONS.get(value, HistorySortField.DATE)
        self._refresh_list()

    def _on_order_change(self, value):
        self._current_order = SortOrder.DESC if value == "Newest First" else SortOrder.ASC
        self._refresh_list()

    def _on_session_click(self, event):
        # Find which line was clicked
        try:
            line_num = int(self._session_text.index(f"@{event.x},{event.y}").split(".")[0]) - 1
            entries = self._get_displayed_entries()
            if 0 <= line_num < len(entries):
                entry = entries[line_num]
                self._selected_entry_id = entry.id
                self._show_detail(entry)
        except Exception:
            pass

    def _get_displayed_entries(self) -> list:
        query = self._search_entry.get().strip()
        if query:
            return self._history_manager.search(query)
        return self._history_manager.get_sorted(self._current_sort, self._current_order)

    def _view_selected(self):
        if not self._selected_entry_id:
            messagebox.showinfo("History", "Select a session first.")
            return
        entry = self._history_manager.get_entry(self._selected_entry_id)
        if not entry:
            return
        # Load results into main engine
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and entry.has_results:
            results = self._history_manager.get_results(entry.id)
            if results:
                app.engine._results.clear()
                app.engine._results.extend(results)
                if hasattr(app, '_log_panel'):
                    app._log_panel.add_log(f"Loaded {len(results)} records from history: {entry.name}", "success")
                # Switch to dashboard
                if hasattr(app, '_switch_panel'):
                    app._switch_panel("dashboard")

    def _export_selected(self):
        if not self._selected_entry_id:
            messagebox.showinfo("History", "Select a session first.")
            return
        entry = self._history_manager.get_entry(self._selected_entry_id)
        if not entry or not entry.has_results:
            messagebox.showinfo("History", "No results to export for this session.")
            return
        results = self._history_manager.get_results(entry.id)
        if not results:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"),
                      ("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            app = self.winfo_toplevel()
            if hasattr(app, 'engine'):
                fmt = path.rsplit(".", 1)[-1].lower()
                app.engine.export_results(fmt, path, data=results)
                if hasattr(app, '_log_panel'):
                    app._log_panel.add_log(f"Exported history results to {path}", "success")
                messagebox.showinfo("Export", f"Exported {len(results)} records to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _delete_selected(self):
        if not self._selected_entry_id:
            return
        if messagebox.askyesno("Delete", "Delete this session from history?"):
            self._history_manager.delete_entry(self._selected_entry_id)
            self._selected_entry_id = None
            self._refresh_list()
            self._clear_detail()
            app = self.winfo_toplevel()
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log("History entry deleted", "info")

    def _clear_all(self):
        if not self._history_manager.entries:
            return
        if messagebox.askyesno("Clear All", "Delete ALL history entries? This cannot be undone."):
            count = self._history_manager.clear_all()
            self._selected_entry_id = None
            self._refresh_list()
            self._clear_detail()
            app = self.winfo_toplevel()
            if hasattr(app, '_log_panel'):
                app._log_panel.add_log(f"Cleared {count} history entries", "warning")

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def _display_entries(self, entries: list):
        self._session_text.configure(state="normal")
        self._session_text.delete("0.0", "end")
        if not entries:
            self._session_text.insert("end", "  No history entries found.")
        else:
            for entry in entries:
                status_icon = "+" if entry.success else "!"
                line = (f" {status_icon}  {entry.timestamp_short}  |  {entry.name[:30]:<30}  |  "
                        f"{entry.records_extracted:>5} rec  |  {entry.duration_formatted:>8}  |  {entry.mode}")
                self._session_text.insert("end", line + "\n")
        self._session_text.configure(state="disabled")

    def _show_detail(self, entry: HistoryEntry):
        self._detail_text.configure(state="normal")
        self._detail_text.delete("0.0", "end")

        lines = [
            f"  Session:  {entry.name}",
            f"  ID:       {entry.id}",
            f"  Time:     {entry.timestamp}",
            f"  Mode:     {entry.mode}",
            f"  Status:   {'Success' if entry.success else 'Failed'}",
            "",
            f"  URLs:           {entry.urls_count}",
            f"  Records:        {entry.records_extracted}",
            f"  Errors:         {entry.errors_count}",
            f"  Duration:       {entry.duration_formatted}",
            f"  Data Size:      {entry.bytes_formatted}",
            f"  Rules Used:     {entry.rules_count}",
            f"  Has Results:    {entry.has_results}",
            "",
        ]

        if entry.urls_sample:
            lines.append("  Sample URLs:")
            for url in entry.urls_sample[:5]:
                lines.append(f"    - {url[:80]}")
            lines.append("")

        if entry.rule_names:
            lines.append("  Extraction Rules:")
            for rn in entry.rule_names[:10]:
                lines.append(f"    - {rn}")
            lines.append("")

        if entry.status_codes:
            lines.append("  Status Codes:")
            for code, count in sorted(entry.status_codes.items()):
                lines.append(f"    {code}: {count}")
            lines.append("")

        if entry.error_message:
            lines.append(f"  Error: {entry.error_message}")

        self._detail_text.insert("end", "\n".join(lines))
        self._detail_text.configure(state="disabled")

    def _clear_detail(self):
        self._detail_text.configure(state="normal")
        self._detail_text.delete("0.0", "end")
        self._detail_text.insert("end", "  Select a session to view details.")
        self._detail_text.configure(state="disabled")

    def _refresh_list(self):
        entries = self._get_displayed_entries()
        self._display_entries(entries)
        self._update_stats()

    def _update_stats(self):
        stats = self._history_manager.get_stats()
        self._stat_sessions.configure(text=f"Sessions: {stats.get('total_sessions', 0)}")
        self._stat_records.configure(text=f"Records: {stats.get('total_records', 0)}")
        self._stat_success.configure(text=f"Success: {stats.get('success_rate', 0):.1f}%")
        self._stat_avg.configure(text=f"Avg: {stats.get('avg_records_per_session', 0):.0f}")
        total_dur = stats.get('total_duration', 0)
        if total_dur < 60:
            self._stat_duration.configure(text=f"Total Time: {total_dur:.0f}s")
        elif total_dur < 3600:
            self._stat_duration.configure(text=f"Total Time: {int(total_dur // 60)}m")
        else:
            self._stat_duration.configure(text=f"Total Time: {int(total_dur // 3600)}h")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def history_manager(self) -> HistoryManager:
        return self._history_manager

    def update_ui(self, engine):
        if not hasattr(self, '_session_text'):
            return
        self._refresh_list()
        if self._selected_entry_id:
            entry = self._history_manager.get_entry(self._selected_entry_id)
            if entry:
                self._show_detail(entry)
