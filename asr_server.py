# vad_asr_server.py
import asyncio
import websockets
import numpy as np
import webrtcvad
from webrtc_noise_gain import AudioProcessor
from reazonspeech.k2.asr import load_model, transcribe, audio_from_numpy

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
CHUNK_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

vad = webrtcvad.Vad(2)
ap = AudioProcessor(3, 3)

model = load_model(device="cpu")

async def handle_client(websocket):
    print("🔌 クライアント接続")
    speech_buf = []
    silence_cnt = 0
    MAX_SILENCE = int(0.4 * 1000 / FRAME_DURATION_MS)

    try:
        async for message in websocket:
            # float32 の音声を受信
            raw = np.frombuffer(message, dtype=np.float32)
            int16_full = (raw * 32768).astype(np.int16)

            for i in range(0, len(int16_full), 160):
                frame = int16_full[i:i+160]
                if len(frame) < 160:
                    continue

                processed = ap.Process10ms(frame.tobytes())
                buf = processed.audio
                chunk = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768

                if processed.is_speech and vad.is_speech((chunk * 32768).astype(np.int16).tobytes(), SAMPLE_RATE):
                    speech_buf.append(chunk)
                    silence_cnt = 0
                else:
                    if speech_buf:
                        silence_cnt += 1
                        if silence_cnt > MAX_SILENCE:
                            audio = audio_from_numpy(np.concatenate(speech_buf), SAMPLE_RATE)
                            result = transcribe(model, audio)
                            text = result.text.strip()
                            if len(text) >= 5:
                                await websocket.send(text)
                            speech_buf.clear()
                            silence_cnt = 0
    except websockets.exceptions.ConnectionClosed:
        print("🔌 切断")

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8000):
        print("🚀 WebSocket音声認識サーバー起動")
        await asyncio.Future()  # 無限待機

if __name__ == "__main__":
    asyncio.run(main())

