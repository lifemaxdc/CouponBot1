import discord
from discord.ext import commands, tasks
import feedparser
import os
import requests
from flask import Flask
from threading import Thread
from waitress import serve

# Config - Replace these with your values
TOKEN = os.environ['DISCORD_TOKEN']
SLICKDEALS_CHANNEL_ID = 1360707075818127471  # Your main deals channel
REDDIT_CHANNEL_ID = 112233445566778899      # Channel for freebies
REDDIT_ROLE_ID = 1102467235190153248        # Role to ping for freebies

# RSS Feeds
SLICKDEALS_RSS = "https://www.slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"
REDDIT_RSS = "https://www.reddit.com/r/Freebies/new/.rss"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
posted_entries = set()  # Tracks all posted deals to avoid duplicates

@tasks.loop(minutes=30)
async def check_feeds():
    try:
        # 1. Check Slickdeals (simple text format)
        slickdeals_channel = bot.get_channel(SLICKDEALS_CHANNEL_ID)
        slickdeals_feed = feedparser.parse(SLICKDEALS_RSS)
        for entry in slickdeals_feed.entries[:5]:  # Only newest 5
            if entry.link not in posted_entries:
                await slickdeals_channel.send(f"🛒 **{entry.title}**\n{entry.link}")
                posted_entries.add(f"slickdeals_{entry.link}")  # Prefix avoids ID conflicts

        # 2. Check Reddit Freebies (with role ping)
        reddit_channel = bot.get_channel(REDDIT_CHANNEL_ID)
        reddit_feed = feedparser.parse(REDDIT_RSS)
        for entry in reddit_feed.entries[:5]:
            if entry.id not in posted_entries:
                await reddit_channel.send(f"<@&{REDDIT_ROLE_ID}> 🎁 **{entry.title}**\n{entry.link}")
                posted_entries.add(f"reddit_{entry.id}")  # Use Reddit's unique ID
                
    except Exception as e:
        print(f"⚠️ Error: {e}")

@bot.event
async def on_ready():
    print(f"🚀 Bot ready as {bot.user}")
    check_feeds.start()

# Keep-alive server (for Replit/Render)
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

Thread(target=lambda: serve(app, host='0.0.0.0', port=8080)).start()
bot.run(TOKEN)
