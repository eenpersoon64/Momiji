import discord
import asyncio
from discord.ext import commands
import sys
import os
import time
import urllib.request
from urllib.parse import urlparse
import json
from io import BytesIO
from collections import Counter
import operator
import random

from cogs import permissions
from cogs import dbhandler
from cogs import utils

from modules import momiji

client = commands.Bot(command_prefix=';', description='Momiji is best wolf')
if not os.path.exists('data'):
	print("Please configure this bot according to readme file.")
	sys.exit("data folder and it's contents are missing")
client.remove_command('help')
appversion = "b20181225"

defaultembedthumbnail = "https://cdn.discordapp.com/emojis/526133207079583746.png"
defaultembedicon = "https://cdn.discordapp.com/emojis/499963996141518872.png"
defaultembedfootericon = "https://avatars0.githubusercontent.com/u/5400432"
uaheaders = {'User-Agent': ' Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0'}

@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')
	if not os.path.exists('data/maindb.sqlite3'):
		appinfo = await client.application_info()
		await dbhandler.query("CREATE TABLE channellogs (guildid, channelid, userid, messageid, contents)")
		await dbhandler.query("CREATE TABLE bridges (channelid, type, value)")
		await dbhandler.query("CREATE TABLE config (setting, parent, value)")
		await dbhandler.query("CREATE TABLE temp (setting, value)")
		await dbhandler.query("CREATE TABLE blacklist (value)")
		await dbhandler.query("CREATE TABLE admins (discordid, permissions)")
		await dbhandler.insert('admins', (str(appinfo.owner.id), "1"))
		await dbhandler.insert('blacklist', ("@",))
		await dbhandler.insert('blacklist', ("discord.gg/",))
		await dbhandler.insert('blacklist', ("https://",))
		await dbhandler.insert('blacklist', ("http://",))
		await dbhandler.insert('blacklist', ("momiji",))

@client.command(name="adminlist", brief="Show bot admin list", description="", pass_context=True)
async def adminlist(ctx):
	await ctx.send(embed=await permissions.adminlist())

@client.command(name="makeadmin", brief="Make a user bot admin", description="", pass_context=True)
async def makeadmin(ctx, discordid: str):
	if await permissions.checkowner(ctx.message.author.id) :
		await dbhandler.insert('admins', (str(discordid), "0"))
		await ctx.send(":ok_hand:")
	else :
		await ctx.send(embed=await permissions.ownererror())

@client.command(name="restart", brief="Restart the bot", description="", pass_context=True)
async def restart(ctx):
	if await permissions.check(ctx.message.author.id) :
		await ctx.send("Restarting")
		quit()
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="gitpull", brief="Update the bot", description="it just does git pull", pass_context=True)
async def gitpull(ctx):
	if await permissions.check(ctx.message.author.id) :
		await ctx.send("Updating my self, I guess. This feels scary though.")
		os.system('git pull')
		quit()
		#exit()
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="echo", brief="Update the bot", description="it just does git pull", pass_context=True)
async def echo(ctx, *, string):
	if await permissions.check(ctx.message.author.id) :
		#await ctx.delete_message(ctx.message)
		await ctx.send(await utils.msgfilter(string, False))
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="help", brief="Help", description="", pass_context=True)
async def help(ctx, admin: str = None):
	helpembed=discord.Embed(title="Momiji is best wolf.", description="Here are just some available commands:", color=0xe95e62)

	helpembed.set_author(name="Momiji %s" % (appversion), icon_url=defaultembedicon, url='https://github.com/Kyuunex/Momiji')
	helpembed.set_thumbnail(url=defaultembedthumbnail)
	
	helpembed.add_field(name="inspire", value="When you crave some inspiration in your life", inline=True)
	helpembed.add_field(name="img", value="Google image search", inline=True)
	helpembed.add_field(name="neko", value="Nekos are life", inline=True)

	if admin == "admin":
		helpembed.add_field(name="gitpull", value="Update the bot", inline=True)
		helpembed.add_field(name="restart", value="Restart the bot", inline=True)
		helpembed.add_field(name="export", value="Exports the chat to json format", inline=True)
		helpembed.add_field(name="import", value="Import the chat into database", inline=True)
		helpembed.add_field(name="echo", value="Echo out a string", inline=True)
		helpembed.add_field(name="bridge", value="Bridge the channel", inline=True)
		helpembed.add_field(name="adminlist", value="List bot admins", inline=True)
		helpembed.add_field(name="makeadmin", value="Make user a bot admin", inline=True)
		helpembed.add_field(name="sql", value="Execute an SQL query", inline=True)

	helpembed.set_footer(text = "Made by Kyuunex", icon_url=defaultembedfootericon)
	await ctx.send(embed=helpembed)

@client.command(name="export", brief="Export the chat", description="Exports the chat to json format.", pass_context=True)
async def exportjson(ctx, channelid: int = None, amount: int = 999999999):
	if await permissions.check(ctx.message.author.id) :
		if channelid == None:
			channel = ctx.message.channel
			channelid = ctx.message.channel.id
		else:
			channel = await utils.get_channel(client.get_all_channels(), channelid)

		log_instance = channel.history(limit=amount)
		#starttime = time.clock()
		exportfilename = "data/export.%s.%s.%s.json" % (str(int(time.time())), str(channelid), str(amount))
		log_file = open(exportfilename, "a", encoding="utf8")	
		collection = []
		logcounter = 0
		async for message in log_instance:
			logcounter += 1
			template = {
				'timestamp': message.created_at.isoformat(), 
				'id': str(message.id), 
				'author': {
					'id': str(message.author.id),
					'username': message.author.name,
					'discriminator': message.author.discriminator,
					'avatar': message.author.avatar,
				},
				'content': message.content, 
			}
			#collection.update(template)
			collection.append(template)
		log_file.write(json.dumps(collection, indent=4, sort_keys=True))
		#timeittook = time.clock() - starttime
		exportembed=discord.Embed(color=0xadff2f)
		exportembed.set_author(name="Exporting finished", url='https://github.com/Kyuunex/Momiji', icon_url=defaultembedicon)
		exportembed.add_field(name="Exported to:", value=exportfilename, inline=False)
		exportembed.add_field(name="Number of messages:", value=logcounter, inline=False)
		#exportembed.add_field(name="Time taken while exporting:", value=str(int(timeittook))+" seconds", inline=False)
		await ctx.send(embed=exportembed)
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="import", brief="Export the chat", description="Exports the chat to json format.", pass_context=True)
async def importmessages(ctx):
	if await permissions.check(ctx.message.author.id) :
		try:
			channel = ctx.message.channel
			log_instance = channel.history(limit=999999999)
			#starttime = time.clock()
			logcounter = 0
			async for message in log_instance:
				if await utils.msgfilter(message, True) != None:
					logcounter += 1
					await dbhandler.insert('channellogs', (message.guild.id, message.channel.id, message.author.id, message.id, message.content.encode('utf-8')))
			#timeittook = time.clock() - starttime
			exportembed=discord.Embed(color=0xadff2f, description="Imported the channel into database.")
			exportembed.set_author(name="Importing finished", url='https://github.com/Kyuunex/Momiji', icon_url=defaultembedicon)
			exportembed.add_field(name="Number of messages:", value=logcounter, inline=False)
			#exportembed.add_field(name="Time taken while importing:", value=str(int(timeittook))+" seconds", inline=False)
			await ctx.send(embed=exportembed)
		except Exception as e:
			print(time.strftime('%X %x %Z'))
			print("in importmessages")
			print(e)
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="bridge", brief="Bridge the channel", description="too lazy to write description", pass_context=True)
async def bridge(ctx, bridgetype: str, value: str):
	if await permissions.check(ctx.message.author.id) :
		if len(value) > 0:
			where = [
				['channelid', ctx.message.channel.id],
			]
			bridgedchannel = await dbhandler.select('bridges', 'value', where)
			if not bridgedchannel:
				await dbhandler.insert('bridges', (ctx.message.channel.id, bridgetype, value))
				await ctx.send("`The bridge was created`")
			else :
				await ctx.send("`This channel is already bridged`")
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="serverstats", brief="Show server stats", description="too lazy to write description", pass_context=True)
async def serverstats(ctx):
	if await permissions.check(ctx.message.author.id) :
		guilddata = await dbhandler.select('channellogs', 'userid', [['guildid', ctx.message.guild.id],])
		results = dict(Counter(guilddata))
		sorted_x = reversed(sorted(results.items(), key=operator.itemgetter(1)))
		counter = 0
		statsembed=discord.Embed(description="Here are 10 most active people in this server:", color=0xffffff)
		statsembed.set_author(name="Top members", icon_url=defaultembedicon)
		statsembed.set_thumbnail(url=defaultembedthumbnail)
		for onemember in sorted_x:
			counter += 1
			memberobject = ctx.guild.get_member(onemember[0][0])
			#messageamount = str(results[onemember])
			messageamount = str(onemember[1])+" messages"
			if not memberobject:
				statsembed.add_field(name="[%s] : %s (%s)" % (counter, onemember[0][0], "User not found"), value=messageamount, inline=False)
			elif memberobject.nick:
				statsembed.add_field(name="[%s] : %s (%s)" % (counter, memberobject.nick, memberobject.name), value=messageamount, inline=False)
			else:
				statsembed.add_field(name="[%s] : %s" % (counter, memberobject.name), value=messageamount, inline=False)
			if counter == 10:
				break
		statsembed.set_footer(text = "Momiji is best wolf.", icon_url=defaultembedfootericon)
		await ctx.send(embed=statsembed)
	else :
		await ctx.send(embed=await permissions.error())

@client.command(name="sql", brief="Executre an SQL query", description="", pass_context=True)
async def sql(ctx, *, query):
	if await permissions.checkowner(ctx.message.author.id) :
		if len(query) > 0:
			response = await dbhandler.query(query)
			await ctx.send(response)
	else :
		await ctx.send(embed=await permissions.ownererror())

@client.command(name="neko", brief="When you want some neko in your life", description="Why are these not real? I am sad.", pass_context=True)
async def neko(ctx):
	if await utils.cooldowncheck('lastnekotime'):
		with urllib.request.urlopen(urllib.request.Request('https://www.nekos.life/api/v2/img/neko', headers=uaheaders)) as jsonresponse:
			if "Content-Type: application/json" in jsonresponse.info().as_string():
				imageurl = json.loads(jsonresponse.read())['url']
				with urllib.request.urlopen(urllib.request.Request(imageurl, headers=uaheaders)) as imageresponse:
					buffer = BytesIO(imageresponse.read())
					a = urlparse(imageurl)
					await ctx.send(file=discord.File(buffer, os.path.basename(a.path)))
					buffer.close()
	else:
		await ctx.send('slow down bruh')

@client.command(name="inspire", brief="When you crave some inspiration in your life", description="", pass_context=True)
async def inspire(ctx):
	if await utils.cooldowncheck('lastinspiretime'):
		with urllib.request.urlopen(urllib.request.Request('http://inspirobot.me/api?generate=true', headers=uaheaders)) as textresponse:
			if "text/html" in textresponse.info().as_string():
				imageurl = textresponse.read().decode('utf-8')
				with urllib.request.urlopen(urllib.request.Request(imageurl, headers=uaheaders)) as imageresponse:
					buffer = BytesIO(imageresponse.read())
					a = urlparse(imageurl)
					await ctx.send(file=discord.File(buffer, os.path.basename(a.path)))
					buffer.close()
	else:
		await ctx.send('slow down bruh')

@client.command(name="img", brief="Google image search", description="Search for stuff on Google images", pass_context=True)
async def img(ctx, *, searchquery):
	try:
		if ctx.channel.is_nsfw():
			if await utils.cooldowncheck('lastimgtime'):
				if len(searchquery) > 0:
					googleapikey = (await dbhandler.select('config', 'value', [['setting', 'googleapikey'],]))
					googlesearchengineid = (await dbhandler.select('config', 'value', [['setting', 'googlesearchengineid'],]))
					if googleapikey:
						query = {
							'q': searchquery,
							'key': googleapikey[0][0],
							'searchType': 'image',
							'cx': googlesearchengineid[0][0],
							'start': str(random.randint(1,21))
						}
						uri = "https://www.googleapis.com/customsearch/v1?"+urllib.parse.urlencode(query)

						with urllib.request.urlopen(urllib.request.Request(uri, headers=uaheaders)) as jsonresponse:
							if "Content-Type: application/json" in jsonresponse.info().as_string():
								imageurl = json.loads(jsonresponse.read())['items'][(random.randint(0,9))]['link']
								if len(imageurl) > 1:
									with urllib.request.urlopen(urllib.request.Request(imageurl, headers=uaheaders)) as imageresponse:
										buffer = BytesIO(imageresponse.read())
										a = urlparse(imageurl)
										await ctx.send(file=discord.File(buffer, os.path.basename(a.path)))
										buffer.close()
					else:
						await ctx.send("This command is not enabled")
			else:
				await ctx.send('slow down bruh')
		else :
			await ctx.send("This command works in NSFW channels only.")
	except Exception as e:
		print(time.strftime('%X %x %Z'))
		print("in img")
		print(e)

#####################################################################################################

@client.event
async def on_message(message):
	try:
		if message.author.id != client.user.id : 
			# TODO: Dynamically load a module depending on the channel used
			await momiji.main(client, message)
	except Exception as e:
		print(time.strftime('%X %x %Z'))
		print("in on_message")
		print(e)
	await client.process_commands(message)

client.run(open("data/token.txt", "r+").read(), bot=True)