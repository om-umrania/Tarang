#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v node >/dev/null 2>&1; then
    echo 'ERROR: Node.js 22.13+ must be available on PATH to run JavaScript checks and bridge filter tests.' >&2
    exit 1
fi

if ! node -e 'const [major, minor] = process.versions.node.split(".").map(Number); process.exit(major > 22 || (major === 22 && minor >= 13) ? 0 : 1)'; then
    echo 'ERROR: Node.js 22.13+ is required; the Node.js runtime on PATH is unsupported.' >&2
    exit 1
fi

python3 - <<'PY'
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import subprocess
import tempfile

root = Path.cwd()
review = root / 'docs/index.html'
errors = []

def check_link(source, target):
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return
    if not (source.parent / unquote(url.path)).exists():
        errors.append(f'{source.relative_to(root)}: missing local link {target}')

class ReviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.in_script = False
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                errors.append(f'Duplicate HTML id: {attrs["id"]}')
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                check_link(review, attrs[key])
        if tag == 'script':
            self.in_script = True
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
    def handle_data(self, data):
        if self.in_script:
            self.scripts.append(data)

parser = ReviewParser()
parser.feed(review.read_text())
for source in [root / 'README.md', root / 'PLANS.md', *sorted((root / 'docs').glob('*.md')), *sorted((root / 'prompts').glob('*.md'))]:
    for target in re.findall(r'\]\(([^)]+)\)', source.read_text()):
        check_link(source, target)

with tempfile.TemporaryDirectory(prefix='tarang-review-') as temp:
    script = Path(temp) / 'review.js'
    script.write_text('\n'.join(parser.scripts))
    result = subprocess.run(['node', '--check', str(script)], capture_output=True, text=True)
    if result.returncode:
        errors.append(result.stderr)

if errors:
    raise SystemExit('\n'.join(errors))
print('PASS: review JavaScript syntax, unique HTML IDs, and local document links.')
print('Static checks passed. Runtime contract tests follow; live integrations require separate evidence.')
PY

node --test bridge/filter.test.mjs
python3 -m pytest -q
git diff --check
