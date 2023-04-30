import websockets
import asyncio
import requests
import argparse
import threading

argparser = argparse.ArgumentParser()
argparser.add_argument("--port", type=int, default=8765)
argparser.add_argument("--host", type=str, default="localhost")
argparser.add_argument("--ws-ssl", type=bool, default=False)
argparser.add_argument("--sd-port", type=int, default=7860)
argparser.add_argument("--sd-host", type=str, default="localhost")
argparser.add_argument("--sd-ssl", type=bool, default=False)
args = argparser.parse_args()

websocket_url = "wss://" if args.ws_ssl else "ws://"
websocket_url += f"{args.host}:{args.port}"

sd_url = "https://" if args.sd_ssl else "http://"
sd_url += f"{args.sd_host}:{args.sd_port}"


async def main():
    
    async with websockets.connect(websocket_url) as websocket:
        while True:
            job_id = 0
            try:
                await websocket.send("NEED_JOB")
                job_id, job_data = (await websocket.recv()).split("::")
                t = threading.Thread(target=lambda :requests.post(f"{sd_url}/sdapi/v1/txt2img", json={"prompt": job_data}) )
                while t.is_alive():
                    await asyncio.sleep(0.5)
                if x.status_code != 200:
                    raise Exception(f"Error: {x.status_code}")
                await websocket.send(f"DONE_JOB::{job_id}::{x.json()['images'][0]}")
            except Exception as e:
                await websocket.send(f"ERROR_JOB::{job_id}::{e}")

asyncio.run(main())