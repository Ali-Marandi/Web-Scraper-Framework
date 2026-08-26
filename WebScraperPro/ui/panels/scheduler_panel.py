"""
WebScraper Pro - Scheduler Panel
Schedule recurring scraping tasks with various interval types.
"""

import uuid
import customtkinter as ctk

from ui.styles import theme, Typography, Spacing, Radius
from core.scheduler import ScheduledTask, ScheduleType


class SchedulerPanel(ctk.CTkFrame):
    """Task scheduler UI with add/enable/disable/delete and history."""

    SCHEDULE_TYPE_OPTIONS = [t.value for t in ScheduleType]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._task_ids: list[str] = []
        self._build_add_form()
        self._build_task_list()
        self._build_history()

    # ------------------------------------------------------------------
    # Add Task Form
    # ------------------------------------------------------------------

    def _build_add_form(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.MD, 0))
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(3, weight=1)
        card.grid_columnconfigure(5, weight=1)

        entry_opts = dict(
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=30,
        )

        row = 0
        ctk.CTkLabel(card, text="Task Name", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=0, padx=(Spacing.MD, Spacing.XS),
                                                                      pady=(Spacing.SM, 0), sticky="w")
        self._name_entry = ctk.CTkEntry(card, placeholder_text="My scheduled task", **entry_opts)
        self._name_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))

        ctk.CTkLabel(card, text="URL", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=3, padx=(Spacing.SM, Spacing.XS),
                                                                      pady=(Spacing.SM, 0), sticky="w")
        self._url_entry = ctk.CTkEntry(card, placeholder_text="https://example.com", **entry_opts)
        self._url_entry.grid(row=row, column=4, columnspan=2, sticky="ew", padx=Spacing.XS, pady=(Spacing.SM, 0))

        row = 1
        ctk.CTkLabel(card, text="Schedule Type", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=0, padx=(Spacing.MD, Spacing.XS),
                                                                      pady=Spacing.SM, sticky="w")
        self._type_menu = ctk.CTkOptionMenu(
            card, values=self.SCHEDULE_TYPE_OPTIONS, width=120,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, button_color=theme.colors.BG_ELEVATED,
            button_hover_color=theme.colors.BG_HOVER,
            dropdown_fg_color=theme.colors.BG_ELEVATED,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            command=self._on_type_change,
        )
        self._type_menu.set("interval")
        self._type_menu.grid(row=row, column=1, padx=Spacing.XS, pady=Spacing.SM, sticky="w")

        ctk.CTkLabel(card, text="Interval (sec)", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=2, padx=(Spacing.SM, Spacing.XS),
                                                                      pady=Spacing.SM, sticky="w")
        self._interval_entry = ctk.CTkEntry(card, placeholder_text="3600", width=90, **entry_opts)
        self._interval_entry.insert("0", "3600")
        self._interval_entry.grid(row=row, column=3, padx=Spacing.XS, pady=Spacing.SM)

        ctk.CTkLabel(card, text="Time (HH:MM)", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                      text_color=theme.colors.TEXT_SECONDARY).grid(row=row, column=4, padx=(Spacing.SM, Spacing.XS),
                                                                      pady=Spacing.SM, sticky="w")
        self._time_entry = ctk.CTkEntry(card, placeholder_text="08:00", width=80, **entry_opts)
        self._time_entry.grid(row=row, column=5, padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

        ctk.CTkButton(card, text="+ Add Task", width=110, height=28,
                       font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
                       fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
                       corner_radius=Radius.MD, command=self._add_task
                       ).grid(row=2, column=0, columnspan=6, sticky="w", padx=Spacing.MD, pady=(0, Spacing.MD))

    def _on_type_change(self, value):
        is_interval = value == "interval"
        is_timed = value in ("daily", "weekly")
        self._interval_entry.configure(state="normal" if is_interval else "disabled")
        self._time_entry.configure(state="normal" if is_timed else "disabled")

    # ------------------------------------------------------------------
    # Task List
    # ------------------------------------------------------------------

    def _build_task_list(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM, padx=Spacing.MD)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Scheduled Tasks",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w",
                                                                     padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._task_text = ctk.CTkTextbox(
            card, height=180, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._task_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.SM))

        btn_bar = ctk.CTkFrame(card, fg_color="transparent")
        btn_bar.grid(row=2, column=0, sticky="ew", padx=Spacing.MD, pady=(0, Spacing.MD))

        ctk.CTkButton(btn_bar, text="Toggle Enable/Disable", width=170, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
                       text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD, border_width=1,
                       border_color=theme.colors.BORDER, command=self._toggle_selected
                       ).pack(side="left", padx=(0, Spacing.SM))

        ctk.CTkButton(btn_bar, text="Delete Task", width=110, height=26,
                       font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
                       fg_color=theme.colors.ERROR, hover_color=theme.colors.ERROR,
                       corner_radius=Radius.MD, command=self._delete_task
                       ).pack(side="left", padx=Spacing.SM)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _build_history(self):
        card = ctk.CTkFrame(self, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=2, column=0, sticky="nsew", padx=Spacing.MD, pady=(0, Spacing.MD))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Execution History",
                      font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
                      text_color=theme.colors.TEXT_PRIMARY).grid(row=0, column=0, sticky="w",
                                                                     padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._history_text = ctk.CTkTextbox(
            card, height=120, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._history_text.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_task(self):
        name = self._name_entry.get().strip()
        url = self._url_entry.get().strip()
        if not name or not url:
            return

        engine = self.winfo_toplevel().engine
        if not engine:
            return

        try:
            interval = int(self._interval_entry.get().strip() or "3600")
        except ValueError:
            interval = 3600

        task = ScheduledTask(
            id=str(uuid.uuid4())[:8],
            name=name,
            url=url,
            schedule_type=ScheduleType(self._type_menu.get()),
            interval_seconds=interval,
            specific_time=self._time_entry.get().strip(),
        )
        engine.scheduler.add_task(task)
        self._name_entry.delete(0, "end")
        self._url_entry.delete(0, "end")
        self.update_ui(engine)

    def _toggle_selected(self):
        engine = self.winfo_toplevel().engine
        if not engine or not self._task_ids:
            return
        for tid in self._task_ids:
            task = engine.scheduler.get_task(tid)
            if task:
                engine.scheduler.enable_task(tid, not task.enabled)
        self.update_ui(engine)

    def _delete_task(self):
        engine = self.winfo_toplevel().engine
        if not engine or not self._task_ids:
            return
        for tid in self._task_ids:
            engine.scheduler.remove_task(tid)
        self.update_ui(engine)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_ui(self, engine):
        if not engine:
            return
        tasks = engine.scheduler.get_all_tasks()
        self._task_ids.clear()

        self._task_text.configure(state="normal")
        self._task_text.delete("0.0", "end")
        if not tasks:
            self._task_text.insert("end", "No scheduled tasks.")
        else:
            for t in tasks:
                self._task_ids.append(t.id)
                status = "ON" if t.enabled else "OFF"
                color_tag = "✅" if t.enabled else "⏸"
                next_run = t.next_run or "N/A"
                line = (f"{color_tag} {t.name:<25}  |  {t.schedule_type.value:<12}  |  "
                        f"runs: {t.total_runs}  |  next: {next_run}  |  id: {t.id}")
                self._task_text.insert("end", line + "\n")
        self._task_text.configure(state="disabled")

        history = engine.scheduler.get_history(limit=50)
        self._history_text.configure(state="normal")
        self._history_text.delete("0.0", "end")
        if not history:
            self._history_text.insert("end", "No execution history yet.")
        else:
            for h in history:
                status = "OK" if h.get("success") else "FAIL"
                records = h.get("records_scraped", 0)
                error = h.get("error", "")
                line = (f"[{h.get('started_at', '?')[:19]}]  {h.get('task_name', '?'):<20}  |  "
                        f"{status:<4}  |  records: {records}")
                if error:
                    line += f"  |  error: {error}"
                self._history_text.insert("end", line + "\n")
        self._history_text.configure(state="disabled")
