FROM python:3.9-slim-buster

# Install system dependencies as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    unzip \
    libgconf-2-4 \
    libnss3 \
    libgl1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libdrm2 \
    libgbm1 \
    libasound2 && \
    apt-get clean && \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Install matching Chromedriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1) \
    && wget -q https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION} \
    && wget -q https://chromedriver.storage.googleapis.com/$(cat LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/bin/ \
    && rm chromedriver_linux64.zip LATEST_RELEASE_${CHROME_VERSION}

# Create user with UID 1000
RUN useradd -m -u 1000 user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    CHROME_DRIVER=/usr/bin/chromedriver \
    CHROME_BIN=/usr/bin/google-chrome-stable \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR $HOME/app

# Switch to non-root user
USER user

# Copy requirements first to leverage Docker cache
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]