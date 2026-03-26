"""
KaluxHost brand-consistent Discord embed builders.
Import these in every module instead of building raw embeds.
"""
import discord
import datetime
from main.config import (
    BOT_NAME, COLOR_BRAND, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARN, COLOR_INFO
)

_FOOTER = f"{BOT_NAME} Bot"
_NOW    = lambda: datetime.datetime.now(datetime.timezone.utc)


def brand(title: str = None, description: str = None) -> discord.Embed:
    e = discord.Embed(color=COLOR_BRAND, timestamp=_NOW())
    if title:       e.title       = title
    if description: e.description = description
    e.set_footer(text=_FOOTER)
    return e


def success(description: str) -> discord.Embed:
    return discord.Embed(
        description=f"✅ {description}",
        color=COLOR_SUCCESS,
        timestamp=_NOW(),
    ).set_footer(text=_FOOTER)


def error(description: str) -> discord.Embed:
    return discord.Embed(
        description=f"❌ {description}",
        color=COLOR_ERROR,
        timestamp=_NOW(),
    ).set_footer(text=_FOOTER)


def warn(description: str) -> discord.Embed:
    return discord.Embed(
        description=f"⚠️ {description}",
        color=COLOR_WARN,
        timestamp=_NOW(),
    ).set_footer(text=_FOOTER)


def info(description: str) -> discord.Embed:
    return discord.Embed(
        description=f"ℹ️ {description}",
        color=COLOR_INFO,
        timestamp=_NOW(),
    ).set_footer(text=_FOOTER)
