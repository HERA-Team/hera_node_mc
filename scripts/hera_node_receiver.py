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
from node_control import __version__, __package__, status_node, udp_sndrcv


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
serverAddress = '0.0.0.0'
redisAddress = 'redishost'
# define socket for binding; necessary for receiving data from Arduino

# Instantiate redis object connected to redis server running on localhost
r = redis.StrictRedis(host=redisAddress)
r.hmset("version:{}:{}".format(__package__, os.path.basename(__file__)),
        {"version": __version__,
         "timestamp": datetime.datetime.now().isoformat()})
rcvr = udp_sndrcv.UdpSenderReceiver(serverAddress, sndrcv='receive')
try:
    while True:
        r.set(script_redis_key, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        data, addr = rcvr.client_socket.recvfrom(1024)
        data_dict = status_node.status_node(data, addr)
        r.hmset(f"status:node:{data_dict['node_ID']}", data_dict)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
