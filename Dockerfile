FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    python3-dev \
    libportaudio2 \
    libsndfile1 \
 && apt-get clean

RUN git clone https://github.com/reazon-research/ReazonSpeech

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install ./ReazonSpeech/pkg/k2-asr && \
    pip install -r requirements.txt && \
    pip install websockets

COPY . .

EXPOSE 8000

CMD ["python", "asr_server.py"]

