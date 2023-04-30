import discord
import asyncio
import websockets
import base64
import io
import logging
import threading

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


intents = discord.Intents()
intents.messages = True
client = discord.Client(intents=intents)
counter = 0
counter_lock = threading.Lock()

generation_queue = asyncio.Queue()


async def serve_jobs(websocket):
    try:
        msgs = {}
        client_id = None
        with counter_lock:
            global counter
            counter += 1
            client_id = counter
        logging.info(f"[{client_id}] NEW CLIENT")
        async for webhook_msg in websocket:
            if webhook_msg == "NEED_JOB":
                logging.info(f"[{client_id}] NEED_JOB")
                msg: discord.Message = await generation_queue.get()
                logging.info(f"[{client_id}] GOT_JOB {msg.id}")
                msgs[str(msg.id)] = msg
                await websocket.send(f"{msg.id}::{msg.content}")
                await msg.reply("JOB TAKEN")
            elif webhook_msg.startswith("DONE_JOB"):
                _, job_id, content = webhook_msg.split("::")
                logging.info(f"[{client_id}] DONE_JOB {job_id}")
                msg: discord.Message = msgs[job_id]
                await msg.reply("DONE")
                fp = io.BytesIO(base64.b64decode(content))
                await msg.reply(file=discord.File(fp, filename="feger.png"))
                del msgs[job_id]
            elif webhook_msg.startswith("ERROR_JOB"):
                _, job_id, content = webhook_msg.split("::")
                logging.info(f"[{client_id}] ERROR_JOB {job_id}")
                msg: discord.Message = msgs[job_id]
                await msg.reply("ERROR")
                await msg.reply(content)
                del msgs[job_id]
    except websockets.exceptions.ConnectionClosedError:
        logging.info("CLIENT DISCONNECTED")
        for msg in msgs.values():
            await msg.reply("CLIENT DISCONNECTED RE ENTERING QUEUE")
            await generation_queue.put(msg)


async def generate_things():
    # make a websocket server
    async with websockets.serve(serve_jobs, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever


@client.event
async def on_ready():
    logging.info(f"we have logged in as {client.user}")
    asyncio.get_event_loop().create_task(generate_things())


@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    await generation_queue.put(msg)


client.run(open("token").read().strip())
