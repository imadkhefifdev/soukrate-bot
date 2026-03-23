import os
import asyncio
import threading
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# =========================
# 🔐 التوكن
# =========================
TOKEN = os.getenv("TOKEN")

# =========================
# 🔐 Firebase
# =========================
import firebase_admin
from firebase_admin import credentials, firestore

firebase_data = json.loads(os.getenv("FIREBASE_KEY"))

cred = credentials.Certificate(firebase_data)
firebase_admin.initialize_app(cred)

db = firestore.client()

# =========================
# 👤 ADMIN
# =========================
ADMIN_ID = 123456789  # ضع ID الخاص بك

# =========================
# 💰 السوق السوداء
# =========================
BLACK_MARKET = {
    "usd_dzd": 240,
    "eur_dzd": 260
}

# =========================
# 📡 API
# =========================
def get_rate(from_currency, to_currency):
    key = f"{from_currency.lower()}_{to_currency.lower()}"

    if key in BLACK_MARKET:
        return BLACK_MARKET[key]

    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
    response = requests.get(url)
    data = response.json()
    return data["rates"].get(to_currency.upper())

# =========================
# 📊 تسجيل المستخدم
# =========================
def track_user(user_id):
    user_ref = db.collection("users").document(str(user_id))
    doc = user_ref.get()

    if doc.exists:
        user_ref.update({
            "count": firestore.Increment(1)
        })
    else:
        user_ref.set({
            "count": 1
        })

# =========================
# 🚀 /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("💵 USD → DZD", callback_data="usd_dzd")],
        [InlineKeyboardButton("💶 EUR → DZD", callback_data="eur_dzd")],
        [InlineKeyboardButton("💱 تحويل مخصص", callback_data="custom")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 مرحبا بك في SoukRate Bot\nاختر نوع التحويل:",
        reply_markup=reply_markup
    )

# =========================
# 🔘 الأزرار
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    track_user(query.from_user.id)

    data = query.data

    if data == "usd_dzd":
        result = get_rate("usd", "dzd")
        await query.edit_message_text(f"💵 1 USD = {result} DZD")

    elif data == "eur_dzd":
        result = get_rate("eur", "dzd")
        await query.edit_message_text(f"💶 1 EUR = {result} DZD")

    elif data == "custom":
        await query.edit_message_text("📌 اكتب مثل:\n100 usd to dzd")

# =========================
# 🧠 الرسائل
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user.id)

    text = update.message.text.lower()

    try:
        parts = text.split()

        if len(parts) == 4 and parts[2] == "to":
            amount = float(parts[0])
            from_currency = parts[1]
            to_currency = parts[3]

            rate = get_rate(from_currency, to_currency)

            if rate:
                result = amount * rate
                await update.message.reply_text(
                    f"💱 {amount} {from_currency.upper()} = {round(result, 2)} {to_currency.upper()}"
                )
            else:
                await update.message.reply_text("❌ عملة غير مدعومة")

        else:
            await update.message.reply_text("📌 اكتب: 100 usd to dzd")

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ خطأ في الإدخال")

# =========================
# 📊 الإحصائيات (Admin فقط)
# =========================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر خاص بالإدارة")
        return

    users = db.collection("users").stream()

    total_users = 0
    total_messages = 0

    for user in users:
        data = user.to_dict()
        total_users += 1
        total_messages += data.get("count", 0)

    await update.message.reply_text(
        f"📊 Firebase Stats:\n\n"
        f"👤 المستخدمين: {total_users}\n"
        f"💬 الاستخدام: {total_messages}"
    )

# =========================
# 🧩 التطبيق
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# =========================
# 🌐 Fake server (Render)
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_server).start()

# =========================
# ⚙️ تشغيل (Python 3.14)
# =========================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

print("Bot is running...")

loop.run_until_complete(app.initialize())
loop.run_until_complete(app.start())
loop.run_until_complete(app.updater.start_polling())

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.run_until_complete(app.stop())
    loop.run_until_complete(app.shutdown())
