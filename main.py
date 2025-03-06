import os
from collections import deque
import discord
from discord.ext import commands
from google import genai
import re
from dotenv import load_dotenv
load_dotenv()

DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai_client = genai.Client(api_key=GEMINI_API_KEY)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)

last5=deque(maxlen=5)
frequency=7

with open('prompt.txt', 'r') as file:
    prompt=file.read()

def contains_link(message:str)->bool:
    url_pattern = re.compile(r"https?://\S+|www\.\S+")
    return bool(url_pattern.search(message))

def ascii_sum(message:str)->int:
    return sum(ord(char) for char in message)

def response()->str:
    messages=list(last5)
    messages="".join(messages)
    print(messages)
    return genai_client.models.generate_content(model="gemini-2.0-flash-lite", contents=(prompt+messages)).text

@bot.event
async def on_ready():
    print("online")

@bot.event
async def on_message(message):
    global frequency
    print(message.content)
    if message.author == bot.user:
        return
    if(contains_link(message.content)==False or not message.content.startswith("-")):
        if(message.author.nick==None):
            last5.append("["+message.author.global_name+" said]: "+message.content+"\n")
        else:
            last5.append("["+message.author.nick+" said]: "+message.content+"\n")
    if ascii_sum(message.content)%frequency==0 or "orwell" in message.content.lower():
        orwell=response()
        await message.channel.send(orwell)
    await bot.process_commands(message)

@bot.command()
async def freqmod(ctx, number:int):
    global frequency
    frequency=number

bot.run(DISCORD_API_KEY)