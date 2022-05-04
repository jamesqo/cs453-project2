import argparse
import sys

from rdt_sock import RDTSocket
from utils import *

def parse_metadata(metadata_msg):
    lines = metadata_msg.splitlines()
    d = {}
    for line in lines:
        k, v = line.split(': ')
        d[k] = v
    return d

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server_name', type=str, default='date.cs.umass.edu')
    parser.add_argument('-p', dest='port_number', type=int, default=8888)
    args = parser.parse_args()

    ## Create a UDP connection to (server_name, port_number)
    sock = RDTSocket(args.server_name, args.port_number)

    sock.send("Hello, world!")
    check_response(sock, "Hello, world!")

    ## Name ourselves jlk-receiver
    sock.send("NAME jlk-receiver")
    check_response(sock, "OK Hello jlk-receiver\n")

    ## Wait for a message from jlk-sender

    msg = sock.receive()
    metadata = parse_metadata(msg)

    ## Receive the contents of the file

    dest_file = metadata['dest_file']
    if dest_file == 'stdout':
        f = sys.stdout
    else:
        f = open(dest_file, 'wb')
    
    try:
        while True:
            msg = sock.receive(binary=True)

            if msg.decode() == EOF_MARKER:
                break

            f.write(msg)
    except:
        if dest_file != 'stdout':
            f.close()
        raise

    ## Quit the session

    sock.send("QUIT")
    check_response(sock, "OK Bye\n")

if __name__ == '__main__':
    main()
