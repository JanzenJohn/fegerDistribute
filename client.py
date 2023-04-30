import websockets
import asyncio
import requests

async def main():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            try:
                await websocket.send("NEED_JOB")
                job_id, job_data = (await websocket.recv()).split("::")
                x = requests.post("http://localhost:7860/sdapi/v1/txt2img", json={"prompt": job_data}) 
                if x.status_code != 200:
                    raise Exception(f"Error: {x.status_code}")
                await websocket.send(f"DONE_JOB::{job_id}::{x.json()['images'][0]}")
            except Exception as e:
                await websocket.send(f"ERROR_JOB::{job_id}::{e}")

asyncio.run(main())