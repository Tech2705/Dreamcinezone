import asyncio
from aiohttp import web
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT

# Set up a simple web server for health checks
app = web.Application()

async def health(request):
    return web.Response(text="OK")

app.router.add_get("/", health)

async def main():
    # Initialize your Telegram bot client
    bot = Client("dreamxbotz_search", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await bot.start()
    print("Bot started")

    # Start the web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    print(f"Health server running on port {PORT}")

    # Keep everything running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
