FROM python:3

ADD rcon.py /

RUN pip3 install discord discord-webhook websocket-client

CMD [ "python3",  "./rcon.py" ]
