FROM python:3.11-slim

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xauth \
    curl \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Proje dosyalarını kopyala
COPY . .

# Python bağımlılıklarını yükle
RUN pip install --no-cache-dir -r requirements.txt

# Playwright tarayıcılarını yükle
RUN playwright install chromium
RUN playwright install-deps

# Ortam değişkenleri
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Uygulamayı başlat (xvfb-run opsiyonel, gerekirse elle ekle)
CMD ["python", "web_main.py"]
