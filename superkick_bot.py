import os
import csv
import nest_asyncio
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
from playwright.async_api import async_playwright
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model

nest_asyncio.apply()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "superkick_data.csv"
MODEL_FILE = "superkick_lstm_model.h5"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def extract_multiplier():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://www.msport.com/ng/m/casino/games/superkick")
            await page.wait_for_timeout(10000)

            element = await page.query_selector(".move-animation")
            if element:
                style = await element.get_attribute("style")
                if style:
                    for part in style.split(';'):
                        if 'scale(' in part:
                            scale_value = float(part.split('scale(')[-1].split(')')[0])
                            await browser.close()
                            return scale_value
            await browser.close()
            return None
    except Exception as e:
        logger.error(f"[!] Error extracting multiplier: {e}")
        return None

async def log_multiplier():
    while True:
        multiplier = await extract_multiplier()
        if multiplier:
            now = datetime.utcnow().isoformat()
            file_exists = os.path.isfile(DATA_FILE)
            with open(DATA_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["timestamp", "multiplier"])
                writer.writerow([now, multiplier])
            logger.info(f"✅ Logged multiplier: {multiplier}")
        await asyncio.sleep(30)

def predict_with_lstm():
    if not os.path.exists(DATA_FILE):
        return "⚠️ No data available for prediction."

    df = pd.read_csv(DATA_FILE)
    if len(df) < 20:
        return "⚠️ Not enough data yet. Wait for a few more rounds."

    data = df['multiplier'].values.reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)
    seq_length = 10

    if len(scaled) <= seq_length:
        return "⚠️ Not enough data to form a prediction sequence."

    input_seq = scaled[-seq_length:].reshape(1, seq_length, 1)

    if not os.path.exists(MODEL_FILE):
        return "⚠️ Trained model not found. Train the model first."

    model = load_model(MODEL_FILE)
    predicted_scaled = model.predict(input_seq)
    predicted = scaler.inverse_transform(predicted_scaled)
    return f"🔮 Based on recent data, the predicted next multiplier is: {predicted[0][0]:.2f}x"

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/predict called")
    prediction = predict_with_lstm()
    await update.message.reply_text(prediction)

if __name__ == '__main__':
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN is missing. Set it in Railway → Variables")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("predict", predict_command))

    asyncio.create_task(log_multiplier())
    app.run_polling()
