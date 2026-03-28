import discord
from discord.ext import commands
import yt_dlp
import asyncio

# Professional YDL Configuration
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'cookiefile': 'cookies.txt',
    'js_runtimes': {'node': {}},
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {} # Stores queues for every server {guild_id: [songs]}
        self.is_247 = {} # Stores 24/7 status {guild_id: True/False}

    def get_queue(self, ctx):
        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []
        return self.queue[ctx.guild.id]

    async def play_next(self, ctx):
        queue = self.get_queue(ctx)
        if len(queue) > 0:
            song = queue.pop(0)
            vc = ctx.voice_client
            
            # Use the URL to play
            vc.play(discord.FFmpegOpusAudio(song['url'], **FFMPEG_OPTIONS), 
                    after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            
            await ctx.send(f"🎶 **Now Playing:** {song['title']}")
        else:
            # If 24/7 is ON, we don't leave. If OFF, we wait 5 mins then leave.
            if not self.is_247.get(ctx.guild.id, False):
                await asyncio.sleep(300)
                if not vc.is_playing():
                    await vc.disconnect()

    @commands.command()
    async def play(self, ctx, *, search: str):
        # 1. Join Voice
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        # 2. Search Song
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                song = {'url': info['url'], 'title': info['title']}
            
            queue = self.get_queue(ctx)
            queue.append(song)

        # 3. Play or Queue
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
        else:
            await ctx.send(f"✅ Added to queue: **{song['title']}**")

    @commands.command()
    async def stay(self, ctx):
        """Toggles 24/7 mode"""
        self.is_247[ctx.guild.id] = not self.is_247.get(ctx.guild.id, False)
        status = "ENABLED" if self.is_247[ctx.guild.id] else "DISABLED"
        await ctx.send(f"🔘 **24/7 Mode is now {status}**")
async def setup(bot):
    await bot.add_cog(Music(bot))
