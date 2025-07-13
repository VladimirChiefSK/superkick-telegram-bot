#!/bin/bash

echo "Installing Playwright browsers..."
npx playwright install chromium

echo "Starting SuperKick bot..."
python superkick_bot.py
