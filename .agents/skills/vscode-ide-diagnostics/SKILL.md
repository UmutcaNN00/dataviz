---
name: vscode-ide-diagnostics
description: >-
  VS Code'da Pylance, Pyright veya Ruff hata badge'leri görüldüğünde, IDE
  diagnostik sorunları çözülürken bu skill kullanılır. Hot-exit buffer sorunu
  teşhisi, pyrightconfig yapılandırması ve type-safety çözümlerini içerir.
---

# VS Code IDE Diagnostik Sorunları Çözümü

## Adım 1: Gerçek Hata Durumunu Kontrol Et

IDE badge'lerine güvenmeden önce **disk üzerindeki gerçek durumu** kontrol et:

```bash
cd dataviz
.venv/Scripts/python.exe -m ruff check . --no-cache
```

Eğer `ruff check` 0 hata gösteriyorsa ama IDE hâlâ kırmızı badge gösteriyorsa → **hot-exit buffer sorunu** var demektir.

## Adım 2: Hot-Exit Buffer Sorunu

### Sorun
VS Code'un hot-exit özelliği dosyaları kapatırken disk'e kaydetmeden buffer'da tutar. Bu buffer'lar eski dosya içeriklerini saklar ve Pylance/Ruff bunları gerçek dosya yerine okur.

### Buffer Konumu
```
C:\Users\umutc\AppData\Roaming\Code\Backups\<workspace-id>\file\
```

### Çözüm
1. VS Code'u kapat
2. Buffer dosyalarını temizle:
   ```powershell
   Remove-Item -Recurse -Force "C:\Users\umutc\AppData\Roaming\Code\Backups\*"
   ```
3. VS Code'u yeniden aç
4. `Ctrl+Shift+P` → "Developer: Reload Window"

## Adım 3: Pyright Yapılandırması

### `pyrightconfig.json` (Proje kökünde)
```json
{
  "venvPath": "dataviz",
  "venv": ".venv",
  "pythonVersion": "3.14",
  "typeCheckingMode": "basic",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false
}
```

### `.vscode/settings.json`
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/dataviz/.venv/Scripts/python.exe",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.diagnosticSeverityOverrides": {
    "reportMissingTypeStubs": "none"
  }
}
```

## Adım 4: Yaygın Type-Safety Düzeltmeleri

### Optional Filename Guard
```python
# ❌ Yanlış — Pylance "possibly None" hatası verir
filename = file.filename
ext = filename.rsplit('.', 1)[-1]

# ✅ Doğru — Guard ile
filename = file.filename
if not filename:
    return jsonify({"error": "Dosya adı bulunamadı"}), 400
ext = filename.rsplit('.', 1)[-1]
```

### Optional Import (transformers gibi)
```python
try:
    from transformers import pipeline  # type: ignore[import-untyped]
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
```

## Kontrol Listesi

- [ ] `ruff check` çalıştır → 0 hata mı?
- [ ] IDE badge'leri kırmızı mı → hot-exit buffer temizle
- [ ] `pyrightconfig.json` doğru `venvPath` gösteriyor mu?
- [ ] `.vscode/settings.json` doğru interpreter yolunu gösteriyor mu?
- [ ] Optional değerlerde guard var mı?
