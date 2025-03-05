import os
import discord
from discord.ext import commands
from google import genai
from google.genai import types
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import server_data
from filter import set_last_message, check_repeat_message, check_profanity, call_smalltalk_is_http
from server_data import init_server_ruleset

from dotenv import load_dotenv
load_dotenv()
DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
MONGODB_URI = os.environ.get('MONGODB_URI')

import ruleset
from moderation import Moderation

genai_client = genai.Client(api_key=GEMINI_API_KEY)
mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)
modActions: Moderation = Moderation(bot)

config = types.GenerateContentConfig(tools=[modActions.timeout, modActions.kick, modActions.ban])

@bot.event
async def on_ready():
    await bot.add_cog(modActions)
    #print("online")


@bot.event
async def on_guild_join(guild):
    #print("Joining: " + str(guild.id))
    init_server_ruleset(mongo_client, guild.id)


@bot.event
async def on_message(ctx):
    """
    Checks every message, filters profanity, links, and messages against the ruleset

    Parameters:
    ctx: Context of the message

    Returns:
    None
    """
    if ctx.author != bot.user:
        #print(ctx)
        #print(f"{ctx.author} said: {ctx.content}")
        if check_profanity(mongo_client, ctx.content):
            await ctx.author.send(f"Please don't swear! Content: {ctx.content}")
            await ctx.delete()

        if call_smalltalk_is_http(ctx.content):
            await ctx.author.send(f"Don't send links in chat. Content: {ctx.content}")
            await ctx.delete()

        repeated_message = check_repeat_message(mongo_client, ctx.author.id, ctx.guild.id, ctx.content)
        if repeated_message:
            #print(str(ctx.author) + " said " + ctx.content + " multiple times!")
            try:
                await ctx.author.send(f"Please don't spam! Content: {ctx.content}")
            except:
                pass
            finally:
                await ctx.delete()
        set_last_message(mongo_client, ctx.author.id, ctx.guild.id, ctx.content)
        await bot.process_commands(ctx)
        if(ctx.content[0]!="-"):
            ctx = await bot.get_context(ctx)
            await judge(ctx, string=ctx.message.content)

#@bot.command()
async def judge(ctx, *, string: str = ""):
    """
    Uses Gemini to judge a user's message against the server's ruleset

    Parameters:
    ctx: the command context
    string: the message to judge

    Returns:
    None
    """
    prompt = server_data.get_server_ruleset(mongo_client, ctx.guild.id)
    punishment = genai_client.models.generate_content(model="gemini-2.0-flash-lite", contents=prompt + "\nUser, "+str(ctx.author)+" says:"+string+"\nDecide none or a punishment for this user's message based on the rules. Respond only with 'none', 'kick', 'ban', or 'timeout'. Respond with 'none' if the message is not againt the rules. If the message is against the rules, select from timeout, kick, and ban, with the severity increasing in that order. Followed by a colon ':' and a brief reason for the punishment in under 100 characters.")
    reason = punishment.text.split(':')
    #print(reason)
    if reason[0].lower() != "none\n":
        await modActions.delete_message(ctx, ctx.message.id, reason=reason[1])
        await punish(ctx, reason[0], ctx.author, reason[1])


async def punish(ctx, message: str, user: discord.User, reason: str):
    """
    Punishes the user based off of Gemini's judgement

    Parameters:
    message: the message to be judged if timeout is the punishment
    user: the user to punish
    reason: the reason for the punishment provided by Gemini

    Returns:
    None
    """
    ctx.author = "Orwell"
    if message.lower() == 'kick':
        await modActions.kick(ctx, user, reason=reason)
    elif message.lower() == 'ban':
        await modActions.ban(ctx, user, reason=reason)
    elif message.lower() == 'timeout':
        prompt = server_data.get_server_ruleset(mongo_client, ctx.guild.id)
        time = genai_client.models.generate_content(model="gemini-2.0-flash-lite", contents = prompt+"User, "+str(ctx.author)+" says:"+str(ctx.message)+"Respond only with a time formatted as 'Days:Hours:Minutes' (for example '0:2:30') based on how long you think the user should be timed out for this offense.")
        times = time.text.split(':')
        #print(times)
        try:
            await modActions.timeout(ctx, user, int(times[0]), int(times[1]), int(times[2]), reason=reason)
        except Exception as e:
            print("Error timing user out: " + e)
    elif message.lower() == 'none':
        return

ruleset.setup(bot)
bot.run(DISCORD_API_KEY)
