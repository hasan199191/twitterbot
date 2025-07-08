FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xauth \
    xvfb \
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

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium
RUN playwright install-deps

ENV PYTHONUNBUFFERED=1
ENV GOOGLE_CHROME_BIN=/usr/bin/google-chrome
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Başlangıç komutu xvfb ile Flask+bot'u başlatır
CMD ["xvfb-run", "-a", "python", "web_main.py"]
