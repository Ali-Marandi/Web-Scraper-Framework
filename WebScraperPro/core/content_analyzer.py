"""
Content Intelligence Module for Web Scraping.

Applies NLP, Information Theory, and text analysis methodologies to scraped
content using ONLY the Python standard library and numpy. No external NLP
libraries are required.

Classes:
    TextStatistics      – Readability, frequency, TF-IDF, entropy, diversity, language detection.
    KeywordExtractor    – TF-IDF keywords, RAKE, basic named-entity pattern extraction.
    SentimentAnalyzer   – Lexicon-based polarity / subjectivity with negation handling.
    ContentFingerprinter – SimHash fingerprints, Hamming similarity, duplicate detection.
    ContentAnalyzer     – Facade combining all of the above plus extractive summarisation.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)
_SENTENCE_RE = re.compile(r"[.!?]+\s*|\n\s*", re.UNICODE)
_WORD_RE = re.compile(r"\b[\w\u4e00-\u9fff]+\b", re.UNICODE)

# Stop-word list (small, covers en/de/es/fr/ru and common English)
_STOP_WORDS: frozenset[str] = frozenset(
    "a about above after again against all am an and any are aren't as at be because "
    "been before being below between both but by can't cannot could couldn't did didn't "
    "do does doesn't doing don't down during each few for from further get got had hadn't "
    "has hasn't have haven't having he he'd he'll he's her here here's hers herself him "
    "himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself "
    "let's me more most mustn't my myself no nor not of off on once only or other ought "
    "our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so "
    "some such than that that's the their theirs them themselves then there there's these "
    "they they'd they'll they're they've this those through to too under until up very was "
    "wasn't we we'd we'll we're we've were weren't what what's when when's where where's "
    "which while who who's whom why why's will with won't would wouldn't you you'd you'll "
    "you're you've your yours yourself yourselves also just like even still well back much "
    "many since may might shall yet however already always never often another every one "
    "two new now way use used using make made said say says go went gone come came take "
    "took taken see saw seen know knew known think thought tell told give gave given find "
    "found found work works working worked call called long look looked get got getting "
    "der die das und in von zu den ist ein eine es sich mit auf fuer hat sein ich "
    "nicht er es auch des dem das wie ein eine und der die "
    "le la les de des du un une en et est que qui dans pour ne pas sur ce il "
    "el la los las de del en un una y es que por con no se su al como "
    .split()
)


def _normalise(text: str) -> str:
    """Lower-case, strip diacritics, collapse whitespace."""
    text = text.lower()
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return _WHITESPACE_RE.sub(" ", text).strip()


def _tokenise(text: str) -> list[str]:
    """Return lowercase word tokens, ignoring pure punctuation."""
    return [w for w in _WORD_RE.findall(_normalise(text)) if w]


def _sentences(text: str) -> list[str]:
    """Split *text* into sentences."""
    parts = _SENTENCE_RE.split(text)
    return [s.strip() for s in parts if s.strip() and len(s.strip()) > 2]


# ===========================================================================
# 1. TextStatistics
# ===========================================================================

class TextStatistics:
    """Quantitative and statistical analysis of text.

    Provides readability metrics (Flesch-Kincaid), word-frequency tables,
    TF-IDF across document collections, Shannon entropy, lexical diversity,
    and a simple statistical language detector.
    """

    # Common-word frequency tables for statistical language detection.
    # Each entry is a set of the ~60 most frequent words in the language.
    _LANG_MARKERS: dict[str, set[str]] = {
        "en": {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
            "people", "into", "year", "your", "good", "some", "could", "them", "see",
            "other", "than", "then", "now", "look", "only", "come", "its", "over",
        },
        "fa": {
            "\u0648", "\u062f\u0631", "\u0628\u0647", "\u0627\u0632", "\u06a9\u0647",
            "\u0627\u06cc\u0646", "\u0631\u0627", "\u0628\u0627", "\u0627\u0633\u062a",
            "\u0628\u0631\u0627\u06cc", "\u0622\u0646", "\u06cc\u06a9", "\u0646\u0645\u06cc",
            "\u0647\u0627\u06cc", "\u06a9\u0631\u062f", "\u0628\u0648\u062f", "\u0647\u0645",
            "\u0628\u0631", "\u062e\u06cc\u0644\u06cc", "\u0627\u0648", "\u0645\u0646",
            "\u0646\u0641\u0631", "\u0631\u0648", "\u062a\u0627", "\u0628\u0627\u06cc\u062f",
            "\u0645\u06cc", "\u0634\u062f\u0647", "\u062f\u0627\u0631\u062f",
            "\u0647\u0645\u06cc\u0646", "\u067e\u06cc\u0634", "\u0628\u0639\u062f",
            "\u0634\u062f", "\u0645\u0648\u0631\u062f", "\u06a9\u0646\u0646\u062f",
            "\u0634\u0648\u062f", "\u0627\u0648\u0644", "\u062f\u0648",
            "\u062f\u06cc\u06af\u0631", "\u0628\u06cc", "\u06af\u0641\u062a",
            "\u0622\u0646\u0647\u0627", "\u06a9\u0646\u062f", "\u0628\u06cc\u0634\u062a\u0631",
            "\u062e\u0648\u0628", "\u0628\u0633\u06cc\u0627\u0631", "\u0647\u0645\u0627\u0646",
            "\u0686\u0646\u062f", "\u0648\u0644\u06cc", "\u0647\u0645\u0686\u0646\u06cc\u0646",
        },
        "de": {
            "der", "die", "und", "in", "den", "von", "zu", "das", "mit", "ist",
            "ein", "eine", "es", "sich", "auf", "nicht", "fuer", "wie", "auch", "hat",
            "sein", "ich", "dem", "so", "er", "war", "aus", "als", "nur", "oder",
            "aber", "noch", "sind", "an", "wird", "hier", "bei", "wir", "was",
            "koennen", "ueber", "dann", "dieser", "einem", "einer", "eines", "doch",
            "schon", "wurde", "durch", "nach", "dies", "jeder", "wo", "well", "sie",
            "haben", "wurden", "diese", "ihre", "kann", "dann", "des", "man", "da",
            "wir", "soll", "euch", "ihr", "mich", "mir", "unser", "euch",
        },
        "fr": {
            "de", "la", "le", "les", "des", "et", "en", "un", "une", "est",
            "que", "qui", "dans", "pour", "ne", "pas", "sur", "ce", "il", "son",
            "avec", "plus", "par", "je", "se", "au", "sont", "mais", "comme", "nous",
            "tout", "ont", "ou", "ete", "aux", "peut", "aussi", "ses", "leurs", "cette",
            "fait", "si", "bien", "elle", "lui", "ou", "meme", "encore", "deux",
            "autres", "tres", "entre", "nous", "apres", "premiere", "temps", "homme",
            "peu", "annees", "pays", "jours", "vie", "grand", "hommes", "monde",
            "contre", "donc", "doit", "rien", "ces", "tout", "sans", "sous",
        },
        "es": {
            "de", "la", "el", "en", "y", "a", "los", "del", "se", "las",
            "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
            "mas", "pero", "sus", "le", "ya", "o", "este", "si", "porque", "esta",
            "entre", "cuando", "muy", "sin", "sobre", "tambien", "me", "hasta", "hay",
            "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les",
            "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto",
            "mi", "antes", "algunos", "que", "unos", "yo", "otro", "otras", "otra",
            "el", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos",
        },
        "ar": {
            "\u0641\u064a", "\u0645\u0646", "\u0639\u0644\u0649", "\u0625\u0644\u0649",
            "\u0639\u0646", "\u0645\u0639", "\u0647\u0630\u0627", "\u0627\u0644\u062a\u064a",
            "\u0623\u0646", "\u0644\u0645", "\u0647\u0648", "\u0643\u0627\u0646",
            "\u0647\u0630\u0647", "\u0642\u062f", "\u0644\u0627", "\u0628\u064a\u0646",
            "\u0643\u0644", "\u0628\u0639\u062f", "\u0639\u0646\u062f",
            "\u0630\u0644\u0643", "\u0628\u0647\u0627", "\u0623\u0646\u0647",
            "\u0625\u0644\u064a\u0647", "\u0644\u0642\u062f", "\u0625\u0630\u0627",
            "\u0644\u064a\u0633", "\u062d\u062a\u0649", "\u0645\u0627",
            "\u0647\u0644", "\u0623\u0648", "\u0644\u0643\u0646",
            "\u0648\u0642\u062f", "\u0643\u0630\u0644\u0643", "\u0623\u0645\u0627",
            "\u062b\u0645", "\u0646\u062d\u0646", "\u0647\u0645",
            "\u0623\u0648\u0644\u0626\u0643", "\u0641\u064a\u0647\u0627",
            "\u0645\u0646\u0647", "\u0647\u0646\u0627", "\u0645\u0646\u0630",
            "\u062d\u0648\u0644", "\u062e\u0644\u0627\u0644",
            "\u0639\u0644\u064a\u0647", "\u0648\u0647\u0648", "\u0648\u0647\u064a",
            "\u0641\u0625\u0646", "\u0648\u0644\u0627", "\u0643\u0627\u0646\u062a",
            "\u0644\u0623\u0646", "\u0648\u0644\u0643\u0646", "\u0648\u0623\u0646",
            "\u0643\u0645\u0627", "\u0625\u0644\u0627", "\u0625\u0644\u064a\u0647\u0627",
            "\u0642\u0628\u0644", "\u0623\u064a", "\u0628\u0647", "\u0644\u0647\u0627",
            "\u0648\u0641\u064a", "\u0630\u0627\u062a", "\u062d\u064a\u062b",
            "\u064a\u0645\u0643\u0646", "\u0648\u0630\u0644\u0643",
            "\u0645\u0646\u0647\u0645", "\u0643\u0627\u0646\u0648\u0627",
            "\u0628\u0647\u0630\u0647", "\u062a\u0644\u0643",
        },
        "zh": {
            "\u7684", "\u4e86", "\u5728", "\u662f", "\u6211", "\u6709", "\u548c",
            "\u5c31", "\u4e0d", "\u4eba", "\u90fd", "\u4e00", "\u4e00\u4e2a", "\u4e0a",
            "\u4e5f", "\u5f88", "\u5230", "\u8bf4", "\u8981", "\u53bb",
            "\u4f60", "\u4f1a", "\u7740", "\u6ca1\u6709", "\u770b", "\u597d",
            "\u81ea\u5df1", "\u8fd9", "\u4ed6", "\u5979", "\u5b83", "\u4eec",
            "\u90a3", "\u91cc", "\u4ec0\u4e48", "\u5417", "\u5427", "\u5462",
            "\u554a", "\u54e6", "\u54c8", "\u55ef", "\u5440", "\u628a",
            "\u88ab", "\u8ba9", "\u7ed9", "\u5bf9", "\u4ece", "\u800c",
            "\u8fc7", "\u8fd8", "\u53c8", "\u53ea", "\u5df2", "\u6765",
            "\u5f97", "\u5730", "\u80fd", "\u4e3a", "\u6240", "\u4ee5",
            "\u4e4b", "\u7b49", "\u4e2d", "\u5927", "\u4e2a", "\u4e0b",
            "\u591a", "\u5c0f",
        },
        "ru": {
            "\u0438", "\u0432", "\u043d\u0435", "\u043d\u0430", "\u044f",
            "\u0441", "\u0447\u0442\u043e", "\u043f\u043e", "\u044d\u0442\u043e", "\u043e\u043d",
            "\u043a\u0430\u043a", "\u0430", "\u0442\u043e", "\u0432\u0441\u0435",
            "\u043e\u043d\u0430", "\u0442\u0430\u043a", "\u0435\u0433\u043e",
            "\u043d\u043e", "\u0434\u0430", "\u0442\u044b", "\u043a", "\u0443",
            "\u0436\u0435", "\u0432\u044b", "\u0437\u0430", "\u0431\u044b",
            "\u0442\u043e\u043b\u044c\u043a\u043e", "\u0435\u0451", "\u043c\u043d\u0435",
            "\u0431\u044b\u043b\u043e", "\u0432\u043e\u0442", "\u043e\u0442",
            "\u043c\u0435\u043d\u044f", "\u0435\u0449\u0451", "\u043d\u0435\u0442",
            "\u043e", "\u0438\u0437", "\u0435\u043c\u0443", "\u0442\u0435\u043f\u0435\u0440\u044c",
            "\u043a\u043e\u0433\u0434\u0430", "\u0434\u0430\u0436\u0435", "\u043d\u0443",
            "\u0432\u0434\u0440\u0443\u0433", "\u043b\u0438", "\u043f\u043e\u0434",
            "\u0436", "\u0442\u043e\u0433\u0434\u0430", "\u043a\u0442\u043e",
            "\u044d\u0442\u043e\u0442", "\u0442\u043e\u0433\u043e",
            "\u043f\u043e\u0442\u043e\u043c\u0443", "\u043a\u0430\u043a\u043e\u0439",
            "\u0441\u043e\u0432\u0441\u0435\u043c", "\u043d\u0438\u043c",
            "\u0437\u0434\u0435\u0441\u044c", "\u044d\u0442\u043e\u043c",
            "\u043e\u0434\u0438\u043d", "\u043f\u043e\u0447\u0442\u0438",
            "\u043c\u043e\u0439", "\u0442\u0435\u043c", "\u0447\u0442\u043e\u0431\u044b",
            "\u043d\u0435\u0435", "\u0441\u0435\u0439\u0447\u0430\u0441",
            "\u0431\u044b\u043b\u0438", "\u043a\u0443\u0434\u0430",
            "\u0437\u0430\u0447\u0435\u043c", "\u0432\u0441\u0435\u0445",
            "\u043d\u0438\u043a\u043e\u0433\u0434\u0430", "\u043c\u043e\u0436\u043d\u043e",
            "\u043f\u0440\u0438", "\u043d\u0430\u043a\u043e\u043d\u0435\u0446",
            "\u0434\u0432\u0430", "\u0441\u0430\u043c", "\u0443\u0436\u0435",
        },
    }

    # ------------------------------------------------------------------
    # Readability
    # ------------------------------------------------------------------

    def compute_readability(self, text: str) -> dict[str, Any]:
        """Compute readability statistics for *text*.

        Returns a dictionary containing:
            flesch_kincaid    -- Flesch-Kincaid Grade Level score
            sentence_count    -- number of sentences
            word_count        -- number of word tokens
            avg_sentence_len  -- mean words per sentence
            avg_word_len      -- mean characters per word
        """
        sentences = _sentences(text)
        words = _tokenise(text)
        n_sents = max(len(sentences), 1)
        n_words = max(len(words), 1)
        avg_sl = n_words / n_sents
        avg_wl = sum(len(w) for w in words) / n_words if words else 0.0

        # Syllable estimation (heuristic for English-like text)
        def _syllables(word: str) -> int:
            w = word.lower()
            if len(w) <= 3:
                return 1
            w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
            w = re.sub(r"^y", "", w)
            count = len(re.findall(r"[aeiouy]{1,2}", w))
            return max(count, 1)

        total_syllables = sum(_syllables(w) for w in words)
        fk = 0.0
        if n_words > 0 and n_sents > 0:
            fk = 0.39 * (n_words / n_sents) + 11.8 * (total_syllables / n_words) - 15.59

        return {
            "flesch_kincaid": round(fk, 2),
            "sentence_count": n_sents,
            "word_count": n_words,
            "avg_sentence_length": round(avg_sl, 2),
            "avg_word_length": round(avg_wl, 2),
        }

    # ------------------------------------------------------------------
    # Word frequency
    # ------------------------------------------------------------------

    def compute_word_frequency(
        self, text: str, top_n: int = 50
    ) -> list[tuple[str, int, float]]:
        """Return the *top_n* most frequent words.

        Each entry is ``(word, raw_count, relative_frequency)`` where
        ``relative_frequency`` is ``count / total_words``.
        Stop-words are **excluded**.
        """
        words = _tokenise(text)
        filtered = [w for w in words if w not in _STOP_WORDS and len(w) > 1]
        total = max(len(filtered), 1)
        counts = Counter(filtered).most_common(top_n)
        return [(w, c, round(c / total, 4)) for w, c in counts]

    # ------------------------------------------------------------------
    # TF-IDF
    # ------------------------------------------------------------------

    def compute_tf_idf(self, documents: list[str]) -> list[dict[str, float]]:
        """Compute a TF-IDF vector for each document in *documents*.

        Returns a list of dictionaries ``{word: tfidf_score, ...}`` sorted
        descending by score (top 100 terms per document).  Stop-words are
        excluded.
        """
        tokenised: list[list[str]] = [
            [w for w in _tokenise(d) if w not in _STOP_WORDS and len(w) > 1]
            for d in documents
        ]
        n_docs = len(documents)
        if n_docs == 0:
            return []

        # Document frequency
        df: Counter[str] = Counter()
        for tokens in tokenised:
            unique = set(tokens)
            for t in unique:
                df[t] += 1

        results: list[dict[str, float]] = []
        for tokens in tokenised:
            tf = Counter(tokens)
            n_words = max(len(tokens), 1)
            vec: dict[str, float] = {}
            for word, count in tf.items():
                term_freq = count / n_words
                idf = math.log((n_docs + 1) / (df[word] + 1)) + 1  # smoothed
                vec[word] = round(term_freq * idf, 6)
            top = sorted(vec.items(), key=lambda x: x[1], reverse=True)[:100]
            results.append(dict(top))
        return results

    # ------------------------------------------------------------------
    # Shannon entropy
    # ------------------------------------------------------------------

    def compute_entropy(self, text: str) -> float:
        """Compute the Shannon entropy (in bits) of the character distribution.

        H = - sum( p(c) * log2(p(c)) )
        """
        counts = Counter(text)
        total = len(text)
        if total == 0:
            return 0.0
        entropy = 0.0
        for c in counts.values():
            p = c / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 4)

    # ------------------------------------------------------------------
    # Lexical diversity
    # ------------------------------------------------------------------

    def compute_lexical_diversity(self, text: str) -> float:
        """Compute the Type-Token Ratio (TTR) for *text*.

        TTR = |unique tokens| / |total tokens|
        """
        words = _tokenise(text)
        if not words:
            return 0.0
        return round(len(set(words)) / len(words), 4)

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def language_detect(self, text: str) -> str:
        """Statistical language detection.

        Compares the overlap of word tokens with per-language marker sets
        and returns the ISO 639-1 code with the highest score.  Falls back
        to ``"unknown"`` when confidence is too low.
        Supported: en, fa, de, fr, es, ar, zh, ru.
        """
        words = set(_normalise(text).split())
        best_lang = "unknown"
        best_score = 0
        for lang, markers in self._LANG_MARKERS.items():
            score = len(words & markers)
            if score > best_score:
                best_score = score
                best_lang = lang
        # Require at least 3 marker matches for a confident detection
        if best_score < 3:
            return "unknown"
        return best_lang


# ===========================================================================
# 2. KeywordExtractor
# ===========================================================================

class KeywordExtractor:
    """Extract keywords and basic named entities from text.

    Implements TF-IDF scoring, the RAKE algorithm (Rapid Automatic Keyword
    Extraction), and pattern-based named-entity recognition for common
    entity types (emails, URLs, phones, dates, prices, hashtags, mentions).
    """

    # ------------------------------------------------------------------
    # TF-IDF keywords
    # ------------------------------------------------------------------

    def extract_keywords_tfidf(
        self, text: str, top_n: int = 20
    ) -> list[tuple[str, float]]:
        """Extract keywords ranked by TF-IDF from a single document.

        The document is split into pseudo-sentences to simulate a small
        corpus so that IDF has meaning.
        """
        sentences = _sentences(text)
        if not sentences:
            sentences = [text]
        ts = TextStatistics()
        tfidf_matrix = ts.compute_tf_idf(sentences)
        # Aggregate scores across pseudo-documents
        agg: Counter[str] = Counter()
        for vec in tfidf_matrix:
            for word, score in vec.items():
                agg[word] += score
        top = agg.most_common(top_n)
        return [(w, round(s, 4)) for w, s in top]

    # ------------------------------------------------------------------
    # RAKE
    # ------------------------------------------------------------------

    def extract_keywords_rake(
        self, text: str, top_n: int = 20
    ) -> list[tuple[str, float]]:
        """Extract keywords using the RAKE algorithm.

        RAKE builds a co-occurrence graph of candidate keywords and scores
        each candidate using the ratio of *degree* (co-occurrences +
        frequency) to *frequency* (word_freq).  A higher ratio means the
        word co-occurs with many different partners -- a signal of
        keyword-ness.
        """
        # Split text into candidate phrases (content words only)
        sentences = _sentences(text)
        phrase_list: list[str] = []
        for sent in sentences:
            words = _tokenise(sent)
            # Build phrases: sequences of non-stop-words
            phrase: list[str] = []
            for w in words:
                if w not in _STOP_WORDS:
                    phrase.append(w)
                else:
                    if phrase:
                        phrase_list.append(" ".join(phrase))
                        phrase = []
            if phrase:
                phrase_list.append(" ".join(phrase))

        if not phrase_list:
            return []

        # Word frequency
        word_freq: Counter[str] = Counter()
        for ph in phrase_list:
            for w in ph.split():
                word_freq[w] += 1

        # Word degree (number of co-occurrence edges)
        word_degree: Counter[str] = Counter()
        for ph in phrase_list:
            words_in_phrase = ph.split()
            degree = len(words_in_phrase) - 1  # edges in complete graph
            for w in words_in_phrase:
                word_degree[w] += degree

        # Score each word: (degree + freq) / freq
        word_score: dict[str, float] = {}
        for w in word_freq:
            deg = word_degree[w] + word_freq[w]
            word_score[w] = deg / word_freq[w]

        # Score each phrase as the sum of member word scores
        phrase_scores: list[tuple[str, float]] = []
        for ph in phrase_list:
            score = sum(word_score.get(w, 0) for w in ph.split())
            phrase_scores.append((ph, score))

        # Deduplicate and sort
        seen: set[str] = set()
        unique: list[tuple[str, float]] = []
        for ph, sc in sorted(phrase_scores, key=lambda x: x[1], reverse=True):
            key = " ".join(sorted(ph.split()))
            if key not in seen:
                seen.add(key)
                unique.append((ph, round(sc, 4)))
        return unique[:top_n]

    # ------------------------------------------------------------------
    # Basic named entities
    # ------------------------------------------------------------------

    def extract_named_entities_basic(self, text: str) -> list[tuple[str, str]]:
        """Extract basic named entities using regex patterns.

        Recognised entity types:
            EMAIL   -- e-mail addresses
            URL     -- HTTP(S)/FTP URLs
            PHONE   -- phone numbers (various formats)
            DATE    -- common date patterns
            PRICE   -- monetary amounts ($/EUR/GBP + digits)
            HASHTAG -- #hashtags
            MENTION -- @mentions
        """
        patterns: list[tuple[str, re.Pattern[str]]] = [
            (
                "EMAIL",
                re.compile(
                    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
                    re.UNICODE,
                ),
            ),
            (
                "URL",
                re.compile(
                    r"https?://[^\s<>\"']+|ftp://[^\s<>\"']+"
                ),
            ),
            (
                "PHONE",
                re.compile(
                    r"(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?"
                    r"\d{3,4}[\s\-.]?\d{3,4}"
                ),
            ),
            (
                "DATE",
                re.compile(
                    r"\d{1,4}[\s/\-]\d{1,2}[\s/\-]\d{1,4}|"
                    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                    r"[a-z]*[\s.]\d{1,2}[\s,]\d{2,4}",
                    re.IGNORECASE,
                ),
            ),
            (
                "PRICE",
                re.compile(
                    r"[$\u20ac\u00a3]\s?\d+(?:[.,]\d{1,2})?"
                    r"(?:\s?(?:million|billion|k|m|b))?",
                    re.IGNORECASE,
                ),
            ),
            ("HASHTAG", re.compile(r"#\w+")),
            ("MENTION", re.compile(r"@\w+")),
        ]
        entities: list[tuple[str, str]] = []
        seen_spans: list[tuple[int, int]] = []
        for etype, pat in patterns:
            for m in pat.finditer(text):
                span = m.span()
                # avoid overlapping matches
                if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
                    continue
                seen_spans.append(span)
                entities.append((m.group(), etype))
        return entities


# ===========================================================================
# 3. SentimentAnalyzer
# ===========================================================================

class SentimentAnalyzer:
    """Lexicon-based sentiment analysis (no ML models).

    Uses a built-in sentiment lexicon of ~200 words with polarity scores
    in [-1, 1].  Supports basic negation handling (e.g. "not good" leads
    to negative) and batch processing.
    """

    _LEXICON: dict[str, float] = {
        # ---- Positive words (score > 0) ----
        "good": 0.7, "great": 0.9, "excellent": 1.0, "amazing": 0.95,
        "wonderful": 0.95, "fantastic": 0.9, "outstanding": 0.95,
        "superb": 0.95, "brilliant": 0.9, "perfect": 1.0,
        "love": 0.9, "loved": 0.9, "loves": 0.9, "loving": 0.85,
        "happy": 0.8, "glad": 0.7, "joyful": 0.9, "pleased": 0.7,
        "beautiful": 0.85, "gorgeous": 0.9, "stunning": 0.9,
        "impressive": 0.8, "remarkable": 0.85, "exceptional": 0.9,
        "delightful": 0.85, "charming": 0.8, "elegant": 0.8,
        "satisfied": 0.7, "recommend": 0.7, "recommended": 0.7,
        "best": 0.9, "better": 0.6, "helpful": 0.7, "useful": 0.6,
        "reliable": 0.7, "efficient": 0.7, "fast": 0.5, "easy": 0.5,
        "enjoy": 0.8, "enjoyed": 0.8, "enjoys": 0.8, "enjoyable": 0.8,
        "positive": 0.7, "success": 0.8, "successful": 0.8,
        "win": 0.7, "winning": 0.7, "winner": 0.7,
        "innovative": 0.7, "creative": 0.7, "exciting": 0.8,
        "awesome": 0.9, "cool": 0.6, "nice": 0.6, "fine": 0.4,
        "solid": 0.6, "smooth": 0.5, "clean": 0.5, "clear": 0.4,
        "bright": 0.5, "warm": 0.5, "fresh": 0.6, "fun": 0.7,
        "paradise": 0.9, "gem": 0.7, "treasure": 0.7, "praise": 0.7,
        "thank": 0.6, "thanks": 0.6, "appreciate": 0.7, "worth": 0.6,
        "valuable": 0.7, "quality": 0.6, "top": 0.6, "pro": 0.5,
        "advantage": 0.6, "benefit": 0.6, "gain": 0.5, "profit": 0.5,
        "improve": 0.6, "improved": 0.6, "improvement": 0.6,
        "growth": 0.5, "progress": 0.6, "achievement": 0.7,
        "celebrate": 0.7, "triumph": 0.8, "victory": 0.8,
        "brave": 0.6, "courage": 0.7, "hope": 0.6, "hopeful": 0.6,
        "kind": 0.6, "generous": 0.7, "honest": 0.6, "fair": 0.5,
        "peaceful": 0.6, "calm": 0.4, "safe": 0.5, "secure": 0.6,
        "comfortable": 0.5, "convenient": 0.5, "affordable": 0.5,
        "friendly": 0.7, "polite": 0.5, "welcome": 0.6, "ideal": 0.7,
        "incredible": 0.9, "magnificent": 0.9, "marvelous": 0.9,
        "splendid": 0.85, "terrific": 0.85, "phenomenal": 0.95,
        "extraordinary": 0.9, "glorious": 0.85, "divine": 0.9,
        "blissful": 0.85, "radiant": 0.7, "vibrant": 0.7,
        "enthusiastic": 0.7, "passionate": 0.7, "inspired": 0.7,
        "confident": 0.6, "proud": 0.7, "grateful": 0.7,
        "blessed": 0.8, "fortunate": 0.7, "lucky": 0.6,
        # ---- Negative words (score < 0) ----
        "bad": -0.7, "terrible": -0.9, "horrible": -0.9, "awful": -0.9,
        "poor": -0.7, "worst": -1.0, "worse": -0.7, "hate": -0.9,
        "hated": -0.9, "hates": -0.9, "disgusting": -0.9,
        "ugly": -0.7, "boring": -0.6, "bored": -0.6, "dull": -0.5,
        "annoying": -0.7, "annoyed": -0.7, "frustrating": -0.7,
        "frustrated": -0.7, "disappointing": -0.8, "disappointed": -0.8,
        "disappointment": -0.8, "failure": -0.7, "fail": -0.7,
        "failed": -0.7, "wrong": -0.6, "error": -0.6, "bug": -0.5,
        "broken": -0.7, "damage": -0.7, "damaged": -0.7,
        "useless": -0.8, "worthless": -0.8, "garbage": -0.9,
        "waste": -0.7, "wasted": -0.7, "crap": -0.9, "junk": -0.7,
        "slow": -0.4, "expensive": -0.5, "overpriced": -0.7,
        "cheap": -0.4, "flimsy": -0.6, "weak": -0.5,
        "difficult": -0.4, "hard": -0.3, "complex": -0.3,
        "confusing": -0.6, "confused": -0.5, "unclear": -0.5,
        "messy": -0.5, "dirty": -0.6, "noisy": -0.4,
        "rude": -0.7, "unhelpful": -0.7, "unfriendly": -0.7,
        "unreliable": -0.8, "inefficient": -0.6, "problem": -0.5,
        "problems": -0.5, "issue": -0.4, "issues": -0.4,
        "complaint": -0.7, "complain": -0.6, "complained": -0.6,
        "regret": -0.7, "regretted": -0.7, "unfortunately": -0.6,
        "sad": -0.7, "unhappy": -0.7, "angry": -0.8, "anger": -0.7,
        "fear": -0.7, "scared": -0.6, "painful": -0.7, "suffer": -0.7,
        "loss": -0.6, "lose": -0.6, "lost": -0.6, "decline": -0.5,
        "crash": -0.7, "crashed": -0.7, "danger": -0.7, "dangerous": -0.8,
        "toxic": -0.8, "corrupt": -0.8, "fraud": -0.9, "scam": -0.9,
        "fake": -0.8, "lie": -0.7, "lies": -0.7, "liar": -0.8,
        "cheat": -0.8, "destroy": -0.8, "destroyed": -0.8,
        "kill": -0.8, "died": -0.7, "death": -0.7, "dead": -0.6,
        "sick": -0.6, "illness": -0.6, "disease": -0.7,
        "poverty": -0.7, "crisis": -0.6, "disaster": -0.8,
        "tragedy": -0.8, "catastrophe": -0.9, "horror": -0.8,
        "dreadful": -0.8, "pathetic": -0.8, "miserable": -0.8,
        "depressing": -0.8, "depressed": -0.7, "anxiety": -0.7,
        "stressful": -0.6, "stress": -0.5, "worry": -0.5,
        "worried": -0.5, "horrendous": -0.9, "abysmal": -0.9,
        "atrocious": -0.9, "lousy": -0.7, "mediocre": -0.4,
        "subpar": -0.5, "inferior": -0.6, "negative": -0.5,
        "unfair": -0.6, "uncomfortable": -0.5, "unpleasant": -0.6,
        "unacceptable": -0.7, "ridiculous": -0.6, "absurd": -0.6,
        "offensive": -0.7, "insulting": -0.7, "disrespectful": -0.7,
        "hostile": -0.7, "aggressive": -0.5,
    }

    _NEGATION_WORDS: frozenset[str] = frozenset(
        "not no never neither nor nothing nobody nowhere hardly barely scarcely "
        "doesn't didn't wasn't weren't isn't aren't couldn't wouldn't shouldn't "
        "won't can't don't ain't haven't hadn't without n't".split()
    )

    # ------------------------------------------------------------------
    # Single-text analysis
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict[str, Any]:
        """Analyse the sentiment of *text*.

        Returns:
            polarity_score  -- float in [-1, 1]  (negative to positive)
            subjectivity    -- float in [0, 1]   (objective to subjective)
            label           -- "positive" | "negative" | "neutral"
        """
        words = _tokenise(text)
        n_words = max(len(words), 1)
        polarity_sum = 0.0
        sentiment_word_count = 0
        i = 0
        while i < len(words):
            word = words[i]
            if word in self._LEXICON:
                score = self._LEXICON[word]
                # Check for preceding negation within a 3-word window
                negated = False
                for j in range(max(0, i - 3), i):
                    if words[j] in self._NEGATION_WORDS:
                        negated = True
                        break
                if negated:
                    score = -score * 0.75  # dampen flip
                polarity_sum += score
                sentiment_word_count += 1
            i += 1

        polarity = polarity_sum / n_words
        # Clamp to [-1, 1]
        polarity = max(-1.0, min(1.0, polarity))

        # Subjectivity: fraction of sentiment-bearing words (scaled)
        subjectivity = min(sentiment_word_count / n_words * 3.0, 1.0)

        if polarity > 0.05:
            label = "positive"
        elif polarity < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "polarity_score": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
        }

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------

    def analyze_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Analyse sentiment for multiple texts.

        Returns a list of result dictionaries, one per input text.
        """
        return [self.analyze(t) for t in texts]


# ===========================================================================
# 4. ContentFingerprinter
# ===========================================================================

class ContentFingerprinter:
    """Content deduplication via SimHash fingerprints.

    Generates a fixed-length bit-vector fingerprint for any text and uses
    Hamming distance to estimate similarity.  Suitable for near-duplicate
    detection in large-scale scraping pipelines.
    """

    _FP_BITS: int = 64  # fingerprint size in bits

    # ------------------------------------------------------------------
    # Fingerprint generation
    # ------------------------------------------------------------------

    def fingerprint(self, text: str, ngram_size: int = 3) -> str:
        """Generate a SimHash fingerprint for *text*.

        The fingerprint is a hexadecimal string representing a
        ``_FP_BITS``-bit vector.  *ngram_size* controls the character
        n-gram window used during hashing.
        """
        text = _normalise(text)
        if not text:
            return "0" * (self._FP_BITS // 4)

        ngrams = [text[i : i + ngram_size] for i in range(len(text) - ngram_size + 1)]
        if not ngrams:
            return "0" * (self._FP_BITS // 4)

        # Initialise bit counts
        v = np.zeros(self._FP_BITS, dtype=np.int32)

        for ng in ngrams:
            h = hashlib.md5(ng.encode("utf-8")).digest()
            # Take enough bytes to cover _FP_BITS
            byte_len = (self._FP_BITS + 7) // 8
            int_hash = int.from_bytes(h[:byte_len], "little")
            for bit in range(self._FP_BITS):
                if int_hash & (1 << bit):
                    v[bit] += 1
                else:
                    v[bit] -= 1

        # SimHash: positive -> 1, negative -> 0
        fp_int = 0
        for bit in range(self._FP_BITS):
            if v[bit] >= 0:
                fp_int |= 1 << bit

        return format(fp_int, f"0{self._FP_BITS // 4}x")

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------

    def similarity(self, fp1: str, fp2: str) -> float:
        """Compute similarity between two fingerprints using normalised Hamming distance.

        ``similarity = 1 - hamming_distance / bit_count``
        """
        if len(fp1) != len(fp2):
            return 0.0
        try:
            i1 = int(fp1, 16)
            i2 = int(fp2, 16)
        except ValueError:
            return 0.0
        xor = i1 ^ i2
        hamming = bin(xor).count("1")
        return round(1.0 - hamming / self._FP_BITS, 4)

    # ------------------------------------------------------------------
    # Duplicate check
    # ------------------------------------------------------------------

    def is_duplicate(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """Return ``True`` if *text1* and *text2* are near-duplicates.

        Uses SimHash similarity with the given *threshold*.
        """
        fp1 = self.fingerprint(text1)
        fp2 = self.fingerprint(text2)
        return self.similarity(fp1, fp2) >= threshold

    # ------------------------------------------------------------------
    # Batch duplicate detection
    # ------------------------------------------------------------------

    def find_duplicates(
        self, texts: list[str], threshold: float = 0.85
    ) -> list[list[int]]:
        """Find groups of near-duplicate texts.

        Returns a list of groups, where each group is a list of indices
        into *texts* that are near-duplicates of each other.  Uses a
        union-find (disjoint set) structure for O(n) merging.
        """
        n = len(texts)
        if n == 0:
            return []

        # Pre-compute fingerprints
        fps = [self.fingerprint(t) for t in texts]

        # Union-Find
        parent: list[int] = list(range(n))
        rank: list[int] = [0] * n

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1

        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                if self.similarity(fps[i], fps[j]) >= threshold:
                    union(i, j)

        # Collect groups
        groups: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            groups[find(i)].append(i)

        # Only return groups with more than one member
        return [sorted(g) for g in groups.values() if len(g) > 1]


# ===========================================================================
# 5. ContentAnalyzer  (facade)
# ===========================================================================

class ContentAnalyzer:
    """Main facade that combines all content-intelligence components.

    Provides a single entry-point for full text analysis, pairwise
    comparison, batch processing, and extractive summarisation.
    """

    def __init__(self) -> None:
        self.stats = TextStatistics()
        self.keywords = KeywordExtractor()
        self.sentiment = SentimentAnalyzer()
        self.fingerprinter = ContentFingerprinter()

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict[str, Any]:
        """Run all analysis components on *text* and return combined results.

        The returned dictionary contains:
            readability         -- from :meth:`TextStatistics.compute_readability`
            word_frequency      -- top-50 words with counts and frequencies
            entropy             -- Shannon entropy (bits)
            lexical_diversity   -- type-token ratio
            language            -- detected ISO 639-1 code
            keywords_tfidf      -- top-20 TF-IDF keywords
            keywords_rake       -- top-20 RAKE keywords
            named_entities      -- list of (entity, type) tuples
            sentiment           -- polarity, subjectivity, label
            fingerprint         -- SimHash hex string
        """
        return {
            "readability": self.stats.compute_readability(text),
            "word_frequency": self.stats.compute_word_frequency(text),
            "entropy": self.stats.compute_entropy(text),
            "lexical_diversity": self.stats.compute_lexical_diversity(text),
            "language": self.stats.language_detect(text),
            "keywords_tfidf": self.keywords.extract_keywords_tfidf(text),
            "keywords_rake": self.keywords.extract_keywords_rake(text),
            "named_entities": self.keywords.extract_named_entities_basic(text),
            "sentiment": self.sentiment.analyze(text),
            "fingerprint": self.fingerprinter.fingerprint(text),
        }

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def compare(self, text1: str, text2: str) -> dict[str, Any]:
        """Compare two texts and return similarity-related metrics.

        Returns:
            fingerprint_similarity -- SimHash-based similarity [0, 1]
            is_duplicate           -- boolean (threshold 0.85)
            language_match         -- whether detected languages agree
            sentiment_diff         -- absolute difference in polarity
            shared_keywords_rake   -- keywords appearing in both texts
            shared_keywords_tfidf  -- TF-IDF keywords appearing in both texts
        """
        fp1 = self.fingerprinter.fingerprint(text1)
        fp2 = self.fingerprinter.fingerprint(text2)
        fp_sim = self.fingerprinter.similarity(fp1, fp2)

        kw1_rake = set(w for w, _ in self.keywords.extract_keywords_rake(text1))
        kw2_rake = set(w for w, _ in self.keywords.extract_keywords_rake(text2))
        kw1_tfidf = set(w for w, _ in self.keywords.extract_keywords_tfidf(text1))
        kw2_tfidf = set(w for w, _ in self.keywords.extract_keywords_tfidf(text2))

        s1 = self.sentiment.analyze(text1)["polarity_score"]
        s2 = self.sentiment.analyze(text2)["polarity_score"]

        lang1 = self.stats.language_detect(text1)
        lang2 = self.stats.language_detect(text2)

        return {
            "fingerprint_similarity": fp_sim,
            "is_duplicate": fp_sim >= 0.85,
            "language_match": lang1 == lang2,
            "sentiment_diff": round(abs(s1 - s2), 4),
            "shared_keywords_rake": sorted(kw1_rake & kw2_rake),
            "shared_keywords_tfidf": sorted(kw1_tfidf & kw2_tfidf),
        }

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------

    def analyze_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Analyse a list of texts individually.

        Returns a list of analysis dictionaries, one per text.
        """
        return [self.analyze(t) for t in texts]

    # ------------------------------------------------------------------
    # Extractive summarisation
    # ------------------------------------------------------------------

    def generate_summary(self, text: str, max_sentences: int = 5) -> str:
        """Generate an extractive summary of *text*.

        Sentences are scored using a combination of:
          1. **Word frequency** -- sentences containing more frequent
             (non-stop) words score higher.
          2. **Position bias** -- earlier sentences receive a small bonus.
          3. **Length normalisation** -- very short sentences are penalised.

        The top *max_sentences* are returned in their original order.
        """
        sents = _sentences(text)
        if not sents:
            return ""
        if len(sents) <= max_sentences:
            return " ".join(sents)

        # Build word frequency table
        word_freq: Counter[str] = Counter(
            w for w in _tokenise(text) if w not in _STOP_WORDS and len(w) > 1
        )
        max_freq = max(word_freq.values()) if word_freq else 1
        n_sents = len(sents)

        scores: list[tuple[int, float]] = []
        for idx, sent in enumerate(sents):
            words = _tokenise(sent)
            if not words:
                scores.append((idx, 0.0))
                continue

            # Frequency score
            freq_score = sum(word_freq.get(w, 0) for w in words) / len(words)
            freq_score /= max_freq  # normalise to [0, 1]

            # Position score: linear decay -- first sentence gets 1.0, last gets ~0
            pos_score = 1.0 - idx / n_sents

            # Length penalty: prefer sentences between 5 and 40 words
            n_w = len(words)
            if n_w < 5:
                length_score = n_w / 5.0
            elif n_w > 40:
                length_score = 40.0 / n_w
            else:
                length_score = 1.0

            combined = 0.5 * freq_score + 0.25 * pos_score + 0.25 * length_score
            scores.append((idx, combined))

        # Select top sentences and return in original order
        top_indices = sorted(
            [idx for idx, _ in sorted(scores, key=lambda x: x[1], reverse=True)[
                :max_sentences
            ]]
        )
        return " ".join(sents[i] for i in top_indices)
