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
    sock = RDTSocket(args.server_name, args.port_number, timeout=10)

    ## Oil check
    sock.udt_send_and_wait(
        "Hello, world!",
        "Hello, world!"
    )

    ## Name ourselves jlk-receiver
    sock.udt_send_and_wait(
        "NAME jlk-receiver",
        "OK Hello jlk-receiver\n"
    )

    ## Wait for a message from jlk-sender

    msg = sock.rdt_receive_text()
    metadata = parse_metadata(msg)

    ## Receive the contents of the file

    dest_file = metadata['dest_file']
    if dest_file == 'stdout':
        f = sys.stdout
    else:
        f = open(dest_file, 'wb')
    
    try:
        while True:
            msg = sock.rdt_receive_text()

            if msg.decode() == "<EOF>":
                break

            f.write(msg)
    except:
        if dest_file != 'stdout':
            f.close()
        raise

    ## Quit the session

    sock.udt_send_and_wait(
        "QUIT",
        "OK Bye\n"
    )

if __name__ == '__main__':
    main()
