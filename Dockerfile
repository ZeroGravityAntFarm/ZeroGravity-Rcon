FROM python:3.11

WORKDIR /rcon

RUN pip3 install discord discord-webhook websocket-client rel

CMD [ "python3",  "main.py" ]
