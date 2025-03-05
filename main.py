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
    #print(message)
    if message.author == bot.user:
        return
    if(contains_link(message.content)==False):
        if(message.author.nick==None):
            last5.append("["+message.author.global_name+"]: "+message.content+"\n")
        else:
            last5.append("["+message.author.nick+"]: "+message.content+"\n")
    if ascii_sum(message.content)%3==0:
        orwell=response()
        await message.channel.send(orwell)

bot.run(DISCORD_API_KEY)