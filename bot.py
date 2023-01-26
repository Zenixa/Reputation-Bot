""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 5.1
"""

import asyncio
import json
import os
import platform
import random
import sys
import time
import requests
import sqlite3

from contextlib import closing

import discord
from discord import Interaction
from discord.ext import tasks, commands
from discord.ext.commands import Bot
from discord.ext.commands import Context

import exceptions

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

"""	
Setup bot intents (events restrictions)
For more information about intents, please go to the following websites:
https://discordpy.readthedocs.io/en/latest/intents.html
https://discordpy.readthedocs.io/en/latest/intents.html#privileged-intents


Default Intents:
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True

Privileged Intents (Needs to be enabled on developer portal of Discord), please use them only if you need them:
intents.members = True
intents.message_content = True
intents.presences = True
"""

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

"""
Uncomment this if you don't want to use prefix (normal) commands.
It is recommended to use slash commands and therefore not use prefix commands.

If you want to use prefix commands, make sure to also enable the intent below in the Discord developer portal.
"""
# intents.message_content = True

bot = Bot(command_prefix=commands.when_mentioned_or(config["prefix"]), intents=intents, help_command=None)


"""
Create a bot variable to access the config file in cogs so that you don't need to import it every time.

The config is available using the following code:
- bot.config # In this file
- self.bot.config # In cogs
"""
bot.config = config

@bot.event
async def on_ready() -> None:
    """
    The code in this even is executed when the bot is ready
    """
    print(f"Logged in as {bot.user.name}")
    print(f"discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    print("-------------------")
    status_task.start()
    #### bg tasks go here
    await bot.tree.sync()

@tasks.loop(minutes=1.0)
async def status_task() -> None:
    await asyncio.sleep(1)

@bot.event
async def on_message(message: discord.Message) -> None:
    
    if message.author == bot.user or message.author.bot:
        return
    
    def unixStampMaker(hours: int):
        unix_now = int(time.time())
        val = 3600 * hours
        return unix_now + val
        
    def isCooldownExpired(author_userid: int, target_userid: int):
        connection = sqlite3.connect("database/database.db")
        cursor = connection.cursor()
        cursor.execute("SELECT cooldown FROM cooldown WHERE author_userid=? AND target_userid=?", (author_userid, target_userid,))
        search = str(cursor.fetchone()).replace("(", "").replace(",", "").replace(")", "")
        if search != "None":
            if int(search) < int(time.time()):
                cursor.execute("DELETE FROM cooldown WHERE cooldown=?", (int(search),))
                connection.commit()
                connection.close()
                return True
            else:
                connection.close()
                return False
        else:
            return True
    
    usageEmbed = discord.Embed(
                    title="Command Usage",
                    description="""`+rep <user mention>` will give the mentioned user +1 rep
`-rep <user mention>` will give the mentioned user -1 rep
`Cooldown Usage` **1 Hour**, you can only +rep/-rep a specific user once an hour"""
                )
    
    if not message.guild:
        ##### message came from dm
        return
    
    else:
        guildExistsInDB = False
        rep_channel_id = 0
        
        connection = sqlite3.connect("database/database.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM servers WHERE server_id=?", (message.guild.id,))
        zxc = cursor.fetchone()
        #print(zxc)
        
        if zxc != None:
            guildExistsInDB = True
            rep_channel_id = zxc[1]
        else:
            cursor.execute("""INSERT INTO servers
            (server_id)
            VALUES
            (?)
            """, (message.guild.id,))
            connection.commit()
            
        connection.close()
        
        
        if message.channel.id == rep_channel_id:
            if message.content.startswith("+rep ") and message.mentions:
                #await message.reply(f"found a mention\nuser {}")
                mentioned_user = message.mentions[0]
                
                if mentioned_user.id == message.author.id:
                    await message.reply("You cannot +rep yourself.", delete_after=3)
                    await message.delete()
                    return
                
                connection = sqlite3.connect('database/database.db')
                cursor = connection.cursor()
                search = '''SELECT * FROM reps WHERE discord_userid=?'''
                cursor.execute(search, (mentioned_user.id,))
                result = cursor.fetchone()
                if isCooldownExpired(author_userid=message.author.id, target_userid=mentioned_user.id) == False:
                    cursor.execute("SELECT cooldown FROM cooldown WHERE author_userid=? AND target_userid=?", (message.author.id, mentioned_user.id,))
                    tmstmp = int(str(cursor.fetchone()).replace("(", "").replace(",", "").replace(")", ""))
                    await message.reply(f"You cannot +rep this user, try again <t:{tmstmp}:R>", delete_after=3)
                    return
                else:
                    connection = sqlite3.connect("database/database.db")
                    cursor = connection.cursor()
                    cursor.execute("UPDATE cooldown SET cooldown=? WHERE author_userid=? AND target_userid=?", (1, message.author.id, mentioned_user.id,))
                    connection.commit()
                
                if result == None:
                    #TODO: make it add user to database here, UPDATE: DONE
                    cursor.execute("""INSERT INTO reps
                          (discord_userid, reps) 
                           VALUES 
                          (?, 1)""", (mentioned_user.id,))
                    connection.commit()
                    cursor.execute("""INSERT INTO cooldown
                        (author_userid, target_userid, cooldown)
                        VALUES
                        (?,?,?)""", (message.author.id, mentioned_user.id, unixStampMaker(1)))
                    connection.commit()
                    await message.reply(f"Gave **+1** rep to {mentioned_user.mention}")
                else:
                    reps = result[1]
                    cursor.execute("UPDATE reps SET reps=? WHERE discord_userid=?", (reps+1, mentioned_user.id))
                    connection.commit()
                    cursor.execute("""INSERT INTO cooldown
                        (author_userid, target_userid, cooldown)
                        VALUES
                        (?,?,?)""", (message.author.id, mentioned_user.id, unixStampMaker(1)))
                    connection.commit()
                    await message.reply(f"Gave **+1** rep to {mentioned_user.mention}")
                
                try:
                    connection.close()
                except:
                    pass
            elif message.content.startswith("-rep ") and message.mentions:
                mentioned_user = message.mentions[0]
                if mentioned_user.id == message.author.id:
                    await message.reply("You cannot -rep yourself.", delete_after=3)
                    await message.delete()
                    return
                
                connection = sqlite3.connect('database/database.db')
                cursor = connection.cursor()
                search = '''SELECT * FROM reps WHERE discord_userid=?'''
                cursor.execute(search, (mentioned_user.id,))
                result = cursor.fetchone()
                if isCooldownExpired(author_userid=message.author.id, target_userid=mentioned_user.id) == False:
                    cursor.execute("SELECT cooldown FROM cooldown WHERE author_userid=? AND target_userid=?", (message.author.id, mentioned_user.id,))
                    tmstmp = int(str(cursor.fetchone()).replace("(", "").replace(",", "").replace(")", ""))
                    await message.reply(f"You cannot +rep this user, try again <t:{tmstmp}:R>", delete_after=3)
                    return
                else:
                    connection = sqlite3.connect("database/database.db")
                    cursor = connection.cursor()
                    cursor.execute("UPDATE cooldown SET cooldown=? WHERE author_userid=? AND target_userid=?", (1, message.author.id, mentioned_user.id,))
                    connection.commit()
                    
                if result == None:
                    #TODO: make it add user to database here, UPDATE: DONE
                    cursor.execute("""INSERT INTO reps
                          (discord_userid, reps) 
                           VALUES 
                          (?, -1)""", (mentioned_user.id,))
                    connection.commit()
                    cursor.execute("""INSERT INTO cooldown
                        (author_userid, target_userid, cooldown)
                        VALUES
                        (?,?,?)""", (message.author.id, mentioned_user.id, unixStampMaker(1)))
                    connection.commit()
                    await message.reply(f"Removed **1** rep from {mentioned_user.mention}")
                else:
                    reps = result[1]
                    cursor.execute("UPDATE reps SET reps=? WHERE discord_userid=?", (reps-1, mentioned_user.id))
                    connection.commit()
                    cursor.execute("""INSERT INTO cooldown
                        (author_userid, target_userid, cooldown)
                        VALUES
                        (?,?,?)""", (message.author.id, mentioned_user.id, unixStampMaker(1)))
                    connection.commit()
                    #connection.close()
                    await message.reply(f"Removed **1** rep from {mentioned_user.mention}")
            elif message.content.startswith("?reps ") and message.mentions:
                mentioned_user = message.mentions[0]
                connection = sqlite3.connect("database/database.db")
                cursor = connection.cursor()
                cursor.execute(f"SELECT reps FROM reps WHERE discord_userid=?", (mentioned_user.id,))
                search = str(cursor.fetchone()).replace("(", "").replace(",", "").replace(")", "")
                if search == None or search == "None":
                    DISCORD_EPOCH = 1420070400000
                    def convertSnowflakeToDate(snowflake: int):
                        abc = (snowflake >> 22)
                        return abc + int(time.time())
                    userInfo = discord.Embed(
                        title=f"**{mentioned_user}**"
                    )
                    userInfo.set_thumbnail(url=mentioned_user.avatar)
                    userInfo.add_field(name="Reps", value=f"{search}", inline=True)
                    import datetime
                    userRoles = []
                    for roles in mentioned_user.roles:
                        if roles.id == message.guild.id:
                            pass
                        else:
                            userRoles.append(f"<@&{roles.id}>")
                    userRolesStr = str(userRoles).replace("[", "").replace("'", "").replace("]", "").replace(",", "")
                    userInfo.add_field(name="Roles", value=f"{userRolesStr}", inline=True)
                    userInfo.add_field(name="Account Created On", value=f"<t:{int(datetime.datetime.timestamp(mentioned_user.created_at))}:F>", inline=True)
                    userInfo.add_field(name="Joined On", value=f"<t:{int(datetime.datetime.timestamp(mentioned_user.joined_at))}:F>", inline=True)
                    
                    await message.reply(embed=userInfo)
                    return
                else:
                    DISCORD_EPOCH = 1420070400000
                    def convertSnowflakeToDate(snowflake: int):
                        abc = (snowflake >> 22)
                        return abc + int(time.time())
                    userInfo = discord.Embed(
                        title=f"**{mentioned_user}**"
                    )
                    userInfo.set_thumbnail(url=mentioned_user.avatar)
                    userInfo.add_field(name="Reps", value=f"{search}", inline=True)
                    import datetime
                    userRoles = []
                    for roles in mentioned_user.roles:
                        if roles.id == message.guild.id:
                            pass
                        else:
                            userRoles.append(f"<@&{roles.id}>")
                    userRolesStr = str(userRoles).replace("[", "").replace("'", "").replace("]", "").replace(",", "")
                    userInfo.add_field(name="Roles", value=f"{userRolesStr}", inline=True)
                    userInfo.add_field(name="Account Created On", value=f"<t:{int(datetime.datetime.timestamp(mentioned_user.created_at))}:F>", inline=True)
                    userInfo.add_field(name="Joined On", value=f"<t:{int(datetime.datetime.timestamp(mentioned_user.joined_at))}:F>", inline=True)
                    userInfo.set_footer(text=f"ID: {mentioned_user.id}", icon_url="https://cdn.discordapp.com/attachments/1067850325739962380/1067950267871547493/image-4.png")
                    userInfo.color = mentioned_user.color
                    userInfo.timestamp = datetime.datetime.utcnow()
                    
                    await message.reply(embed=userInfo)
                    
                connection.close()
            elif message.content == "?rep":
                
                await message.reply(embed=usageEmbed, delete_after=10)
                await asyncio.sleep(10)
                await message.delete()
            elif message.content == "?reps":
                await message.reply(embed=usageEmbed, delete_after=10)
                await asyncio.sleep(10)
                await message.delete()
            elif message.content == "+rep":
                await message.reply(embed=usageEmbed, delete_after=10)
                await asyncio.sleep(10)
                await message.delete()
            elif message.content == "-rep":
                await message.reply(embed=usageEmbed, delete_after=10)
                await asyncio.sleep(10)
                await message.delete()
    await bot.process_commands(message)


@bot.event
async def on_command_completion(context: Context) -> None:
    """
    The code in this event is executed every time a normal command has been *successfully* executed
    :param context: The context of the command that has been executed.
    """
    full_command_name = context.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    if context.guild is not None:
        print(
            f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})")
    else:
        print(f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs")


@bot.event
async def on_command_error(context: Context, error) -> None:
    """
    The code in this event is executed every time a normal valid command catches an error
    :param context: The context of the normal command that failed executing.
    :param error: The error that has been faced.
    """
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(
            title="Hey, please slow down!",
            description=f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        """
        The code here will only execute if the error is an instance of 'UserBlacklisted', which can occur when using
        the @checks.not_blacklisted() check in your command, or you can raise the error by yourself.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are blacklisted from using the bot.",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserNotOwner):
        """
        Same as above, just for the @checks.is_owner() check.
        """
        embed = discord.Embed(
            title="Error!",
            description="You are not the owner of the bot!",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Error!",
            description="You are missing the permission(s) `" + ", ".join(
                error.missing_permissions) + "` to execute this command!",
            color=0xE02B2B
        )
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Error!",
            # We need to capitalize because the command arguments have no capital letter in the code.
            description=str(error).capitalize(),
            color=0xE02B2B
        )
        await context.send(embed=embed)
    raise error


async def load_cogs() -> None:
    """
    The code in this function is executed whenever the bot will start.
    """
    for file in os.listdir(f"./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}")


asyncio.run(load_cogs())
bot.run(config["token"])
