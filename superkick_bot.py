import os
import csv
import asyncio
import nest_asyncio
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")
CSV_FILE = "superkick_data.csv"

# Ensure the CSV file exists
def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['multiplier', 'timestamp'])

# Append a new multiplier entry
def log_multiplier(multiplier):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([multiplier, datetime.now().isoformat()])

# Extract multiplier using Playwright (async version)
async def extract_multiplier():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://www.msport.com")
            await page.wait_for_timeout(5000)
            element = await page.query_selector(".move-animation")
            if element:
                style = await element.get_attribute("style")
                if style:
                    scale_part = [s for s in style.split(';') if 'scale' in s]
                    if scale_part:
                        scale_value = float(scale_part[0].split('scale(')[1].rstrip(')'))
                        await browser.close()
                        return round(scale_value, 2)
            await browser.close()
    except Exception as e:
        print(f"[!] Error extracting multiplier: {e}")
    return None

# ML prediction
def predict_next_multiplier():
    if not os.path.exists(CSV_FILE):
        return None

    df = pd.read_csv(CSV_FILE)
    if len(df) < 10:
        return None

    X = np.array(range(len(df))).reshape(-1, 1)
    y = df['multiplier'].values

    model = LinearRegression()
    model.fit(X, y)
    next_index = np.array([[len(df)]])
    prediction = model.predict(next_index)[0]
    return round(prediction, 2)

# Telegram commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to SuperKick AI Predictor Bot! Use /predict to get the next multiplier prediction.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prediction = predict_next_multiplier()
    if prediction:
        await update.message.reply_text(f"🔮 Based on recent trends, the next multiplier is likely around: {prediction}x")
    else:
        await update.message.reply_text("⚠️ Not enough data yet. Wait for a few rounds.")

# Background logger
async def background_logger():
    while True:
        multiplier = await extract_multiplier()
        if multiplier:
            print(f"[+] Multiplier logged: {multiplier}")
            log_multiplier(multiplier)
        await asyncio.sleep(30)

# Main bot runner
async def run():
    ensure_csv()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    asyncio.create_task(background_logger())
    await app.run_polling()

if __name__ == "__main__":
    print("✅ Bot is running with auto-logging and ML predictions...")
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(run())
