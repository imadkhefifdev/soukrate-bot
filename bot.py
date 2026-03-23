
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import requests

TOKEN = "ضع_التوكن_هنا8684287596:AAFkCfJgL2oirY6QbH67baISNjHAf8GjgGQ"

# جلب السعر من API
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

        # مثال: 100 usd to dzd
        if len(parts) == 4 and parts[2] == "to":
            amount = float(parts[0])
            from_currency = parts[1]
            to_currency = parts[3]

            rate = get_rate(from_currency, to_currency)

            if rate:
                result = amount * rate
                await update.message.reply_text(
                    f"{amount} {from_currency.upper()} = {round(result,2)} {to_currency.upper()}"
                )
            else:
                await update.message.reply_text("❌ عملة غير مدعومة")

        else:
            await update.message.reply_text("📌 اكتب: 100 usd to dzd")

    except:
        await update.message.reply_text("❌ خطأ في الإدخال")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
