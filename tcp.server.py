#!/usr/bin/python

import socket
import atexit
import os

# import pEp, Django...

from pprint import pformat
from _thread import *

server = socket.socket()
host = "127.0.0.1"
port = 1337


def threaded_client(conn):
    peer = conn.getpeername()
    print(f"Thread started: {peer[0]}:{peer[1]}")
    conn.send(str.encode("Mail please!\n"))
    while True:
        data = conn.recv(4096)
        if not data:
            conn.close()
            break
        try:
            data = data.decode("utf8")
            print("IN: " + data.strip())
            reply = "Server Says: " + data
            conn.sendall(str.encode(reply))
            # TODO: import pEpGatemain, process "data"
        except:
            print(f"Closing connection: {peer[0]}:{peer[1]}")
            conn.close()
            break
    print(f"Thread ended: {peer[0]}:{peer[1]}")


def cleanup():
    print("Cleanup")
    global server
    server.close()


atexit.register(cleanup)

try:
    server.bind((host, port))
except socket.error as e:
    print(str(e))
    exit(1)

print("Server ready!")
server.listen(5)

while True:
    client, address = server.accept()
    print("Connection from: " + address[0] + ":" + str(address[1]))
    start_new_thread(threaded_client, (client,))
