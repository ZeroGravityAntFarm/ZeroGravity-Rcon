import re

class Dewparser(object):
    def __init__(self, message):
        self.message = message

    def parse(self):
        #[0/0/0 00:00:00] <name/uid/ip> chat message
        self.srv_msg = self.message.split(" ")
        self.player_data = re.split('[ /<>]', self.srv_msg[2])

        self.date = self.srv_msg[0].strip("[")
        self.time = self.srv_msg[1].strip("]")
        self.name = self.player_data[1]
        self.uid = self.player_data[2]
        self.ip = self.player_data[3]
        self.message = self.srv_msg[3:]