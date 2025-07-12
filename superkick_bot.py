import os
import csv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ✅ Read from Railway environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
AUTHORIZED_USERNAME = os.environ.get("AUTHORIZED_USERNAME")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing. Set it in Railway → Variables")

# Mock predictor for now
def predict_next(scale_values):
    return "Medium (1.6x – 2.9x) — [ML coming soon]"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to SuperKick Predictor!\nUse /predict to get the next multiplier.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user != AUTHORIZED_USERNAME:
        await update.message.reply_text("⛔ You're not authorized.")
        return

    try:
        with open("superkick_data.csv", "r") as file:
            rows = list(csv.reader(file))[-10:]
            values = [float(r[1]) for r in rows]
            result = predict_next(values)
            await update.message.reply_text(f"🔮 Prediction:\n{result}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.run_polling()
