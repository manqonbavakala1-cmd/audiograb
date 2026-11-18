FROM python:3.11-slim

# Install FFmpeg AND Node.js (for yt-dlp signature solving)
RUN apt-get update && apt-get install -y ffmpeg nodejs

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD gunicorn -w 4 -b 0.0.0.0:$PORT web:app
