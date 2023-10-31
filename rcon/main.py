import discord
import threading
import urllib.request
import logging
import json
import _thread
import time
import rel
import asyncio
from dewcon import Dewparser
from threading import Thread
from discord_webhook import DiscordWebhook, DiscordEmbed
from websocket import create_connection


#Instantiate our logger instance
logging.basicConfig(level = logging.INFO)
log = logging.getLogger("dewcon-logs")


#Get and return config
def getConfig():
    with open("dewcon.config") as configfile:
        dewconfig = json.load(configfile)
        configfile.close()
        log.info("Config loaded!")

        return dewconfig


#Update config with new data (bad words, uids, names, etc)
def configupdate(dewconfig):
    try:
        with open("dewcon.config", "w") as outfile:
            json.dump(dewconfig, outfile)
            outfile.close()
            log.info("Updated config.")

    except:
        log.error("Failed to update config!")


#Method to handle discord webhook communication
def discordhook(hookmsg):
    dewconfig = getConfig()

    if hookmsg:
        try:
            webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"], content=hookmsg)

            #Webhook has a response value that should be handled. !TODO!
            response = webhook.execute()
            log.info("Webhook sent: ")
            log.info(hookmsg)

        except:
            log.warning("Failed to send message to discord webhook!")
            log.warning(response)


#Method to handle discord webhook communication
def discordHookEmbed(chatmsg, msg_type):
    dewconfig = getConfig()

    msg = Dewparser(chatmsg)
    msg.parse()

    if msg_type == "ban":
        color = "f54242"

    if msg_type == "msg":
        color = "0f0f0f"

    if msg_type == "log":
        color = "faf43e"


    webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"])

    #Build out embed
    embed = DiscordEmbed(title=msg.name, description=msg.message, color=color)

    embed.add_embed_field(name="IP", value=msg.ip, inline=True)
    embed.add_embed_field(name="UID", value=msg.uid, inline=True)
    embed.set_footer(text=msg.date + " " + msg.time)

    webhook.add_embed(embed)

    try:    #Webhook has a response value that should be handled. !TODO!
        response = webhook.execute()
        log.info(response)

    except Exception as e:
        log.warning("Failed to send message to discord webhook! " + e)



#Check inbound rcon message for bad words, banned players, etc, then send to discord
def feedParser(rconMessage):
    rconMessage = rconMessage.strip('<SERVER/0000000000000000/127.0.0.1>')
    if '<discord>' in rconMessage:
        return

    #Try to catch a broken web socket, our client will auto connect in the background
    elif 'No session available' in rconMessage:
        return

    elif rconMessage == "accept":
        return

    elif rconMessage == None:
        return

    else:
        #The parser isnt very smart and will break on invalid chat messages(server command output). We can leverage this to check for command responses.
        chat = Dewparser(rconMessage)
        try:
            chat.parse()

        except:
            discordhook(rconMessage)
            return

        #Check for bad words, names, and uids in chat. If found, ban the player, update the config, then send a notification.
        for x in dewconfig["ed_banned_words"]:
            if x in chat.message:
                ws.send("server.kickbanuid " + chat.uid)
                banmsg = "**Banned " + chat.name + " for saying " + x + "**"
                dewconfig["ed_banned_uid"].append(chat.uid)
                configupdate()
                discordhook(banmsg)
                continue

        for x in dewconfig["ed_banned_names"]:
            if x in chat.name:
                ws.send("server.kickbanuid " + chat.uid)
                banmsg = "**Banned " + chat.name + " for having illegal name**"
                dewconfig["ed_banned_uid"].append(chat.uid)
                configupdate()
                discordhook(banmsg)
                continue

        for x in dewconfig["ed_banned_uid"]:
            if x in chat.uid:
                ws.send("server.kickbanuid " + chat.uid)
                banmsg = "**Banned " + chat.name + "**"
                discordhook(banmsg)
                continue

        discordHookEmbed(rconMessage, "msg")
        return


#Append to the banlist then update the config
def ban(banid, idtype):
    try:
        if idtype == "name":
            dewconfig["ed_banned_names"].append(banid)
            configupdate(dewconfig)

        elif idtype == "uid":
            dewconfig["ed_banned_uid"].append(banid)
            configupdate(dewconfig)

        elif idtype == "word":
            dewconfig["ed_banned_words"].append(banid)
            configupdate(dewconfig)

        discordhook("Added " + banid + " to banlist.")

    except:
        discordhook("Failed to add " + banid + " to banlist.")


#Forgive a ban then update the config
def forgive(banid, idtype):
    try:
        if idtype == "name":
            dewconfig["ed_banned_names"].remove(banid)
            configupdate(dewconfig)

        elif idtype == "uid":
            dewconfig["ed_banned_uid"].remove(banid)
            configupdate(dewconfig)

        elif idtype == "word":
            dewconfig["ed_banned_words"].remove(banid)
            configupdate(dewconfig)

        discordhook("Removed " + banid + " from banlist.")

    except:
        discordhook(banid + " not found in banlist.")


#Send a list of banned items
def banlist():
    payload = "Names: " + str(dewconfig["ed_banned_names"]) + "\n" + "UIDs: " + str(dewconfig["ed_banned_uid"]) + "\n" + "Words: " + str(dewconfig["ed_banned_words"])
    discordhook(payload)


#Sends a list of commands to discord
def help_menu():

    webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"])
    embed = DiscordEmbed(title="Help Menu", description="Game Management", color="10dce3")
    embed.add_embed_field(name="!game.gametype", value="<variant name> Force load a game variant", inline=False)
    embed.add_embed_field(name="!game.map", value="<map name> force load a map", inline=False)
    embed.add_embed_field(name="!game.start", value="Start a match with force loaded map and variant", inline=False)
    embed.add_embed_field(name="!Server.ReloadVotingJson", value="Reload voting.json", inline=False)
    embed.add_embed_field(name="!Server.CancelVote", value="Cancel in progress vote", inline=False)
    embed.set_footer(text="Page 1")
    webhook.add_embed(embed)

    webhook.execute()

    webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"])
    embed = DiscordEmbed(title="Help Menu", description="Auto Moderation", color="10dce3")
    embed.add_embed_field(name="!banuid", value="Add UID to ban config", inline=False)
    embed.add_embed_field(name="!banname", value="Add player name to ban config", inline=False)
    embed.add_embed_field(name="!banword", value="Add a chat word to ban config", inline=False)
    embed.add_embed_field(name="!forgiveuid", value="Remove UID from ban config", inline=False)
    embed.add_embed_field(name="!forgivename", value="Remove player name from ban config", inline=False)
    embed.add_embed_field(name="!forgiveword", value="Remove chat word from ban config", inline=False)
    embed.set_footer(text="Page 2")
    webhook.add_embed(embed)

    webhook.execute()

    webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"])
    embed = DiscordEmbed(title="Help Menu", description="Player Management", color="10dce3")
    embed.add_embed_field(name="!Server.KickBanIndex", value="Kick and ban player by index", inline=False)
    embed.add_embed_field(name="!Server.KickBanPlayer", value="Kick and ban player by name", inline=False)
    embed.add_embed_field(name="!Server.KickBanUid", value="Kick and ban player by UID", inline=False)
    embed.add_embed_field(name="!Server.KickIndex", value="Show kick index", inline=False)
    embed.add_embed_field(name="!Server.KickTempBanPlayer", value="Kick and temporarily ban player by name", inline=False)
    embed.add_embed_field(name="!Server.KickUid", value="Kick player by UID", inline=False)
    embed.add_embed_field(name="!Server.unban ip {ip}", value="Unban player IP, takes IP as argument", inline=False)
    embed.add_embed_field(name="!Server.ListPlayers", value="List players", inline=False)
    embed.set_footer(text="Page 3")
    webhook.add_embed(embed)

    webhook.execute()

    webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"])
    embed = DiscordEmbed(title="Help Menu", description="Miscellaneous", color="10dce3")
    embed.add_embed_field(name="!Server.say", value="Talk in chat as server", inline=False)
    embed.add_embed_field(name="!Server.sprintenabled", value="Enable sprint, takes 0 or 1 as arguments", inline=False)
    embed.add_embed_field(name="!Server.UnlimitedSprint", value="Enable infinite sprint, takes 0 or 1 as arguments", inline=False)
    embed.add_embed_field(name="!scoreboard", value="Show active scoreboard", inline=False)
    embed.add_embed_field(name="!match", value="Show current game info", inline=False)
    embed.set_footer(text="Page 4")
    webhook.add_embed(embed)

    webhook.execute()


#Grab scoreboard data from the eldewrito server api then return to discord
def scoreboard():
    players = ["```"]
    try:
        with urllib.request.urlopen(dewconfig["ed_server_api"]) as url:
            data = json.loads(url.read().decode())

        for player in data["players"]:
            players.append("{} - Alive: {}, Kills: {}, Deaths: {}, Betrayals: {}, Suicides: {}".format(player["name"], player["isAlive"], player["kills"], player["deaths"], player["betrayals"], player["suicides"]))

        players.append("```")
        players = "\n".join(players)
        discordhook(players)

    except:
        log.error("Could not connect to the dewrito meta data api.")


#Grab match data from the eldewrito server api then return to discord
def matchdata():
    try:
        with urllib.request.urlopen(dewconfig["ed_server_api"]) as url:
            data = json.loads(url.read().decode())

        payload = "Players: {}, Status: {},  Map: {}, GameType: {}".format(data["numPlayers"], data["status"], data["map"], data["variant"])
        discordhook(payload)

    except:
        log.warning("Could not connect to the dewrito meta data api.")


#Gets around client.run being a blocking operation
def discord_init():
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)


    #Log a successful discord api connection
    @client.event
    async def on_ready():
        discordhook('Connected to discord as {0.user}'.format(client))


    #Handle outbound rcon commands and messages
    @client.event
    async def on_message(message):

        log.info("message from discord")
        #Several checks to prevent endless loops
        if message.author == client.user:
            return

        elif message.author.name == dewconfig["discord_webhook_name"]:
            return

        elif message.channel.name != dewconfig["discord_webhook_channel"]:
            log.info(message.channel.name)
            return

        #Check to see if a incoming message is a server command. We check for custom commands first, then assume the commmand was meant for the eldewrito server.
        elif '!' in message.content[0]:

            log.info('command detected')
            #Getto arg parsing for disc commands.
            arg = str(message.content).split(" ")

            if message.content[1:] == "match":
                matchdata()
                return

            elif message.content[1:] == "scoreboard":
                scoreboard()
                return

            elif "!banuid" in message.content:
                ban(arg[1], "uid")
                return

            elif "!banname" in message.content:
                ban(arg[1], "name")
                return

            elif "!banword" in message.content:
                ban(arg[1], "word")
                return

            elif message.content[1:] == "banlist":
                banlist()
                return

            elif "!forgiveuid" in message.content:
                forgive(arg[1], "uid")
                return

            elif "!forgivename" in message.content:
                forgive(arg[1], "name")
                return

            elif "!forgiveword" in message.content:
                forgive(arg[1], "word")
                return

            elif message.content[1:] == "help":
                log.info(message.content[1:])
                help_menu()
                return

            else:
                ws.send(message.content[1:])
                log.info(message.content[1:])

        #If no commands are detected then send to the game chat
        else:
            ws.send('server.say {0.author}: {0.content}'.format(message))

    client.run(dewconfig["discord_api_token"])
    discordhook("Discord client thread started")


#Initialize websocket connection, and retry on failure
def wsInit():
    while True:
        try:
            global ws
            ws = create_connection("ws://" + dewconfig["ed_server_ip"] + ":" + dewconfig["ed_server_rcon_port"], subprotocols=["dew-rcon"])
            ws.send(dewconfig["ed_rcon_password"])

        except Exception as e:
            log.info("Rcon connection failed, retrying...")
            time.sleep(5)

            continue

        log.info("Succesfully connected to rcon!")
        discordhook("Connected to Eldewrito!")

        break


#Loop for websocket thread
def rconMain():
    while True:
        try:
            message = ws.recv()

        except:
            log.warning("Rcon connection failed, retrying...")
            wsInit()

            continue

        if message:
            feedParser(message)

        else:
            pass


#Entry Point
if __name__ == "__main__":
    dewconfig = getConfig()

    #Initialize websocket client
    wsInit()

    #Start listening to eldewrito websocket
    wsRcon = threading.Thread(target=rconMain)
    wsRcon.start()

    #Call discord client.run in asyncio wrapper
    discord_init()