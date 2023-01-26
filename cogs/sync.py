import discord
from discord.ext import commands
from typing import Literal, Optional

class syncCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    #@checks.is_owner:
    @commands.hybrid_command(
        title='sync',
        description='reload all cogs',
    )
    async def sync(self, context: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None):

        if not guilds:
            if spec == "~":
                synced = await context.bot.tree.sync(guild=context.guild)
            elif spec == "*":
                context.bot.tree.copy_global_to(guild=context.guild)
                synced = await context.bot.tree.sync(guild=context.guild)
            elif spec == "^":
                context.bot.tree.clear_commands(guild=context.guild)
                await context.bot.tree.sync(guild=context.guild)
                synced = []
            else:
                synced = await context.bot.tree.sync()

            print(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild'}.", __name__)
            await context.reply(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild'}.")
            return

        ret = 0
        for guild in guilds:
            try:
                await context.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        print(f"Synced the tree to {ret}/{len(guilds)}.", __name__)
        await context.reply(f"Synced the tree to {ret}/{len(guilds)}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(syncCommand(bot))
