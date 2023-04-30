import discord
import asyncio
import websockets
import base64
import io



intents = discord.Intents()
intents.messages = True
client = discord.Client(intents=intents)

generation_queue = asyncio.Queue()
msgs = {}

async def serve_jobs(websocket):
    async for webhook_msg in websocket:
        if webhook_msg == "NEED_JOB":
            msg: discord.Message = await generation_queue.get()
            await websocket.send(f"{msg.id}::{msg.content}")
            await msg.reply("JOB TAKEN")
            msgs[str(msg.id)] = msg
        elif webhook_msg.startswith("DONE_JOB"):
            _, job_id, content = webhook_msg.split("::")
            msg: discord.Message = msgs[job_id]
            await msg.reply("DONE")
            fp = io.BytesIO(base64.b64decode(content))
            await msg.reply(file=discord.File(fp, filename="feger.png"))
            del msgs[job_id]
        elif webhook_msg.startswith("ERROR_JOB"):
            _, job_id, content = webhook_msg.split("::")
            msg: discord.Message = msgs[job_id]
            await msg.reply("ERROR")
            await msg.reply(content)
            del msgs[job_id]
        
            
            
            

async def generate_things():
    # make a websocket server
    async with websockets.serve(serve_jobs, "localhost", 8765):
        await asyncio.Future()  # run forever
    
        

@client.event
async def on_ready():
    print(f"we have logged in as {client.user}")
    asyncio.get_event_loop().create_task(generate_things())

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return
    
    await generation_queue.put(msg)
    
    

client.run(open("token").read().strip())