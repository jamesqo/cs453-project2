import argparse
import time

from rdt_sock import RDTSocket
from utils import *

def parse_users(list_msg):
    PREFIX = "OK LIST = "
    assert list_msg.startswith(PREFIX)
    list_msg = list_msg.lstrip(PREFIX)
    user_strs = list_msg.split(' ')
    
    users = []
    for user_str in user_strs:
        # There's a trailing '\\n' in the response message for some reason
        if '/' not in user_str:
            continue
        name, ipaddr = user_str.split('/')
        users.append({'name': name, 'ipaddr': ipaddr})
    return users

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='server_name', type=str, default='date.cs.umass.edu')
    parser.add_argument('-p', dest='port_number', type=int, default=8888)
    parser.add_argument('-t', dest='filenames', nargs=2)
    args = parser.parse_args()

    ## Create a UDP connection to (server_name, port_number)
    sock = RDTSocket(args.server_name, args.port_number)

    sock.send("Hello, world!")
    check_response(sock, "Hello, world!")

    ## Name ourselves jlk-sender
    sock.send("NAME jlk-sender")
    check_response(sock, "OK Hello jlk-sender\n")

    if args.filenames is not None:
        source_file = args.filenames[0]
        dest_file = args.filenames[1]
    else:
        source_file = 'stdin'
        dest_file = 'stdout'
    
    ## Every 5 seconds, issue a LIST command to the server and look for a user named jlk-receiver.

    while True:
        sock.send("LIST")
        msg = sock.receive()
        users = parse_users(msg)

        receiver = next((u for u in users if u['name'] == 'jlk-receiver'), None)
        if receiver is not None:
            break
        time.sleep(5)
    
    ## Connect to jlk-receiver

    receiver_addr = receiver['ipaddr']
    sock.send(f"CONN {receiver_addr}")
    check_response(sock, f"OK Relaying to /{receiver_addr}\n")

    ## Send metadata about the file

    metadata = '\n'.join([
        f"source_file: {source_file}",
        f"dest_file: {dest_file}"
    ])
    sock.send(metadata)

    ## Send the contents of the file

    if source_file == 'stdin':
        ## Send the contents of stdin line-by-line until Ctrl+C is pressed
        while True:
            try:
                next_line = input()
                sock.send(next_line)
            except KeyboardInterrupt:
                break
    else:
        ## Send all of the contents at once
        with open(source_file, 'rb') as f:
            sock.send(f.read(), binary=True)
    
    ## Send a special message to indicate EOF

    sock.send(EOF_MARKER)
    
    ## Switch out of relay mode

    sock.send(".")
    check_response(sock, "OK Not relaying\n")
    
    ## Quit the session

    sock.send("QUIT")
    check_response(sock, "OK Bye\n")

if __name__ == '__main__':
    main()
