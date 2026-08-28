#!/usr/bin/env python3
"""
Timeline Tracker for Storyboard Manager

This script analyzes markdown files in a storyboard project to extract and organize
timeline events, helping writers maintain chronological consistency.
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class TimelineEvent:
    """Represents a single event in the story timeline"""

    def __init__(self, content: str, location: str, chapter: str = None,
                 timepoint: str = None, characters: List[str] = None):
        self.content = content
        self.location = location  # File path where event was found
        self.chapter = chapter
        self.timepoint = timepoint  # Relative time (e.g., "Day 1", "3 weeks later")
        self.characters = characters or []

    def __repr__(self):
        return f"TimelineEvent({self.timepoint}: {self.content[:50]}...)"


class TimelineTracker:
    """Main timeline tracking and analysis class"""

    # Patterns to detect time markers in text
    TIME_PATTERNS = [
        r'(?:Day|Night)\s+(\d+)',  # Day 1, Night 3
        r'(\d+)\s+(?:days?|weeks?|months?|years?)\s+(?:later|ago|after|before)',
        r'(?:Morning|Afternoon|Evening|Night)\s+of\s+(?:Day\s+)?(\d+)',
        r'Chapter\s+(\d+)',  # Chapter markers
        r'\*\*(?:Timeline|Time|When):\*\*\s*(.+?)(?:\n|$)',  # Explicit timeline markers
        r'\*\*Date:\*\*\s*(.+?)(?:\n|$)',
    ]

    # Patterns to detect character mentions
    CHARACTER_PATTERNS = [
        r'\*\*Characters?:\*\*\s*(.+?)(?:\n|$)',
        r'\*\*(?:POV|Perspective):\*\*\s*(.+?)(?:\n|$)',
    ]

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.events: List[TimelineEvent] = []
        self.characters: set = set()

    def scan_directory(self, directory: Path) -> List[Path]:
        """Recursively find all markdown files in directory"""
        md_files = []
        if not directory.exists():
            return md_files

        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.md':
                md_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                md_files.extend(self.scan_directory(item))

        return md_files

    def extract_characters_from_file(self, file_path: Path) -> List[str]:
        """Extract character names from character profile files"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for character name in title (# Character Name)
            name_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
            if name_match:
                return [name_match.group(1).strip()]

            # Look for explicit name field
            name_match = re.search(r'\*\*Name:\*\*\s*(.+?)(?:\n|$)', content)
            if name_match:
                return [name_match.group(1).strip()]

        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

        return []

    def extract_timeline_markers(self, content: str) -> List[Tuple[str, int]]:
        """Extract time markers from content, return list of (timepoint, position)"""
        markers = []

        for pattern in self.TIME_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                timepoint = match.group(1) if match.lastindex else match.group(0)
                markers.append((timepoint.strip(), match.start()))

        return sorted(markers, key=lambda x: x[1])

    def extract_character_mentions(self, content: str) -> List[str]:
        """Extract character names from explicit character markers"""
        characters = []

        for pattern in self.CHARACTER_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                char_text = match.group(1)
                # Split by commas, 'and', '&'
                names = re.split(r'[,&]|\sand\s', char_text)
                characters.extend([name.strip() for name in names if name.strip()])

        return characters

    def find_character_references(self, content: str, known_characters: set) -> List[str]:
        """Find mentions of known characters in content"""
        found = []
        for character in known_characters:
            # Simple word boundary check
            if re.search(r'\b' + re.escape(character) + r'\b', content, re.IGNORECASE):
                found.append(character)
        return found

    def parse_chapter_file(self, file_path: Path) -> List[TimelineEvent]:
        """Parse a chapter/scene file for timeline events"""
        events = []

        try:
            content = file_path.read_text(encoding='utf-8')

            # Get chapter number/name from filename or title
            chapter = file_path.stem
            title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
            if title_match:
                chapter = title_match.group(1).strip()

            # Extract explicit character mentions
            explicit_chars = self.extract_character_mentions(content)

            # Find timeline markers
            markers = self.extract_timeline_markers(content)

            # Split content into sections based on markers
            if markers:
                sections = []
                for i, (timepoint, pos) in enumerate(markers):
                    start_pos = pos
                    end_pos = markers[i + 1][1] if i + 1 < len(markers) else len(content)
                    section_content = content[start_pos:end_pos]

                    # Find characters in this section
                    section_chars = explicit_chars.copy()
                    section_chars.extend(self.find_character_references(
                        section_content, self.characters))

                    event = TimelineEvent(
                        content=section_content[:500],  # First 500 chars as preview
                        location=str(file_path.relative_to(self.project_root)),
                        chapter=chapter,
                        timepoint=timepoint,
                        characters=list(set(section_chars))
                    )
                    events.append(event)
            else:
                # No explicit markers, treat whole file as one event
                all_chars = explicit_chars.copy()
                all_chars.extend(self.find_character_references(content, self.characters))

                event = TimelineEvent(
                    content=content[:500],
                    location=str(file_path.relative_to(self.project_root)),
                    chapter=chapter,
                    timepoint=None,
                    characters=list(set(all_chars))
                )
                events.append(event)

        except Exception as e:
            print(f"Warning: Error parsing {file_path}: {e}", file=sys.stderr)

        return events

    def analyze_project(self) -> Dict:
        """Analyze entire project and build timeline"""

        # First, find all characters
        char_dirs = ['characters', 'Characters', 'cast']
        for dirname in char_dirs:
            char_dir = self.project_root / dirname
            if char_dir.exists():
                for char_file in self.scan_directory(char_dir):
                    names = self.extract_characters_from_file(char_file)
                    self.characters.update(names)

        # Then scan chapters/scenes
        content_dirs = ['chapters', 'Chapters', 'scenes', 'Scenes', 'story']
        for dirname in content_dirs:
            content_dir = self.project_root / dirname
            if content_dir.exists():
                for content_file in self.scan_directory(content_dir):
                    events = self.parse_chapter_file(content_file)
                    self.events.extend(events)

        # Build analysis
        analysis = {
            'total_events': len(self.events),
            'total_characters': len(self.characters),
            'characters': sorted(list(self.characters)),
            'events_by_timepoint': self._group_events_by_time(),
            'events_by_character': self._group_events_by_character(),
            'events_by_chapter': self._group_events_by_chapter(),
            'timeline': self._build_timeline(),
            'warnings': self._check_consistency()
        }

        return analysis

    def _group_events_by_time(self) -> Dict[str, List[Dict]]:
        """Group events by their timepoint"""
        grouped = defaultdict(list)

        for event in self.events:
            timepoint = event.timepoint or "Unspecified"
            grouped[timepoint].append({
                'location': event.location,
                'chapter': event.chapter,
                'characters': event.characters,
                'preview': event.content[:200]
            })

        return dict(grouped)

    def _group_events_by_character(self) -> Dict[str, List[Dict]]:
        """Group events by character appearance"""
        grouped = defaultdict(list)

        for event in self.events:
            for character in event.characters:
                grouped[character].append({
                    'location': event.location,
                    'chapter': event.chapter,
                    'timepoint': event.timepoint,
                    'preview': event.content[:200]
                })

        return dict(grouped)

    def _group_events_by_chapter(self) -> Dict[str, List[Dict]]:
        """Group events by chapter"""
        grouped = defaultdict(list)

        for event in self.events:
            chapter = event.chapter or "Unknown"
            grouped[chapter].append({
                'location': event.location,
                'timepoint': event.timepoint,
                'characters': event.characters,
                'preview': event.content[:200]
            })

        return dict(grouped)

    def _build_timeline(self) -> List[Dict]:
        """Build chronological timeline of events"""
        # Sort events by timepoint (this is simplified, real implementation
        # would need more sophisticated time parsing)
        timeline = []

        for event in self.events:
            timeline.append({
                'timepoint': event.timepoint or "Unknown",
                'chapter': event.chapter,
                'location': event.location,
                'characters': event.characters,
                'preview': event.content[:200]
            })

        return timeline

    def _check_consistency(self) -> List[str]:
        """Check for potential timeline inconsistencies"""
        warnings = []

        # Check for events without time markers
        unmarked_events = [e for e in self.events if not e.timepoint]
        if unmarked_events:
            warnings.append(
                f"Found {len(unmarked_events)} events without timeline markers"
            )

        # Check for characters appearing in timeline without character files
        mentioned_chars = set()
        for event in self.events:
            mentioned_chars.update(event.characters)

        undefined_chars = mentioned_chars - self.characters
        if undefined_chars:
            warnings.append(
                f"Characters mentioned but not defined: {', '.join(sorted(undefined_chars))}"
            )

        return warnings


def main():
    """Main entry point for timeline tracker"""

    if len(sys.argv) < 2:
        print("Usage: timeline_tracker.py <project_directory> [--output json|markdown]")
        sys.exit(1)

    project_dir = sys.argv[1]
    output_format = 'markdown'

    if len(sys.argv) > 2 and sys.argv[2] == '--output':
        output_format = sys.argv[3] if len(sys.argv) > 3 else 'markdown'

    tracker = TimelineTracker(project_dir)
    analysis = tracker.analyze_project()

    if output_format == 'json':
        print(json.dumps(analysis, indent=2))
    else:
        # Markdown output
        print("# Timeline Analysis\n")
        print(f"**Total Events:** {analysis['total_events']}")
        print(f"**Total Characters:** {analysis['total_characters']}\n")

        print("## Characters")
        for char in analysis['characters']:
            appearances = len(analysis['events_by_character'].get(char, []))
            print(f"- {char} ({appearances} appearances)")

        print("\n## Timeline")
        for event in analysis['timeline']:
            print(f"\n### {event['timepoint']} - {event['chapter']}")
            print(f"**Location:** {event['location']}")
            if event['characters']:
                print(f"**Characters:** {', '.join(event['characters'])}")
            print(f"\n{event['preview']}...\n")
            print("---")

        if analysis['warnings']:
            print("\n## Warnings")
            for warning in analysis['warnings']:
                print(f"- ⚠️  {warning}")


if __name__ == '__main__':
    main()
