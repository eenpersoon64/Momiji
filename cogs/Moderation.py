from discord.ext import commands
from modules import permissions


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", brief="Purge X amount of messages", description="")
    @commands.guild_only()
    async def purge(self, ctx, amount, author=None):
        # TODO: make this more usable
        if not (ctx.channel.permissions_for(ctx.message.author)).manage_messages:
            await ctx.send("lol no")
            return None

        if not amount.isdigit():
            return None

        try:
            await ctx.message.delete()
            if len(ctx.message.mentions) > 0:
                for one_member in ctx.message.mentions:
                    async with ctx.channel.typing():
                        def is_user(m):
                            if m.author == one_member:
                                return True
                            else:
                                return False

                        deleted = await ctx.channel.purge(limit=int(amount), check=is_user)
                    await ctx.send(f"Deleted {len(deleted)} message(s) by {one_member.display_name}")
            else:
                async with ctx.channel.typing():
                    deleted = await ctx.channel.purge(limit=int(amount))
                await ctx.send(f"Deleted {len(deleted)} message(s)")
        except Exception as e:
            await ctx.send(e)

    @commands.command(name="regex_purge", brief="Purge X amount of messages with regex checks", description="")
    @commands.guild_only()
    @commands.check(permissions.is_admin)
    async def regex_purge(self, ctx, amount, string):
        # TODO: this is just a placeholder

        if not amount.isdigit():
            return None

        try:
            await ctx.message.delete()
            async with ctx.channel.typing():
                def the_check(m):
                    if string in m.content:
                        return True
                    else:
                        return False

                deleted = await ctx.channel.purge(limit=int(amount), check=the_check)
            await ctx.send(f"Deleted {len(deleted)} message(s)")
        except Exception as e:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Moderation(bot))
