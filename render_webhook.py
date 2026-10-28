"""Render Free Web Service: Telegram webhook receiver. Run: python render_webhook.py"""
import hashlib
import logging
import os
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot import bot, dp
import agent
import storage

WEBHOOK_PATH = "/telegram/webhook"


def app_factory():
    base_url = (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PUBLIC_URL") or "").strip().rstrip("/")
    if not base_url.startswith("https://"):
        raise RuntimeError("RENDER_EXTERNAL_URL yoki PUBLIC_URL https:// bilan boshlanishi kerak")
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL sozlanmagan. Ma'lumotlar yo'qolmasligi uchun Neon PostgreSQL ulanishi majburiy.")
    # Telegram secret token must be ASCII [A-Za-z0-9_-], 1..256 characters.
    secret = (os.getenv("WEBHOOK_SECRET") or hashlib.sha256(bot.token.encode()).hexdigest()).strip()

    async def startup(bot):
        storage.init_db()
        await bot.set_webhook(
            f"{base_url}{WEBHOOK_PATH}", secret_token=secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=False,
        )
        me = await bot.get_me()
        logging.getLogger("logo_bot").info("Render webhook ready: @%s | engine %s", me.username, agent.PROVIDER)

    dp.startup.register(startup)
    app = web.Application()
    async def health(_request):
        return web.json_response({"ok": True, "service": "logo-agent-webhook"})
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret, handle_in_background=True).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app_factory(), host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
