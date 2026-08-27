"""WebScraper Pro - Analytics Panel

Integrates quantitative analysis modules: Fuzzy Logic, Content Intelligence,
Anomaly Detection, Data Quality (Bayesian), and Graph Theory.
Provides five tabbed views for advanced data analysis capabilities.
"""

import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ui.styles import theme, Typography, Spacing, Radius


class AnalyticsPanel(ctk.CTkFrame):
    """Advanced analytics panel with five tabbed views for quantitative analysis.

    Tabs:
        - Fuzzy Matching: Compare strings and deduplicate items.
        - Content Analysis: Text statistics, sentiment, keywords, entities, summary.
        - Anomaly Detection: Z-score, IQR, Modified Z-Score, Ensemble, CUSUM.
        - Data Quality: Dimension scores, Bayesian tracker, Information Theory.
        - Graph Analysis: PageRank, centrality, connected components, bridges.
    """

    TAB_VALUES = [
        "Fuzzy Matching",
        "Content Analysis",
        "Anomaly Detection",
        "Data Quality",
        "Graph Analysis",
    ]

    def __init__(self, master, **kwargs):
        """Initialize the analytics panel with a segmented button tab bar."""
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_tabs()

    def _build_tabs(self):
        """Create the segmented button and allocate a frame for each tab."""
        self._tab_seg = ctk.CTkSegmentedButton(
            self, values=self.TAB_VALUES,
            font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            selected_color=theme.colors.BRAND_PRIMARY,
            selected_hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            command=self._switch_tab,
        )
        self._tab_seg.set(self.TAB_VALUES[0])
        self._tab_seg.grid(
            row=0, column=0, sticky="ew",
            padx=Spacing.MD, pady=(Spacing.MD, 0),
        )

        self._frames = {}
        for tab_name in self.TAB_VALUES:
            frame = ctk.CTkFrame(self, fg_color="transparent")
            frame.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)
            frame.grid_rowconfigure(1, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            self._frames[tab_name] = frame

        self._build_fuzzy_tab(self._frames["Fuzzy Matching"])
        self._build_content_tab(self._frames["Content Analysis"])
        self._build_anomaly_tab(self._frames["Anomaly Detection"])
        self._build_quality_tab(self._frames["Data Quality"])
        self._build_graph_tab(self._frames["Graph Analysis"])
        self._switch_tab(self.TAB_VALUES[0])

    def _switch_tab(self, value):
        """Show the selected tab frame and hide all others."""
        for name, frame in self._frames.items():
            if name == value:
                frame.grid()
            else:
                frame.grid_remove()

    def update_ui(self, engine):
        """Public API stub for engine-driven UI updates."""
        pass

    # ==================================================================
    # Fuzzy Matching Tab
    # ==================================================================

    def _build_fuzzy_tab(self, parent):
        """Build the fuzzy matching tab with two string entries, compare button, results, and dedup section."""
        top = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            top, text="String 1", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM, sticky="w")

        self._fuzzy_s1 = ctk.CTkEntry(
            top, placeholder_text="First string...",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=32,
        )
        self._fuzzy_s1.grid(row=0, column=1, sticky="ew", padx=Spacing.XS, pady=Spacing.SM)

        ctk.CTkLabel(
            top, text="String 2", font=(Typography.FONT_FAMILY, Typography.SMALL_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).grid(row=0, column=2, padx=(Spacing.MD, Spacing.XS), pady=Spacing.SM, sticky="w")

        self._fuzzy_s2 = ctk.CTkEntry(
            top, placeholder_text="Second string...",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=32,
        )
        self._fuzzy_s2.grid(row=0, column=3, sticky="ew", padx=(Spacing.XS, Spacing.MD), pady=Spacing.SM)

        ctk.CTkButton(
            top, text="Compare", width=80, height=28,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_fuzzy_compare,
        ).grid(row=1, column=0, columnspan=4, sticky="e", padx=Spacing.MD, pady=(0, Spacing.SM))

        # Results area
        res = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        res.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        res.grid_rowconfigure(0, weight=1)
        res.grid_columnconfigure(0, weight=1)

        self._fuzzy_results = ctk.CTkTextbox(
            res, font=(Typography.MONO_FONT, Typography.SMALL_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._fuzzy_results.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

        # Dedup section
        dedup_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        dedup_card.grid(row=2, column=0, sticky="nsew", pady=Spacing.SM)
        dedup_card.grid_rowconfigure(1, weight=1)
        dedup_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(dedup_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Fuzzy Deduplication (one item per line)",
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            text_color=theme.colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        threshold_frame = ctk.CTkFrame(header, fg_color="transparent")
        threshold_frame.grid(row=0, column=1, padx=Spacing.SM)

        ctk.CTkLabel(
            threshold_frame, text="Threshold:",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).pack(side="left")

        self._dedup_threshold = ctk.CTkEntry(
            threshold_frame, width=50, height=24,
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._dedup_threshold.insert("0", "0.85")
        self._dedup_threshold.pack(side="left", padx=Spacing.XS)

        ctk.CTkButton(
            threshold_frame, text="Deduplicate", width=100, height=24,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_fuzzy_dedup,
        ).pack(side="left", padx=Spacing.XS)

        self._dedup_input = ctk.CTkTextbox(
            dedup_card, height=100, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._dedup_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

    def _run_fuzzy_compare(self):
        """Compare two strings using fuzzy matching algorithms and display scores."""
        s1 = self._fuzzy_s1.get().strip()
        s2 = self._fuzzy_s2.get().strip()
        if not s1 or not s2:
            return

        from core.fuzzy_engine import FuzzyMatcher
        m = FuzzyMatcher()
        fe = m.fuzzy_equal(s1, s2)
        jw = m.jaro_winkler(s1, s2)
        lev = m.levenshtein(s1, s2)
        fc = m.fuzzy_contains(s1, s2)
        max_len = max(len(s1), len(s2), 1)
        norm_lev = 1.0 - (lev / max_len)

        self._fuzzy_results.configure(state="normal")
        self._fuzzy_results.delete("0.0", "end")
        self._fuzzy_results.insert("end", f"  Fuzzy Equal Score:  {fe:.4f}\n")
        self._fuzzy_results.insert("end", f"  Jaro-Winkler:       {jw:.4f}\n")
        self._fuzzy_results.insert("end", f"  Levenshtein Dist:   {lev}\n")
        self._fuzzy_results.insert("end", f"  Fuzzy Contains:     {fc:.4f}\n")
        self._fuzzy_results.insert("end", f"  Max Length:         {max_len}\n")
        self._fuzzy_results.insert("end", f"  Normalized Lev Sim: {norm_lev:.4f}\n")
        self._fuzzy_results.configure(state="disabled")

    def _run_fuzzy_dedup(self):
        """Run fuzzy deduplication on a list of items using the configured threshold."""
        text = self._dedup_input.get("0.0", "end").strip()
        if not text:
            return
        items = [line.strip() for line in text.split("\n") if line.strip()]
        try:
            threshold = float(self._dedup_threshold.get().strip())
        except ValueError:
            threshold = 0.85

        from core.fuzzy_engine import FuzzyMatcher
        m = FuzzyMatcher()
        unique = m.deduplicate(items, threshold)
        removed = len(items) - len(unique)

        self._fuzzy_results.configure(state="normal")
        self._fuzzy_results.delete("0.0", "end")
        self._fuzzy_results.insert("end", f"  Input items:   {len(items)}\n")
        self._fuzzy_results.insert("end", f"  Unique items:  {len(unique)}\n")
        self._fuzzy_results.insert("end", f"  Duplicates:    {removed}\n")
        self._fuzzy_results.insert("end", f"  Threshold:     {threshold:.2f}\n")
        self._fuzzy_results.insert("end", f"\n  --- Unique Items ---\n")
        for item in unique:
            self._fuzzy_results.insert("end", f"  {item}\n")
        self._fuzzy_results.configure(state="disabled")

    # ==================================================================
    # Content Analysis Tab
    # ==================================================================

    def _build_content_tab(self, parent):
        """Build the content analysis tab with URL entry, text area, analyze button, and results."""
        top = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        top.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(top, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bar, text="URL (optional - fetch content)",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w")

        self._content_url = ctk.CTkEntry(
            bar, placeholder_text="https://example.com (leave empty to use text below)",
            font=(Typography.MONO_FONT, Typography.BODY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            height=30,
        )
        self._content_url.grid(row=1, column=0, sticky="ew", pady=(Spacing.XS, 0))

        ctk.CTkButton(
            bar, text="Analyze", width=80, height=28,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_content_analysis,
        ).grid(row=1, column=1, padx=(Spacing.SM, 0))

        # Text input
        mid = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        mid.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        mid.grid_rowconfigure(1, weight=1)
        mid.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mid, text="Text Content (or paste HTML)",
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            text_color=theme.colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=Spacing.MD, pady=(Spacing.SM, 0))

        self._content_input = ctk.CTkTextbox(
            mid, height=120, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._content_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        res = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        res.grid(row=2, column=0, sticky="nsew", pady=Spacing.SM)
        res.grid_rowconfigure(0, weight=1)
        res.grid_columnconfigure(0, weight=1)

        self._content_results = ctk.CTkTextbox(
            res, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._content_results.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    def _run_content_analysis(self):
        """Fetch content from URL in a background thread or analyze pasted text directly."""
        url = self._content_url.get().strip()
        text = self._content_input.get("0.0", "end").strip()

        if url and not text:
            def _fetch():
                """Background thread: fetch URL content and trigger analysis on the main thread."""
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                    soup = BeautifulSoup(resp.text, "lxml")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    fetched = soup.get_text(separator=" ", strip=True)
                    self.after(0, lambda: self._content_input.insert("0.0", fetched))
                    self.after(0, lambda: self._analyze_content(fetched))
                except Exception as exc:
                    self.after(0, lambda: self._show_content_error(str(exc)))

            threading.Thread(target=_fetch, daemon=True).start()
        elif text:
            self._analyze_content(text)

    def _analyze_content(self, text: str):
        """Run all content analysis modules on the given text and display results."""
        from core.content_analyzer import (
            ContentAnalyzer, TextStatistics,
            SentimentAnalyzer, KeywordExtractor,
        )

        self._content_results.configure(state="normal")
        self._content_results.delete("0.0", "end")

        try:
            stats = TextStatistics()
            readability = stats.compute_readability(text)
            freq = stats.compute_word_frequency(text, top_n=15)
            entropy = stats.compute_entropy(text)
            diversity = stats.compute_lexical_diversity(text)
            lang = stats.language_detect(text)

            self._content_results.insert("end", "=== Text Statistics ===\n")
            self._content_results.insert("end", f"  Words:            {readability['word_count']}\n")
            self._content_results.insert("end", f"  Sentences:        {readability['sentence_count']}\n")
            self._content_results.insert("end", f"  Avg Sentence:     {readability['avg_sentence_length']:.1f} words\n")
            self._content_results.insert("end", f"  Avg Word Len:     {readability['avg_word_length']:.2f} chars\n")
            self._content_results.insert("end", f"  Flesch-Kincaid:   {readability['flesch_kincaid']:.1f}\n")
            self._content_results.insert("end", f"  Shannon Entropy:  {entropy:.4f}\n")
            self._content_results.insert("end", f"  Lexical Div:      {diversity:.4f}\n")
            self._content_results.insert("end", f"  Detected Lang:    {lang}\n")

            sa = SentimentAnalyzer()
            sent = sa.analyze(text)
            self._content_results.insert("end", f"\n=== Sentiment Analysis ===\n")
            self._content_results.insert("end", f"  Polarity:     {sent['polarity_score']:.3f} [-1, 1]\n")
            self._content_results.insert("end", f"  Subjectivity: {sent['subjectivity']:.3f} [0, 1]\n")
            self._content_results.insert("end", f"  Label:        {sent['label']}\n")

            ke = KeywordExtractor()
            keywords = ke.extract_keywords_rake(text, top_n=10)
            self._content_results.insert("end", f"\n=== Top Keywords (RAKE) ===\n")
            for kw, score in keywords:
                self._content_results.insert("end", f"  {score:.3f}  {kw}\n")

            entities = ke.extract_named_entities_basic(text)
            if entities:
                self._content_results.insert("end", f"\n=== Named Entities ===\n")
                for ent, etype in entities[:20]:
                    self._content_results.insert("end", f"  [{etype}] {ent}\n")

            summary = ContentAnalyzer().generate_summary(text, max_sentences=3)
            if summary:
                self._content_results.insert("end", f"\n=== Extractive Summary ===\n")
                self._content_results.insert("end", f"  {summary}\n")

        except Exception as exc:
            self._content_results.insert("end", f"Error: {exc}\n")

        self._content_results.configure(state="disabled")

    def _show_content_error(self, msg: str):
        """Display a fetch error message in the content results textbox."""
        self._content_results.configure(state="normal")
        self._content_results.delete("0.0", "end")
        self._content_results.insert("end", f"  Fetch error: {msg}\n")
        self._content_results.configure(state="disabled")

    # ==================================================================
    # Anomaly Detection Tab
    # ==================================================================

    def _build_anomaly_tab(self, parent):
        """Build the anomaly detection tab with numeric input, threshold, and result display."""
        input_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        input_card.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(input_card, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bar, text="Numeric Data (one value per line - e.g. response times, data sizes)",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w")

        opts = ctk.CTkFrame(bar, fg_color="transparent")
        opts.grid(row=0, column=1, padx=Spacing.SM)

        ctk.CTkLabel(
            opts, text="Z-Score Threshold:",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).pack(side="left")

        self._anomaly_threshold = ctk.CTkEntry(
            opts, width=50, height=24,
            font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._anomaly_threshold.insert("0", "2.5")
        self._anomaly_threshold.pack(side="left", padx=Spacing.XS)

        ctk.CTkButton(
            opts, text="Detect Anomalies", width=120, height=24,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_anomaly_detection,
        ).pack(side="left", padx=Spacing.XS)

        ctk.CTkButton(
            opts, text="Generate Sample", width=110, height=24,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            border_width=1, border_color=theme.colors.BORDER,
            command=self._generate_anomaly_sample,
        ).pack(side="left", padx=Spacing.XS)

        self._anomaly_input = ctk.CTkTextbox(
            input_card, height=80, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._anomaly_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        res = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        res.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        res.grid_rowconfigure(0, weight=1)
        res.grid_columnconfigure(0, weight=1)

        self._anomaly_results = ctk.CTkTextbox(
            res, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._anomaly_results.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    def _generate_anomaly_sample(self):
        """Generate a sample dataset with injected outliers for testing anomaly detection."""
        import random
        random.seed(42)
        values = [random.gauss(100, 15) for _ in range(45)]
        values[10] = 250.0
        values[25] = 5.0
        values[38] = 300.0
        text = "\n".join(f"{v:.1f}" for v in values)
        self._anomaly_input.delete("0.0", "end")
        self._anomaly_input.insert("0.0", text)

    def _run_anomaly_detection(self):
        """Parse numeric input and run all anomaly detection algorithms."""
        text = self._anomaly_input.get("0.0", "end").strip()
        if not text:
            return
        try:
            threshold = float(self._anomaly_threshold.get().strip())
        except ValueError:
            threshold = 2.5

        values = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                try:
                    values.append(float(line))
                except ValueError:
                    continue

        if len(values) < 5:
            self._anomaly_results.configure(state="normal")
            self._anomaly_results.delete("0.0", "end")
            self._anomaly_results.insert("end", "  Need at least 5 numeric values.\n")
            self._anomaly_results.configure(state="disabled")
            return

        from core.anomaly_detector import StatisticalAnomalyDetector, ChangePointDetector
        import numpy as np

        sd = StatisticalAnomalyDetector()
        self._anomaly_results.configure(state="normal")
        self._anomaly_results.delete("0.0", "end")

        arr = np.array(values)
        self._anomaly_results.insert("end", f"=== Data Overview ({len(values)} values) ===\n")
        self._anomaly_results.insert("end", f"  Mean:   {np.mean(arr):.3f}\n")
        self._anomaly_results.insert("end", f"  Std:    {np.std(arr):.3f}\n")
        self._anomaly_results.insert("end", f"  Median: {np.median(arr):.3f}\n")
        self._anomaly_results.insert("end", f"  Min:    {np.min(arr):.3f}\n")
        self._anomaly_results.insert("end", f"  Max:    {np.max(arr):.3f}\n")

        # Z-Score detection
        zscore_outliers = sd.zscore_detect(values, threshold=threshold)
        self._anomaly_results.insert("end", f"\n=== Z-Score Detection (threshold={threshold}) ===\n")
        self._anomaly_results.insert("end", f"  Anomalies found: {len(zscore_outliers)}\n")
        for idx, val, score in zscore_outliers:
            self._anomaly_results.insert("end", f"  [{idx}] value={val:.3f}  z-score={score:.3f}\n")

        # IQR detection
        iqr_outliers = sd.iqr_detect(values)
        self._anomaly_results.insert("end", f"\n=== IQR Detection (k=1.5) ===\n")
        self._anomaly_results.insert("end", f"  Anomalies found: {len(iqr_outliers)}\n")
        for idx, val, is_out in iqr_outliers:
            if is_out:
                self._anomaly_results.insert("end", f"  [{idx}] value={val:.3f}\n")

        # Modified Z-Score (MAD)
        mod_z_outliers = sd.modified_zscore_detect(values, threshold=threshold)
        self._anomaly_results.insert("end", f"\n=== Modified Z-Score (MAD) ===\n")
        self._anomaly_results.insert("end", f"  Anomalies found: {len(mod_z_outliers)}\n")
        for idx, val, score in mod_z_outliers:
            self._anomaly_results.insert("end", f"  [{idx}] value={val:.3f}  modified-z={score:.3f}\n")

        # Ensemble voting
        ensemble = sd.ensemble_detect(values)
        self._anomaly_results.insert("end", f"\n=== Ensemble Voting ===\n")
        anomaly_count = sum(1 for _, is_a, _ in ensemble if is_a)
        self._anomaly_results.insert("end", f"  Total anomalies (ensemble): {anomaly_count}/{len(values)}\n")
        for idx, is_a, conf in ensemble:
            if is_a:
                self._anomaly_results.insert("end", f"  [{idx}] value={values[idx]:.3f}  confidence={conf:.2f}\n")

        # CUSUM change points
        if len(values) >= 10:
            cpd = ChangePointDetector()
            cps = cpd.detect_cusum(values)
            self._anomaly_results.insert("end", f"\n=== Change Points (CUSUM) ===\n")
            self._anomaly_results.insert("end", f"  Change points: {len(cps)}\n")
            for cp in cps:
                self._anomaly_results.insert("end", f"  At index {cp}, value={values[cp]:.3f}\n")

        self._anomaly_results.configure(state="disabled")

    # ==================================================================
    # Data Quality Tab
    # ==================================================================

    def _build_quality_tab(self, parent):
        """Build the data quality tab with JSON input, assess button, and load sample button."""
        input_card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        input_card.grid_rowconfigure(0, weight=1)
        input_card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(input_card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=(Spacing.SM, 0))

        ctk.CTkLabel(
            header, text="JSON Data (list of objects)",
            font=(Typography.FONT_FAMILY, Typography.BODY_SIZE),
            text_color=theme.colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header, text="Assess Quality", width=110, height=26,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_quality_check,
        ).grid(row=0, column=1, padx=Spacing.SM)

        ctk.CTkButton(
            header, text="Load Sample", width=100, height=26,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            border_width=1, border_color=theme.colors.BORDER,
            command=self._load_quality_sample,
        ).grid(row=0, column=2, padx=Spacing.SM)

        self._quality_input = ctk.CTkTextbox(
            input_card, height=150, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._quality_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        res = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        res.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        res.grid_rowconfigure(0, weight=1)
        res.grid_columnconfigure(0, weight=1)

        self._quality_results = ctk.CTkTextbox(
            res, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._quality_results.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    def _load_quality_sample(self):
        """Load a sample JSON dataset with intentional quality issues for testing."""
        import json
        sample = [
            {"name": "Product A", "price": 29.99, "url": "https://example.com/a", "category": "Electronics"},
            {"name": "Product B", "price": "", "url": "https://example.com/b", "category": "Electronics"},
            {"name": "", "price": 15.50, "url": "invalid-url", "category": "Electronics"},
            {"name": "Product D", "price": 45.00, "url": "https://example.com/d", "category": ""},
            {"name": "Product E", "price": 89.99, "url": "https://example.com/e", "category": "Books"},
            {"name": "Product F", "price": 12.00, "url": "https://example.com/f", "category": "Books"},
            {"name": "Product G", "price": -5.00, "url": "https://example.com/g", "category": "Electronics"},
            {"name": "Product H", "price": 199.99, "url": "https://example.com/h", "category": "Electronics"},
        ]
        self._quality_input.delete("0.0", "end")
        self._quality_input.insert("0.0", json.dumps(sample, indent=2))

    def _run_quality_check(self):
        """Parse JSON input and run the full data quality assessment pipeline."""
        text = self._quality_input.get("0.0", "end").strip()
        if not text:
            return

        import json
        try:
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Expected a list of objects")
        except (json.JSONDecodeError, ValueError) as exc:
            self._quality_results.configure(state="normal")
            self._quality_results.delete("0.0", "end")
            self._quality_results.insert("end", f"  Invalid JSON: {exc}\n")
            self._quality_results.configure(state="disabled")
            return

        from core.data_quality import (
            DataQualityAssessor, BayesianScorer,
            InformationTheoryMetrics, QualityDimension,
        )

        self._quality_results.configure(state="normal")
        self._quality_results.delete("0.0", "end")

        try:
            assessor = DataQualityAssessor()
            report = assessor.assess(data)

            self._quality_results.insert("end", f"=== Data Quality Report ===\n")
            self._quality_results.insert("end", f"  Records analyzed:  {report.record_count}\n")
            self._quality_results.insert("end", f"  Overall Score:     {report.overall_score:.3f} / 1.0\n")
            self._quality_results.insert("end", f"  Weighted Score:    {report.weighted_score:.3f} / 1.0\n")

            self._quality_results.insert("end", f"\n=== Dimension Scores ===\n")

            dim_labels = {
                QualityDimension.COMPLETENESS: "Completeness",
                QualityDimension.CONSISTENCY: "Consistency",
                QualityDimension.ACCURACY: "Accuracy",
                QualityDimension.TIMELINESS: "Timeliness",
                QualityDimension.UNIQUENESS: "Uniqueness",
                QualityDimension.VALIDITY: "Validity",
            }
            for dim, score in report.dimension_scores.items():
                label = dim_labels.get(dim, str(dim))
                bar_len = int(score * 20)
                bar_char = "#" * bar_len + "-" * (20 - bar_len)
                color_tag = "OK" if score >= 0.8 else ("WARN" if score >= 0.6 else "BAD")
                self._quality_results.insert("end", f"  {label:<14} {bar_char} {score:.3f}  [{color_tag}]\n")

            if report.issues:
                self._quality_results.insert("end", f"\n=== Issues ({len(report.issues)}) ===\n")
                for issue in report.issues:
                    sev_icon = {
                        "critical": "!!", "high": "!",
                        "medium": "*", "low": ".",
                    }.get(issue.severity, "?")
                    self._quality_results.insert(
                        "end",
                        f"  {sev_icon} [{issue.severity.upper()}] {issue.dimension.value}: "
                        f"{issue.description} ({issue.affected_count} records)\n",
                    )

            suggestions = assessor.get_improvement_suggestions()
            if suggestions:
                self._quality_results.insert("end", f"\n=== Improvement Suggestions ===\n")
                for dim, suggestion, severity in suggestions:
                    self._quality_results.insert("end", f"  [{severity}] {suggestion}\n")

            # Bayesian scoring
            self._quality_results.insert("end", f"\n=== Bayesian Quality Tracker ===\n")
            bs = BayesianScorer()
            for record in data:
                is_good = all(v is not None and str(v).strip() for v in record.values())
                bs.update(is_good)
            self._quality_results.insert("end", f"  Posterior Score:  {bs.get_score():.3f}\n")
            self._quality_results.insert("end", f"  Confidence:       {bs.get_confidence():.3f}\n")
            ci = bs.get_credible_interval(0.95)
            self._quality_results.insert("end", f"  95% CI:          [{ci[0]:.3f}, {ci[1]:.3f}]\n")

            # Information Theory metrics
            self._quality_results.insert("end", f"\n=== Information Theory Metrics ===\n")
            itm = InformationTheoryMetrics()
            for key in data[0].keys() if data else []:
                col_values = [str(r.get(key, "")) for r in data]
                ent = itm.shannon_entropy(col_values)
                self._quality_results.insert("end", f"  {key:<14} entropy = {ent:.4f}\n")

        except Exception as exc:
            self._quality_results.insert("end", f"Error: {exc}\n")

        self._quality_results.configure(state="disabled")

    # ==================================================================
    # Graph Analysis Tab
    # ==================================================================

    def _build_graph_tab(self, parent):
        """Build the graph analysis tab with URL list input, analyze button, and load from explorer."""
        card = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        card.grid(row=0, column=0, sticky="ew", pady=(0, Spacing.SM))
        card.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=Spacing.MD, pady=Spacing.SM)
        bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bar, text="Enter URLs (one per line) to build a link graph, or use Explorer results",
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            text_color=theme.colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            bar, text="Analyze Graph", width=100, height=24,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BRAND_PRIMARY, hover_color=theme.colors.BRAND_PRIMARY_HOVER,
            corner_radius=Radius.MD, command=self._run_graph_analysis,
        ).grid(row=0, column=1, padx=Spacing.SM)

        ctk.CTkButton(
            bar, text="Load from Explorer", width=130, height=24,
            font=(Typography.FONT_FAMILY, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_ELEVATED, hover_color=theme.colors.BG_HOVER,
            text_color=theme.colors.TEXT_PRIMARY, corner_radius=Radius.MD,
            border_width=1, border_color=theme.colors.BORDER,
            command=self._load_graph_from_explorer,
        ).grid(row=0, column=2, padx=Spacing.SM)

        self._graph_input = ctk.CTkTextbox(
            card, height=100, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
        )
        self._graph_input.grid(row=1, column=0, sticky="nsew", padx=Spacing.MD, pady=(Spacing.XS, Spacing.MD))

        # Results
        res = ctk.CTkFrame(parent, fg_color=theme.colors.BG_CARD, corner_radius=Radius.LG)
        res.grid(row=1, column=0, sticky="nsew", pady=Spacing.SM)
        res.grid_rowconfigure(0, weight=1)
        res.grid_columnconfigure(0, weight=1)

        self._graph_results = ctk.CTkTextbox(
            res, font=(Typography.MONO_FONT, Typography.TINY_SIZE),
            fg_color=theme.colors.BG_INPUT, border_color=theme.colors.BORDER,
            border_width=1, corner_radius=Radius.MD, text_color=theme.colors.TEXT_PRIMARY,
            state="disabled",
        )
        self._graph_results.grid(row=0, column=0, sticky="nsew", padx=Spacing.MD, pady=Spacing.MD)

    def _load_graph_from_explorer(self):
        """Load discovered links from the Explorer panel into the graph analysis input."""
        app = self.winfo_toplevel()
        if not hasattr(app, '_panels') or 'explorer' not in app._panels:
            messagebox.showinfo("Graph", "Explorer panel not found.")
            return
        explorer = app._panels['explorer']
        if not explorer._result or not explorer._result.links:
            messagebox.showinfo("Graph", "No Explorer results. Explore a URL first.")
            return

        from core.url_explorer import LinkCategory
        links = [
            l.url for l in explorer._result.links
            if l.category in (LinkCategory.INTERNAL, LinkCategory.EXTERNAL) and not l.is_broken
        ]
        self._graph_input.delete("0.0", "end")
        self._graph_input.insert("0.0", "\n".join(links[:200]))
        app._log_panel.add_log(
            f"Loaded {len(links[:200])} links from Explorer to Graph Analysis", "success"
        )

    def _run_graph_analysis(self):
        """Build a directed graph from the URL list and compute PageRank, centrality, components, and bridges."""
        text = self._graph_input.get("0.0", "end").strip()
        if not text:
            return

        urls = [line.strip() for line in text.split("\n") if line.strip()]
        if len(urls) < 2:
            self._graph_results.configure(state="normal")
            self._graph_results.delete("0.0", "end")
            self._graph_results.insert("end", "  Need at least 2 URLs to build a graph.\n")
            self._graph_results.configure(state="disabled")
            return

        from core.graph_analyzer import DiGraph, CentralityAnalyzer, CommunityDetector
        from urllib.parse import urlparse

        self._graph_results.configure(state="normal")
        self._graph_results.delete("0.0", "end")

        try:
            g = DiGraph()
            domains = set()
            for url in urls:
                parsed = urlparse(url)
                domain = parsed.netloc or url
                domains.add(domain)
                g.add_node(url)

            for url in urls:
                parsed = urlparse(url)
                domain = parsed.netloc
                for other in urls:
                    if other == url:
                        continue
                    other_domain = urlparse(other).netloc
                    if domain == other_domain or not domain or not other_domain:
                        g.add_edge(url, other)

            nodes = g.get_all_nodes()
            edges = g.get_all_edges()

            self._graph_results.insert("end", f"=== Graph Structure ===\n")
            self._graph_results.insert("end", f"  Nodes:         {len(nodes)}\n")
            self._graph_results.insert("end", f"  Edges:         {len(edges)}\n")
            self._graph_results.insert("end", f"  Domains:       {len(domains)}\n")

            density = g.density()
            self._graph_results.insert("end", f"  Density:       {density:.4f}\n")

            # PageRank
            if len(nodes) > 0:
                ca = CentralityAnalyzer()
                pr = ca.pagerank(nodes, edges)
                top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]
                self._graph_results.insert("end", f"\n=== PageRank (Top 10) ===\n")
                for url, score in top_pr:
                    short = url[:60] + "..." if len(url) > 60 else url
                    self._graph_results.insert("end", f"  {score:.4f}  {short}\n")

                # Degree Centrality
                dc = ca.degree_centrality(nodes, edges)
                top_dc = sorted(dc.items(), key=lambda x: x[1], reverse=True)[:5]
                self._graph_results.insert("end", f"\n=== Degree Centrality (Top 5) ===\n")
                for url, score in top_dc:
                    short = url[:55] + "..." if len(url) > 55 else url
                    self._graph_results.insert("end", f"  {score:.4f}  {short}\n")

                # Closeness Centrality
                cc = ca.closeness_centrality(nodes, edges)
                top_cc = sorted(cc.items(), key=lambda x: x[1], reverse=True)[:5]
                self._graph_results.insert("end", f"\n=== Closeness Centrality (Top 5) ===\n")
                for url, score in top_cc:
                    short = url[:55] + "..." if len(url) > 55 else url
                    self._graph_results.insert("end", f"  {score:.4f}  {short}\n")

            # Connected Components
            cd = CommunityDetector()
            components = cd.connected_components(nodes, edges)
            self._graph_results.insert("end", f"\n=== Connected Components ===\n")
            self._graph_results.insert("end", f"  Components: {len(components)}\n")
            for i, comp in enumerate(components[:5]):
                self._graph_results.insert("end", f"  Component {i + 1}: {len(comp)} nodes\n")

            # Bridge links
            if len(nodes) >= 3 and len(edges) >= 2:
                bridges = cd.find_bridges(nodes, edges)
                self._graph_results.insert("end", f"\n=== Bridge Links ===\n")
                self._graph_results.insert("end", f"  Bridge edges: {len(bridges)}\n")
                for src, dst in bridges[:10]:
                    s = src[:40] + "..." if len(src) > 40 else src
                    self._graph_results.insert("end", f"  {s} -> {dst[:40]}\n")

        except Exception as exc:
            self._graph_results.insert("end", f"Error: {exc}\n")
            import traceback
            self._graph_results.insert("end", traceback.format_exc())

        self._graph_results.configure(state="disabled")
