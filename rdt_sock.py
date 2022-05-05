import hashlib
import socket

DATA_PREFIX = b'data|'
ACK = b'ack'
NAK = b'nak'

def make_packet(seqnum, data):
    checksum = hashlib.md5(data).digest()
    return b'data|' + str(seqnum).encode() + b'|' + checksum + b'|' + data

def extract_data(packet):
    if not packet.startswith(DATA_PREFIX):
        return False, None
    packet = packet[len(DATA_PREFIX):]

    seqnum = int(packet[0].decode())
    checksum = packet[2:18]
    data = packet[19:]
    if hashlib.md5(data).digest() != checksum:
        return False, None
    return True, data

class RDTSocket:
    def __init__(self, server, port, bufsize=2048):
        self.server = server
        self.port = port
        self.bufsize = bufsize
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seqnum = 0
    
    def udp_send(self, message):
        self.udp_sock.sendto(message, (self.server, self.port))
    
    def udp_receive(self):
        return self.udp_sock.recv(self.bufsize)
    
    def flip_seqnum(self):
        self.seqnum = (1 - self.seqnum)
    
    def send(self, message, binary=False):
        if not binary:
            print(f"Sending message: `{message}`")
            message = message.encode()
        while True:
            packet = make_packet(seqnum=self.seqnum, data=message)
            self._send(packet)
            ack = self.udp_receive()
            if ack == ACK:
                self.flip_seqnum()
                break
    
    def receive(self, binary=False):
        while True:
            packet = self.udp_receive()
            success, seqnum, data = extract_data(packet)
            if success:
                if seqnum == self.seqnum:
                    break # Success!
                self._send(ACK) # Sender is retransmitting an old packet
            else:
                self._send(NAK) # We received a corrupted packet
        self._send(ACK)
        self.flip_seqnum()
        if not binary:
            data = data.decode()
            print(f"Received message: `{data}`")
        return data
