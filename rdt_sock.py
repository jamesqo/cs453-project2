import hashlib
import select
import socket

DATA_PREFIX = b'data|'
ACK = b'ack'
NAK = b'nak'

"""
Creates an RDT packet from binary data, its MD5 checksum and a sequence number.
"""
def make_packet(seqnum, data):
    if isinstance(data, str):
        data = data.encode()
    checksum = hashlib.md5(data).digest()
    return b'data|' + str(seqnum).encode() + b'|' + checksum + b'|' + data

"""
Extracts data from an RDT packet.
Returns (success, seqnum, data) where success indicates successful extraction, seqnum is the sequence number, and data is the data.
"""
def extract_data(packet):
    if not packet.startswith(DATA_PREFIX):
        return False, None, None
    packet = packet[len(DATA_PREFIX):]

    if packet[0] == ord('0'):
        seqnum = 0
    elif packet[0] == ord('1'):
        seqnum = 1
    else:
        return False, None, None # Corrupted seqnum

    checksum = packet[2:18]
    data = packet[19:]
    if hashlib.md5(data).digest() != checksum:
        return False, None, None # Corrupted data or checksum

    return True, seqnum, data

class RDTSocket:
    def __init__(self, server, port, bufsize=2048, udt_timeout=None):
        self.server = server
        self.port = port
        self.bufsize = bufsize
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if udt_timeout is not None:
            self.udp_sock.settimeout(udt_timeout)
        self.seqnum = 0
    
    def flip_seqnum(self):
        self.seqnum = (1 - self.seqnum)
    
    def udt_send(self, message):
        if isinstance(message, str):
            message = message.encode()
        print(f"Sending: {repr(message)}")
        self.udp_sock.sendto(message, (self.server, self.port))
    
    def udt_receive(self):
        message = self.udp_sock.recv(self.bufsize)
        print(f"Receiving: {repr(message)}")
        return message
    
    """
    Sends message and waits for server to respond, re-sending message as needed.
    Optionally verifies that the server's response matches the string expected_response, repeating if not.
    """
    def udt_send_and_wait(self, message, expected_response=None):
        while True:
            try:
                self.udt_send(message)
                response = self.udt_receive()
                break
            except socket.timeout:
                continue
        if expected_response is not None:
            if response != expected_response.encode():
                print(f"WARNING: Expected response msg of {repr(expected_response)}, but got {repr(response)}")
        return response

    """
    Sends a message using the RDT protocol.
    """
    def rdt_send(self, message):
        packet = make_packet(seqnum=self.seqnum, data=message)
        while True:
            try:
                self.udt_send(packet)
                ack = self.udt_receive()
            except socket.timeout:
                continue

            if ack == ACK:
                break
        self.flip_seqnum()
    
    """
    Receives a message using the RDT protocol.
    setup_sender is used to set up a connection to the sender when this function is called for the first time.
    """
    def rdt_receive(self, setup_sender=None):
        # During the first time around, we don't try sending ACKs/NAKs back until the sender is set up properly.
        firsttime = setup_sender is not None

        while True:
            packet = self.udt_receive()
            success, seqnum, data = extract_data(packet)
            if success:
                if seqnum == self.seqnum:
                    break # Success!
                if not firsttime:
                    self.udt_send(ACK) # Sender is retransmitting an old packet
            elif not firsttime:
                self.udt_send(NAK) # We received a corrupted packet
        if firsttime:
            setup_sender(data)
        self.udt_send(ACK)
        self.flip_seqnum()
        return data
    
    def can_read(self):
        rlist, _, _ = select.select([self.udp_sock], [], [], 0)
        return len(rlist) > 0
    
    def flush_pending_messages(self):
        while self.can_read():
            _ = self.udt_receive()
