import json
from logging import getLogger

from discord import Member, ActivityType
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.commands import Cog, Context, commands

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
            channel_map=dict(),
            reason="Automatically moved to your streaming channel since you started streaming."
        )

    async def cog_load(self) -> None:
        await super().cog_load()

    @commands.group()
    async def movethestreamer(self, ctx: Context) -> None:
        pass

    @movethestreamer.command(name="add")
    async def _movethestreamer_add(self, ctx: Context, user_id: int, channel_id: int) -> None:
        if not ctx.guild:
            await ctx.send("Can't use this command with DM's")
            return

        user = self.bot.get_user(user_id)
        if not user:
            await ctx.send(f"Could not find user with id '{user_id}'.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            await ctx.send(f"Could not find channel with id '{channel}'.")
            return

        channel_map = await self.config.channel_map()
        if user.id not in channel_map.keys():
            channel_map[int(user.id)] = int(channel.id)
            await self.config.channel_map.set(channel_map)
            await ctx.send(f"Moving '{user.name}' to '{channel.name}' when they start streaming.")
        else:
            await ctx.send(f"User '{user.name}' already mapped to channel '{channel.name}'.")

    @movethestreamer.command(name="del")
    async def _movethestreamer_del(self, ctx: Context, user_id: int) -> None:
        if not ctx.guild:
            await ctx.send("Can't use this command with DM's")
            return

        user = self.bot.get_user(user_id)
        if not user:
            await ctx.send(f"Could not find user with id '{user_id}'.")
            return

        channel_map = await self.config.channel_map()
        if user.id in channel_map.keys():
            channel_id = channel_map[user.id]
            channel = self.bot.get_channel(channel_id)
            del channel_map[user.id]
            await self.config.channel_map.set(channel_map)
            await ctx.send(f"'{user.name}' will not be moved to '{channel.name}' when they start streaming.")
        else:
            await ctx.send(f"'{user.name}' is not mapped to any channel.")

    @movethestreamer.command(name="clear")
    async def _movethestreamer_clear(self, ctx: Context) -> None:
        await self.config.channel_map.set(dict())
        await ctx.send("Removed all user to channel mappings.")

    @movethestreamer.command(name="list")
    async def _movethestreamer_list(self, ctx: Context) -> None:
        channel_map = await self.config.channel_map()
        text = "Users who will be automatically moved to another channel as soon as they start streaming:\n"
        for k, v in channel_map.items():
            user = self.bot.get_user(k)
            channel = self.bot.get_channel(v)
            user_name = user.name if user else k
            channel_name = channel.name if channel else v
            text += f"{user_name} -> {channel_name}\n"
        await ctx.send(text)

    @movethestreamer.command(name="dump")
    async def _movethestreamer_dump(self, ctx: Context) -> None:
        channel_map = await self.config.channel_map()
        await ctx.send(json.dumps(channel_map))

    @Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        activity_change = before.activity != after.activity
        activity_str = "streaming" if after.activity == ActivityType.streaming else "stopped streaming"
        if activity_change:
            log.debug(f"User {before.name} {activity_str}")
            channel_map = await self.config.channel_map()
            if before.id in channel_map.keys():
                channel = self.bot.get_channel(channel_map[before.id])
                reason = self.config.reason()
                await before.move_to(channel, reason=reason)
                await before.send(reason)
