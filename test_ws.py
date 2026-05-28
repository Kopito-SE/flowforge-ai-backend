import asyncio
import websockets
import json


async def listen():
    print("🔌 Trying to connect to WebSocket...")

    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws/executions/") as websocket:
            print("✅ Connected! Waiting for workflow messages...")
            print("Press Ctrl+C to stop\n")

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    print(f"📨 Message received: {json.dumps(data, indent=2)}")
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed normally")
                    break
    except Exception as e:
        print(f"❌ Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(listen())