import argparse
import time

from rdt_sock import RDTSocket

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

    ## Create a connection socket for (server_name, port_number)
    sock = RDTSocket(args.server_name, args.port_number) # timeout=10

    ## Oil check
    print("Checking oil...")
    sock.udt_send_and_wait(
        "Hello, world!",
        "Hello, world!"
    )

    ## Name ourselves jlk-sender
    print("Naming ourselves jlk-sender...")
    sock.udt_send_and_wait(
        "NAME jlk-sender",
        "OK Hello jlk-sender\n"
    )

    if args.filenames is not None:
        source_file = args.filenames[0]
        dest_file = args.filenames[1]
    else:
        source_file = 'stdin'
        dest_file = 'stdout'
    
    ## Every 5 seconds, issue a LIST command to the server and look for a user named jlk-receiver.

    while True:
        print("Looking for receiver...")
        msg = sock.udt_send_and_wait("LIST").decode()
        users = parse_users(msg)

        receiver = next((u for u in users if u['name'] == 'jlk-receiver'), None)
        if receiver is not None:
            break
        time.sleep(5)
    
    ## Connect to jlk-receiver

    print("Found receiver!")
    receiver_addr = receiver['ipaddr']
    sock.udt_send_and_wait(
        f"CONN {receiver_addr}",
        f"OK Relaying to /{receiver_addr}\n"
    )

    ## Send metadata about the file

    print("Sending file metadata...")
    file_contents = None
    content_length = None
    if source_file != 'stdin':
        with open(source_file, 'rb') as f:
            file_contents = f.read()
            content_length = len(file_contents)

    metadata = [
        f"source_file: {source_file}",
        f"dest_file: {dest_file}"
    ]
    if content_length is not None:
        metadata += [f"content_length: {content_length}"]
    metadata = '\n'.join(metadata)
    sock.rdt_send(metadata)

    ## Send the contents of the file

    print("Sending file contents...")
    if source_file == 'stdin':
        ## Send the contents of stdin line-by-line until Ctrl+C is pressed
        while True:
            try:
                next_line = input()
                sock.rdt_send(next_line)
            except KeyboardInterrupt:
                break
    else:
        ## Send all of the contents at once
        sock.rdt_send(file_contents)
    
    ## Send a special message to indicate EOF

    sock.rdt_send("<EOF>")
    
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
