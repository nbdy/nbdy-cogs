from redbot.core.commands import Cog, Context, admin_or_permissions, hybrid_command
from redbot.core import Config
from redbot.core.bot import Red
from discord import Member, ActivityType, utils
from logging import getLogger

log = getLogger("red.nbdy-cogs.movethestreamer")


class MoveTheStreamer(Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            42069,
            cog_name="MoveTheStreamer",
            force_registration=True
        )
        self.config.register_global(
            channel_map={},
            seperator=":",
            reason="Automatically moved to your streaming channel since you started streaming."
        )

    async def cog_load(self) -> None:
        await super().cog_load()

    def get_channel_map(self) -> dict[str, str]:
        return self.config.channel_map()

    def get_user_channel(self, text: str) -> tuple[str, str]:
        user, channel = text.split(self.config.seperator())
        return user, channel

    @hybrid_command()
    @admin_or_permissions()
    async def add_twitch_channel(self, ctx: Context, *, text: str = None):
        if text:
            channel_map = self.get_channel_map()
            user, channel = self.get_user_channel(text)
            if user not in channel_map.keys():
                channel_map[user] = channel
                self.config.channel_map.set(channel_map)
                await ctx.send(f"Moving '{user}' to '{channel_map[user]}' when they start streaming.")
            else:
                await ctx.send(f"User already mapped to channel '{channel_map[user]}'.")
        else:
            await ctx.send("Please provide a user:channel combination.")

    @hybrid_command()
    @admin_or_permissions()
    async def del_twitch_channel(self, ctx: Context, *, text: str = None):
        if text:
            channel_map = self.get_channel_map()
            user = text
            if user in channel_map.keys():
                del channel_map[user]
                self.config.channel_map.set(channel_map)
                await ctx.send(f"'{user}' will not be moved to '{channel_map[user]}' when they start streaming.")
            else:
                await ctx.send(f"'{user}' is not mapped to any channel yet.")
        else:
            await ctx.send("Please provide a user.")

    @Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        activity_change = before.activity != after.activity
        activity_str = "streaming" if after.activity == ActivityType.streaming else "stopped streaming"
        if activity_change:
            log.debug(f"User {before.name} {activity_str}")
            channel_map = self.get_channel_map()
            ctx = await self.bot.get_context(after)
            if before.name in channel_map.keys():
                channel = await utils.get(ctx.guild.channels, name=channel_map[before.name])
                await before.move_to(channel, reason=self.config.reason())
