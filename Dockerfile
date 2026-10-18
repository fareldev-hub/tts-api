FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p models && \
    wget -O models/id_ID-news_tts-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx" && \
    wget -O models/id_ID-news_tts-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx.json"

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]