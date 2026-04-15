FROM python:3.11-slim

# install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

# copy requirements dulu (cache optimization)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy semua source
COPY . .

# railway pakai env PORT
ENV PORT=8000

# run app
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]