import os
import csv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("7663833155:AAHbzU-mGaukLUv056psU3bS05uBBs_qoyg")
AUTHORIZED_USERNAME = os.environ.get("@VladimirchiefSK")

def mock_predict(data):
    return "Medium (1.6–2.9x) — [AI model coming soon]"

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username

    if username != AUTHORIZED_USERNAME:
        await update.message.reply_text("⛔ You’re not authorized to use this bot.")
        return

    try:
        with open("superkick_data.csv", "r") as file:
            reader = list(csv.reader(file))[-10:]
            scale_values = [float(row[1]) for row in reader]

        prediction = mock_predict(scale_values)
        await update.message.reply_text(f"🔮 Prediction based on last 10 rounds:\n{prediction}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to the SuperKick AI Predictor.\nUse /predict to get the next multiplier estimate.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.run_polling()
