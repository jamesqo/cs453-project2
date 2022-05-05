import hashlib
import socket

DATA_PREFIX = b'data|'
ACK = b'ack'
NAK = b'nak'

"""
Creates an RDT packet from binary data, its MD5 checksum and a sequence number.
"""
def make_packet(seqnum, data):
    checksum = hashlib.md5(data).digest()
    return b'data|' + str(seqnum).encode() + b'|' + checksum + b'|' + data

"""
Extracts data from an RDT packet.
Returns (success, seqnum, data) where success indicates successful extraction, seqnum is the sequence number, and data is the data.
"""
def extract_data(packet):
    if not packet.startswith(DATA_PREFIX):
        return False, None
    packet = packet[len(DATA_PREFIX):]

    seqnum = int(packet[0].decode())
    checksum = packet[2:18]
    data = packet[19:]
    if hashlib.md5(data).digest() != checksum:
        return False, seqnum, None
    return True, seqnum, data

class RDTSocket:
    def __init__(self, server, port, bufsize=2048, timeout=None):
        self.server = server
        self.port = port
        self.bufsize = bufsize
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if timeout is not None:
            self.udp_sock.settimeout(timeout)
        self.seqnum = 0
    
    def flip_seqnum(self):
        self.seqnum = (1 - self.seqnum)
    
    def udt_send(self, message):
        if isinstance(message, str):
            message = message.encode()
        self.udp_sock.sendto(message, (self.server, self.port))
    
    def udt_receive(self):
        return self.udp_sock.recv(self.bufsize)
    
    def udt_receive_text(self):
        return self.udt_receive().decode()
    
    """
    Sends message and waits for server to respond, re-sending message as needed.
    Optionally verifies that the server's response matches the string expected_response.
    """
    def udt_send_and_wait(self, message, expected_response=None):
        while True:
            try:
                self.udt_send(message)
                response = self.udt_receive()
                break
            except TimeoutError:
                continue
        if expected_response is not None:
            if response.decode() != expected_response:
                print(f"WARNING: Expected response msg of '{expected_response}', but got '{response.decode()}'")
        return response
    
    """
    Sends a message using the RDT protocol.
    """
    def rdt_send(self, message):
        while True:
            packet = make_packet(seqnum=self.seqnum, data=message)
            self.udt_send(packet)
            ack = self.udt_receive()
            if ack == ACK:
                self.flip_seqnum()
                break
    
    """
    Receives a message using the RDT protocol.
    """
    def rdt_receive(self):
        while True:
            packet = self.udt_receive()
            success, seqnum, data = extract_data(packet)
            if success:
                if seqnum == self.seqnum:
                    break # Success!
                self.udt_send(ACK) # Sender is retransmitting an old packet
            else:
                self.udt_send(NAK) # We received a corrupted packet
        self.udt_send(ACK)
        self.flip_seqnum()
        return data
    
    def rdt_receive_text(self):
        return self.rdt_receive().decode()
