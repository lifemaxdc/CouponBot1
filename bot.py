import discord
import asyncio
import feedparser
import requests

# ---- CONFIG ----
DISCORD_TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
REDDIT_RSS = 'https://www.reddit.com/r/Freebies/new/.rss'
SLICKDEALS_RSS = 'https://slickdeals.net/newsearch.php?mode=popdeals&searcharea=deals&searchin=first&rss=1'
REDDIT_CHANNEL_ID = 123456789012345678  # Replace with your channel ID
SLICKDEALS_CHANNEL_ID = 987654321098765432  # Replace with your channel ID

# ---- Setup ----
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
posted_entries = set()

# ---- Feed Formatters ----
def format_reddit(entry):
    return f"**{entry.title}**\n{entry.link}"

def format_slickdeals(entry):
    return f"**{entry.title}**\n{entry.link}"

# ---- Feed Checker ----
async def check_feeds():
    await bot.wait_until_ready()

    while not bot.is_closed():
        print("🔄 Checking feeds...")

        try:
            # --- Reddit ---
            print("📡 Fetching Reddit RSS...")
            reddit_channel = bot.get_channel(REDDIT_CHANNEL_ID)
            if not reddit_channel:
                print("❌ Reddit channel not found.")
            else:
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(REDDIT_RSS, headers=headers)
                reddit_feed = feedparser.parse(res.content)
                print(f"📥 Found {len(reddit_feed.entries)} Reddit entries")

                for entry in reddit_feed.entries[:5]:
                    entry_id = f"reddit_{entry.id}"
                    if entry_id not in posted_entries:
                        await reddit_channel.send(format_reddit(entry))
                        print(f"✅ Posted Reddit: {entry.title[:60]}")
                        posted_entries.add(entry_id)

        except Exception as e:
            print(f"❌ Reddit error: {e}")

        try:
            # --- Slickdeals ---
            print("📡 Fetching Slickdeals RSS...")
            slickdeals_channel = bot.get_channel(SLICKDEALS_CHANNEL_ID)
            if not slickdeals_channel:
                print("❌ Slickdeals channel not found.")
            else:
                feed = feedparser.parse(SLICKDEALS_RSS)
                print(f"📥 Found {len(feed.entries)} Slickdeals entries")

                for entry in feed.entries[:5]:
                    entry_id = f"slick_{entry.id}"
                    if entry_id not in posted_entries:
                        await slickdeals_channel.send(format_slickdeals(entry))
                        print(f"✅ Posted Slickdeals: {entry.title[:60]}")
                        posted_entries.add(entry_id)

        except Exception as e:
            print(f"❌ Slickdeals error: {e}")

        await asyncio.sleep(1800)  # 30 minutes

# ---- Start Bot ----
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

bot.loop.create_task(check_feeds())
bot.run(DISCORD_TOKEN)
