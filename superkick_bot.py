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
    await update.message.reply_text("👋 Welcome to SuperKick AI Bot!\nUse /predict or /history.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user != AUTHORIZED_USERNAME:
        await update.message.reply_text("⛔ You're not authorized to use this bot.")
        return

    try:
        with open(CSV_FILE, "r") as f:
            rows = list(csv.reader(f))[1:]  # skip header
            if len(rows) < 3:
                await update.message.reply_text("⚠️ Not enough data yet. Wait for at least 3 rounds.")
                return

            recent = rows[-5:]  # Use last 5 entries
            multipliers = [float(r[1]) for r in recent if r[1]]

        avg = sum(multipliers) / len(multipliers)
        prediction = f"🔮 Based on the last {len(multipliers)} rounds:\nEstimated next multiplier: {avg:.2f}x"
        await update.message.reply_text(prediction)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error reading data: {e}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.username
    if user != AUTHORIZED_USERNAME:
        await update.message.reply_text("⛔ You're not authorized to use this bot.")
        return

    try:
        with open(CSV_FILE, "r") as f:
            rows = list(csv.reader(f))[1:]  # skip header
            if not rows:
                await update.message.reply_text("📉 No data logged yet.")
                return

            last_entries = rows[-5:]
            formatted = "\n".join([f"{r[0].split('T')[1][:8]} — {r[1]}x" for r in last_entries])
            await update.message.reply_text(f"📜 Last 5 multipliers:\n{formatted}")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error reading history: {e}")

# === Main Execution ===
if __name__ == "__main__":
    threading.Thread(target=log_loop, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("history", history))
    app.run_polling()
