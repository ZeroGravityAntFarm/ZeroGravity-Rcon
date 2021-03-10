import discord
import time
import threading
import urllib.request
import logging
import json
from websocket import create_connection
from dewcon import Dewparser
from discord_webhook import DiscordWebhook


#Instantiate our logger instance
logging.basicConfig(level = logging.INFO)
log = logging.getLogger("dewcon-logs")

#Load our config
with open("dewcon.config") as configfile:
    dewconfig = json.load(configfile)
    configfile.close()
    log.info("Config loaded!")

def configupdate():
    try:
        with open("dewcon.config", "w") as outfile:
            json.dump(dewconfig, outfile)
            outfile.close()
            log.info("Updated config.")
    except:
        log.error("Failed to update config!")

#Method to handle connection to the eldewrito rcon port
def connectSock():
    while True:
        try:
            global ws
            ws = create_connection("ws://" + dewconfig["ed_server_ip"] + ":" + dewconfig["ed_server_rcon_port"], subprotocols=["dew-rcon"])
            ws.send(dewconfig["ed_rcon_password"])

        except Exception as e:
            time.sleep(10)
            continue

        log.info("Succesfully connected to rcon!")
        discordhook("Connected to Eldewrito!")
        break

#Method to handle discord webhook communication
def discordhook(hookmsg):
    try:
        webhook = DiscordWebhook(url=dewconfig["discord_webhook_url"], content=hookmsg)
        response = webhook.execute()

    except:
        log.warning("Failed to send message to discord webhook!")

#Main thread handling rcon input from the game. This is where most of our actions on chat events will take place (checking for bad words/names, etc.)
def rconfeed():
    while True:
        try:
            result = ws.recv()
        except:
            connectSock()
            continue

        result = result.strip('<SERVER/0000000000000000/127.0.0.1>')

        #Make sure message wasnt sent from discord preventing endless loop
        if '<discord>' in result:
            continue

        #Try to catch a broken web socket
        elif 'No session available' in result:
            continue

        elif result == "accept":
            continue

        elif result == None:
            continue

        else:
            #The parser isnt very smart so we must have valid ed messages coming through or it will break.
            chat = Dewparser(result)
            try:
                chat.parse()
            except:
                discordhook(result)
                continue

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

            discordhook(result)
            continue

#####################################################
#                 Command Helpers                   #
#####################################################

#Append to the banlist then update the config
def ban(banid, idtype):
    try:
        if idtype == "name":
            dewconfig["ed_banned_names"].append(banid)
            configupdate()

        elif idtype == "uid":
            dewconfig["ed_banned_uid"].append(banid)
            configupdate()

        elif idtype == "word":
            dewconfig["ed_banned_words"].append(banid)
            configupdate()

        discordhook("Added " + banid + " to banlist.")

    except:
        discordhook("Failed to add " + banid + " to banlist.")

#Forgive a ban then update the config
def forgive(banid, idtype):
    try:
        if idtype == "name":
            dewconfig["ed_banned_names"].remove(banid)
            configupdate()

        elif idtype == "uid":
            dewconfig["ed_banned_uid"].remove(banid)
            configupdate()

        elif idtype == "word":
            dewconfig["ed_banned_words"].remove(banid)
            configupdate()

        discordhook("Removed " + banid + " from banlist.")

    except:
        discordhook(banid + " not found in banlist.")

#Send a list of banned items
def banlist():
    payload = "Names: " + str(dewconfig["ed_banned_names"]) + "\n" + "UIDs: " + str(dewconfig["ed_banned_uid"]) + "\n" + "Words: " + str(dewconfig["ed_banned_words"])
    discordhook(payload)

#Sends a list of commands to discord
def help_menu():

    payload = """ ```       -------------[Game Management]-------------
        !game.gametype "<variant name>" #Force load a game variant
        !game.map "<map name>" #Force load a Map
        !game.start #Start a match with a force loaded map and variant
        !game.stop #Stop any in progress match and return to lobby
        !Server.ReloadVotingJson #Reload voting.json
        !Server.CancelVote

        -------------[Sentry Gun]-------------
        !banuid
        !banname
        !banword
        !forgiveuid
        !forgivename
        !forgiveword

        -------------[Player Management]-------------
        !Server.KickBanIndex
        !Server.KickBanPlayer
        !Server.KickBanUid
        !Server.KickIndex
        !Server.KickPlayer
        !Server.KickTempBanPlayer
        !Server.KickTempBanUid
        !Server.KickUid
        !Server.unban ip <ip>
        !Server.ListPlayers

        -------------[Miscellaneous]-------------
        !Server.say
        !Server.sprintenabled #Valid arguments are 1 or 0
        !Server.UnlimitedSprint #Valid arguments are 1 or 0
        !scoreboard #Active scoreboard
        !match #Active map and variant``` """

    discordhook(payload)

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

        try:
            discordhook(players)

        except:
            log.warning("Failed to connect to the discord webhook url.")

    except:
        log.error("Could not connect to the dewrito meta data api.")

#Grab match data from the eldewrito server api then return to discord
def matchdata():
    try:
        with urllib.request.urlopen(dewconfig["ed_server_api"]) as url:
            data = json.loads(url.read().decode())

        payload = "Players: {}, Status: {},  Map: {}, GameType: {}".format(data["numPlayers"], data["status"], data["map"], data["variant"])

        try:
            discordhook(payload)

        except:
            log.warning("Failed to connect to the discord webhook url.")

    except:
        log.warning("Could not connect to the dewrito meta data api.")


#####################################################
#               Thread Instantiation                #
#####################################################

x = threading.Thread(target=rconfeed)
x.start()


#####################################################
#               Discord Async Client                #
#####################################################

client = discord.Client()

#Log a successful discord api connection
@client.event
async def on_ready():
    log.info('Connected to discord! {0.user}'.format(client))

#Async event to detect discord messages
@client.event
async def on_message(message):
    #Several checks to prevent endless loops
    if message.author == client.user:
        return
    elif message.author.name == dewconfig["discord_webhook_name"]:
        return
    elif message.channel.name != dewconfig["discord_webhook_channel"]:
        return

    #Check to see if a incoming message is a server command. We check for custom commands first, then assume the commmand was meant for the eldewrito server.
    elif '!' in message.content[0]:

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

        elif "!forgivename" in message.content:
            forgive(arg[1], "name")

        elif "!forgiveword" in message.content:
            forgive(arg[1], "word")

        elif message.content[1:] == "help":
            help_menu()

        else:
            try:
                ws.send(message.content[1:])
                log.info(message.content[1:])

            except:
                log.warning("Failed to connect to rcon, retrying...")
                connectSock()

    #If no commands are detected then send to the game chat
    else:
        try:
            ws.send('server.say {0.author}:{0.content}'.format(message))

        except:
            log.warning('Failed to connect to rcon, retrying...')
            connectSock()

client.run(dewconfig["discord_api_token"])
