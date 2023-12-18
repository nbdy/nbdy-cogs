from redbot.core.commands import Cog, Context, admin_or_permissions, hybrid_command, commands
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

    @commands.group()
    async def movethestreamer(self, ctx: Context) -> None:
        pass

    @movethestreamer.command(name="add")
    async def _movethestreamer_add(self, ctx: Context, name: str, channel: str) -> None:
        member = utils.get(ctx.guild.members, name=name)
        if not member:
            await ctx.send(f"Could not find user '{name}'.")
            return

        channel = utils.get(ctx.guild.channels, name=channel)
        if not channel:
            await ctx.send(f"Could not find channel '{channel}'.")
            return

        channel_map = self.get_channel_map()
        if member.name not in channel_map.keys():
            channel_map[member.name] = channel.name
            self.config.channel_map.set(channel_map)
            await ctx.send(f"Moving '{member.name}' to '{channel.name}' when they start streaming.")
        else:
            await ctx.send(f"User '{member.name}' already mapped to channel '{channel.name}'.")

    @movethestreamer.command(name="del")
    async def _movethestreamer_del(self, ctx: Context, name: str) -> None:
        member = utils.get(ctx.guild.members, name=name)
        if not member:
            await ctx.send(f"Could not find user '{name}'.")
            return

        channel_map = self.get_channel_map()
        if member.name in channel_map.keys():
            channel = channel_map[member.name]
            del channel_map[member.name]
            await ctx.send(f"User '{member.name}' will not be moved to channel '{channel}' when they start streaming.")
        else:
            await ctx.send(f"User '{member.name}' is not mapped to any channel.")

    @movethestreamer.command(name="list")
    async def _movethestreamer_list(self, ctx: Context) -> None:
        channel_map = self.get_channel_map()
        text = "Users who will be automatically moved to another channel as soon as they start streaming:\n"
        for k, v in channel_map.items():
            text += f"{k} -> {v}\n"
        await ctx.send(text)

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
                reason = self.config.reason()
                await before.move_to(channel, reason=reason)
                await before.send(reason)
