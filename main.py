import discord
from discord.ext import commands, tasks
import feedparser
import re
import os
from flask import Flask
from threading import Thread

# Config
TOKEN = os.environ['DISCORD_TOKEN']  # From Replit Secrets
CHANNEL_ID = 1360707075818127471
RSS_URL = "https://www.slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
posted_deals = set()

def extract_image_url(entry):
    """Extract image URL using multiple methods"""
    # 1. Check RSS enclosure links (original working method)
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.rel == 'enclosure' and 'image' in link.type:
                return link.href
    
    # 2. Parse from description HTML (newer method)
    if 'description' in entry:
        img_match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
        if img_match:
            return img_match.group(1)
    
    # 3. Check media content (fallback)
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if media.get('medium') == 'image':
                return media['url']
    
    return None

def format_deal(entry):
    """Create beautiful embed with image"""
    embed = discord.Embed(
        title=f"🛒 {entry.title[:200]}" if len(entry.title) > 200 else f"🛒 {entry.title}",
        url=entry.link,
        color=0xFF6B00  # Slickdeals orange
    )
    
    # Add image if available
    image_url = extract_image_url(entry)
    if image_url:
        embed.set_image(url=image_url)
    
    embed.set_footer(text="🔔 New Deal Alert")
    return embed

@tasks.loop(minutes=30)
async def check_deals():
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Channel not found! Check CHANNEL_ID")
            return
            
        feed = feedparser.parse(RSS_URL)
        
        if not feed.entries:
            print("⚠️ No deals found in RSS feed")
            return
            
        new_deals = 0
        for entry in feed.entries[:5]:  # Process 5 newest deals
            if entry.link not in posted_deals:
                try:
                    await channel.send(embed=format_deal(entry))
                    posted_deals.add(entry.link)
                    new_deals += 1
                    print(f"✅ Posted: {entry.title[:50]}...")
                except Exception as e:
                    print(f"❌ Failed to post deal: {e}")
                    
        print(f"📊 Found {len(feed.entries)} deals | Posted {new_deals} new")
        
    except Exception as e:
        print(f"⚠️ RSS check failed: {e}")

@bot.command()
async def test(ctx):
    """Manual trigger for testing"""
    await check_deals()
    await ctx.send("✅ Manual check complete!")

@bot.event
async def on_ready():
    print(f"🚀 Bot ready as {bot.user}")
    check_deals.start()

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"
keep_alive = Thread(target=app.run, kwargs={'host':'0.0.0.0','port':8080})
keep_alive.start()

bot.run(TOKEN)

