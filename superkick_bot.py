import os
import csv
import time
import threading
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from playwright.sync_api import sync_playwright

# === Configuration ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
AUTHORIZED_USERNAME = os.environ.get("AUTHORIZED_USERNAME")
CSV_FILE = "superkick_data.csv"
SUPERKICK_URL = "https://www.msport.com/gh/games/superkick"

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing. Set it in Railway → Variables")

# === Ensure CSV file exists ===
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "multiplier"])  # header row

# === Playwright Scraper ===
def extract_multiplier():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(SUPERKICK_URL, timeout=60000)
            page.wait_for_selector(".sk-animation-odds", timeout=10000)
            text = page.locator(".sk-animation-odds").text_content().strip()
            browser.close()
            return float(text.replace("x", ""))
    except Exception as e:
        print(f"[!] Error extracting multiplier: {e}")
        return None

# === Background Logger ===
def log_loop():
    while True:
        multiplier = extract_multiplier()
        if multiplier:
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().isoformat(), multiplier])
                print(f"[+] Logged: {multiplier}")
        time.sleep(10)

# === Telegram Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to SuperKick AI Bot!\nUse /predict to get a forecast.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user != AUTHORIZED_USERNAME:
        await update.message.reply_text("⛔ You're not authorized to use this bot.")
        return

    try:
        with open(CSV_FILE, "r") as f:
            rows = list(csv.reader(f))[1:]  # skip header
            if len(rows) < 1:
                await update.message.reply_text("⚠️ Not enough data yet. Wait for a few rounds.")
                return

            recent = rows[-10:]
            multipliers = [float(r[1]) for r in recent if r[1]]

        avg = sum(multipliers) / len(multipliers)
        prediction = f"🔮 Based on the last {len(multipliers)} kicks:\nEstimated next multiplier: {avg:.2f}x"
        await update.message.reply_text(prediction)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error reading data: {e}")

# === Main Execution ===
if __name__ == "__main__":
    # Start logging thread
    threading.Thread(target=log_loop, daemon=True).start()

    # Start Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.run_polling()
