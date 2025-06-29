# send_audio_client.py
import sounddevice as sd
import asyncio
import websockets
import numpy as np
import queue
import threading

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print("⚠️", status)
    q.put(indata.copy().astype(np.float32).tobytes())

async def send_audio(websocket):
    while True:
        data = await asyncio.get_event_loop().run_in_executor(None, q.get)
        await websocket.send(data)

async def recv_result(websocket):
    try:
        async for message in websocket:
            print("=> ", message)
            with open("result.txt", "a", encoding="utf-8") as f:
                f.write(message + "\n")
    except websockets.exceptions.ConnectionClosed:
        print("❌ 接続が切れました")


async def main():
    uri = "ws://localhost:8000"
    async with websockets.connect(uri) as websocket:
        print("クライアントが接続されました！")  
        loop = asyncio.get_event_loop()
        # 録音ストリーム開始は同期的に
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback)
        with stream:
            send_task = asyncio.create_task(send_audio(websocket))
            recv_task = asyncio.create_task(recv_result(websocket))
            await asyncio.gather(send_task, recv_task)

if __name__ == "__main__":
    asyncio.run(main())
