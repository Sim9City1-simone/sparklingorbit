FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    fonts-liberation \
    fontconfig \
    nodejs \
    npm \
    git \
    build-essential \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Build bgutil PO Token server (version must match pip package 1.3.1)
RUN git clone --single-branch --branch 1.3.1 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /bgutil \
    && cd /bgutil/server \
    && npm ci \
    && npx tsc \
    && rm -rf /bgutil/.git /bgutil/server/node_modules/.cache

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/data"]

EXPOSE 8000

CMD ["bash", "start_production.sh"]
