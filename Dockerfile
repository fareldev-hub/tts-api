FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True)" && \
    chmod -R 755 /root/nltk_data

ENV NLTK_DATA=/root/nltk_data

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "app.py"]