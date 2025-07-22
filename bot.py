import sys
import glob
import importlib
from pathlib import Path
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
import asyncio
from datetime import date, datetime
import pytz
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import logging
import logging.config

from database.ia_filterdb import Media, Media2
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from dreamxbotz.Bot import dreamxbotz
from dreamxbotz.util.keepalive import ping_server
from dreamxbotz.Bot.clients import initialize_clients
from plugins import check_expired_premium
from globals import botStartTime


# Logging Setup
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# FastAPI Web App
web_app = FastAPI()

@web_app.get("/")
async def health_check():
    return JSONResponse({"status": "ok"})

async def start_fastapi():
    config = uvicorn.Config(web_app, host="0.0.0.0", port=8080, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

async def load_plugins():
    plugin_files = glob.glob("plugins/*.py")
    for name in plugin_files:
        with open(name) as _:
            plugin_name = Path(name).stem
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, f"plugins/{plugin_name}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[import_path] = module
            print(f"✅ Loaded Plugin: {plugin_name}")

async def throttled_check_expired():
    while True:
        await check_expired_premium(dreamxbotz)
        await asyncio.sleep(60)  # sleep to reduce CPU

async def throttled_keep_alive():
    while True:
        await ping_server()
        await asyncio.sleep(30)

async def dreamxbotz_start():
    print("\n🚀 Initializing DreamxBotz...")
    await dreamxbotz.start()
    await initialize_clients()

    await load_plugins()

    dreamxbotz.loop.create_task(check_expired_premium(dreamxbotz))
    dreamxbotz.loop.create_task(start_fastapi())  # ✅ Starts FastAPI for Koyeb health checks

    await idle()  # ✅ Keeps the bot running


    # Fetch banned users and chats
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats

    # Set up DB indexes
    await Media.ensure_indexes()
    if MULTIPLE_DB:
        await Media2.ensure_indexes()
        print("🗃 Multiple DB Mode Active")
    else:
        print("🗃 Single DB Mode Active")

    # Set identity globals
    me = await dreamxbotz.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    dreamxbotz.username = f'@{me.username}'

    # Log startup info
    logging.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    logging.info(LOG_STR)
    logging.info(script.LOGO)

    # Send restart notification
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    today = date.today()
    timestamp = now.strftime("%H:%M:%S %p")
    await dreamxbotz.send_message(LOG_CHANNEL, script.RESTART_TXT.format(temp.B_LINK, today, timestamp))

    # Start background tasks
    asyncio.create_task(throttled_check_expired())
    asyncio.create_task(throttled_keep_alive())
    asyncio.create_task(start_fastapi())

    # Keep alive
    await idle()

if __name__ == "__main__":
    try:
        asyncio.run(dreamxbotz_start())
    except KeyboardInterrupt:
        logging.info("🛑 Bot stopped by user")
