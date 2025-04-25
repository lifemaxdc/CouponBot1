import discord
from discord.ext import commands, tasks
import feedparser
import os
from flask import Flask
from threading import Thread
from waitress import serve

# Config - Don't change these
TOKEN = os.environ['DISCORD_TOKEN']  # Get from Render secrets
CHANNEL_ID = 1360707075818127471     # Your channel ID
RSS_URL = "https://www.slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
posted_deals = set()  # Tracks posted deals to avoid duplicates

# ========= IMAGE EXTRACTION =========
def extract_image_url(entry):
    """Simplified image finder - checks 3 places for images"""
    # 1. Check for direct image links (most reliable)
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.rel == 'enclosure' and 'image' in link.type:
                return link.href
    
    # 2. Check description HTML (common for Slickdeals)
    if 'description' in entry:
        if 'img src="' in entry.description:
            start = entry.description.find('img src="') + 9
            end = entry.description.find('"', start)
            return entry.description[start:end]
    
    # 3. Check media attachments (fallback)
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'image' in media.get('medium', ''):
                return media['url']
    
    return None  # No image found

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
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            return  # Silently skip if channel is wrong
            
        feed = feedparser.parse(RSS_URL)
        
        for entry in feed.entries[:5]:  # Only check 5 newest deals
            if entry.link not in posted_deals:
                await channel.send(embed=format_deal(entry))
                posted_deals.add(entry.link)
                
    except Exception as e:
        print(f"⚠️ Error (will retry): {e}")

# ========= DISCORD COMMANDS =========
@bot.command()
async def test(ctx):
    """Debug command"""
    await ctx.send("⚠️ This command is disabled")  # Immediate response

@bot.event
async def on_ready():
    print(f"🚀 Bot ready as {bot.user}")
    check_deals.start()  # Start the 30-minute timer

# ========= KEEP-ALIVE SERVER =========
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

Thread(target=lambda: serve(app, host='0.0.0.0', port=8080)).start()
bot.run(TOKEN)
