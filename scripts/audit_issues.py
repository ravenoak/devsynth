#!/usr/bin/env python3
"""Audit and categorize all issues in the issues/ directory."""

import os
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple

def parse_issue_file(filepath: Path) -> Dict[str, str]:
    """Parse an issue file and extract metadata."""
    try:
        content = filepath.read_text(encoding='utf-8')
        metadata = {}

        # Extract front matter or header metadata
        lines = content.split('\n')
        i = 0

        # Look for metadata patterns
        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()

            # Status patterns
            status_match = re.search(r'(?i)status:\s*(\w+)', line)
            if status_match:
                metadata['status'] = status_match.group(1).lower()

            # Priority patterns
            priority_match = re.search(r'(?i)priority:\s*(\w+)', line)
            if priority_match:
                metadata['priority'] = priority_match.group(1).lower()

            # Affected Area patterns
            area_match = re.search(r'(?i)affected.area:\s*([^\n]+)', line)
            if area_match:
                metadata['affected_area'] = area_match.group(1).strip().lower()

            # Alternative affected area patterns
            area_match2 = re.search(r'(?i)affected.area:\s*(\w+)', line)
            if area_match2 and 'affected_area' not in metadata:
                metadata['affected_area'] = area_match2.group(1).lower()

        # Set defaults if not found
        metadata.setdefault('status', 'unknown')
        metadata.setdefault('priority', 'unknown')
        metadata.setdefault('affected_area', 'unknown')

        # Normalize status values
        if metadata['status'] in ['open', 'active', 'new']:
            metadata['status'] = 'open'
        elif metadata['status'] in ['closed', 'resolved', 'done', 'complete', 'completed']:
            metadata['status'] = 'closed'
        elif metadata['status'] in ['ready', 'pending', 'in_progress', 'progress']:
            metadata['status'] = 'in_progress'

        # Normalize priority values
        if metadata['priority'] in ['critical', 'high', 'urgent']:
            metadata['priority'] = 'high'
        elif metadata['priority'] in ['medium', 'normal', 'moderate']:
            metadata['priority'] = 'medium'
        elif metadata['priority'] in ['low', 'minor', 'trivial']:
            metadata['priority'] = 'low'

        return metadata

    except Exception as e:
        return {
            'status': 'unknown',
            'priority': 'unknown',
            'affected_area': 'unknown',
            'error': str(e)
        }

def main():
    """Main audit function."""
    issues_dir = Path('issues')

    # Categorization counters
    status_counts = Counter()
    priority_counts = Counter()
    area_counts = Counter()
    issues_by_category = defaultdict(list)

    total_issues = 0

    # Walk through all issue files
    for filepath in issues_dir.rglob('*.md'):
        # Skip certain directories and files
        if any(skip in str(filepath) for skip in [
            'issues/archived/',
            'issues/triage/',
            'issues/epics/',
            'issues/README.md',
            'issues/TEMPLATE.md'
        ]):
            continue

        metadata = parse_issue_file(filepath)
        total_issues += 1

        # Update counters
        status_counts[metadata['status']] += 1
        priority_counts[metadata['priority']] += 1
        area_counts[metadata['affected_area']] += 1

        # Group issues by category
        category_key = f"{metadata['status']}_{metadata['priority']}_{metadata['affected_area']}"
        issues_by_category[category_key].append(filepath.name)

    # Print summary
    print("=== ISSUES AUDIT SUMMARY ===")
    print(f"Total Active Issues: {total_issues}")
    print()

    print("=== STATUS BREAKDOWN ===")
    for status, count in sorted(status_counts.items()):
        percentage = (count / total_issues) * 100 if total_issues > 0 else 0
        print(".1f")
    print()

    print("=== PRIORITY BREAKDOWN ===")
    for priority, count in sorted(priority_counts.items()):
        percentage = (count / total_issues) * 100 if total_issues > 0 else 0
        print(".1f")
    print()

    print("=== AFFECTED AREA BREAKDOWN (Top 10) ===")
    for area, count in sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / total_issues) * 100 if total_issues > 0 else 0
        print(".1f")
    print()

    print("=== ISSUES REQUIRING IMMEDIATE ATTENTION ===")

    # High priority open issues
    high_priority_open = []
    for category, issues in issues_by_category.items():
        status, priority, area = category.split('_', 2)
        if status == 'open' and priority in ['high', 'critical']:
            high_priority_open.extend(issues)

    if high_priority_open:
        print(f"High Priority Open Issues ({len(high_priority_open)}):")
        for issue in sorted(high_priority_open)[:20]:  # Show first 20
            print(f"  - {issue}")
        if len(high_priority_open) > 20:
            print(f"  ... and {len(high_priority_open) - 20} more")
    else:
        print("No high priority open issues found.")
    print()

    print("=== ACTION ITEMS ===")
    print("1. Review high priority open issues for immediate remediation")
    print("2. Update status for resolved issues")
    print("3. Categorize unknown status/priority issues")
    print("4. Create issues for newly identified gaps")
    print("5. Archive resolved issues appropriately")

if __name__ == '__main__':
    main()
