import os
import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# التوكن من Render
TOKEN = os.getenv("TOKEN")

# جلب سعر العملة
def get_rate(from_currency, to_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
    response = requests.get(url)
    data = response.json()
    return data["rates"].get(to_currency.upper())

# معالجة الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    f"{amount} {from_currency.upper()} = {round(result, 2)} {to_currency.upper()}"
                )
            else:
                await update.message.reply_text("❌ عملة غير مدعومة")

        else:
            await update.message.reply_text("📌 اكتب: 100 usd to dzd")

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ خطأ في الإدخال")

# إنشاء التطبيق
app = ApplicationBuilder().token(TOKEN).build()

# إضافة الهاندلر
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 🔥 حل مشكلة Python 3.14 (event loop)
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
