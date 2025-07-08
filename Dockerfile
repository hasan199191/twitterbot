FROM python:3.11-slim

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libasound2 \
    libgbm1 \
    libxshmfence1 \
    libxrandr2 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libdrm2 \
    libxfixes3 \
    libxext6 \
    libx11-6 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    xvfb \
    xauth \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Google Chrome yükle
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Proje dosyalarını kopyala
COPY . .

# Python bağımlılıklarını yükle
RUN pip install --no-cache-dir -r requirements.txt

# Playwright bağımlılıklarını yükle
RUN pip install playwright
RUN playwright install chromium
RUN playwright install-deps

# Ortam değişkenleri
ENV PYTHONUNBUFFERED=1

# Uygulamayı başlat
CMD ["xvfb-run", "-a", "python", "web_main.py"]
