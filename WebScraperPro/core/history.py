"""
WebScraper Pro - Scrape History Manager
Records and manages past scraping sessions with full metadata, statistics, and results.
"""

import json
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class HistorySortField(Enum):
    DATE = "date"
    NAME = "name"
    RECORDS = "records"
    DURATION = "duration"
    SUCCESS = "success"


class SortOrder(Enum):
    DESC = "desc"
    ASC = "asc"


@dataclass
class HistoryEntry:
    """A single scraping session record."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = "Untitled Session"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    mode: str = "static"
    urls_count: int = 0
    urls_sample: List[str] = field(default_factory=list)
    records_extracted: int = 0
    errors_count: int = 0
    duration_seconds: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    total_bytes: int = 0
    export_formats_used: List[str] = field(default_factory=list)
    rules_count: int = 0
    rule_names: List[str] = field(default_factory=list)
    success: bool = False
    error_message: str = ""
    # Results stored separately in a JSON sidecar file
    has_results: bool = False
    results_file: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "urls_count": self.urls_count,
            "urls_sample": self.urls_sample[:10],
            "records_extracted": self.records_extracted,
            "errors_count": self.errors_count,
            "duration_seconds": self.duration_seconds,
            "status_codes": self.status_codes,
            "total_bytes": self.total_bytes,
            "export_formats_used": self.export_formats_used,
            "rules_count": self.rules_count,
            "rule_names": self.rule_names,
            "success": self.success,
            "error_message": self.error_message,
            "has_results": self.has_results,
            "results_file": self.results_file,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        d = data.copy()
        return cls(**d)

    @property
    def duration_formatted(self) -> str:
        secs = self.duration_seconds
        if secs < 60:
            return f"{secs:.1f}s"
        elif secs < 3600:
            mins = int(secs // 60)
            secs_r = secs % 60
            return f"{mins}m {secs_r:.0f}s"
        else:
            hours = int(secs // 3600)
            mins = int((secs % 3600) // 60)
            return f"{hours}h {mins}m"

    @property
    def bytes_formatted(self) -> str:
        b = self.total_bytes
        if b < 1024:
            return f"{b} B"
        elif b < 1048576:
            return f"{b / 1024:.1f} KB"
        else:
            return f"{b / 1048576:.1f} MB"

    @property
    def timestamp_short(self) -> str:
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return self.timestamp[:16]


class HistoryManager:
    """
    Manages scrape session history with persistence.
    
    Stores session metadata in a JSON index file and optionally
    saves full results as separate JSON files.
    """

    MAX_ENTRIES = 200
    MAX_RESULTS_FILE_SIZE_MB = 50

    def __init__(self, history_dir: str = "history"):
        self._history_dir = history_dir
        self._results_dir = os.path.join(history_dir, "results")
        self._index_file = os.path.join(history_dir, "index.json")
        self._entries: Dict[str, HistoryEntry] = {}

        os.makedirs(self._results_dir, exist_ok=True)
        self._load_index()

    @property
    def entries(self) -> List[HistoryEntry]:
        return list(self._entries.values())

    @property
    def count(self) -> int:
        return len(self._entries)

    def record_session(self, name: str, mode: str, urls: List[str],
                       records: List[Dict], errors: List[Dict],
                       duration: float, status_codes: Dict[int, int],
                       total_bytes: int, rule_names: List[str],
                       error_message: str = "") -> HistoryEntry:
        """Record a completed scraping session."""
        entry = HistoryEntry(
            name=name,
            mode=mode,
            urls_count=len(urls),
            urls_sample=urls[:10],
            records_extracted=len(records),
            errors_count=len(errors),
            duration_seconds=round(duration, 2),
            status_codes=status_codes,
            total_bytes=total_bytes,
            rules_count=len(rule_names),
            rule_names=rule_names,
            success=len(records) > 0,
            error_message=error_message[:200],
        )

        # Save results to a sidecar file
        if records:
            entry.has_results = True
            entry.results_file = os.path.join(self._results_dir, f"{entry.id}.json")
            try:
                with open(entry.results_file, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False, default=str)
            except Exception:
                entry.has_results = False
                entry.results_file = ""

        self._entries[entry.id] = entry
        self._enforce_limit()
        self._save_index()
        return entry

    def get_entry(self, entry_id: str) -> Optional[HistoryEntry]:
        return self._entries.get(entry_id)

    def get_results(self, entry_id: str) -> Optional[List[Dict]]:
        """Load results for a history entry from its sidecar file."""
        entry = self._entries.get(entry_id)
        if not entry or not entry.has_results or not entry.results_file:
            return None
        if not os.path.exists(entry.results_file):
            entry.has_results = False
            return None
        try:
            with open(entry.results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def delete_entry(self, entry_id: str) -> bool:
        entry = self._entries.pop(entry_id, None)
        if entry:
            # Delete results file
            if entry.results_file and os.path.exists(entry.results_file):
                try:
                    os.remove(entry.results_file)
                except Exception:
                    pass
            self._save_index()
            return True
        return False

    def clear_all(self) -> int:
        """Delete all history entries. Returns count of deleted entries."""
        count = len(self._entries)
        # Delete all result files
        for entry in self._entries.values():
            if entry.results_file and os.path.exists(entry.results_file):
                try:
                    os.remove(entry.results_file)
                except Exception:
                    pass
        self._entries.clear()
        self._save_index()
        return count

    def get_sorted(self, sort_field: HistorySortField = HistorySortField.DATE,
                   order: SortOrder = SortOrder.DESC) -> List[HistoryEntry]:
        """Return entries sorted by the given field."""
        entries = list(self._entries.values())
        reverse = (order == SortOrder.DESC)

        if sort_field == HistorySortField.DATE:
            entries.sort(key=lambda e: e.timestamp, reverse=reverse)
        elif sort_field == HistorySortField.NAME:
            entries.sort(key=lambda e: e.name.lower(), reverse=reverse)
        elif sort_field == HistorySortField.RECORDS:
            entries.sort(key=lambda e: e.records_extracted, reverse=reverse)
        elif sort_field == HistorySortField.DURATION:
            entries.sort(key=lambda e: e.duration_seconds, reverse=reverse)
        elif sort_field == HistorySortField.SUCCESS:
            entries.sort(key=lambda e: (e.success, e.records_extracted), reverse=reverse)

        return entries

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all history entries."""
        entries = list(self._entries.values())
        if not entries:
            return {"total_sessions": 0}

        total_records = sum(e.records_extracted for e in entries)
        total_errors = sum(e.errors_count for e in entries)
        total_duration = sum(e.duration_seconds for e in entries)
        successful = sum(1 for e in entries if e.success)
        total_bytes = sum(e.total_bytes for e in entries)

        return {
            "total_sessions": len(entries),
            "successful_sessions": successful,
            "failed_sessions": len(entries) - successful,
            "total_records": total_records,
            "total_errors": total_errors,
            "total_duration": round(total_duration, 1),
            "avg_records_per_session": round(total_records / len(entries), 1),
            "total_bytes": total_bytes,
            "success_rate": round(successful / len(entries) * 100, 1),
        }

    def search(self, query: str) -> List[HistoryEntry]:
        """Search history entries by name, URL, or mode."""
        if not query:
            return list(self._entries.values())
        q = query.lower()
        results = []
        for entry in self._entries.values():
            if (q in entry.name.lower()
                    or q in entry.mode.lower()
                    or q in entry.error_message.lower()
                    or any(q in url.lower() for url in entry.urls_sample)):
                results.append(entry)
        return results

    def _enforce_limit(self):
        """Remove oldest entries if over the limit."""
        if len(self._entries) <= self.MAX_ENTRIES:
            return
        sorted_entries = sorted(self._entries.values(), key=lambda e: e.timestamp)
        to_remove = sorted_entries[:len(self._entries) - self.MAX_ENTRIES]
        for entry in to_remove:
            if entry.results_file and os.path.exists(entry.results_file):
                try:
                    os.remove(entry.results_file)
                except Exception:
                    pass
            del self._entries[entry.id]

    def _save_index(self):
        try:
            data = {eid: e.to_dict() for eid, e in self._entries.items()}
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_index(self):
        if not os.path.exists(self._index_file):
            return
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for eid, edata in data.items():
                self._entries[eid] = HistoryEntry.from_dict(edata)
        except Exception:
            pass
