import os
import re

files = []
for root, dirs, fnames in os.walk('.'):
    if any(p in root for p in ['.git', '.venv', '__pycache__', 'node_modules', 'uploads']):
        continue
    for f in fnames:
        if f.endswith(('.html', '.js', '.css', '.py')):
            files.append(os.path.join(root, f))

# Look for typical mojibake sequences
patterns = [
    r'â[€†šŸƒ™]',
    r'ğŸ',
    r'ï¸',
    r'Ã[¼¶§„‡–œ]',
    r'Ä[°Ÿ]',
    r'Å[žŸ]',
    r'â€¢',
    r'â†[\'"]',
    r'CE Panoya',
    r'Â'
]

combined = re.compile('|'.join(patterns))

found = {}
for path in files:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()
        matches = combined.findall(content)
        if matches:
            found[path] = len(matches)
    except Exception as e:
        pass

for p, count in sorted(found.items(), key=lambda x: -x[1]):
    print(f'{p}: {count} occurrences')
