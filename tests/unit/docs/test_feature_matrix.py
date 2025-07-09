import re
from pathlib import Path
import os
ALLOWED = {'Complete', 'Partial', 'Missing'}


def test_feature_rows_have_status_succeeds():
    """Test that feature rows have status succeeds.

ReqID: N/A"""
    repo_root = Path(os.environ.get('ORIGINAL_CWD', Path.cwd()))
    path = repo_root / 'docs' / 'implementation' / 'feature_status_matrix.md'
    lines = path.read_text().splitlines()
    in_table = False
    for line in lines:
        if line.startswith('| Feature | Status'):
            in_table = True
            continue
        if in_table:
            if line.startswith('## '):
                break
            if not line.startswith('|') or line.startswith('|---------'):
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) < 2:
                continue
            status = cells[1]
            assert status in ALLOWED, f'Row status invalid or missing: {line}'
