FROM python:3.9.5-slim-buster

# Install system dependencies
RUN apt -qq update && \
    apt -qq install -y --no-install-recommends \
    curl \
    git \
    gnupg2 \
    unzip \
    wget \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libappindicator3-1 \
    libxrender1 \
    libxtst6 \
    libnss3 \
    libatk1.0-0 \
    libxss1 \
    fonts-liberation \
    libasound2 \
    libgbm-dev \
    libu2f-udev \
    libvulkan1 \
    libgl1-mesa-dri \
    xdg-utils \
    python3-dev \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/

# Install Chrome
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i ./google-chrome-stable_current_amd64.deb || apt-get install -fqqy && \
    rm ./google-chrome-stable_current_amd64.deb

# Install Chromedriver
RUN mkdir -p /tmp/ && \
    cd /tmp/ && \
    wget -O chromedriver.zip https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip && \
    unzip -o chromedriver.zip chromedriver -d /usr/bin/ && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver.zip

# Create user with UID 1000
RUN useradd -m -u 1000 user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    CHROME_DRIVER=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/google-chrome-stable \
    PYTHONUNBUFFERED=1 \
    PIP_CACHE_DIR=/home/user/.cache/pip

# Set working directory
WORKDIR $HOME/app

# Switch to non-root user
USER user

# Create cache directory and set permissions
RUN mkdir -p $HOME/.cache/pip && chmod -R 777 $HOME/.cache

# Copy requirements first to leverage Docker cache
COPY --chown=user requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt  # Removed --no-cache-dir

# Copy application code
COPY --chown=user . .

# Verification commands
RUN google-chrome --version && chromedriver --version

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]