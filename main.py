import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai_client = genai.Client(api_key=GEMINI_API_KEY)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print("online")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return