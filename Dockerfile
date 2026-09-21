# Resmi, stabil ve hafif Python 3.11 taban imajı
FROM python:3.11-slim

# Ortam değişkenleri (Python bytecode üretmesin, logları anında yazsın)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Konteyner içi çalışma dizini
WORKDIR /app

# Gerekli sistem paketleri (curl sağlık kontrolü için)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje kaynak kodlarını kopyala
COPY . .

# uploads dizinini garanti altına al
RUN mkdir -p uploads

# Port tanımlaması
EXPOSE 5000

# Konteyner sağlık kontrolü (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Uygulamayı başlat
CMD ["python", "app.py"]
