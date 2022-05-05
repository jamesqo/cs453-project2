import argparse
import sys

from rdt_sock import RDTSocket

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

    ## Create a connection socket for (server_name, port_number)
    sock = RDTSocket(args.server_name, args.port_number)

    try:
        ## Oil check
        print("Checking oil...")
        sock.udt_send_and_wait(
            "Hello, world!",
            "Hello, world!"
        )

        ## Name ourselves jlk-receiver
        print("Naming ourselves jlk-receiver...")
        sock.udt_send_and_wait(
            "NAME jlk-receiver",
            "OK Hello jlk-receiver\n"
        )

        ## Wait for metadata from jlk-sender

        def setup_sender(msg):
            print("Setting up connection to sender...")
            metadata = parse_metadata(msg.decode())
            sender_addr = metadata['sender_addr']
            # For debugging: flush out all of the messages currently in the queue
            # It's possible that a bunch of metadata messages from the sender may have queued up.
            sock.flush_pending_messages()
            sock.udt_send_and_wait(
                f"CONN {sender_addr}",
                f"OK Relaying to /{sender_addr}\n"
            )

        print("Receiving metadata...")
        # During the very first rdt_receive(), we need to tell the server to CONN to sender_addr
        # before attempting to respond with an ACK, otherwise the ACK won't be relayed to the sender and it'll
        # simply be echoed back to us.
        # In the scenario where we receive a corrupted packet with a garbled IP address, we will fail to parse it.
        # After not hearing back from us for a while, the sender will re-transmit the packet.
        # It will continue doing this until it sends us an uncorrupted packet that we can parse and establish a connection with.
        msg = sock.rdt_receive(setup_sender=setup_sender).decode()
        metadata = parse_metadata(msg)

        dest_file = metadata['dest_file']
        if dest_file == 'stdout':
            f = sys.stdout
        else:
            f = open(dest_file, 'wb')

        ## Receive the file contents

        print("Receiving file contents...")    
        try:
            while True:
                msg = sock.rdt_receive()

                if msg.decode() == "<EOF>":
                    break

                f.write(msg)
        finally:
            if dest_file != 'stdout':
                f.close()
    finally:
        sock.flush_pending_messages()

        ## Switch out of relay mode

        print("Switching out of relay mode...")
        sock.udt_send_and_wait(
            ".",
            "OK Not relaying\n"
        )

        ## Quit the session

        print("Quitting...")
        sock.udt_send_and_wait(
            "QUIT",
            "OK Bye\n"
        )

    print("Done.")

if __name__ == '__main__':
    main()
