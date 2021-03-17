# ZeroGravity - Rcon
The official zero gravity rcon tool.

## Usage:
Fill out the config file in the rcon folder then run ./build.sh

#### Commands
```
        -------------[Game Management]-------------
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
        !match #Active map and variant
```

#### Build:
This will build the container image then start a new instance.
```
sudo ./build.sh
```

#### Control
```
./control.sh <start/stop>
```
