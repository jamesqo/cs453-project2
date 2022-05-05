import hashlib
import socket

DATA_PREFIX = b'data|'
ACK = b'ack'
NAK = b'nak'

def make_packet(data):
    checksum = hashlib.md5(data).digest()
    return b'data|' + checksum + b'|' + data

def extract_data(packet):
    if not packet.startswith(DATA_PREFIX):
        return False, None
    packet = packet[len(DATA_PREFIX):]

    checksum = packet[:16]
    data = packet[16+1:]
    if hashlib.md5(data).digest() != checksum:
        return False, None
    return True, data

class RDTSocket:
    def __init__(self, server, port, bufsize=2048):
        self.server = server
        self.port = port
        self.bufsize = bufsize
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    def _send(self, message):
        self.udp_sock.sendto(message, (self.server, self.port))
    
    def receive_ack(self):
        packet = self.udp_sock.recv(self.bufsize)
        if packet == ACK or packet == NAK:
            return packet
        else:
            raise Exception("Corrupted ACK or NAK!") # TODO: what do we do here?
    
    def send(self, message, binary=False):
        if not binary:
            print(f"Sending message: `{message}`")
            message = message.encode()
        while True:
            self._send(message)
            ack = self.receive_ack()
            if ack == ACK:
                break
    
    def receive(self, binary=False):
        while True:
            packet = self.udp_sock.recv(self.bufsize)
            success, data = extract_data(packet)
            if success:
                break
            self._send(NAK)
        self._send(ACK)
        if not binary:
            ret = ret.decode()
            print(f"Received message: `{ret}`")
        return ret
