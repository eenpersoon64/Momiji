import asyncio

import discord
import youtube_dl

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "data/%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "source_address": "0.0.0.0"
}

ffmpeg_options = {
    "options": "-vn"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


async def is_dj(ctx):
    if not ctx.author.voice:
        return False
    if not (ctx.author.voice.channel.permissions_for(ctx.message.author)).priority_speaker:
        return False
    return True


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="m_join", brief="Join a voice channel", description="")
    @commands.check(is_dj)
    async def m_join(self, ctx):
        pass

    @commands.command(name="m_leave", brief="Disconnect from a voice channel", description="")
    @commands.check(is_dj)
    async def m_leave(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command(name="m_play", brief="Plays from a url (almost anything youtube_dl supports)", description="")
    @commands.check(is_dj)
    async def m_play(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print("Player error: %s" % e) if e else None)
        await ctx.send(f"Now playing: `{player.title}`")

    @commands.command(name="m_stream",
                      brief="Streams from a url",
                      description="Same as m_play, but doesn't pre-download")
    @commands.check(is_dj)
    async def m_stream(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print("Player error: %s" % e) if e else None)

        await ctx.send(f"Now playing: `{player.title}`")

    @commands.command(name="m_stop", brief="Stop the music", description="")
    @commands.check(is_dj)
    async def m_stop(self, ctx):
        ctx.voice_client.stop()

    @m_play.before_invoke
    @m_stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Music(bot))
