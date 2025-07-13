import os
import csv
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing. Set it in Railway → Variables")

# Initialize data file if not exists
if not os.path.exists("superkick_data.csv"):
    with open("superkick_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["multiplier", "timestamp"])

# Extract latest multiplier from the game
async def extract_multiplier():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://www.msport.com.gh/game/superkick")
            await page.wait_for_selector(".move-animation", timeout=15000)

            scale_value = await page.eval_on_selector(".move-animation", "el => el.style.transform")
            await browser.close()

            if scale_value:
                try:
                    scale_num = float(scale_value.split("scale(")[1].split(")")[0])
                    return scale_num
                except:
                    print("[!] Error parsing scale() value")
                    return None
    except Exception as e:
        print(f"[!] Error extracting multiplier: {e}")
        return None

# Log data to CSV
async def log_multiplier():
    value = await extract_multiplier()
    if value:
        with open("superkick_data.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([value, datetime.now().isoformat()])
        print(f"[+] Logged multiplier: {value}")

# Predict based on past values
async def predict():
    try:
        with open("superkick_data.csv", "r") as f:
            rows = list(csv.reader(f))[1:]
        values = [float(r[0]) for r in rows if float(r[0]) > 0]
        if len(values) < 10:
            return None
        avg = round(sum(values[-10:]) / 10, 2)
        return avg
    except:
        return None

# Command: /predict
async def predict_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_multiplier()
    result = await predict()
    if result:
        prediction = f"🔮 Based on recent patterns, the next multiplier may land around {result}x."
    else:
        prediction = "⚠️ Not enough data yet. Wait for a few rounds."
    await update.message.reply_text(prediction)

# Command: /log (see how many entries)
async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("superkick_data.csv", "r") as f:
            lines = f.readlines()
        await update.message.reply_text(f"📝 Logged rounds: {len(lines) - 1}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error reading log: {e}")

# Setup and run bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("predict", predict_handler))
app.add_handler(CommandHandler("log", log_handler))

if __name__ == "__main__":
    print("✅ Bot is running...")
    asyncio.run(app.run_polling())
