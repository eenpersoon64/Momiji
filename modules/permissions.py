import discord
from modules import db

admin_list = []
for admin_id in db.query("SELECT user_id FROM admins"):
    admin_list.append(admin_id[0])


owner_list = []
for owner_id in db.query(["SELECT user_id FROM admins WHERE permissions = ?", [str(1)]]):
    owner_list.append(owner_id[0])


async def is_admin(ctx):
    return str(ctx.author.id) in admin_list


async def is_owner(ctx):
    return str(ctx.author.id) in owner_list


def get_admin_list():
    contents = ""
    for user_id in admin_list:
        contents += f"<@{user_id}>\n" 
    return discord.Embed(title="Bot admin list", description=contents, color=0xffffff)


def check_admin(user_id):
    return str(user_id) in admin_list


def check_owner(user_id):
    return str(user_id) in owner_list
