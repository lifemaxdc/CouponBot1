import discord
from discord.ext import commands, tasks
import feedparser
import os
import requests
from flask import Flask
from threading import Thread
from waitress import serve


REDDIT_RSS_URL = "https://www.reddit.com/r/Freebies/new/.rss"
ROLE_ID = "1102467235190153248"  # Replace with the role ID to ping (e.g., "123456789")

# Config - Don't change these
TOKEN = os.environ['DISCORD_TOKEN']  # Get from Render secrets
CHANNEL_ID = 1360707075818127471     # Your channel ID
RSS_URL = "https://www.slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"

# Add this BELOW your existing CHANNEL_ID (around line 7), this is used for the freebies posted elsewhere
REDDIT_CHANNEL_ID = 112233445566778899  # Replace with your target channel ID

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
posted_deals = set()  # Tracks posted deals to avoid duplicates



# ========= MESSAGE FORMATTING =========
def format_deal(entry):
    """Creates pretty Discord messages with images"""
    embed = discord.Embed(
        title=f"🛒 {entry.title[:200]}",  # Shortens long titles
        url=entry.link,
        color=0xFF6B00  # Orange color
    )
    
    if img_url := extract_image_url(entry):  # Walrus operator (Python 3.8+)
        embed.set_image(url=img_url)
    
    embed.set_footer(text="🔔 New Deal Alert")
    return embed

# ========= MAIN DEAL CHECKER =========
@tasks.loop(minutes=30)
async def check_deals():
    try:
        # Original Slickdeals logic (unchanged)
        slickdeals_channel = bot.get_channel(CHANNEL_ID)
        slickdeals_feed = feedparser.parse(RSS_URL)
        for entry in slickdeals_feed.entries[:5]:
            if entry.link not in posted_deals:
                await slickdeals_channel.send(embed=format_deal(entry))
                posted_deals.add(entry.link)
        
        # New Reddit logic (separate channel)
        reddit_channel = bot.get_channel(REDDIT_CHANNEL_ID)
        reddit_feed = feedparser.parse(REDDIT_RSS_URL)
        for entry in reddit_feed.entries[:5]:
            if entry.link not in posted_deals:
                message = f"<@&{ROLE_ID}> 🎁 **{entry.title}**\n{entry.link}"
                await reddit_channel.send(message)  # Sent to different channel!
                posted_deals.add(entry.link)
                
    except Exception as e:
        print(f"⚠️ Error: {e}")

# ========= DISCORD COMMANDS =========
@bot.command()
async def test(ctx):
    """Debug command"""
    await ctx.send("⚠️ This command is disabled")  # Immediate response

@bot.event
async def on_ready():
    keepalive.start()  # Fixed indentation
    print(f"🚀 Bot ready as {bot.user}")
    check_deals.start()  # Start the 30-minute timer

# ========= KEEP-ALIVE SERVER =========
@tasks.loop(minutes=4)
async def keepalive():
    try:
        requests.get("https://couponbot1-1.onrender.com")
    except:
        pass

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

Thread(target=lambda: serve(app, host='0.0.0.0', port=8080)).start()
bot.run(TOKEN)
