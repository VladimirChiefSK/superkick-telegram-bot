#!/bin/bash

echo "✅ Installing Chromium for Playwright..."
playwright install chromium

echo "🚀 Starting your Telegram bot..."
python superkick_bot.py
