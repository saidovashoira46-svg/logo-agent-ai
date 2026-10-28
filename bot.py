"""AI Logo Agent Telegram bot. Ishga tushirish: python bot.py"""
import asyncio
import html
import logging
import os
import random
import re

from dotenv import load_dotenv
load_dotenv()  # Muhim: agent import qilinishidan oldin

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import agent
import designer
import storage

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylga BOT_TOKEN=... yozing.")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("logo_bot")
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
BUSY: set[int] = set()


def design_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Boshqa variant", callback_data="again")],
        [InlineKeyboardButton(text="🖌 Minimal", callback_data="tweak:minimal"),
         InlineKeyboardButton(text="✨ Luxury", callback_data="tweak:luxury")],
        [InlineKeyboardButton(text="🔵 Ko'k", callback_data="color:navy_ice"),
         InlineKeyboardButton(text="🟡 Oltin", callback_data="color:black_gold"),
         InlineKeyboardButton(text="➕ Yangi logo", callback_data="new")],
    ])


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Logo yaratish", callback_data="create")],
        [InlineKeyboardButton(text="💡 Misollar", callback_data="samples"),
         InlineKeyboardButton(text="❓ Yordam", callback_data="help")],
    ])


WELCOME = (
    "✨ <b>AI LOGO AGENT</b>\n"
    "<i>G'oyangizga mos, esda qolarli logotip.</i>\n\n"
    "🎨 <b>Birgina xabar bilan boshlang!</b>\n"
    "Brend yoki ismingizni yozing. AI maqsadingizni tushunib, "
    "rang, shrift va dizayn yo'nalishini tanlaydi.\n\n"
    "💬 <b>Masalan:</b>\n"
    "<code>Ayub degan so'zga logo kerak</code>\n"
    "<code>Ali Market uchun oq-ko'k minimal logo</code>\n"
    "<code>My Coffee nomiga premium logotip</code>\n\n"
    "🛠 Natijadan keyin <i>'rangini ko'k qil'</i> deb yozing "
    "yoki variant tugmalarini bosing.\n\n"
    "🚀 <b>Keling, birinchi logongizni yarataylik!</b>"
)

HELP = (
    "🧭 <b>Qanday foydalaniladi?</b>\n\n"
    "<b>1.</b> Brend yoki ismingizni yozing.\n"
    "<b>2.</b> Rang va uslubni xohishingizcha belgilang.\n"
    "<b>3.</b> Tayyor logoni PNG ko'rinishida oling.\n"
    "<b>4.</b> 'Rangini yashil qil', 'minimal qil', "
    "'ramkasini olib tashla' kabi buyruqlar bilan tahrirlang.\n\n"
    "<b>Buyruqlar:</b> /start — bosh sahifa, /new — yangi logo, "
    "/help — yordam, /status — AI holati, /testai — haqiqiy API sinovi."
)


async def send_logo(message: Message, uid: int, spec: dict):
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
    image_bytes = await asyncio.to_thread(designer.render, spec, random.randint(1, 10**9))
    safe_brand = html.escape(spec["brand"])
    engine = "🧠 Gemini AI" if spec.get("_engine") == "AI" else "⚙️ AI javobi tuzatildi / zaxira dizayn"
    caption = (f"✅ <b>{safe_brand}</b> — logotipingiz tayyor!\n"
               f"🎭 Uslub: {html.escape(spec.get('style') or 'zamonaviy')}\n"
               f"{engine}\n\n"
               "🎨 O'zgartirish kerakmi? <i>Rangini ko'k qil</i> deb yozing "
               "yoki quyidagi tugmalardan foydalaning.")
    await message.answer_photo(
        BufferedInputFile(image_bytes, filename="preview.png"),
        caption=caption,
        reply_markup=design_keyboard(),
    )
    file_name = re.sub(r"[^a-zA-Z0-9_-]", "_", spec["brand"])[:35].strip("_") or "logo"
    await message.answer_document(
        BufferedInputFile(image_bytes, filename=f"{file_name}_logo.png"),
        caption="📦 <b>1024 × 1024 PNG</b> — yuklab olishga tayyor",
    )
    # Faqat muvaffaqiyatli yuborilgandan so'ng saqlash
    storage.save_spec(uid, spec)


async def handle_text(message: Message, uid: int, text: str):
    if uid in BUSY:
        await message.answer("⏳ Logotipingiz tayyorlanmoqda. Oldingi ish tugagach yozing.")
        return
    BUSY.add(uid)
    status = None
    try:
        status = await message.answer("🧠 <b>So'rovingiz tahlil qilinmoqda...</b>")
        prev = storage.get_spec(uid)
        spec = await agent.analyze(text, prev)
        if spec.get("mode") == "chat":
            # AI foydalanuvchi matniga HTML kod qo'sha olmasin
            await status.edit_text(html.escape(spec.get("reply") or "Qaysi nomga logo kerak?"))
            return
        await status.edit_text(f"🎨 <b>{html.escape(spec['brand'])}</b> uchun logo tayyorlanmoqda...")
        await send_logo(message, uid, spec)
        logger.info("DONE | user=%s | logo tayyor", uid)
        await status.delete()
    except Exception:
        logger.exception("LOGO ERROR")
        if status:
            await status.edit_text("❌ Logo yaratishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
        else:
            await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
    finally:
        BUSY.discard(uid)


@dp.message(CommandStart())
async def start(message: Message):
    # /start avvalgi logoni o'chirmaydi: tahrirlash davom etishi mumkin.
    await message.answer(WELCOME, reply_markup=welcome_keyboard())


@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(HELP)


@dp.message(Command("new"))
async def new_cmd(message: Message):
    storage.reset_spec(message.from_user.id)
    await message.answer("🌟 <b>Yangi loyiha!</b>\nQaysi ism yoki brendga logo kerak?\n\n<i>Masalan: Ayub uchun qora-oltin logo</i>")


@dp.message(Command("status"))
async def status_cmd(message: Message):
    if not agent._client:
        await message.answer("⚠️ <b>Gemini API ulanmagan.</b>\n.env faylga GEMINI_API_KEY yozing. Hozir zaxira tizim ishlayapti.")
    else:
        state = agent.AI_LAST_RESULT
        await message.answer(f"🧠 AI provayder: <b>{html.escape(agent.PROVIDER)}</b>\n"
                             f"Model: <code>{html.escape(agent.LLM_MODEL)}</code>\n"
                             f"So'nggi holat: <b>{html.escape(state)}</b>\n"
                             f"{('Xatolik: ' + html.escape(agent.AI_LAST_ERROR)) if agent.AI_LAST_ERROR else ''}\n"
                             "<i>Kalit mavjudligi uning ishlashini kafolatlamaydi; botga sinov xabari yozing.</i>")


@dp.message(Command("testai"))
async def test_ai_cmd(message: Message):
    status = await message.answer("🔎 Gemini API ulanishi sinovdan o'tkazilmoqda...")
    ok, reason = await agent.check_ai()
    if ok:
        await status.edit_text("✅ <b>AI ishlayapti!</b>\n" + html.escape(reason))
    else:
        await status.edit_text("❌ <b>Gemini ishlamayapti</b>\n" + html.escape(reason) +
                               "\n\n.env faylidagi GEMINI_API_KEY va GEMINI_MODEL ni tekshiring.")


@dp.callback_query(F.data == "create")
async def create_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer("✍️ Logoga qanday nom yozamiz? Masalan: <b>Ayub</b> yoki <b>Ali Market uchun ko'k minimal logo</b>")


@dp.callback_query(F.data == "samples")
async def examples_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer("💡 <b>Namuna so'rovlar:</b>\n\n"
                              "• <code>Ayub uchun gaming uslubda ko'k logo</code>\n"
                              "• <code>TechNova nomiga texnologik logo</code>\n"
                              "• <code>My Coffee uchun premium yashil-oltin logo</code>\n"
                              "• <code>Ali CMBK uchun qoramtir minimal logo</code>")


@dp.callback_query(F.data == "help")
async def help_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer(HELP)


@dp.callback_query(F.data == "new")
async def new_callback(call: CallbackQuery):
    await call.answer()
    storage.reset_spec(call.from_user.id)
    await call.message.answer("➕ <b>Yangi logotip</b>\nYangi brend nomini yozing.")


@dp.callback_query(F.data == "again")
async def again(call: CallbackQuery):
    await call.answer()
    prev = storage.get_spec(call.from_user.id)
    if not prev:
        await call.message.answer("Avval brend nomini yozing 🙂")
        return
    await run_variant(call.message, call.from_user.id, designer.vary(prev))


@dp.callback_query(F.data.startswith("tweak:"))
async def tweak(call: CallbackQuery):
    await call.answer()
    prev = storage.get_spec(call.from_user.id)
    if not prev:
        await call.message.answer("Avval brend nomini yozing 🙂")
        return
    key = call.data.split(":", 1)[1]
    if key not in {"minimal", "luxury"}:
        return
    await run_variant(call.message, call.from_user.id, designer.tweak(prev, key))


@dp.callback_query(F.data.startswith("color:"))
async def color_callback(call: CallbackQuery):
    await call.answer()
    prev = storage.get_spec(call.from_user.id)
    if not prev:
        await call.message.answer("Avval brend nomini yozing 🙂")
        return
    key = call.data.split(":", 1)[1]
    if key not in {"navy_ice", "black_gold"}:
        return
    spec = dict(prev, palette=key, custom_colors=None)
    await run_variant(call.message, call.from_user.id, spec)


async def run_variant(message: Message, uid: int, spec: dict):
    if uid in BUSY:
        await message.answer("⏳ Hozir boshqa variant tayyorlanmoqda.")
        return
    BUSY.add(uid)
    try:
        await send_logo(message, uid, spec)
    except Exception:
        logger.exception("VARIANT ERROR")
        await message.answer("❌ Variant yaratishda xatolik yuz berdi.")
    finally:
        BUSY.discard(uid)


@dp.message(F.text)
async def text_handler(message: Message):
    if message.text.strip():
        await handle_text(message, message.from_user.id, message.text)


@dp.message()
async def other(message: Message):
    await message.answer("✍️ Logo uchun nomni matn shaklida yuboring, masalan: <b>Ayub</b>.")


async def main():
    storage.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s | agent: %s | model: %s", me.username, agent.PROVIDER, agent.LLM_MODEL)
    if not agent._client:
        logger.warning("GEMINI_API_KEY yo'q: zaxira agent ishlaydi, haqiqiy Gemini ishlamaydi.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")
