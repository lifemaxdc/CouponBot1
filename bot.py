import discord
from discord.ext import commands, tasks
import feedparser
import os
import requests
from flask import Flask
from threading import Thread
from waitress import serve

# Config - Don't change these
TOKEN = os.environ['DISCORD_TOKEN']
SLICKDEALS_CHANNEL_ID = 1360707075818127471  # Your existing deals channel
REDDIT_CHANNEL_ID = 112233445566778899      # New channel for freebies
REDDIT_ROLE_ID = 1102467235190153248        # Role to ping for freebies

# RSS Feeds
SLICKDEALS_RSS = "https://www.slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"
REDDIT_RSS = "https://www.reddit.com/r/Freebies/new/.rss"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
posted_entries = set()  # Tracks all posted deals

# ========= ORIGINAL SLICKDEALS EMBED FORMATTING =========
def format_slickdeals(entry):
    """Your beautiful existing embed format for Slickdeals"""
    embed = discord.Embed(
        title=f"🛒 {entry.title[:200]}",
        url=entry.link,
        color=0xFF6B00  # Orange
    )
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.rel == 'enclosure' and 'image' in link.type:
                embed.set_image(url=link.href)
                break
    embed.set_footer(text="🔔 New Deal Alert")
    return embed

# ========= SIMPLE REDDIT FORMATTING =========
def format_reddit(entry):
    """Clean text format for Reddit posts"""
    return f"<@&{REDDIT_ROLE_ID}> 🎁 **{entry.title}**\n{entry.link}"

@tasks.loop(minutes=30)
async def check_feeds():
    try:
        # 1. Process Slickdeals (with your original embeds)
        channel = bot.get_channel(SLICKDEALS_CHANNEL_ID)
        feed = feedparser.parse(SLICKDEALS_RSS)
        for entry in feed.entries[:5]:
            if entry.link not in posted_entries:
                await channel.send(embed=format_slickdeals(entry))
                posted_entries.add(f"slickdeals_{entry.link}")

        # 2. Process Reddit (simple text + role ping)
        reddit_channel = bot.get_channel(REDDIT_CHANNEL_ID)
        reddit_feed = feedparser.parse(REDDIT_RSS)
        for entry in reddit_feed.entries[:5]:
            if entry.id not in posted_entries:
                await reddit_channel.send(format_reddit(entry))
                posted_entries.add(f"reddit_{entry.id}")
                
    except Exception as e:
        print(f"⚠️ Error: {str(e)[:200]}")

# ========= KEEP YOUR EXISTING COMMANDS/EVENTS =========
@bot.event
async def on_ready():
    print(f"🚀 Bot ready as {bot.user}")
    check_feeds.start()

# Keep your existing keep-alive and bot.run() code below
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

Thread(target=lambda: serve(app, host='0.0.0.0', port=8080)).start()
bot.run(TOKEN)
