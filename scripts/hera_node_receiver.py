#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key. <hera_node_receiver>
"""
from __future__ import print_function
import sys
from node_control import __version__, __package__, status_node, send_receive, node_control


def noneify(v, noneval=-99.0):
    """
    Return None if v==noneval. Else return v.
    """
    if v == noneval:
        return 'None'
    else:
        return v


script_redis_key = "status:script:{}:{}".format(send_receive.this_host, __file__)
heartbeat = 60

# Instantiate redis object connected to redis server running on localhost
r = node_control.get_redis_client('redishost')
rkey, rval = node_control.get_service_redis_entry(__file__, __package__, __version__)
r.hmset(rkey, rval)

# Make udp object
rcvr = send_receive.UdpSenderReceiver(send_receive.serverAddress, sndrcv='receive')

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
