# 🎨 AI Logo Agent — Gemini orqali ishlaydigan Telegram logo-bot

## Nimalar yangilandi?

- Gemini haqiqiy AI orqali mijoz yozgan gapdan **faqat brend nomini** va dizayn talabini ajratadi.
- Masalan: `manga Ayub degan sozga logo kere` → **AYUB** yozuvi bilan logo.
- `rangini ko'k qil`, `minimal qil`, `ramkasini olib tashla`, `yana variant` — oldingi logoni tahrirlash.
- Qulay `/start` sahifasi va tugmalar; `/new`, `/help`, `/status` buyruqlari.
- PNG preview va 1024x1024 PNG fayl yuboriladi. Logoni internetga yubormasdan `Pillow` chizadi.
- So'nggi logotip SQLite `data/` papkasiga saqlanadi; restartdan keyin tahrirlash davom etadi.
- API ishlamasa, cheklangan **zaxira** algoritm foydalaniladi va foydalanuvchiga belgilanadi.

> **Muhim:** Gemini matnni tahlil qiladi. Rasmlarni Gemini generatsiya qilmaydi;
> oldingi `designer.py` geometriya, shrift, palitra yordamida bepul chizadi.
> Gemini bepul limiti va mavjudligi Google hisobingizga bog'liq. Server ham doim tekin bo'lishi kafolatlanmagan.

## Windows 11 + VS Code orqali

1. ZIP ni Desktop'ga **alohida papkaga** chiqaring.
2. VS Code'da loyiha papkasini oching.
3. `.env.example` fayldan nusxa olib `.env` nomini bering.
4. `.env` ichida yangi `BOT_TOKEN` va `GEMINI_API_KEY` ni yozing.
5. PowerShell terminalda:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe bot.py
```

Birinchi ikki komanda keyingi ishga tushirishda shart emas.
Yoki `run_windows.bat` faylni ishga tushiring.

## Sinov

- `/start` — zamonaviy salomlashuv.
- `manga Ayub degan sozga logo kere` — faqat **AYUB** nomi bilan logo.
- `rangini ko'k qil` — ayni logoning rangini o'zgartiradi.
- `boshqa variant` — nomni o'zgartirmay yangi variant.
- `/status` — AI konfiguratsiyasi va oxirgi chaqiruv holati.
- `/new` — navbatdagi nomga yangi loyiha.

## Linux serverda

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# .env ni to'ldiring
.venv/bin/python bot.py
```

24/7 ishlash uchun Linux'da `systemd` xizmatidan foydalanish mumkin. Bitta tokenni
bir vaqtning o'zida ikki joyda (`VS Code` va server) `polling` qilib ishga tushirmang.
Doimiy ma'lumotlar uchun `data/` papkasi diskda saqlanishi kerak.

## Fayllar

- `bot.py` — Telegram aiogram bot
- `agent.py` — Gemini tahlil, brend ajratish, zaxira agent
- `designer.py` — original PNG dizayn dvigateli
- `storage.py` — SQLite xotira
- `fonts/` va `examples/` — original shriftlar, logo namunalari
- `tests/` — kalitsiz lokal testlar

## Xavfsizlik

- **ZIP ichida ataylab `.env` yo'q.** `.env.example` da soxta placeholder yozuvlar bor.
- Oldingi ZIP'ingizda `.env` bor edi: `BotFather /revoke` bilan bot tokenini almashtiring,
  API kalitlarni ham qayta chiqaring, yangi `.env` yozing.
- `.env`, `venv/`, `data/` papkalarini ommaviy repository'ga joylamang.
- Bepul hisob limiti ko'p foydalanuvchida tez tugashi mumkin.
