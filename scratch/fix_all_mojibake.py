import re

target_file = 'templates/analysis.html'

with open(target_file, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# Exact replacements for mojibake found in analysis.html
replacements = [
    ('â† ', '← '),
    ('â†\'', '←'),
    ('â†', '←'),
    ('âœ“', '✓'),
    ('â€º', '›'),
    ('â€¢', '•'),
    ('â€"', '—'),
    ('â€•', '—'),
    ('â•', '═'),
    ('âƒ£', '⃣'),
    ('0ï¸ âƒ£', '0️⃣'),
    ('0ï¸ ⃣', '0️⃣'),
    ('ğŸ—‘ï¸ ', '🗑️'),
    ('ğŸ—‘', '🗑️'),
    ('ğŸŽ¨', '🎨'),
    ('âŸ™', '🎨'),
    ('âš™ï¸ ', '⚙️'),
    ('âš™', '⚙️'),
    ('⚙️ï¸ ', '⚙️'),
    ('📈Œ', '📌'),
    ('📈‚', '📁'),
    ('📈„', '📄'),
    ('🧠¹', '🗑️'),
    ('ğŸŽ›ï¸ ', '🎛️'),
    ('ğŸŽ›', '🎛️'),
    ('🔍—', '🔗'),
    ('RÂ²', 'R²'),
    ('Â²', '²'),
    ('Â³', '³'),
    ('Â±', '±'),
    ('Ã·', '÷'),
    ('âœ¨', '✨'),
    ('KÃ¢r', 'Kâr'),
    ('BOÅž DEÄžER', 'BOŞ DEĞER'),
    ('BOÅž', 'BOŞ'),
    ('SÖZEL / ALAKASIZ DEÄžER', 'SÖZEL / ALAKASIZ DEĞER'),
    ('VERİ İÅžLEMLERİ', 'VERİ İŞLEMLERİ'),
    ('SEKME İÇERİÄžİ', 'SEKME İÇERİĞİ'),
    ('İÇERİÄžİ', 'İÇERİĞİ'),
    ('AÅžAMA', 'AŞAMA'),
    ('VERİ SAÄžLIÄžI', 'VERİ SAĞLIĞI'),
    ('SAÄžLIÄžI', 'SAĞLIĞI'),
    ('SAÄž', 'SAĞ'),
    ('AKILLI VERİ BİRLEÅžTİRİCİ', 'AKILLI VERİ BİRLEŞTİRİCİ'),
    ('BİRLEÅžTİRİCİ', 'BİRLEŞTİRİCİ'),
    ('FORMÜL / HESAPLANMIÅž SÜTUN', 'FORMÜL / HESAPLANMIŞ SÜTUN'),
    ('HESAPLANMIÅž', 'HESAPLANMIŞ'),
    ('Åžehir', 'Şehir'),
    ('Åžeridi', 'Şeridi'),
    ('DEÄžER', 'DEĞER'),
    ('SEÇİMİ â•', 'SEÇİMİ ═'),
    ('MODALI â•', 'MODALI ═'),
    ('YÜKLEME â•', 'YÜKLEME ═'),
    ('TEMİZLEME) MODALI â•', 'TEMİZLEME) MODALI ═'),
]

for src, dst in replacements:
    text = text.replace(src, dst)

# Also fix any remaining  characters or weird byte sequences in comments
text = re.sub(r'<!-- [\x90-\x9f═\s]+', '<!-- ══════════ ', text)
text = re.sub(r'[\x90-\x9f═\s]+ -->', ' ══════════ -->', text)

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Fixed {target_file} successfully.")
