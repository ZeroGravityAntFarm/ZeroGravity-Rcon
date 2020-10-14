import discord
import time
import threading
import urllib.request
import json
from websocket import create_connection
from discord_webhook import DiscordWebhook


###########################  Config  ###################################
password = '' #ed management password
server = '' #ed server address
port = '11776'
apiToken = ''
botName = '' #Webhook name MUST match bot name !!! IF YOU ARE HAVING ISSUES TRIPLE CHECK THIS !!!
discordChan = ''
serverAdmin = '<@&>' #if anyone mentions hack or admin keyword notify the server admin in discord
webHook = 'https://discordapp.com/api/webhooks/xxx/yyy'
motd_msg = 'Join us on discord! https://discord.gg/'
dew_api = 'http://:11775'
##########################  Config  ###################################

keywords = ['admin', 'hack', 'hacker', 'server', 'Admin']

#build our dewrito rcon connection
def connectSock():

    while True:
        try:
            global ws
            ws = create_connection("ws://" + server + ":" + port, subprotocols=["dew-rcon"])
            print("Connected!")
            ws.send(password)
            print("Authenticated!")

        except Exception as e:
            print("Failed to connect to your eldewrito server, retrying...")
            time.sleep(10)
            continue

        break

#initiate our dewrito rcon connection
connectSock()

#thread to handle sending messages from dewrito to discord
def chatTX():
    while True:
        try:
            result = ws.recv()
        except:
            connectSock()
            continue

        result = result.strip('<SERVER/0000000000000000/127.0.0.1>')

        if '<discord>' in result:
            continue

        elif motd_msg in result:
            continue

        elif 'No session available' in result:
            continue

        else:
            for x in keywords:
                if x in result:
                    result = result + ' ' + serverAdmin
                    break

            try:
                webhook = DiscordWebhook(url=webHook, content=result)
                response = webhook.execute()

            except:
                print("Discord webhook rate limit reached!")

def server_meta():
    try:
        with urllib.request.urlopen(dew_api) as url:
            data = json.loads(url.read().decode())

        payload = "Players: {}, Status: {},  Map: {}, GameType: {}".format(data["numPlayers"], data["status"], data["map"], data["variant"])

        try:
            webhook = DiscordWebhook(url=webHook, content=payload)
            response = webhook.execute()

        except:
            print("Failed to connect to the discord webhook url.")

    except:
        print("Could not connect to the dewrito meta data api.")

def help_menu():

    payload = """ ```               !game.gametype "<variant name>" #Force load a game variant
               !game.map "<map name>" #Force load a Map
               !game.start #Start a match with a force loaded map and variant
               !game.stop #Stop any in progress match and return to lobby
               !Server.ReloadVotingJson #Reload voting.json
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
               !Server.CancelVote
               !Server.say
               !Server.sprintenabled #Valid arguments are 1 or 0
               !Server.UnlimitedSprint #Valid arguments are 1 or 0
               !playerstats #Active scoreboard
               !serverstats #Active map and variant``` """

    try:
        webhook = DiscordWebhook(url=webHook, content=payload)
        response = webhook.execute()

    except:
        print("Failed to connect to the discord webhook url.")


def player_meta():
    players = ["```"]

    try:
        with urllib.request.urlopen(dew_api) as url:
            data = json.loads(url.read().decode())

        for player in data["players"]:
            players.append("{} - Alive: {}, Kills: {}, Deaths: {}, Betrayals: {}, Suicides: {}".format(player["name"], player["isAlive"], player["kills"], player["deaths"], player["betrayals"], player["suicides"]))

        players.append("```")

        players = "\n".join(players)

        try:
            webhook = DiscordWebhook(url=webHook, content=str(players))
            response = webhook.execute()

        except:
            print("Failed to connect to the discord webhook url.")

    except:
        print("Could not connect to the dewrito meta data api.")


def motd():
    while True:
        time.sleep(1800)
        try:
            ws.send("server.say " + motd_msg)

        except:
            print('Failed to send motd, retrying...')

            continue

def uidban():
    while True:
        time.sleep(5)
        try:
            ws.send("server.kickbanuid fffb1647b332421a")
        except:
            print('User not found.')
            continue

#start our dewrito to discord bridge
x = threading.Thread(target=chatTX)
x.start()

y = threading.Thread(target=motd)
y.start()

z = threading.Thread(target=uidban)
#z.start()

client = discord.Client()

@client.event
async def on_ready():
    print('ohai {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    elif message.author.name == botName:
        return

    elif message.channel.name != discordChan:
        return

    elif '!' in message.content[0]:
        if message.content[1:] == "serverstats": #Check for custom commands first, then forward the command to the eldewrito server
            server_meta()

        elif message.content[1:] == "playerstats":
            player_meta()

        elif message.content[1:] == "help":
            help_menu()

        else:
            try:
                ws.send(message.content[1:])
                print(message.content[1:])

            except:
                print('Failed to connect, retrying...')
                connectSock()

    else:
    #await message.channel.send('sent message!')
        try:
            ws.send('server.say {0.author}:{0.content}'.format(message))

        except:
            print('Failed to connect, retrying...')
            connectSock()

client.run(apiToken)
