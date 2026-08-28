#!/usr/bin/env python3
"""
Consistency Checker for Storyboard Manager

This script analyzes markdown files in a storyboard project to detect inconsistencies
in character details, plot elements, and world-building across the story.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class ConsistencyIssue:
    """Represents a consistency issue found in the story"""

    def __init__(self, issue_type: str, severity: str, description: str,
                 locations: List[str], details: Dict = None):
        self.issue_type = issue_type  # character, plot, world, timeline
        self.severity = severity  # critical, warning, info
        self.description = description
        self.locations = locations
        self.details = details or {}

    def __repr__(self):
        return f"ConsistencyIssue({self.severity}: {self.description})"

    def to_dict(self):
        return {
            'type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'locations': self.locations,
            'details': self.details
        }


class CharacterProfile:
    """Stores character information from profile files"""

    def __init__(self, name: str, file_path: str):
        self.name = name
        self.file_path = file_path
        self.attributes = {}
        self.aliases = []
        self.relationships = {}

    def add_attribute(self, key: str, value: str):
        """Add a character attribute"""
        self.attributes[key.lower()] = value

    def get_attribute(self, key: str) -> Optional[str]:
        """Get a character attribute"""
        return self.attributes.get(key.lower())


class ConsistencyChecker:
    """Main consistency checking class"""

    # Patterns to extract character attributes
    ATTRIBUTE_PATTERNS = {
        'age': r'\*\*Age:\*\*\s*(.+?)(?:\n|$)',
        'appearance': r'\*\*Appearance:\*\*\s*(.+?)(?:\n|$)',
        'hair': r'(?:hair|Hair)[\s:]+([^,\n]+)',
        'eyes': r'(?:eyes|Eyes)[\s:]+([^,\n]+)',
        'height': r'\*\*Height:\*\*\s*(.+?)(?:\n|$)',
        'role': r'\*\*Role:\*\*\s*(.+?)(?:\n|$)',
    }

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.characters: Dict[str, CharacterProfile] = {}
        self.issues: List[ConsistencyIssue] = []
        self.world_facts: Dict[str, Tuple[str, str]] = {}  # fact -> (value, location)

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

    def load_character_profile(self, file_path: Path) -> Optional[CharacterProfile]:
        """Load character information from a profile file"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract character name from title
            name_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
            if not name_match:
                return None

            name = name_match.group(1).strip()
            profile = CharacterProfile(name, str(file_path.relative_to(self.project_root)))

            # Extract attributes
            for attr_name, pattern in self.ATTRIBUTE_PATTERNS.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    profile.add_attribute(attr_name, match.group(1).strip())

            # Extract aliases/nicknames
            alias_match = re.search(
                r'\*\*(?:Nicknames?|Aliases?):\*\*\s*(.+?)(?:\n|$)',
                content, re.IGNORECASE
            )
            if alias_match:
                aliases = re.split(r'[,;]', alias_match.group(1))
                profile.aliases = [a.strip() for a in aliases if a.strip()]

            return profile

        except Exception as e:
            print(f"Warning: Could not read character profile {file_path}: {e}",
                  file=sys.stderr)
            return None

    def load_all_characters(self):
        """Load all character profiles from the project"""
        char_dirs = ['characters', 'Characters', 'cast', 'Cast']

        for dirname in char_dirs:
            char_dir = self.project_root / dirname
            if char_dir.exists():
                for char_file in self.scan_directory(char_dir):
                    profile = self.load_character_profile(char_file)
                    if profile:
                        self.characters[profile.name] = profile

    def check_character_mentions(self, file_path: Path):
        """Check character mentions in content for inconsistencies"""
        try:
            content = file_path.read_text(encoding='utf-8')
            location = str(file_path.relative_to(self.project_root))

            for char_name, profile in self.characters.items():
                # Check if character is mentioned
                if not re.search(r'\b' + re.escape(char_name) + r'\b', content, re.IGNORECASE):
                    continue

                # Check for attribute contradictions
                for attr_name, attr_value in profile.attributes.items():
                    # Look for contradicting descriptions
                    if attr_name == 'age':
                        age_mentions = re.finditer(
                            r'\b' + re.escape(char_name) + r'\b[^.!?]*\b(\d+)[\s-](?:year|yr)',
                            content, re.IGNORECASE
                        )
                        for match in age_mentions:
                            mentioned_age = match.group(1)
                            profile_age = re.search(r'\d+', attr_value)
                            if profile_age and mentioned_age != profile_age.group(0):
                                self.issues.append(ConsistencyIssue(
                                    issue_type='character',
                                    severity='warning',
                                    description=f"Age inconsistency for {char_name}",
                                    locations=[location, profile.file_path],
                                    details={
                                        'character': char_name,
                                        'profile_age': attr_value,
                                        'mentioned_age': mentioned_age
                                    }
                                ))

                    elif attr_name in ['hair', 'eyes']:
                        # Check for contradicting physical descriptions
                        desc_pattern = rf'\b{re.escape(char_name)}\b[^.!?]*\b({attr_name})\b[^.!?]*'
                        desc_mentions = re.finditer(desc_pattern, content, re.IGNORECASE)
                        for match in desc_mentions:
                            context = match.group(0).lower()
                            # Simple check: if profile says "black hair" but text says "blonde"
                            profile_value_lower = attr_value.lower()
                            if profile_value_lower not in context:
                                # Extract the contradicting description
                                color_pattern = r'\b(black|brown|blonde|red|auburn|white|gray|grey|blue|green|hazel)\b'
                                colors = re.findall(color_pattern, context, re.IGNORECASE)
                                if colors:
                                    self.issues.append(ConsistencyIssue(
                                        issue_type='character',
                                        severity='warning',
                                        description=f"{attr_name.capitalize()} color inconsistency for {char_name}",
                                        locations=[location, profile.file_path],
                                        details={
                                            'character': char_name,
                                            'profile': attr_value,
                                            'context': match.group(0)[:100]
                                        }
                                    ))

        except Exception as e:
            print(f"Warning: Error checking {file_path}: {e}", file=sys.stderr)

    def check_character_relationships(self):
        """Check for inconsistent character relationships"""
        # This is a placeholder for more sophisticated relationship checking
        # Would analyze relationship declarations in character files and compare
        # with how relationships are portrayed in chapters

        relationship_keywords = ['friend', 'enemy', 'lover', 'sibling', 'parent', 'child']

        for char_name, profile in self.characters.items():
            # Extract relationship info from profile
            # Compare with relationships mentioned in story files
            # Flag inconsistencies
            pass

    def check_world_building(self, file_path: Path):
        """Check for world-building inconsistencies"""
        try:
            content = file_path.read_text(encoding='utf-8')
            location = str(file_path.relative_to(self.project_root))

            # Look for world-building facts (places, magic systems, technology, etc.)
            # This is a simplified version - would need more sophisticated pattern matching

            # Example: Check for location descriptions
            location_pattern = r'\*\*Location:\*\*\s*(.+?)(?:\n|$)'
            for match in re.finditer(location_pattern, content, re.IGNORECASE):
                loc_name = match.group(1).strip()

                if loc_name in self.world_facts:
                    # Check if description is consistent
                    prev_value, prev_location = self.world_facts[loc_name]
                    # In a real implementation, would do semantic comparison
                else:
                    self.world_facts[loc_name] = (match.group(0), location)

        except Exception as e:
            print(f"Warning: Error checking world-building in {file_path}: {e}",
                  file=sys.stderr)

    def check_plot_consistency(self):
        """Check for plot inconsistencies"""
        # Placeholder for plot consistency checking
        # Would track plot points, events, and check for contradictions

        # Examples to check:
        # - Events happening out of order
        # - Characters appearing after their death
        # - Objects used before acquisition
        # - Locations visited before discovery
        pass

    def check_name_variations(self, file_path: Path):
        """Check for inconsistent name usage"""
        try:
            content = file_path.read_text(encoding='utf-8')
            location = str(file_path.relative_to(self.project_root))

            # Check if character names are spelled consistently
            for char_name, profile in self.characters.items():
                # Look for potential misspellings (Levenshtein distance)
                # This is simplified - would use actual string distance algorithm

                # Check for variations in capitalization
                variations = re.findall(
                    r'\b' + re.escape(char_name) + r'\b',
                    content,
                    re.IGNORECASE
                )

                inconsistent_caps = [v for v in variations if v != char_name]
                if inconsistent_caps:
                    unique_variations = list(set(inconsistent_caps))
                    if len(unique_variations) > 0:
                        self.issues.append(ConsistencyIssue(
                            issue_type='character',
                            severity='info',
                            description=f"Name capitalization variations for {char_name}",
                            locations=[location],
                            details={
                                'character': char_name,
                                'variations': unique_variations
                            }
                        ))

        except Exception as e:
            print(f"Warning: Error checking names in {file_path}: {e}", file=sys.stderr)

    def analyze_project(self) -> Dict:
        """Run all consistency checks on the project"""

        # Load character profiles
        self.load_all_characters()

        # Check all content files
        content_dirs = ['chapters', 'Chapters', 'scenes', 'Scenes', 'story']
        content_files = []

        for dirname in content_dirs:
            content_dir = self.project_root / dirname
            if content_dir.exists():
                content_files.extend(self.scan_directory(content_dir))

        # Run checks on each file
        for content_file in content_files:
            self.check_character_mentions(content_file)
            self.check_world_building(content_file)
            self.check_name_variations(content_file)

        # Run project-wide checks
        self.check_character_relationships()
        self.check_plot_consistency()

        # Organize results
        issues_by_severity = defaultdict(list)
        for issue in self.issues:
            issues_by_severity[issue.severity].append(issue.to_dict())

        analysis = {
            'total_issues': len(self.issues),
            'critical_issues': len(issues_by_severity['critical']),
            'warnings': len(issues_by_severity['warning']),
            'info': len(issues_by_severity['info']),
            'characters_analyzed': len(self.characters),
            'issues_by_severity': dict(issues_by_severity),
            'all_issues': [issue.to_dict() for issue in self.issues]
        }

        return analysis


def main():
    """Main entry point for consistency checker"""

    if len(sys.argv) < 2:
        print("Usage: consistency_checker.py <project_directory> [--output json|markdown]")
        sys.exit(1)

    project_dir = sys.argv[1]
    output_format = 'markdown'

    if len(sys.argv) > 2 and sys.argv[2] == '--output':
        output_format = sys.argv[3] if len(sys.argv) > 3 else 'markdown'

    checker = ConsistencyChecker(project_dir)
    analysis = checker.analyze_project()

    if output_format == 'json':
        print(json.dumps(analysis, indent=2))
    else:
        # Markdown output
        print("# Consistency Analysis\n")
        print(f"**Total Issues Found:** {analysis['total_issues']}")
        print(f"- Critical: {analysis['critical_issues']}")
        print(f"- Warnings: {analysis['warnings']}")
        print(f"- Info: {analysis['info']}\n")
        print(f"**Characters Analyzed:** {analysis['characters_analyzed']}\n")

        if analysis['total_issues'] == 0:
            print("✅ No consistency issues found!\n")
        else:
            # Display issues by severity
            for severity in ['critical', 'warning', 'info']:
                issues = analysis['issues_by_severity'].get(severity, [])
                if issues:
                    severity_emoji = {
                        'critical': '🔴',
                        'warning': '⚠️',
                        'info': 'ℹ️'
                    }
                    print(f"\n## {severity_emoji[severity]} {severity.upper()}\n")

                    for issue in issues:
                        print(f"### {issue['description']}")
                        print(f"**Type:** {issue['type']}")
                        print(f"**Locations:**")
                        for loc in issue['locations']:
                            print(f"- {loc}")

                        if issue['details']:
                            print(f"**Details:**")
                            for key, value in issue['details'].items():
                                print(f"- {key}: {value}")

                        print()


if __name__ == '__main__':
    main()
