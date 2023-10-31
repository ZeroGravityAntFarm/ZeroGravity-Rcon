#!/bin/bash

name="zgaf_rcon"

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

start() {
    if [ ! "$(docker ps -q -f name=$name)" ]; then
        if [ "$(docker ps -aq -f status=exited -f name=$name)" ]; then
            echo "Old container found, removing..."
            docker rm $name
        fi
        docker run -d --name $name -v $PWD/rcon:/rcon $name
    fi
}

stop() {
    docker container kill $name
}

status() {
    docker ps -f name=$name
}

reload() {
    docker kill -s HUP $name
}

build() {
    docker build -t $name .
    stop
    start
}

logs() {
    docker logs $name
}

case "$1" in
    start)
       start
       ;;
    stop)
       stop
       ;;
    reload)
       reload
       ;;
    status)
       status
       ;;
    build)
       build
       ;;
    logs)
       logs
       ;;
    *)
       echo "Usage: $0 {start|stop|status|reload|build}"
esac

exit 0
