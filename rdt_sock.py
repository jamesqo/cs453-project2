import socket

class RDTSocket:
    def __init__(self, server, port, bufsize=2048):
        self.server = server
        self.port = port
        self.bufsize = bufsize
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def send(self, message, binary=False):
        if not binary:
            print(f"Sending message: `{message}`")
            message = message.encode()
        self.udp_sock.sendto(message, (self.server, self.port))
    
    def receive(self, binary=False):
        ret = self.udp_sock.recv(self.bufsize)
        if not binary:
            ret = ret.decode()
            print(f"Received message: `{ret}`")
        return ret
