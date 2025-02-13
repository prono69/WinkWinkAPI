FROM python:3.9.5-buster

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    git \
    gnupg2 \
    unzip \
    wget \
    xvfb \
    libgconf-2-4 \
    libnss3 \
    libxrender1 \
    libxtst6 \
    libatk1.0-0 \
    libxss1 \
    fonts-liberation \
    libasound2 \
    libvulkan1 \
    xdg-utils \
    ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN mkdir -p /tmp/chrome && cd /tmp/chrome && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i ./google-chrome*.deb || apt-get -y install -f && \
    rm -rf /tmp/chrome

# Install Chromedriver
RUN mkdir -p /tmp/chromedriver && cd /tmp/chromedriver && \
    wget -q https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip && \
    unzip chromedriver.zip -d /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/chromedriver

# Non-root user setup
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    CHROME_DRIVER=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/google-chrome-stable \
    PYTHONUNBUFFERED=1
WORKDIR $HOME/app
USER user

# Python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application code
COPY --chown=user . .

# Verification
RUN google-chrome --version && chromedriver --version

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]