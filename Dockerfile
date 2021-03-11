FROM python:3

RUN mkdir app

WORKDIR /app

RUN pip3 install discord discord-webhook websocket-client

CMD [ "python3",  "rcon.py" ]
