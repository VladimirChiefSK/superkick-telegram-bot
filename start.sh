#!/bin/bash

# Ensure Chromium is installed
npx playwright install chromium

# Start your bot
python superkick_bot.py
