FROM python:3.11.11-bullseye

# Install system dependencies
RUN apt -qq update && \
    apt -qq install -y --no-install-recommends \
    curl \
    ca-certificates \
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


# Create user with UID 1000
RUN useradd -m -u 1000 user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
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

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]