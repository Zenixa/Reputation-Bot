import discord, sqlite3
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context
from tqdm import tqdm
from typing import List
from datetime import date
import string,random,json,sys,os, time, asyncio

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

zenixa = 997643229593866370

# Here we name the cog and create a new class for the cog.
class General(commands.Cog, name="general"):
    def __init__(self, bot):
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    @commands.hybrid_command(
        name="config",
        description="Configure the guild settings for the bot (admin only)",
    )
    @commands.has_permissions(administrator=True)
    async def settings(self, context: Context, reputation_channel: discord.TextChannel):
        connection = sqlite3.connect("database/database.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM servers WHERE server_id=?", (context.guild.id,))
        abc = cursor.fetchone()
        
        
        if abc[0] == None:
            cursor.execute("""INSERT INTO servers
                (server_id)
                VALUES
                (?)""", (context.guild.id,))
            connection.commit()
            cursor.execute("UPDATE servers SET reputation_channel_id=? WHERE server_id=?", (reputation_channel.id, context.guild.id,))
            connection.commit()
            await context.send(f"Set {reputation_channel.mention} as the reputation channel.\n(+/-)rep(s) will only work in that channel.", delete_after=10)
            connection.close()
        else:
            cursor.execute("UPDATE servers SET reputation_channel_id=? WHERE server_id=?", (reputation_channel.id, context.guild.id,))
            connection.commit()
            await context.send(f"Set {reputation_channel.mention} as the reputation channel.\n(+/-)rep(s) will only work in that channel.", delete_after=10)
            connection.close()

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(General(bot))
