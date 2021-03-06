import random
import discord
from discord.ext import commands
import time
from modules import db


class MomijiSpeak(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bridged_extensions = db.query("SELECT channel_id, extension_name FROM bridged_extensions")
        self.momiji_responses = db.query("SELECT * FROM mmj_responses")

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bridged_extensions:
            for bridge in self.bridged_extensions:
                if str(bridge[0]) == str(message.channel.id):
                    return None
        await self.main(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.bridged_extensions:
            for bridge in self.bridged_extensions:
                if str(bridge[0]) == str(message.channel.id):
                    return None
        db.query(["UPDATE mmj_message_logs SET deleted = ? WHERE message_id = ?",
                  [str("1"), str(message.id)]])

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if self.bridged_extensions:
            for bridge in self.bridged_extensions:
                if str(bridge[0]) == str(after.channel.id):
                    return None
        if not await self.check_privacy(after):
            db.query(["UPDATE mmj_message_logs SET contents = ? WHERE message_id = ?",
                      [str(after.content), str(after.id)]])
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, deleted_channel):
        if self.bridged_extensions:
            for bridge in self.bridged_extensions:
                if str(bridge[0]) == str(deleted_channel.id):
                    return None
        db.query(["UPDATE mmj_message_logs SET deleted = ? WHERE channel_id = ?",
                  [str("1"), str(deleted_channel.id)]])

    async def join_spam_train(self, message):
        counter = 0
        async for previous_message in message.channel.history(limit=2+random.randint(1, 4)):
            if (message.content == previous_message.content) and (message.author.id != previous_message.author.id):
                if message.author.bot:
                    counter = -500
                else:
                    counter += 1
        if counter == 3:
            if await self.check_message_contents(message.content):
                await message.channel.send(message.content)

    async def check_privacy(self, message):
        if message.guild:
            if db.query(["SELECT * FROM mmj_private_guilds WHERE guild_id = ?", [str(message.guild.id)]]):
                return True
        if db.query(["SELECT * FROM mmj_private_channels WHERE channel_id = ?", [str(message.channel.id)]]):
            return True
        return False

    async def bridge_check(self, channel_id):
        bridged_channel = db.query(["SELECT depended_channel_id FROM mmj_channel_bridges "
                                    "WHERE channel_id = ?", [str(channel_id)]])
        if bridged_channel:
            return str(bridged_channel[0][0])
        else:
            return str(channel_id)

    async def check_message_contents(self, string):
        if len(string) > 0:
            blacklist = db.query("SELECT word FROM mmj_word_blacklist")
            if not (any(str(c[0]) in str(string.lower()) for c in blacklist)):
                if not (any(string.startswith(c) for c in (";", "'", "!", ",", ".", "=", "-", "t!", "t@"))):
                    return True
        return False

    async def pick_message(self, message, depended_channel_id):
        all_potential_messages = db.query(["SELECT * FROM mmj_message_logs "
                                           "WHERE channel_id = ? AND bot = ? AND deleted = ?", 
                                           [str(depended_channel_id), "0", "0"]])
        if all_potential_messages:
            counter = 0
            while True:
                if counter > 50:
                    print("I looked over 50 random messages to send but nothing passed the check.")
                    return False
                counter += 1
                message_from_db = random.choice(all_potential_messages)
                if await self.check_privacy(message):
                    self.bot.get_channel(int(depended_channel_id))
                    picked_message = await message.channel.fetch_message(message_from_db[3])
                    content_to_send = picked_message.content
                else:
                    content_to_send = str(message_from_db[6])
                if await self.check_message_contents(content_to_send):
                    return content_to_send
        else:
            print("The query returned nothing")
            return False

    async def momiji_speak(self, message):
        channel = message.channel

        depended_channel_id = await self.bridge_check(channel.id)

        async with channel.typing():
            message_contents_to_send = await self.pick_message(message, depended_channel_id)

        if message_contents_to_send:
            sent_message = await channel.send(message_contents_to_send)
            db.query(["INSERT INTO cr_pair VALUES (?, ?)", [str(message.id), str(sent_message.id)]])
            return True
        else:
            return False

    async def store_message(self, message):
        if await self.check_privacy(message):
            content = None
        else:
            content = str(message.content)
        if message.guild:
            message_guild_id = message.guild.id
        else:
            message_guild_id = "0"

        db.query(
            [
                "INSERT INTO mmj_message_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    str(message_guild_id),
                    str(message.channel.id), 
                    str(message.author.id), 
                    str(message.id),
                    str(message.author.name),
                    str(int(message.author.bot)),
                    content,
                    str(int(time.mktime(message.created_at.timetuple()))),
                    str("0"),
                ]
            ]
        )

    async def main(self, message):
        if not message.author.bot:
            msg = message.content.lower()
            if "@everyone" in msg:
                await message.channel.send(file=discord.File("res/pinged.gif"))
            else:
                if "momiji" in msg or self.bot.user.mention in message.content:
                    await self.momiji_speak(message)
                else:
                    # await self.join_spam_train(message)

                    if message.content.isupper() and len(message.content) > 1 and random.randint(0, 20) == 1:
                        await self.momiji_speak(message)

                    for one_response in self.momiji_responses:
                        trigger = one_response[0]
                        response = one_response[1]
                        condition = one_response[2]  # type startswith, is, in
                        one_in = int(one_response[3])  # chances

                        if self.condition_validate(condition, msg, trigger):
                            if random.randint(1, one_in) == 1:
                                if len(response) > 0:
                                    response_msg = await message.channel.send(response)
                                    db.query(["INSERT INTO cr_pair VALUES (?, ?)",
                                              [str(message.id), str(response_msg.id)]])
                                else:
                                    await self.momiji_speak(message)
        await self.store_message(message)

    def condition_validate(self, condition, msg, trigger):
        if condition == "startswith":
            return msg.startswith(trigger)
        elif condition == "is":
            return msg == trigger
        elif condition == "in":
            return trigger in msg


def setup(bot):
    bot.add_cog(MomijiSpeak(bot))
