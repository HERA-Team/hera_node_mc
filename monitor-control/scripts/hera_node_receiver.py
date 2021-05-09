#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key. <hera_node_receiver>
"""
from __future__ import print_function
import datetime
import redis
import socket
import sys
import os
from node_control import __version__, __package__, status_node


def noneify(v, noneval=-99.0):
    """
    Return None if v==noneval. Else return v.
    """
    if v == noneval:
        return 'None'
    else:
        return v


hostname = socket.gethostname()
script_redis_key = "status:script:{}:{}".format(hostname, __file__)

heartbeat = 60

# Define rcvPort for socket creation
rcvPort = 8889
serverAddress = '0.0.0.0'
redisAddress = 'redishost'
redisPort = 6379
# define socket for binding; necessary for receiving data from Arduino
localSocket = (serverAddress, rcvPort)

# Instantiate redis object connected to redis server running on localhost
r = redis.StrictRedis(host=redisAddress, port=redisPort)
r.hmset("version:{}:{}".format(__package__, os.path.basename(__file__)),
        {"version": __version__,
         "timestamp": datetime.datetime.now().isoformat()})

# Create a UDP socket
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set these options so multiple processes can connect to this socket
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created", file=sys.stderr)
except socket.error as msg:
    print('Failed to create socket. Error Code : {}  Message {}'.format(msg[0], msg[1]),
          file=sys.stderr)
    sys.exit()

# Bind socket to local host and port
try:
    client_socket.bind(localSocket)
    print('Bound socket', file=sys.stderr)
except socket.error as msg:
    print('Bind failed. Error Code : {}  Message {}'.format(msg[0], msg[1]), file=sys.stderr)
    sys.exit()

try:
    while True:
        r.set(script_redis_key, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        data, addr = client_socket.recvfrom(1024)
        data_dict = status_node.status_node(data, addr)
        r.hmset(f"status:node:{data_dict['node_ID']}", data_dict)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
