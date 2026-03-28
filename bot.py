"""
KaluxHost Discord Bot — Entry Point
Runs the bot defined in main/bot.py
"""
import asyncio
import sys
import os

# Make sure imports resolve from this directory
sys.path.insert(0, os.path.dirname(__file__))

from main.bot import KaluxBot

if __name__ == "__main__":
    asyncio.run(KaluxBot().start_bot())
