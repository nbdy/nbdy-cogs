from redbot.core.bot import Red
from .movethestreamer import MoveTheStreamer


async def setup(bot: Red):
    await bot.add_cog(MoveTheStreamer(bot))
