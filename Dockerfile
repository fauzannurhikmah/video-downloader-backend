# Base image
FROM python:3.11-slim

# Install ffmpeg (buat yt-dlp)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements dulu (biar caching jalan)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua source code
COPY . .

# Railway inject PORT otomatis
ENV PORT=8000

# Run FastAPI 
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT